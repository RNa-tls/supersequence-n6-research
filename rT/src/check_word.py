#!/usr/bin/env python3
"""Round T -- three logically different coverage checks of an n = 8 word (alphabet 0..7).
 A  set of window strings        B  numpy: Lehmer rank of every window, bincount
 C  class structure: the word is cut at every step of weight >= 2 into maximal weight-1 runs; the cyclic classes
    visited and the permutations seen in each are counted (a class = rotation class of a permutation)
usage: check_word.py WORD.txt [OUT.json]"""
import sys, json, hashlib, math
import numpy as np
raw = open(sys.argv[1], "rb").read(); assert raw.endswith(b"\n") and raw.count(b"\n") == 1
w = raw[:-1].decode(); n = 8; L = len(w); assert set(w) <= set("01234567")
res = dict(length=L, sha256_with_lf=hashlib.sha256(raw).hexdigest(), sha256_no_lf=hashlib.sha256(raw[:-1]).hexdigest(), alphabet="".join(sorted(set(w))))
# A
seen = set(); occ = 0
for i in range(L - n + 1):
    s = w[i:i + n]
    if len(set(s)) == n: seen.add(s); occ += 1
res["A_set"] = dict(perm_windows=occ, distinct=len(seen), missing=math.factorial(n) - len(seen))
# B
a = np.frombuffer(raw[:-1], np.uint8) - 48; W = np.lib.stride_tricks.sliding_window_view(a, n)
ok = (np.sort(W, axis=1) == np.arange(n)).all(axis=1); P = W[ok].astype(np.int64)
rank = np.zeros(len(P), np.int64)
for i in range(n): rank += (P[:, i + 1:] < P[:, i:i + 1]).sum(axis=1) * math.factorial(n - 1 - i)
cnt = np.bincount(rank, minlength=math.factorial(n))
res["B_rank"] = dict(perm_windows=int(ok.sum()), distinct=int((cnt > 0).sum()), missing=int((cnt == 0).sum()), max_multiplicity=int(cnt.max()), repeated=int((cnt - 1).clip(0).sum()))
# C
idx = np.nonzero(ok)[0]; runs = []; cur = [idx[0]]
for i in idx[1:]:
    if i == cur[-1] + 1: cur.append(i)
    else: runs.append(cur); cur = [i]
runs.append(cur)
def cls(s):
    i = s.index("0"); return s[i:] + s[:i]
classes = {}; lens = {}
for r in runs:
    c = cls(w[r[0]:r[0] + n]); assert all(cls(w[i:i + n]) == c for i in r)
    classes.setdefault(c, set()).update(w[i:i + n] for i in r); lens[len(r)] = lens.get(len(r), 0) + 1
gaps = {}
for x, y in zip(runs, runs[1:]): gaps[int(y[0] - x[-1])] = gaps.get(int(y[0] - x[-1]), 0) + 1
res["C_classes"] = dict(weight1_runs=len(runs), run_length_histogram={str(k): v for k, v in sorted(lens.items())}, classes=len(classes), classes_complete=sum(len(v) == n for v in classes.values()),
                        step_weight_histogram={str(k): v for k, v in sorted(gaps.items())}, sum_weights=int(sum(k * v for k, v in gaps.items())), first_window_is_perm=bool(ok[0]), last_window_is_perm=bool(ok[-1]))
res["ok"] = all(res[k]["missing"] == 0 for k in ("A_set", "B_rank")) and res["C_classes"]["classes"] == 5040 == res["C_classes"]["classes_complete"]
print(json.dumps(res))
if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], "w"), indent=1)
