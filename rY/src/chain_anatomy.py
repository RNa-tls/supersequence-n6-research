#!/usr/bin/env python3
"""Round Y -- anatomy of the extremal chains of Round X (dump format: r, d, v, pieces, entries).
For each chain: the moving symbol z of each row (last symbol of the row's first block entry), the seam type between
consecutive rows (d: z kept, C changed; e: z and C kept; b/c/f: z changes), the 2-cycle (z, C) of each row, and the
number of classes of each used 2-cycle that the chain leaves uncovered (the 'complement demand').
usage: chain_anatomy.py DUMP.jsonl.gz [LIMIT]"""
import sys, json, gzip, collections
def cls(w):  # rotation class of a permutation word: rotate so that '8' is first
    i = w.index('8'); return w[i:] + w[:i]
def twocycle(entry):
    z = entry[-1]; c = cls(entry)
    # C = cyclic order of the other symbols, canonical rotation starting at the smallest symbol
    i = c.index(z); rest = c[i + 1:] + c[:i]
    j = rest.index(min(rest)); return z, rest[j:] + rest[:j]
def exitw(entry): return entry[-1] + entry[:-1]            # rot^7(entry) = z e1 ... e7
def seamtype(prev_exit, nxt_entry):
    z, v1, v2 = prev_exit[0], prev_exit[1], prev_exit[2]
    if nxt_entry[:5] != prev_exit[3:]: return '?'
    t = nxt_entry[5:]
    return {z + v2 + v1: 'c', v1 + z + v2: 'b', v1 + v2 + z: 'e', v2 + z + v1: 'f', v2 + v1 + z: 'd'}.get(t, '?')
def door(e): return e[1:-1] + e[0] + e[-1]  # entry e1..e7 z -> next entry e2..e7 e1 z
def main():
    f = gzip.open(sys.argv[1], 'rt'); lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    tot = collections.Counter(); nchains = 0
    for k, l in enumerate(f):
        if k >= lim: break
        d = json.loads(l)
        if "pieces" not in d: continue
        P, EB = d["pieces"], d["entries"]; nchains += 1
        assert len(P) == d['r'] and len(EB) == sum(P)
        starts = [sum(P[:i]) for i in range(len(P))]
        E = [EB[s] for s in starts]
        for i in range(len(P)):          # the blocks of a piece follow by doors
            e = E[i]
            for q in range(P[i]):
                assert EB[starts[i] + q] == e, (i, q); e = door(e)
        zs = [e[-1] for e in E]; tc = [twocycle(e) for e in E]
        seams = []
        for i in range(len(P) - 1):
            e = EB[starts[i] + P[i] - 1]
            seams.append(seamtype(exitw(e), E[i + 1]))
        used = collections.Counter(tc)
        st = collections.Counter(seams); labels = collections.Counter(zs)
        tot.update(st)
        if k < 12 or d['v'] >= 56:
            print(f"r={d['r']} d={d['d']} v={d['v']} labels={dict(labels)} seams={dict(st)} groups={len(used)} repeated_groups={sum(1 for g, c in used.items() if c > 1)}")
            print("   pieces:", ''.join(str(x) for x in P))
            print("   seams :", ''.join(seams))
    print("chains", nchains, "seam types total", dict(tot))
main()
