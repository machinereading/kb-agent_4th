import json
import urllib3
import copy
import pymysql

import NLU
import Entity_Summarization
import Dialog_Manager

class_dict = {'level_1': ['Disease', 'Event', 'Food', 'Place', 'Species', 'Work'],
				'level_2': ['Sport', 'Organisation', 'Person', 'PopulatedPlace', 'Film', 'MusicalWork'],
				'level_3': ['FictionalCharacter', 'Company', 'SportsTeam', 'Artist', 'Athlete', 'Scientist', 'Writer',
							  'SportsEvent', 'Settlement'],
				'level_4': ['College', 'University', 'School', 'MusicalArtist', 'Station']}
start_question_list = ['어느 대학에 관심이 있나요?']
prior_property_file = 'prior_property.json'
stop_word = ['끝']
logout_word = ['로그아웃']

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


if __name__ == "__main__":
	with open(prior_property_file) as json_file:
		prior_property_dict = json.load(json_file)

	stop = False

	dialogDB_json = {}

	while True:
		tmp_stop = False
		if stop:
			break
		print('User ID: ')
		user_ID = input()
		if user_ID == '끝':
			break
		userDB_json = {'userID': user_ID, 'command': 'LOGIN'}
		userDB_response = Dialog_Manager.UserDBaccess(userDB_json)
		print(userDB_response)
		if not userDB_response['user_name']:

			system_output = '첫 대화를 환영합니다. 이름을 알려주세요.'
			print(system_output)
			dialogDB_json = {'user_id': user_ID, 'mode': 'make_table'}
			DialogDBaccess(dialogDB_json)
			dialogDB_json['mode'] = 'add_data'
			dialogDB_json['utterance'] = system_output
			dialogDB_json['speaker'] = 'system'
			dialog_index = DialogDBaccess(dialogDB_json)
			user_name = input()
			if user_name == '끝':
				break
			dialogDB_json['utterance'] = user_name
			dialogDB_json['speaker'] = 'user'
			dialog_index = DialogDBaccess(dialogDB_json)
			userDB_json['command'] = 'REGISTER'
			userDB_json['triple'] = [['http://kbox.kaist.ac.kr/flagship/userid/' + user_ID, 'http://ko.dbpedia.org/property/user_name', 'http://ko.dbpedia.org/resource/'+user_name], ['http://kbox.kaist.ac.kr/flagship/userid/' + user_ID + 'http://ko.dbpedia.org/property/user_name' + 'http://ko.dbpedia.org/resource/'+user_name, 'http://kbox.kaist.ac.kr/flagship/dialogid', 'http://ko.dbpedia.org/resource/' + str(dialog_index)]]
			Dialog_Manager.UserDBaccess(userDB_json)
			Dialog_Manager.UserDBaccess(userDB_json)
		else:
			user_name = userDB_response['user_name']
		system_output = user_name+'님 안녕하세요!'
		print(system_output)
		dialogDB_json['mode'] = 'add_data'
		dialogDB_json['user_id'] = user_ID
		dialogDB_json['utterance'] = system_output
		dialogDB_json['speaker'] = 'system'
		dialog_index = DialogDBaccess(dialogDB_json)
		#first_system = start_question_list[random.randint(0, len(start_question_list)-1)]
		KB_language = {
			'user_ID': user_ID,
			'user_name': user_name,
			'entities': [],
			'frames': [],
			'triples': []
		}
		while True:
			if tmp_stop:
				break
			'''system initiative
			system_output = KB_language['user_name']+'님은 '+first_system
			print(system_output)
			dialogDB_json['mode'] = 'add_data'
			dialogDB_json['utterance'] = system_output
			dialogDB_json['speaker'] = 'system'
			dialog_index = DialogDBaccess(dialogDB_json)
			'''
			user_input = input()
			if user_input == '로그아웃':
				break
			elif user_input == '끝':
				stop = True
				break
			dialogDB_json['utterance'] = user_input
			dialogDB_json['speaker'] = 'user'
			dialog_index = DialogDBaccess(dialogDB_json)
			NLU_response = NLU.Frame_Interpreter(user_input)
			#frame기반
			if NLU_response['frames']:
				KB_language['frames'] = NLU_response['frames']
				#for now_frame in KB_language['frames']:
				now_frame = KB_language['frames'][-1]
				question_list = []
				with open('./frame_info_full.json', 'r', encoding='utf-8') as f:
					frame_json_data = json.load(f)
					frame_data = frame_json_data[now_frame['frame']]
					for ele in frame_data['arguments']:
						if ele['coreType'] == 'Core':
							question_list.append(ele['fe'])
				print(question_list)
				for exi_ele in now_frame['ele']:
					if exi_ele in question_list:
						question_list.remove(exi_ele)
				print(question_list)
				if question_list:
					single_answer_list = []
					for single_question in question_list:
						system_output = \
						NLG([now_frame['frame'] + '\t' + single_question + '\t' + '?o'],
							'Knowledge_question')[0]
						print(system_output)
						dialogDB_json['utterance'] = system_output
						dialogDB_json['speaker'] = 'system'
						dialog_index = DialogDBaccess(dialogDB_json)
						user_input = input()
						if user_input == '로그아웃':
							tmp_stop = True
							break
						elif user_input == '끝':
							stop = True
							tmp_stop = True
							break
						dialogDB_json['utterance'] = user_input
						dialogDB_json['speaker'] = 'user'
						dialog_index = DialogDBaccess(dialogDB_json)
						single_answer_list.append(user_input)
						tmp_user_answer = ETRI_NER(single_answer_list[-1])
					system_output = '감사합니다.'
					print(system_output)
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
				else:
					system_output = '그렇군요.'
					print(system_output)
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
			#entity 기반
			elif NLU_response['entities']:
				KB_language['entities'] = NLU_response['entities']
				KBM_response = Entity_Summarization.ES(KB_language['entities'][0]['text'])
				KB_language['triples'] = KBM_response
				utterances = NLG(KB_language['triples'], 'Knowledge_inform')
				for system_output in utterances:
					if 'wiki' in system_output or 'abstract' in system_output:
						continue
					print(system_output)
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
				utterances = []
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
					system_output = KB_language['entities'][0]['text']+'에 대해서 몇 가지 물어보고 싶은게 있어요.'
					print(system_output)
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
					single_answer_list = []
					new_triple = []
					for single_question in question_list:
						system_output = NLG([single_question[0]+'\t'+single_question[1]+'\t'+single_question[2]], 'Knowledge_question')[0]
						print(system_output)
						dialogDB_json['utterance'] = system_output
						dialogDB_json['speaker'] = 'system'
						dialog_index = DialogDBaccess(dialogDB_json)
						user_input = input()
						if user_input == '로그아웃':
							tmp_stop = True
							break
						elif user_input == '끝':
							stop = True
							tmp_stop = True
							break
						dialogDB_json['utterance'] = user_input
						dialogDB_json['speaker'] = 'user'
						dialog_index = DialogDBaccess(dialogDB_json)
						single_answer_list.append(user_input)
						tmp_user_answer = ETRI_NER(single_answer_list[-1])
						if tmp_user_answer:
							new_triple.append('http://kbox.kaist.ac.kr/resource/'+single_question[0]+'\t'+single_question[1]+'\thttp://kbox.kaist.ac.kr/resource/'+tmp_user_answer[0][0])
							new_triple.append('http://kbox.kaist.ac.kr/resource/'+single_question[0]+single_question[1]+'http://kbox.kaist.ac.kr/resource/'+tmp_user_answer[0][0]+'\thttp://kbox.kaist.ac.kr/flagship/dialogid\thttp://ko.dbpedia.org/resource/' + str(dialog_index))
					if new_triple:
						triples =[]
						for ele in new_triple:
							#print(ele)
							if 'flagship/dialogid' not in ele:
								system_output = NLG([ele], 'Knowledge_inform')[0]
								print(system_output)
								dialogDB_json['utterance'] = system_output
								dialogDB_json['speaker'] = 'system'
								dialog_index = DialogDBaccess(dialogDB_json)
							s, p, o = ele.split('\t')
							triples.append([s, p, o])
					system_output = '감사합니다.'
					print(system_output)
					dialogDB_json['utterance'] = system_output
					dialogDB_json['speaker'] = 'system'
					dialog_index = DialogDBaccess(dialogDB_json)
					if tmp_stop:
						break
					else:
						if triples:
							userDB_json['command'] = 'REGISTER'
							userDB_json['triple'] = triples
							Dialog_Manager.UserDBaccess(userDB_json)
			else:
				system_output = '제가 아직 이해할 수 없는 문장이에요.'
				print(system_output)
				dialogDB_json['utterance'] = system_output
				dialogDB_json['speaker'] = 'system'
				dialog_index = DialogDBaccess(dialogDB_json)

			#while first_system in KB_language['start_question']:
			#first_system = start_question_list[random.randint(0, len(start_question_list) - 1)]

			#KB_language['start_question'].append(first_system)
