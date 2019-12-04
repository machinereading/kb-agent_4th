# -*- coding:utf-8 -*-
import requests
import json


# statement로부터 분석기(추후 FrameNet 추가)
def Frame_Interpreter(text):
	# ETRI NER API 사용
	'''
	openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"
	accessKey = "abfa1639-8789-43e0-b1da-c29e46b431db"
	analysisCode = "ner"
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
	#print("[responseCode] " + str(response.status))
	res_json = json.loads(str(response.data,"utf-8"))

	if res_json['return_object']['sentence'][0]['NE'] is None:
		print('없음')
	else:
		print(res_json['return_object']['sentence'][0]['NE'])
	'''
	#Kor_FrameNet
	targetURL = "http://wisekb.kaist.ac.kr:1106/FRDF"
	headers = {'Content-Type': 'application/json; charset=utf-8'}
	requestJson = {
		"text": text
	}
	response = requests.post(targetURL, data=json.dumps(requestJson), headers=headers)
	print("[responseCode] " + str(response.status_code))
	#print(response.json())
	result_json = response.json()
	result_frame = {'frames': []}
	if not result_json['textae']:
		print('no frame')
	else:
		for now_frame in result_json['textae']:
			ele_list = []
			if len(now_frame['denotations']) > 1:
				for i in range(1, len(now_frame['denotations'])):
					ele_list.append(now_frame['denotations'][i]['obj'])
			tmp_dict = {'frame': now_frame['frame'], 'lu': now_frame['lu'], 'ele': ele_list}
			result_frame['frames'].append(tmp_dict)
	#print(result_frame)

	# Entity Linking 사용
	targetURL = "http://wisekb.kaist.ac.kr:6120/entity_linking_plain/"
	requestJson = {
		"content": text
	}
	'''
			headers={
				"Accept": "application/json, text/plain, */*",
				"Content-Type": "application/json; charset = utf-8"
			},
	'''
	response = requests.post(targetURL, data=requestJson)
	print("[responseCode] " + str(response.status_code))

	result_frame['entities'] = response.json()[0]['entities']

	return result_frame



if __name__ == "__main__":
	print(Frame_Interpreter("로마에서 휴일을 보냈어."))
'''
	targetURL = "http://kbox.kaist.ac.kr:6121/flagship"
	requestJson = {
		'user_id': 'asm427',
		'command': 'QUERY',
		'triple': [['asm427', 'user_name', '상민']],
		'query': "select * where { <http://ko.dbpedia.org/resource/asm427> ?p ?o }"
	}
	headers = {'Content-Type': 'application/json; charset=utf-8'}
	response = requests.post(targetURL, headers=headers, data=json.dumps(requestJson))
	print("[responseCode] " + str(response.status_code))
	print(response.json())
'''