#!/usr/bin/env python3
"""Round S -- second implementation of the skip weight law (no code shared with skip_weights.py / runs_io.py / chains.py).
Reads the family JSON directly, computes every weight by string comparison, finds the chains from the cut weights and
checks  w(Q_end, N_0) = 3 + k  for every run of k <= 4 consecutive full chains of every trail version.
usage: skip_weights_check.py FAMILY.json OUT.json"""
import sys, json
from collections import Counter
fam = json.load(open(sys.argv[1]))
def w(x, y):                      # x, y: first permutations (strings of 8 symbols) of two runs
    lx = x[7] + x[:7]
    for s in range(1, 8):
        if lx[s:] == y[:8 - s]: return s
    return 8
cnt = Counter(); bad = 0; nfull = 0
for t, tr in enumerate(fam["trails"]):
    for v, sv in enumerate(tr["versions"]):
        R = [sv[8 * k:8 * k + 8] for k in range(len(sv) // 8)]; m = len(R)
        c = [w(R[k - 1], R[k]) for k in range(m)]
        starts = [k for k in range(m) if c[k] == 3]; assert set(c) <= {2, 3}
        ch = []                                    # (first run, last run, full?)
        for i, s0 in enumerate(starts):
            e = starts[(i + 1) % len(starts)]; L = (e - s0) % m or m; last = (s0 + L - 1) % m
            ch.append((s0, last, L == 7 and w(R[last], R[s0]) == 2))
        n = len(ch); nfull += sum(1 for x in ch if x[2])
        for i in range(n):
            for k in range(1, 5):
                if k > n - 2: break
                if not all(ch[(i + 1 + j) % n][2] for j in range(k)): break
                ww = w(R[ch[i][1]], R[ch[(i + 1 + k) % n][0]]); cnt[("A" if m > 100 else "phi", k, ww)] += 1
                if ww != 3 + k: bad += 1
out = dict(full_chains=nfull, counts=[dict(kind=a, k=k, weight=x, count=n_) for (a, k, x), n_ in sorted(cnt.items())], violations=bad, law_holds=(bad == 0))
json.dump(out, open(sys.argv[2], "w"), indent=1); print(json.dumps(out))
