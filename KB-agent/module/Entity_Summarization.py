# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode
import urllib3

main_server = 'http://kbox.kaist.ac.kr:5820/myDB/'
entity_summaryURL = 'http://133.186.162.38:5000/summary'


def select(entity):
	server = main_server

	query = """select distinct (<http://kbox.kaist.ac.kr/resource/""" + entity + """> as ?s) ?p ?o ?kb
    where {
      {  <http://kbox.kaist.ac.kr/resource/""" + entity + """> ?p ?o.  }
        union
      {  <http://kbox.kaist.ac.kr/resource/""" + entity + """> owl:sameAs ?ko.  ?ko ?p ?o  }
        union
      {  <http://kbox.kaist.ac.kr/resource/""" + entity + """> owl:sameAs ?ko.  ?ko ?p ?o. ?kb owl:sameAs ?o. }
    }order by ?p ?o ?kb"""

	# print(query)
	values = urlencode({'query': query})
	http = urllib3.PoolManager()

	headers = {
		'Content-Type': 'application/x-www-form-urlencoded, application/sparql-query, text/turtle',
		'Accept': 'text/turtle, application/rdf+xml, application/n-triples, application/trig, application/n-quads, '
				  'text/n3, application/trix, application/ld+json, '  # application/sparql-results+xml, '
				  'application/sparql-results+json, application/x-binary-rdf-results-table, text/boolean, text/csv, '
				  'text/tsv, text/tab-separated-values '
	}
	url = server + 'query?' + values
	r = http.request('GET', url, headers=headers)
	# print(r.status)
	# for xml
	# str = r.data.decode('UTF-8')
	# print(str)
	label = ''
	# for json
	request = json.loads(r.data.decode('UTF-8'))
	# print(request)
	result_list = request['results']['bindings']
	# print(result_list)
	out_list = []
	type_list = []
	dic = {}
	for item in result_list:
		s = item['s']['value']
		p = item['p']['value']
		o = item['o']['value']
		if len(item) > 3:
			kb = item['kb']['value']
			o = kb
		else:
			kb = ""
		out = s + '\t' + p + '\t' + o  # + ' .'
		# print(out)
		if 'type' in p:
			type_list.append(o)
		if 'label' in p:
			label = o.replace('_', ' ')

		if out in dic:
			count = dic[out]
			count = count + 1
			dic[out] = count
		else:
			dic[out] = 1
	# print(len(result_list))
	for (k, v) in dic.items():
		key = k
		val = v
		out_list.append(key.split('\t'))

	# type_list.sort()
	# out_list.sort()
	# out_list = sorted(out_list, key=lambda x: (x, len(x)))
	# print(label)
	out_dic = {'title': label, 'type': type_list, 'property': out_list}
	# for i in out_list:
	#     print(i)
	# print(out_list)
	return out_dic


def find_Knowledge(entity):
	result = select(entity)
	result_list = []
	for triple in result['property']:
		tmp_string = '<' + triple[0] + '> <' + triple[1] + '> '
		if "http" in triple[2]:
			tmp_string = tmp_string + '<' + triple[2] + '> .'
		else:
			tmp_string = tmp_string + "'" + triple[2] + "' ."
		result_list.append(tmp_string)
	tmp_dict = {}
	tmp_dict["entity"] = entity
	tmp_dict["KB"] = result_list

	return tmp_dict


def entity_summary(input_json):
	http = urllib3.PoolManager()
	response = http.request(
		"POST",
		entity_summaryURL,
		body=json.dumps(input_json)
	)

	return json.loads(response.data)

def ES(entity):
	tmp_dict = find_Knowledge(entity)
	return entity_summary(tmp_dict)['top5']


if __name__ == "__main__":
	tmp_dict = find_Knowledge('싸이')
	summarized_list = entity_summary(tmp_dict)
	print(summarized_list)
