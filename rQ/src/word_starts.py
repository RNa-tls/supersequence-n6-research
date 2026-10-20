#!/usr/bin/env python3
"""Round Q -- run starts (route order) of an r = 0 word as N x 8 bytes, for runls / run-level tools.
usage: word_starts.py WORD OUT.bin"""
import sys, math
n = 8
text = "".join(ch for ch in open(sys.argv[1]).read() if not ch.isspace())
al = sorted(set(text)); w = [al.index(c) for c in text]
seen = set(); route = []
for i in range(len(w) - n + 1):
    p = tuple(w[i:i + n])
    if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
assert len(route) == math.factorial(n)
st = route[0::n]
for b, s in enumerate(st):
    for j in range(n): assert route[n * b + j] == s[j:] + s[:j], "not r = 0"
open(sys.argv[2], "wb").write(bytes(x for s in st for x in s))
print(len(text), len(st))
