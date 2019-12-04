import requests
import json

def Statement_Generation(triple_list, dialog_act):
	targetURL = "http://kbox.kaist.ac.kr:4885/generation"
	requestJson = {
		"triples": triple_list,
		"act": dialog_act
	}

	headers = {'Content-Type': 'application/json; charset=utf-8'}
	response = requests.post(targetURL, headers=headers, data=json.dumps(requestJson))
	#print("[responseCode] " + str(response.status_code))
	#print(response.json())

	return response.json()


if __name__ == '__main__':
	print(Statement_Generation([
        {"S": {"name": "http://kbox.kaist.ac.kr/resource/한국과학기술원", "class": ["http://dbpedia.org/ontology/University"]},
        "P": "http://dbpedia.org/ontology/country",
        "O": {"name": "http://kbox.kaist.ac.kr/resource/대한민국", "class": ["http://dbpedia.org/ontology/Country"]}}
    ], 'Knowledge_Inform'))