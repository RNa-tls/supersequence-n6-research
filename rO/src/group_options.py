#!/usr/bin/env python3
"""Round O -- option-level action of the family symmetry group (order 12).
g in S_8 maps run k of (t, v) to run (off + k) of (t', v'), hence option (t, v, k) -> (t', v', off + k):
entry st[k] -> st'[off + k] and exit last(st[k-1]) -> last(st'[off + k - 1]).  Checked: every image
option has the same cut, and E[g o, g o'] = E[o, o'] for all option pairs (sampled + full row check).
usage: group_options.py FAMILY.json E.npy OUT.npz"""
import sys, os, json, itertools
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rN", "src"))
import options as OP

def main():
    fam_p, E_p, out = sys.argv[1:4]
    fam, opts = OP.load(fam_p)
    key = {(o["t"], o["v"], o["k"]): i for i, o in enumerate(opts)}
    seqs = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            seqs[(t, v)] = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
    owner = {}
    for kk, ss in seqs.items():
        for k, p in enumerate(ss): owner.setdefault(p, []).append((kk, k))
    probe = seqs[(1, 0)][0]; perms = []; tperms = []
    for g in itertools.permutations(range(8)):
        if tuple(g[x] for x in probe) not in owner: continue
        img = {}; ok = True
        for kk, ss in seqs.items():
            q0 = tuple(g[x] for x in ss[0]); found = False
            for (k2, off) in owner.get(q0, []):
                s2 = seqs[k2]
                if len(s2) == len(ss) and all(tuple(g[x] for x in ss[i]) == s2[(off + i) % len(s2)] for i in range(len(ss))):
                    img[kk] = (k2, off); found = True; break
            if not found: ok = False; break
        if not ok: continue
        P = np.zeros(len(opts), np.int64); tp = np.zeros(30, np.int64)
        for i, o in enumerate(opts):
            (t2, v2), off = img[(o["t"], o["v"])]
            P[i] = key[(t2, v2, (off + o["k"]) % o["m"])]; tp[o["t"]] = t2
        perms.append(P); tperms.append(tp)
    E = np.load(E_p); cut = np.array([o["cut"] for o in opts]); rng = np.random.default_rng(0)
    for P in perms:
        assert np.array_equal(cut[P], cut)
        rows = rng.choice(len(opts), 200, replace=False)
        assert np.array_equal(E[np.ix_(P[rows], P)], E[rows]), "E not invariant"
    np.savez_compressed(out, operm=np.array(perms), tperm=np.array(tperms))
    print(json.dumps(dict(order=len(perms), invariant_checked=True)))

main()
