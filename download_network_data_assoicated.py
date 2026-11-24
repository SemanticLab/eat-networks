import requests
import json

url = "https://query.semlab.io/proxy/wdqs/bigdata/namespace/wdq/sparql"

sparql = """
	select * where{
	  
	  ?doc wdt:P1 wd:Q19069.
	  ?doc wdt:P11 wd:Q19104.
	  ?doc rdfs:label ?docLabel. 

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

docs = []

for result in data['results']['bindings']:


	qid = result['doc']['value'].split('/')[-1]
	label = result['docLabel']['value']
	print(qid,label)


	sparql = """
		select * { 
		  {select * where { 
		    ?block wdt:P24 wd:<QID>.
		    ?block wdt:P21 ?assoicatedEntity. 
		  }}
				  
		  ?assoicatedEntity wdt:P1 ?type .
		  ?type rdfs:label ?typeLabel.
  		  ?assoicatedEntity rdfs:label ?entityLabel.

		}
	"""

	sparql = sparql.replace('<QID>',qid)
	params = {
		'query' : sparql
	}

	r = requests.get(url, params=params, headers=headers)

	entity_data = json.loads(r.text)

	if len(entity_data['results']['bindings']) > 0:


		doc = {
			'qid': qid, 
			'label': label,
			'entities': [],
		}


		for entity_result in entity_data['results']['bindings']:


			doc['entities'].append({
					'block_qid': entity_result['block']['value'].split('/')[-1],
					'entity_qid': entity_result['assoicatedEntity']['value'].split('/')[-1],
					'entity_label': entity_result['entityLabel']['value'],
					'type_label':  entity_result['typeLabel']['value'],
					'type_qid': entity_result['type']['value'].split('/')[-1],


				})


		docs.append(doc)
		json.dump(docs,open('associated_entities_raw.json','w'),indent=2)
		print(len(entity_data['results']['bindings']), ' blocks')
	else:
		print('No blocks!')
