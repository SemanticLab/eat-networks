import json
import itertools
import os


people_lookup = json.load(open('people_lookup.json'))

nodes = []
nodesAdded ={}
links = []
missing=[]
all_relationships = {}

## assoicated entities network

# Prefer the scrubbed file (no references to deleted blocks) if it exists.
raw_path = 'associated_entities_raw.cleaned.json' if os.path.exists('associated_entities_raw.cleaned.json') else 'associated_entities_raw.json'
print(f'reading {raw_path}')

# Co-mention links, weighted. Every pair of people named in the same block
# (passage) is a tie. A pair's weight sums 1/(k-1) over the passages it shares,
# where k is the number of people in that passage: two people alone in a
# passage count 1, a 50-name list contributes almost nothing per pair. We also
# keep how many passages (p) and documents (d) each pair shares, and the first
# block as its reference, so the pages can prune one-off ties.
pairs = {}          # (a, b) -> {'w':, 'p':, 'docs': set(), 'ref':}
people_seen = {}
for doc in json.load(open(raw_path)):
	blocks = {}
	for e in doc['entities']:
		if e['type_qid'] != 'Q1':
			continue
		blocks.setdefault(e['block_qid'], [])
		if e['entity_qid'] not in blocks[e['block_qid']]:
			blocks[e['block_qid']].append(e['entity_qid'])
	for b, qids in blocks.items():
		qids = [q for q in qids if q in people_lookup or missing.append(q) or False]
		if len(qids) < 2:
			continue
		share = 1.0 / (len(qids) - 1)
		for q in qids:
			people_seen[q] = True
		for a, b2 in itertools.combinations(sorted(qids, key=lambda q: int(q[1:])), 2):
			rec = pairs.get((a, b2))
			if rec is None:
				rec = pairs[(a, b2)] = {'w': 0.0, 'p': 0, 'docs': set(), 'ref': b}
			rec['w'] += share
			rec['p'] += 1
			rec['docs'].add(doc['qid'])

for qid in people_seen:
	nodes.append({
		'id': int(qid[1:]),
		'name': people_lookup[qid]['label'],
		'img': people_lookup[qid]['image']
	})
for (a, b2), rec in pairs.items():
	links.append({
		'source': int(a[1:]),
		'target': int(b2[1:]),
		'ref': rec['ref'],
		'w': round(rec['w'], 4),
		'p': rec['p'],
		'd': len(rec['docs']),
	})
missing = sorted(set(missing))
print(f"{len(nodes)} people, {len(links)} co-mention pairs; "
      f"{sum(1 for l in links if l['p'] >= 2)} shared by 2+ passages, {sum(1 for l in links if l['d'] >= 2)} by 2+ documents")

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

print(f'{len(missing)} entities not in people_lookup:', missing[:20], '...' if len(missing) > 20 else '')


# stuff = [1, 2, 3]
# for L in range(len(stuff) + 1):
#     for subset in itertools.combinations(stuff, 2):
#         print(subset)


