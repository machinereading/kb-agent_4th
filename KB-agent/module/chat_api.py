import json
import urllib3
import copy
import pymysql
from flask import Flask, request, jsonify

import NLU
import Entity_Summarization
import Dialog_Manager

class_dict = {'level_1': ['Disease', 'Event', 'Food', 'Place', 'Species', 'Work'],
				'level_2': ['Sport', 'Organisation', 'Person', 'PopulatedPlace', 'Film', 'MusicalWork'],
				'level_3': ['FictionalCharacter', 'Company', 'SportsTeam', 'Artist', 'Athlete', 'Scientist', 'Writer',
							  'SportsEvent', 'Settlement'],
				'level_4': ['College', 'University', 'School', 'MusicalArtist', 'Station']}
#start_question_list = ['어느 대학에 관심이 있나요?']
prior_property_file = 'prior_property.json'
#stop_word = ['끝']
#logout_word = ['로그아웃']

def NLG(triple_list, dialogAct):
	answer_list = []
	for ele in triple_list:
		if 'abstract' in ele:
			triple_list.remove(ele)
	if dialogAct == 'Knowledge_inform':
		for triple in triple_list:
			s, p, o = triple.split('\t')
			s = s.split('/')[-1].rstrip('>')
			p = p.split('/')[-1].rstrip('>')
			if 'http://kbox' in o:
				o = o.split('/')[-1].rstrip('>')
			answer_list.append(s+'의 '+p+'는 '+o+'에요.')
	elif dialogAct == 'Knowledge_question':
		for triple in triple_list:
			s, p, o = triple.split('\t')
			s = s.split('/')[-1].rstrip('>')
			p = p.split('/')[-1].rstrip('>')
			answer_list.append(s+'의 '+p+'를 알려주세요.')
	elif dialogAct == 'greeting':
		for triple in triple_list:
			s, p, o = triple.split()
			answer_list.append(o+' 님, 안녕하세요.')

	return answer_list


def ETRI_NER(YOUR_SENTENCE):
	openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"
	accessKey = "abfa1639-8789-43e0-b1da-c29e46b431db"
	analysisCode = "ner"
	text = YOUR_SENTENCE

	if (text == ''): return []
	requestJson = {
		"access_key": accessKey,
		"argument": {
			"text": text,
			"analysis_code": analysisCode
		}
	}

	http = urllib3.PoolManager()
	response = http.request(
		"POST",
		openApiURL,
		headers={"Content-Type": "application/json; charset=UTF-8"},
		body=json.dumps(requestJson)
	)

	result = json.loads(str(response.data, "utf-8"))
	NE_list = result["return_object"]["sentence"][0]["NE"]
	result = list()
	for NE in NE_list:
		result.append([NE['text'], NE['type']])
	# print(result)
	return result


def DialogDBaccess(data):
	conn = pymysql.connect(host='143.248.135.146', port=3142, user='flagship', passwd='kbagent', db='dialogDB',
						   charset='utf8')
	curs = conn.cursor()
	result = None
	if data['mode'] == 'make_table':
		sql = "CREATE TABLE IF NOT EXISTS " + data['user_id'] + " LIKE dialog"
		curs.execute(sql)
	elif data['mode'] == 'add_data':
		sql = "INSERT INTO " + data['user_id'] + " (utterance, date_time, speaker) VALUES(%s, now(), %s)"
		curs.execute(sql, (data['utterance'], data['speaker']))
		result = curs.lastrowid

	conn.commit()
	curs.close()
	conn.close()

	return result

app = Flask(__name__)

