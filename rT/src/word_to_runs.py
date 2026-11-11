#!/usr/bin/env python3
"""Round T -- the route of a word: first permutation of every class visit, in order (8 digits per line).
usage: word_to_runs.py WORD.txt OUT.txt"""
import sys
w = "".join(ch for ch in open(sys.argv[1]).read() if not ch.isspace()); al = sorted(set(w)); w = "".join(str(al.index(c)) for c in w)
ok = [len(set(w[i:i + 8])) == 8 for i in range(len(w) - 7)]; out = []; i = 0
while i < len(ok):
    assert all(ok[i:i + 8]); out.append(w[i:i + 8]); j = i + 8
    while j < len(ok) and (not ok[j] or (j == i + 8 and w[j:j + 8] == w[i:i + 8])): j += 1
    i = j
assert len(out) == 5040 and len({min(x[k:] + x[:k] for k in range(8)) for x in out}) == 5040
open(sys.argv[2], "w").write("\n".join(out) + "\n")
