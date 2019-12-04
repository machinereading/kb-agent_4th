import json
import requests
import csv
import urllib3



'''
	class_dict = {'level_1': ['Agent', 'Place'],
				  'level_2': [ 'Person', 'PopulatedPlace', 'Organisation'],
				  'level_3': ['EducationalInstitution', 'Settlement', 'Artist'],
				  'level_4': ['College', 'University', 'Actor', 'MusicalArtist', 'City', 'Town']}

	# print(ontology('PopulatedPlace'))

	result_dict = {}

	for list in class_dict.keys():
		for type in class_dict[list]:
			result_dict[type] = ontology(type)

	with open('prior_property.json', 'w') as f:
		f.write(json.dumps(result_dict, ensure_ascii=False, indent='\t'))

'''

'''
#Frame

targetURL = "http://wisekb.kaist.ac.kr:1106/FRDF"
headers = {'Content-Type': 'application/json; charset=utf-8'}
text = "나도 독일에서 지냈어."
requestJson = {
	"text": text
}
response = requests.post(targetURL, data=json.dumps(requestJson), headers=headers)
print("[responseCode] " + str(response.status_code))
print(response.json())
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
print(result_frame)
for now_frame in result_frame['frames']:
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
'''

'''DB test
conn = pymysql.connect(host='143.248.135.146', port=3142, user='flagship', passwd='kbagent', db='dialogDB', charset='utf8')
curs = conn.cursor()
table_name = "test_table"
sql = "CREATE TABLE IF NOT EXISTS " + table_name + " LIKE dialog"
curs.execute(sql)
conn.commit()

conn.close()
'''
