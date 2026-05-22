import json
import itertools


people_lookup = json.load(open('people_lookup.json'))

nodes = []
nodesAdded ={}
links = []
missing=[]
all_relationships = {}

## assoicated entities network

for doc in json.load(open('associated_entities_raw.json')):


	blocks = {}

	for e in doc['entities']:

		if e['block_qid'] not in blocks:
			blocks[e['block_qid']] = {}
			blocks[e['block_qid']]['relationshipsAdded'] = {}
			blocks[e['block_qid']]['relationships'] = []
			blocks[e['block_qid']]['qids'] = []

		if e['type_qid'] == 'Q1':

			if e['entity_qid'] not in blocks[e['block_qid']]:
				blocks[e['block_qid']]['qids'].append(e['entity_qid'])


	for b in blocks:
		if len(blocks[b]['qids']) > 1:
			print(b)
			print(blocks[b])
			for subset in itertools.combinations(blocks[b]['qids'], 2):

				print(subset)
				ltr = f"{subset[0]}-{subset[1]}"
				rtl = f"{subset[1]}-{subset[0]}"


				# if ltr not in blocks[b]['relationshipsAdded'] and rtl not in blocks[b]['relationshipsAdded']:
				if ltr not in all_relationships and rtl not in all_relationships:
				

					blocks[b]['relationships'].append(
					        {
					            "source": int(subset[0][1:]),
					            "target": int(subset[1][1:]),
					            "ref":b
					        })

						
					# blocks[b]['relationshipsAdded'][ltr] = True
					# blocks[b]['relationshipsAdded'][rtl] = True
					all_relationships[ltr] = True
					all_relationships[rtl] = True



	# build nodes and links
	for b in blocks:
		if len(blocks[b]['qids']) > 1:
			links = links + blocks[b]['relationships']
			for qid in blocks[b]['qids']:
				if qid not in nodesAdded:

					if qid not in people_lookup:
						missing.append(qid)
						continue

					nodesAdded[qid] = True
					nodes.append({
						'id': int(qid[1:]),
						'name': people_lookup[qid]['label'],
						'img': people_lookup[qid]['image']
					})


# Drop links pointing at nodes that were skipped (missing from people_lookup),
# otherwise force-graph throws "node not found".
node_ids = {n['id'] for n in nodes}
clean_links = [l for l in links if l['source'] in node_ids and l['target'] in node_ids]
dropped = len(links) - len(clean_links)
if dropped:
	print(f"dropped {dropped} links referencing missing nodes")
links = clean_links

json.dump({ 'nodes': nodes, 'links': links },open('people_network.json','w'))

with open('people_network.js','w') as outfile:

	all_data = json.dumps({ 'nodes': nodes, 'links': links })
	outfile.write(f"const allData = {all_data}")

print(missing)


# stuff = [1, 2, 3]
# for L in range(len(stuff) + 1):
#     for subset in itertools.combinations(stuff, 2):
#         print(subset)


