#!/usr/bin/env python3
"""Round Q -- boundary excess between two fragments of the SAME trail (same version) and between the two
versions of a trail.  For a trail-version with runs r_0..r_{m-1} (cyclic), joins c_i = w(last(r_{i-1}), first(r_i)):
  jump(j -> i) = w(last(r_j), first(r_i)) - c_i - 1     (exit of a fragment ending at run j, entry of one starting at i)
i = j + 1 is the internal join itself (value -1 = re-merging the fragments).  Also reports the cross-version values
(exit run of version v, entry run of version 1-v of the same trail) for the version-mixing discussion.
usage: same_trail_jumps.py FAMILY.json OUT.json"""
import sys, json
from collections import Counter
import numpy as np

def main():
    fam = json.load(open(sys.argv[1])); res = []
    tot = Counter(); totx = Counter()
    for t, tr in enumerate(fam["trails"]):
        R = []
        for s in tr["versions"]:
            runs = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
            R.append(runs)
        rec = dict(trail=t)
        for v in range(2):
            runs = R[v]; m = len(runs)
            first = np.array([[int(ch) for ch in p] for p in runs], np.int64)
            last = np.array([[int(ch) for ch in (p[7:] + p[:7])] for p in runs], np.int64)
            # w(last_j, first_i) for all j, i (vectorised over overlaps)
            W = np.full((m, m), 8, np.int64)
            for s_ in range(7, 0, -1):
                k = 8 - s_
                a = (last[:, s_:] * (8 ** np.arange(k))).sum(1); b = (first[:, :k] * (8 ** np.arange(k))).sum(1)
                W[a[:, None] == b[None, :]] = s_
            c = np.array([W[(i - 1) % m, i] for i in range(m)])
            J = W - c[None, :] - 1
            mask = np.ones((m, m), bool)
            for i in range(m): mask[(i - 1) % m, i] = False
            vals = J[mask]
            h = Counter(vals.tolist()); tot.update(h)
            rec[f"v{v}"] = dict(min_jump=int(vals.min()), hist={int(k): int(n) for k, n in sorted(h.items())[:6]})
            if v == 0: F0, L0, c0 = first, last, c
            else: F1, L1, c1 = first, last, c
        # cross-version: exit run of version 0 -> entry run of version 1 (and back)
        for (La, Fb, cb, tag) in ((L0, F1, c1, "v0->v1"), (L1, F0, c0, "v1->v0")):
            m = len(La); W = np.full((m, m), 8, np.int64)
            for s_ in range(7, 0, -1):
                k = 8 - s_
                a = (La[:, s_:] * (8 ** np.arange(k))).sum(1); b = (Fb[:, :k] * (8 ** np.arange(k))).sum(1)
                W[a[:, None] == b[None, :]] = s_
            X = W - cb[None, :] - 1; totx.update(Counter(X.ravel().tolist()))
            rec[tag] = int(X.min())
        res.append(rec)
    summ = dict(same_version_min_jump=min(min(r["v0"]["min_jump"], r["v1"]["min_jump"]) for r in res),
                same_version_hist={int(k): int(n) for k, n in sorted(tot.items())},
                cross_version_min=min(min(r["v0->v1"], r["v1->v0"]) for r in res),
                cross_version_hist={int(k): int(n) for k, n in sorted(totx.items())})
    json.dump(dict(summary=summ, trails=res), open(sys.argv[2], "w"), indent=1)
    print(json.dumps(summ))
    print(json.dumps(res[0])); print(json.dumps(res[1]))

main()
