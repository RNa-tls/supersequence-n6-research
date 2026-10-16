#!/usr/bin/env python3
"""Round N -- transfer the exact single-visit catalog of one phi trail-version to every phi
trail-version by an explicit internal isomorphism: offset d with W_T[k, k'] = W_0[k + d, k' + d] for
ALL run pairs (checked entrywise on the full 42 x 42 internal weight matrices; the catalog depends only
on these weights).  Writes the extended option list: (trail, version, entry run index, exit run index,
kappa) for kappa <= KMAX.
usage: phi_catalog_all.py FAMILY.json CATALOG.json KMAX OUT.json"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP

def last(p): return p[-1:] + p[:-1]

def main():
    fam = json.load(open(sys.argv[1])); cat = json.load(open(sys.argv[2])); KMAX = int(sys.argv[3])
    tab = {tuple(int(x) for x in k.split(",")): v for k, v in cat["table"].items()}
    def Wmat(t, v):
        s = fam["trails"][t]["versions"][v]
        st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
        return OP.weight_block([last(p) for p in st], st).astype(np.int64)
    W0 = Wmat(cat["trail"], cat["version"]); m = W0.shape[0]
    out = []; maps = {}
    for t, tr in enumerate(fam["trails"]):
        if len(tr["versions"][0]) // 8 != m: continue
        for v in (0, 1):
            Wt = Wmat(t, v); found = None
            for d in range(m):
                perm = [(k + d) % m for k in range(m)]
                if np.array_equal(Wt, W0[np.ix_(perm, perm)]): found = d; break
            assert found is not None, "no internal isomorphism for trail %d v%d" % (t, v)
            maps["%d,%d" % (t, v)] = found
            for (y, x), kap in tab.items():
                if kap <= KMAX:
                    out.append((t, v, (y - found) % m, (x - found) % m, kap))
    json.dump(dict(kmax=KMAX, offsets=maps, options=out), open(sys.argv[4], "w"))
    from collections import Counter
    print(json.dumps(dict(trail_versions=len(maps), options=len(out), by_kappa=dict(Counter(o[4] for o in out)))))

if __name__ == "__main__":
    main()
