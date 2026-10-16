#!/usr/bin/env python3
"""Round N (sections 1, 6) -- census of the weight-2 and weight-3 transitions of a family
configuration, classified by trail and chain position.  usage: g0_census.py FAMILY.json [VERS]"""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from famstruct import Fam

def main():
    vers = None
    if len(sys.argv) > 2: vers = [int(c) for c in sys.argv[2]]
    fm = Fam(sys.argv[1], vers)
    kinds = Counter(len(c["runs"]) for c in fm.chains); full = sum(c["full"] for c in fm.chains)
    print(json.dumps(dict(runs=fm.N, chains=len(fm.chains), full=full, chain_len_hist=dict(sorted(kinds.items())))))
    # weight-2 transitions
    w2 = Counter()
    for r in range(fm.N):
        s = fm.fsucc(r)
        if s is None: w2["absent"] += 1; continue
        c1, c2 = fm.chain_of[r], fm.chain_of[s]
        if c1 == c2:
            if fm.pos[s] == fm.pos[r] + 1: w2["trail F-step"] += 1
            elif fm.pos[s] == 1 and fm.pos[r] == 7: w2["wrap-around"] += 1
            else: w2["same chain other"] += 1
        else:
            w2["different chain" + (" same trail" if fm.chains[c1]["trail"] == fm.chains[c2]["trail"] else " other trail")] += 1
    print(json.dumps(dict(weight2=dict(w2))))
    # weight-3 transitions: classified by (same trail?, src chain kind/pos, dst pos)
    w3 = Counter(); inter = Counter(); intra = Counter()
    for r in range(fm.N):
        for s in fm.succ_w(r, 3):
            cr, cs = fm.chains[fm.chain_of[r]], fm.chains[fm.chain_of[s]]
            key = ("F" if cr["full"] else "S%d" % len(cr["runs"])) + "p%d" % fm.pos[r] + "->" + ("F" if cs["full"] else "S%d" % len(cs["runs"])) + "p%d" % fm.pos[s]
            if cr["trail"] == cs["trail"]:
                tag = "link" if (fm.chain_of[r] != fm.chain_of[s] and fm.pos[s] == 1 and fm.pos[r] == len(cr["runs"]) and
                                 fm.chains[fm.chain_of[s]]["ord"] == (cr["ord"] + 1) % len(fm.trail_chains[cr["trail"]])) else "alt"
                intra[tag + ":" + key] += 1
            else:
                inter[key] += 1
    print(json.dumps(dict(intra_w3=dict(sorted(intra.items(), key=lambda kv: -kv[1])))))
    print(json.dumps(dict(inter_w3=dict(sorted(inter.items(), key=lambda kv: -kv[1])))))

if __name__ == "__main__":
    main()
