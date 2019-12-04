import json
import requests
import urllib3
from urllib.parse import urlencode


def SPARQL_Generation(Qtype, triple, user_id):
	s, p, o = triple
	if s[0] == '?':
		target = s
		p = '<' + p + '>'
		o = '<' + o + '>'
	elif p[0] == '?':
		target = p
		s = '<' + s + '>'
		o = '<' + o + '>'
	elif o[0] == '?':
		s = '<' + s + '>'
		p = '<' + p + '>'
		target = o
	result_query = Qtype
	if Qtype == 'SELECT':
		result_query = result_query + ' ' + target
	if user_id:
		result_query = result_query + ' where { graph <http://kbox.kaist.ac.kr/username/' + user_id + '> { ' + s + ' ' + p + ' ' + o + ' } }'
	else:
		result_query = result_query + ' where { ' + s + ' ' + p + ' ' + o + ' }'

	return result_query

def UserDBaccess(userDB_json):
	userID = userDB_json['userID']
	command = userDB_json['command']
	targetURL = "http://kbox.kaist.ac.kr:6121/flagship"
	requestJson = {
		'user_id': userID,
		'command': command,
	}
	headers = {'Content-Type': 'application/json; charset=utf-8'}

	if command == 'QUERY':
		requestJson['query'] = userDB_json['query']
	elif command == 'REGISTER':
		requestJson['triple'] = userDB_json['triple']

	print(requestJson)
	response = requests.post(targetURL, headers=headers, data=json.dumps(requestJson))
	print("[responseCode] " + str(response.status_code))
	if command == 'REGISTER':
		result = None
	else:
		result = response.json()

	return result


def MasterDBaccess(query):
	server = 'http://kbox.kaist.ac.kr:5820/myDB/'

	values = urlencode({'query': query})
	http = urllib3.PoolManager()
	#print(query)

	headers = {
		'Content-Type': 'application/x-www-form-urlencoded, application/sparql-query, text/turtle',
		'Accept': 'text/turtle, application/rdf+xml, application/n-triples, application/trig, application/n-quads, '
				  'text/n3, application/trix, application/ld+json, '  # application/sparql-results+xml, '
				  'application/sparql-results+json, application/x-binary-rdf-results-table, text/boolean, text/csv, '
				  'text/tsv, text/tab-separated-values '
	}
	url = server + 'query?' + values
	r = http.request('GET', url, headers=headers)
	request = json.loads(r.data.decode('UTF-8'))
	#print(request)
	if 'SELECT' in query:
		result_list = request['results']['bindings']
	elif 'ASK' in query:
		result_list = request['boolean']

	return result_list

if __name__ == "__main__":
	MasterDBaccess()