@app.route('/', methods = ['POST'])
def main():
	with open(prior_property_file) as json_file:
		prior_property_dict = json.load(json_file)

	dialogDB_json = {}

	input_json = request.get_json()
	print(input_json)
	user_ID = input_json['user_id']
	userDB_json = {'userID': user_ID, 'command': 'LOGIN'}
	userDB_response = Dialog_Manager.UserDBaccess(userDB_json)

	KB_language = {
		'user_ID': user_ID,
		'entities': [],
		'frames': [],
		'triples': []
	}

	result_json = {'user_id': user_ID, 'frames': [], 'entities': [], 'q_list': [], 'knowledge': []}

	user_input = input_json['utterance']
	dialogDB_json['user_id'] = KB_language['user_ID']
	dialogDB_json['utterance'] = user_input
	dialogDB_json['speaker'] = 'user'
	dialogDB_json['mode'] = 'make_table'
	dialog_index = DialogDBaccess(dialogDB_json)

	dialogDB_json['mode'] = 'add_data'
	dialogDB_json['utterance'] = user_input
	dialogDB_json['speaker'] = 'user'
	dialog_index = DialogDBaccess(dialogDB_json)

	if not input_json['q_list'] and not input_json['knowledge']:
		NLU_response = NLU.Frame_Interpreter(user_input)
		#frame기반
		if NLU_response['frames']:
			KB_language['frames'] = NLU_response['frames']
			result_json['frames'] = KB_language['frames']
			now_frame = KB_language['frames'][-1]
			question_list = []
			with open('./frame_info_full.json', 'r', encoding='utf-8') as f:
				frame_json_data = json.load(f)
				frame_data = frame_json_data[now_frame['frame']]
				for ele in frame_data['arguments']:
					if ele['coreType'] == 'Core':
						question_list.append(ele['fe'])
			for exi_ele in now_frame['ele']:
				if exi_ele in question_list:
					question_list.remove(exi_ele)
			if question_list:
				result_json['q_list'] = question_list
				system_output = \
					NLG([now_frame['frame'] + '\t' + question_list[0] + '\t' + '?o'],
						'Knowledge_question')[0]
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
			else:
				system_output = '감사합니다.'
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
		#entity기반
		elif NLU_response['entities']:
			KB_language['entities'] = NLU_response['entities']
			result_json['entities'] = KB_language['entities']
			KBM_response = Entity_Summarization.ES(KB_language['entities'][0]['text'])
			KB_language['triples'] = KBM_response
			utterances = NLG(KB_language['triples'], 'Knowledge_inform')
			system_output = ''
			for candi in utterances:
				if 'wiki' in candi or 'abstract' in candi:
					continue
				system_output += candi
			tmp_list = []
			for ele in NLU_response['entities'][0]['type']:
				if 'http://dbpedia.org/ontology/' in ele:
					tmp_list.append(ele.split('/')[-1])
			KB_language['entities'][0]['type'] = copy.deepcopy(tmp_list)
			for tmp_class in KB_language['entities'][0]['type']:
				if tmp_class in class_dict['level_4']:
					entity_class = tmp_class
					break
				elif tmp_class in class_dict['level_3']:
					entity_class = tmp_class
					break
				elif tmp_class in class_dict['level_2']:
					entity_class = tmp_class
					break
				elif tmp_class in class_dict['level_1']:
					entity_class = tmp_class
					break
			question_list = []
			question_property_list = prior_property_dict[entity_class]
			question_num = 0
			for candi_question in question_property_list:
				if question_num == 3:
					break
				tmp_user_query = Dialog_Manager.SPARQL_Generation('ASK', [KB_language['entities'][0]['uri'], candi_question, '?o'], KB_language['user_ID'])
				tmp_master_query = Dialog_Manager.SPARQL_Generation('ASK', [KB_language['entities'][0]['uri'], candi_question, '?o'], "")
				userDB_json['query'] = tmp_user_query
				userDB_json['command'] = 'QUERY'
				#print(UserDBaccess(userDB_json))
				if not Dialog_Manager.MasterDBaccess(tmp_master_query) and not Dialog_Manager.UserDBaccess(userDB_json)['query_result']:
					question_list.append([KB_language['entities'][0]['text'], candi_question, '?o'])
					question_num += 1
			if question_list:
				result_json['q_list'] = question_list
				system_output += '\n' + KB_language['entities'][0]['text'] + '에 대해서 몇 가지 물어보고 싶은게 있어요.'
				system_output += '\n'+NLG([question_list[0][0]+'\t'+question_list[0][1]+'\t'+question_list[0][2]], 'Knowledge_question')[0]
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
			else:
				system_output = '감사합니다.'
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
		else:
			system_output = '제가 아직 이해할 수 없는 문장이에요.'
			result_json['utterance'] = system_output
			dialogDB_json['utterance'] = system_output
			dialogDB_json['speaker'] = 'system'
			dialog_index = DialogDBaccess(dialogDB_json)
	elif input_json['q_list']:
		dialogDB_json['utterance'] = user_input
		dialogDB_json['speaker'] = 'user'
		dialog_index = DialogDBaccess(dialogDB_json)
		if input_json['frames']:
			result_json['frames'] = input_json['frames']
			tmp_user_answer = ETRI_NER(user_input)
			tmp_knowledge_list = input_json['knowledge']
			if tmp_user_answer:
				tmp_knowledge_list.append(tmp_user_answer[0][0])
			result_json['knowledge'] = tmp_knowledge_list
			result_json['q_list'] = input_json['q_list']
			del result_json['q_list'][0]
			if result_json['q_list']:
				now_frame = input_json['frames'][-1]
				system_output = \
					NLG([now_frame['frame'] + '\t' + result_json['q_list'][0] + '\t' + '?o'],
						'Knowledge_question')[0]
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
			else:
				if input_json['knowledge']:
					#frame지식저장
					system_output = '감사합니다'
					result_json['frames'] = []
					result_json['entities'] = []
					result_json['knowledge'] = []
					result_json['utterance'] = system_output
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
				else:
					system_output = '감사합니다'
					result_json['frames'] = []
					result_json['entities'] = []
					result_json['utterance'] = system_output
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
		elif input_json['entities']:
			result_json['entities'] = input_json['entities']
			tmp_user_answer = ETRI_NER(user_input)
			new_triple = []
			tmp_knowledge_list = input_json['knowledge']
			result_json['q_list'] = input_json['q_list']
			if tmp_user_answer:
				new_triple.append('http://kbox.kaist.ac.kr/resource/' + result_json['q_list'][0][0] + '\t' + result_json['q_list'][0][
					1] + '\thttp://kbox.kaist.ac.kr/resource/' + tmp_user_answer[0][0])
				new_triple.append('http://kbox.kaist.ac.kr/resource/' + result_json['q_list'][0][0] + result_json['q_list'][0][
					1] + 'http://kbox.kaist.ac.kr/resource/' + tmp_user_answer[0][
									  0] + '\thttp://kbox.kaist.ac.kr/flagship/dialogid\thttp://ko.dbpedia.org/resource/' + str(
					dialog_index))
				s1, p1, o1 = new_triple[0].split('\t')
				s2, p2, o2 = new_triple[1].split('\t')
				tmp_knowledge_list.append([s1, p1, o1])
				tmp_knowledge_list.append([s2, p2, o2])
			result_json['knowledge'] = tmp_knowledge_list
			del result_json['q_list'][0]
			if result_json['q_list']:
				system_output = '\n' + NLG(
					[result_json['q_list'][0][0] + '\t' + result_json['q_list'][0][1] + '\t' + result_json['q_list'][0][2]],
					'Knowledge_question')[0]
				result_json['utterance'] = system_output
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)
			else:
				if result_json['knowledge']:
					system_output = ''
					for triple in result_json['knowledge']:
						if 'flagship/dialogid' not in triple:
							system_output += NLG(['\t'.join(triple)], 'Knowledge_inform')[0] + '\n'
					userDB_json['command'] = 'REGISTER'
					userDB_json['triple'] = result_json['knowledge']
					Dialog_Manager.UserDBaccess(userDB_json)
					result_json['entities'] = []
					result_json['knowledge'] = []
					system_output += '감사합니다'
					result_json['utterance'] = system_output
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
				else:
					result_json['entities'] = []
					system_output = '감사합니다'
					result_json['utterance'] = system_output
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
		else:
			print('input error')
			result_json = input_json
			result_json['utterance'] = 'input error'
	else:
		print('input error')
		result_json = input_json
		result_json['utterance'] = 'input error'

	return jsonify(result_json)

if __name__ == "__main__":
	app.run()

