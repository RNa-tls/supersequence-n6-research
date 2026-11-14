#!/usr/bin/env python3
"""Round Y -- anatomy of the Round X extremal chain dumps (JSON lines with r, d, v, pieces, entries of every block).
Rebuilds every piece from its block entries (consecutive blocks of a piece are linked by doors; the check is an
assert), classifies every seam (c, b, e, f, d; '?' if the next entry is none of the five seam words), and reports
over all chains: seam types, moving symbols, piece sizes, number of chains using a 2-cycle twice.
usage: anatomy_summary.py DUMP.jsonl.gz [...] OUT.json"""
import sys, json, gzip, collections
def door(e): return e[1:7] + e[0] + e[7]
def cls(w):
    i = w.index('8'); return w[i:] + w[:i]
def twocycle(entry):
    z = entry[-1]; c = cls(entry); i = c.index(z); rest = c[i + 1:] + c[:i]; j = rest.index(min(rest)); return z, rest[j:] + rest[:j]
def seamtype(y, nxt):
    z, v1, v2 = y[0], y[1], y[2]
    if nxt[:5] != y[3:]: return '?'
    return {z + v2 + v1: 'c', v1 + z + v2: 'b', v1 + v2 + z: 'e', v2 + z + v1: 'f', v2 + v1 + z: 'd'}.get(nxt[5:], '?')
out = []
for fn in sys.argv[1:-1]:
    seams = collections.Counter(); labels = collections.Counter(); sizes = collections.Counter(); rep = 0; n = 0; vals = collections.Counter()
    for l in gzip.open(fn, 'rt'):
        d = json.loads(l)
        if 'pieces' not in d: continue
        P, EB = d['pieces'], d['entries']; n += 1; vals[d['v']] += 1
        assert len(P) == d['r'] and len(EB) == sum(P)
        st = 0; firsts = []
        for i, b in enumerate(P):
            e = EB[st]; firsts.append(e)
            for q in range(b):
                assert EB[st + q] == e; e = door(e)
            if i + 1 < len(P):
                last = EB[st + b - 1]; y = last[-1] + last[:-1]
                seams[seamtype(y, EB[st + b])] += 1
            st += b
        for e in firsts: labels[e[-1]] += 1
        sizes.update(P)
        tc = collections.Counter(twocycle(e) for e in firsts); rep += any(c > 1 for c in tc.values())
    out.append(dict(file=fn, chains=n, values=dict(sorted(vals.items())), seam_types=dict(seams), moving_symbols=dict(labels),
                    piece_sizes=dict(sorted(sizes.items())), chains_using_a_2cycle_twice=rep))
json.dump(out, open(sys.argv[-1], 'w'), indent=1); print(json.dumps(out, indent=1))
