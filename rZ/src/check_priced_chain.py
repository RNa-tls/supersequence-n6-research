#!/usr/bin/env python3
"""Round Z -- independent check (no code shared with rZ/csrc/dsearch_lab.c) of the chain that a priced line search
reports as attaining its largest value:  the model rules (exit, door, seam = y[3:] + permutation of y[0:3], pieces of
1..7 blocks, all rotation classes distinct, first entry 12345678), the seam types (b, c, f change the last letter of
the entries), every prefix value 4r-9d+lam*L (or the given line) in (0, cap], and the final value.
usage: check_priced_chain.py RESULT.json"""
import sys, json
d = json.loads(open(sys.argv[1]).read())
a, b, c = d['params']; lam = d['lambda']; cap = d['keep_cap']
bc = d['best_chain']; ent = [e.upper().replace('0X', '') for e in bc['entries']]; ent = [e.lower() for e in ent]
pieces = bc['pieces']
def exitw(D): return D[7] + D[:7]
def door(x): return x[2:] + x[1] + x[0]
def canon(w): i = w.index('8'); return w[i:] + w[:i]
assert ent[0] == '12345678' and sum(pieces) == len(ent) and all(1 <= p <= 7 for p in pieces)
assert all(sorted(e) == list('12345678') for e in ent)
assert len({canon(e) for e in ent}) == len(ent), 'repeated class'
k = 0; starts = []
for p in pieces:
    starts.append(k)
    for j in range(1, p): assert ent[k + j] == door(exitw(ent[k + j - 1])), 'door'
    k += p
types = []
for i in range(1, len(pieces)):
    y = exitw(ent[starts[i] - 1]); e = ent[starts[i]]
    assert e[:5] == y[3:] and sorted(e[5:]) == sorted(y[:3]), 'seam'
    z, v1, v2 = y[0], y[1], y[2]
    types.append({z + v2 + v1: 'c', v1 + z + v2: 'b', v1 + v2 + z: 'e', v2 + z + v1: 'f', v2 + v1 + z: 'd'}[e[5:]])
assert ''.join(types) == bc['seams'], 'seam types differ'
val = 0; L = 0
for i, p in enumerate(pieces):
    if i > 0 and types[i - 1] in 'bcf': L += 1
    val = a * (i + 1) - b * sum(7 - q for q in pieces[:i + 1]) + lam * L
    assert 0 < val <= cap, 'prefix value out of (0, cap]'
assert val == d['max_value'], (val, d['max_value'])
print(json.dumps(dict(file=sys.argv[1], ok=True, r=len(pieces), d=sum(7 - q for q in pieces), label_changes=L, value=val, seams=dict((t, types.count(t)) for t in set(types)))))
