#!/usr/bin/env python3
"""Round Q -- structure of the 30 closed trails of the 6A+24phi family (rM/certs/family_46187.json).
For every trail and version: number of runs m, multiset of internal join weights c_i = w(last(run i-1), first(run i)),
cyclic total W, whether the two versions cover the same rotation classes, and how their cyclic orders relate.
usage: family_struct.py FAMILY.json OUT.json"""
import sys, json
from collections import Counter

def w(x, y):
    for s in range(1, 8):
        if x[s:] == y[:8 - s]: return s
    return 8

def main():
    fam = json.load(open(sys.argv[1])); out = []
    allcls = Counter(); tot = 0
    for t, tr in enumerate(fam["trails"]):
        rec = dict(trail=t, versions=[])
        clsets = []; seqs = []
        for v, s in enumerate(tr["versions"]):
            runs = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
            m = len(runs)
            last = lambda p: p[7:] + p[:7]
            c = [w(last(runs[i - 1]), runs[i]) for i in range(m)]
            canon = [min(p[j:] + p[:j] for j in range(8)) for p in runs]
            clsets.append(set(canon)); seqs.append(canon)
            rec["versions"].append(dict(m=m, W=sum(c), join_hist=dict(sorted(Counter(c).items()))))
            if v == 0:
                for x in canon: allcls[x] += 1
                tot += m
        rec["same_class_set"] = clsets[0] == clsets[1]
        a, b = seqs
        pos = {x: i for i, x in enumerate(a)}
        if rec["same_class_set"]:
            idx = [pos[x] for x in b]; m = len(a)
            fwd = all((idx[i + 1] - idx[i]) % m == 1 for i in range(m - 1))
            rev = all((idx[i] - idx[i + 1]) % m == 1 for i in range(m - 1))
            # number of version-1 consecutive pairs that are also consecutive (either direction) in version 0
            adj0 = {frozenset((a[i], a[(i + 1) % m])) for i in range(m)}
            shared = sum(frozenset((b[i], b[(i + 1) % m])) in adj0 for i in range(m))
            rec.update(v1_is_rotation_of_v0=fwd, v1_is_reversal_of_v0=rev, shared_undirected_adjacencies=shared)
        out.append(rec)
    summary = dict(total_runs_version0=tot, distinct_classes=len(allcls), classes_covered_once=all(v == 1 for v in allcls.values()),
                   W_total=sum(r["versions"][0]["W"] for r in out), W_equal_across_versions=all(r["versions"][0]["W"] == r["versions"][1]["W"] for r in out))
    json.dump(dict(summary=summary, trails=out), open(sys.argv[2], "w"), indent=1)
    print(json.dumps(summary))
    for r in out[:2] + [out[28]]: print(json.dumps(r))

main()
