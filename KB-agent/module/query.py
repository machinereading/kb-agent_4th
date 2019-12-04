# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode
import urllib3

main_server = 'http://kbox.kaist.ac.kr:5820/myDB/'


def select(entity):
    server = main_server

    query = """select distinct (<http://kbox.kaist.ac.kr/resource/"""+entity+"""> as ?s) ?p ?o ?kb
    where {
      {  <http://kbox.kaist.ac.kr/resource/"""+entity+"""> ?p ?o.  }
        union
      {  <http://kbox.kaist.ac.kr/resource/"""+entity+"""> owl:sameAs ?ko.  ?ko ?p ?o  }
        union
      {  <http://kbox.kaist.ac.kr/resource/"""+entity+"""> owl:sameAs ?ko.  ?ko ?p ?o. ?kb owl:sameAs ?o. }
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
        out = s + '\t' + p + '\t' + o # + ' .'
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
    #print(label)
    out_dic = {'title': label, 'type': type_list, 'property': out_list}
    # for i in out_list:
    #     print(i)
    # print(out_list)
    return out_dic


def select_rev(entity):
    server = main_server

    query = """select distinct ?kb ?s ?p (<http://kbox.kaist.ac.kr/resource/"""+entity+"""> as ?o)
    where {
        {  ?s ?p <http://kbox.kaist.ac.kr/resource/"""+entity+"""> .}
        union
        {  <http://kbox.kaist.ac.kr/resource/"""+entity+"""> owl:sameAs ?ko.  ?s ?p ?ko.}
        union
        {  <http://kbox.kaist.ac.kr/resource/"""+entity+"""> owl:sameAs ?ko.  ?s ?p ?ko. ?kb owl:sameAs ?s. }
    }order by ?p ?s ?kb """
    # print(query)
    values = urlencode({'query': query, 'user': 'anonymous', 'password': 'anonymous'})
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
    result_list = request['results']['bindings']
    out_list = []
    dic = {}
    for item in result_list:
        s = item['s']['value']
        p = item['p']['value']
        o = item['o']['value']
        if len(item) > 3:
            kb = item['kb']['value']
            s = kb
        else:
            kb = ""
        out = s + '\t' + p + '\t' + o  # + ' .'
        # print(out)

        if out in dic:
            count = dic[out]
            count = count + 1
            dic[out] = count
        else:
            dic[out] = 1
    for (k, v) in dic.items():
        key = k
        val = v
        out_list.append(key.split('\t'))

    # out_list = sorted(out_list, key=lambda x: (x[1], x[0]))
    out_dic = {'re_property': out_list}
    # for i in out_list:
    #     print(i)
    # print(out_list)
    return out_dic


def select_all(entity):
    result = select(entity)
    #re = select_rev(entity)
    #result['re_property'] = re['re_property']
    #print(result['type'])
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
    print(json.dumps(tmp_dict, ensure_ascii=False))
    with open('141_desc.nt', 'w', encoding='UTF-8') as f:
        f.write('<' + triple[0] + '> <' + triple[1] + '> ')
        if "http" in triple[2]:
            f.write('<' + triple[2] + '> .\n')
        else:
            f.write("'" + triple[2] + "' .\n")

def ontology(prop):
    server = 'http://kbox.kaist.ac.kr:5820/myDB/'

    query = '''select ?p (count(distinct ?s) as ?count) where { 
  ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/''' + prop + '''>.
  ?s ?p ?o.
  FILTER regex(str(?p), "ontology")
  FILTER (!regex(str(?p), "wiki"))
}GROUP BY ?p
ORDER BY DESC(?count)'''
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
    result_list = request['results']['bindings']
    for item in result_list:
        # print(item)
        out_p = item['p']['value']
        out_c = item['count']['value']
        print(out_p, out_c)

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

    return json.dumps(tmp_dict, ensure_ascii=False)

if __name__ == "__main__":
    # select('애플_(기업)')
    # select_rev('애플_(기업)')
    #select_all('로마')
    ontology('PopulatedPlace')

