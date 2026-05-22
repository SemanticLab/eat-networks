"""
Probe every block QID referenced by associated_entities_raw.json against the
wikibase. Any block that no longer has a `wdt:P19` (text) statement is treated
as deleted, and references to it are removed from a cleaned copy of the file.

Outputs:
  - associated_entities_raw.cleaned.json
  - dead_blocks.txt (one QID per line)

After running, re-run build_networks.py against the cleaned file to regenerate
people_network.{json,js}.
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SPARQL = "https://query.semlab.io/proxy/wdqs/bigdata/namespace/wdq/sparql"
HEADERS = {"Accept": "application/json", "User-Agent": "scrub_dead_blocks"}
BATCH = 200  # block QIDs per VALUES batch


def sparql(query):
    url = SPARQL + "?" + urlencode({"query": query})
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def live_blocks(qids):
    """Return the subset of input QIDs that currently have a wdt:P19 statement."""
    found = set()
    qids = list(qids)
    for i in range(0, len(qids), BATCH):
        chunk = qids[i : i + BATCH]
        values = " ".join(f"wd:{q}" for q in chunk)
        query = f"""
            SELECT DISTINCT ?block WHERE {{
              VALUES ?block {{ {values} }}
              ?block wdt:P19 ?text .
            }}
        """
        data = sparql(query)
        for b in data["results"]["bindings"]:
            found.add(b["block"]["value"].split("/")[-1])
        print(f"  probed {i + len(chunk)}/{len(qids)} blocks, {len(found)} live so far")
    return found


def main():
    raw = json.load(open("associated_entities_raw.json"))

    all_blocks = set()
    for doc in raw:
        for e in doc.get("entities", []):
            if e.get("block_qid"):
                all_blocks.add(e["block_qid"])
    print(f"unique blocks referenced: {len(all_blocks)}")

    live = live_blocks(all_blocks)
    dead = all_blocks - live
    print(f"live: {len(live)}  dead: {len(dead)}")

    with open("dead_blocks.txt", "w") as f:
        for q in sorted(dead):
            f.write(q + "\n")

    # Rewrite cleaned copy: drop entity rows whose block_qid is dead.
    cleaned = []
    removed_rows = 0
    for doc in raw:
        new_entities = []
        for e in doc.get("entities", []):
            if e.get("block_qid") in dead:
                removed_rows += 1
                continue
            new_entities.append(e)
        new_doc = dict(doc)
        new_doc["entities"] = new_entities
        cleaned.append(new_doc)
    print(f"removed {removed_rows} entity rows pointing at dead blocks")

    with open("associated_entities_raw.cleaned.json", "w") as f:
        json.dump(cleaned, f, indent=2)
    print("wrote associated_entities_raw.cleaned.json")


if __name__ == "__main__":
    main()
