#!/usr/bin/env python3
"""Round N -- option dominance in the single-opening model.
Option o' of trail T dominates option o of T when, against every option of every OTHER trail,
  min(e(x -> o'), CAP) <= min(e(x -> o), CAP)   and   min(e(o' -> y), CAP) <= min(e(o -> y), CAP),
and [cut(o') = 2] <= [cut(o) = 2] (start cost).  Arcs with e >= CAP are 'else' arcs of cost CAP in the
EMAX = CAP - 1 relaxation, so replacing o by o' in any solution of that relaxation never increases its
cost: the relaxation optimum is unchanged when dominated options are deleted (ties broken by index).
usage: dominance.py FAMILY.json E.npy CAP OUT.json"""
import sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def main():
    fam, opts = OP.load(sys.argv[1]); E = np.load(sys.argv[2]); CAP = int(sys.argv[3])
    tr = np.array([o["t"] for o in opts]); cut = np.array([o["cut"] for o in opts])
    Ec = np.minimum(E, CAP).astype(np.int8)
    keep = []; t0 = time.time(); stats = {}
    for t in sorted(set(tr.tolist())):
        ids = np.nonzero(tr == t)[0]; others = np.nonzero(tr != t)[0]
        IN = Ec[np.ix_(others, ids)].T          # |ids| x |others|
        OUT = Ec[np.ix_(ids, others)]
        P = np.concatenate([IN, OUT], axis=1)   # profile
        sc = (cut[ids] == 2).astype(np.int8)
        # sort by profile sum so dominators come first; dominated = exists j != i with P[j] <= P[i], sc[j] <= sc[i], (strict or j < i)
        order = np.lexsort((np.arange(len(ids)), P.sum(1)))
        undom = []
        for i in order:
            dom = False
            for j in undom:
                if sc[j] <= sc[i] and np.all(P[j] <= P[i]): dom = True; break
            if not dom: undom.append(i)
        stats[int(t)] = dict(options=len(ids), undominated=len(undom))
        keep += [int(ids[i]) for i in undom]
        print(json.dumps(dict(trail=int(t), options=len(ids), undominated=len(undom), sec=round(time.time() - t0, 1))), flush=True)
    json.dump(dict(cap=CAP, keep=sorted(keep), stats=stats), open(sys.argv[4], "w"))

if __name__ == "__main__":
    main()
