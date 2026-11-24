import requests
import json

url = "https://query.semlab.io/proxy/wdqs/bigdata/namespace/wdq/sparql"

sparql = """
	select * where{
	  
	  ?person wdt:P1 wd:Q1.
	  ?person wdt:P11 wd:Q19104.
	  ?person rdfs:label ?personLabel. 
	  OPTIONAL{
	   ?person wdt:P3 ?image. 
	   }

	}
"""

params = {
	'query' : sparql
}

headers = {
	'Accept' : 'application/json',
	'User-Agent': 'semlab-data-process (eat-network-tests)'
}

r = requests.get(url, params=params, headers=headers)

data = json.loads(r.text)

docs = {}

for result in data['results']['bindings']:


	qid = result['person']['value'].split('/')[-1]
	label = result['personLabel']['value']
	if 'image' in result:
		image = result['image']['value']
	else:
		image = None


	print(qid,label,image)
	docs[qid] = {'qid':qid, 'id': int(qid[1:]), 'label':label, 'image': image}

	json.dump(docs,open('people_lookup.json','w'),indent=2)
