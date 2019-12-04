
#영균이형
# -*- coding: utf-8 -*-
import json
import urllib3
from urllib.parse import urlencode


def ontology(prop):
	server = 'http://kbox.kaist.ac.kr:5820/myDB/'

	query = '''select ?p ?count (count(distinct ?s) as ?count) where { 
  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/''' + prop + '''>.
  ?s ?p ?o.
  FILTER regex(str(?p), "ontology")
  FILTER (!regex(str(?p), "wiki"))
  FILTER (!regex(str(?p), "abstract"))
  FILTER (!regex(str(?p), "type"))
}GROUP BY ?p
ORDER BY DESC(?count)
LIMIT 20'''
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
	# for json
	request = json.loads(r.data.decode('UTF-8'))
	#print(request)
	tmp_list = request['results']['bindings']
	result_list = []
	if len(tmp_list) > 10:
		limit = 10
	else:
		limit = len(tmp_list)
	for i in range(limit):
		try:
			tmp_tuple = (tmp_list[i]['p']['value'], tmp_list[i]['count']['value'])
			result_list.append(tmp_tuple)
		except KeyError:
			print(tmp_list[i])
			print(prop)
	# print(item)
	# out_p = item['p']['value']
	# out_c = item['count']['value']
	# print(out_p, out_c)
	return result_list


if __name__ == "__main__":
	result_dict = {}

	with open('person-organisation-class.json', 'r', encoding='utf-8') as f1:
		json_data = json.load(f1)
		process_count = 0

		for now_class in json_data:
			server = 'http://kbox.kaist.ac.kr:5820/myDB/'

			query = '''select ?count (count(distinct ?s) as ?count) where { 
			  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/''' + now_class + '''>.
			  }
			ORDER BY DESC(?count)'''
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
			# for json
			request = json.loads(r.data.decode('UTF-8'))
			#print(request)
			sum_num = request['results']['bindings'][0]['count']['value']

			tmp_list = ontology(now_class)
			tmp_dict = {'count': sum_num, 'prior_property': tmp_list}
			result_dict[now_class] = tmp_dict
			with open('prior_property_person_organisation.json', 'w') as f:
				f.write(json.dumps(result_dict, ensure_ascii=False, indent='\t'))
			process_count += 1
			print(process_count)
