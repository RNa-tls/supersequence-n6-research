#!/usr/bin/env python3
"""Round S -- the cheapest cover cycles (brackets) of the option graph.
A cover cycle of a bracket tree is a closed walk  u -> z_1 -> ... -> z_k -> u  through options of k + 1 DIFFERENT trails
(u = anchor, z_i = mains); its cost is the sum of e over its arcs and the bracket adds 1 + cost to G.
The zero graph (arcs with e = 0) has no cycle, so every cover cycle costs >= 1.  This program enumerates
  * all simple zero paths (distinct trails): their numbers by length (longest = 5 options);
  * all cover cycles of cost 1 and of cost 2, by number of vertices, with their orbits under the family group and the
    trails involved.
Every cycle is counted once (start = its option of least index).
usage: cheap_cycles.py RUNS.bin GROUP.bin OUT.json [MAXCOST]"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains
from collections import Counter

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs)
    cache = os.environ.get("W_CACHE")
    W = np.load(cache) if cache and os.path.exists(cache) else runs_io.weight_matrix(runs)
    ci = chains.chain_info(W, tofs, mlen); cut = ci["cut"]
    T = np.array([x[0] for x in tv]); pred = np.zeros(N, np.int64)
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]; m = mlen[t]
            for k in range(m): pred[o0 + k] = o0 + (k - 1) % m
    E = (W[pred, :].astype(np.int16) - cut[None, :].astype(np.int16) - 1).astype(np.int8)
    cross = T[:, None] != T[None, :]
    assert int(E[cross].min()) == 0
    MAXC = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    adj = [[] for _ in range(N)]
    for c in range(MAXC + 1):
        ai, aj = np.nonzero((E == c) & cross)
        for a, b in zip(ai.tolist(), aj.tolist()): adj[a].append((b, c))
    Tl = T.tolist(); El = E
    # group action on options (for orbits)
    f = open(sys.argv[2], "rb"); G = struct.unpack("<i", f.read(4))[0]
    tperm = np.frombuffer(f.read(4 * G * 30), np.int32).reshape(G, 30); operm = np.frombuffer(f.read(4 * G * N), np.int32).reshape(G, N)
    zero_paths = Counter(); cycles = {c: [] for c in range(1, MAXC + 1)}
    sys.setrecursionlimit(100000)
    def dfs(path, used, cost, start, only_zero):
        last = path[-1]; k = len(path)
        if only_zero: zero_paths[k] += 1
        if k >= 2:
            cl = int(El[last, start]) + cost
            if 1 <= cl <= MAXC and Tl[last] != Tl[start]: cycles[cl].append(tuple(path))
        for b, c in adj[last]:
            if cost + c > MAXC or Tl[b] in used: continue
            if b < start and not (only_zero and c == 0): continue      # canonical start for the cycles
            if b < start:
                # zero path continuing below the start: only for the zero-path statistics
                used.add(Tl[b]); path.append(b); dfs_zero(path, used); path.pop(); used.discard(Tl[b]); continue
            used.add(Tl[b]); path.append(b); dfs(path, used, cost + c, start, only_zero and c == 0); path.pop(); used.discard(Tl[b])
    def dfs_zero(path, used):
        zero_paths[len(path)] += 1; last = path[-1]
        for b, c in adj[last]:
            if c != 0 or Tl[b] in used: continue
            used.add(Tl[b]); path.append(b); dfs_zero(path, used); path.pop(); used.discard(Tl[b])
    for o in range(N): dfs([o], {Tl[o]}, 0, o, True)
    out = dict(options=N, zero_arcs=int(((E == 0) & cross).sum()), zero_paths_by_number_of_options=dict(sorted(zero_paths.items())),
               longest_zero_path_options=max(zero_paths))
    isA = [mlen[t] > 100 for t in range(30)]
    for c in range(1, MAXC + 1):
        cyc = cycles[c]; by = Counter(len(p) for p in cyc)
        # orbits: canonical form of a cycle = lexicographically least rotation; orbit under the group
        def canon(p):
            i = p.index(min(p)); return p[i:] + p[:i]
        S = set(canon(p) for p in cyc); assert len(S) == len(cyc)
        seen = set(); orbits = []
        for p in sorted(S):
            if p in seen: continue
            orb = set(canon(tuple(int(operm[g][o]) for o in p)) for g in range(G))
            assert orb <= S, "group image of a cheap cycle is not a cheap cycle"
            seen |= orb; orbits.append((p, len(orb)))
        comp = Counter((len(p), sum(isA[Tl[o]] for o in p)) for p in cyc)
        trailsets = Counter(tuple(sorted(Tl[o] for o in p)) for p in cyc)
        out["cost_%d_cycles" % c] = dict(total=len(cyc), by_number_of_vertices=dict(sorted(by.items())), orbits=len(orbits), orbit_sizes=dict(Counter(n for _, n in orbits)),
                                         by_vertices_and_A_vertices={"%d,%d" % k: v for k, v in sorted(comp.items())}, distinct_trail_sets=len(trailsets),
                                         representatives=[dict(options=[[Tl[o], int(tv[o][1]), int(tv[o][2])] for o in p], e=[int(El[p[i], p[(i + 1) % len(p)]]) for i in range(len(p))], orbit=n) for p, n in orbits[:200]])
        print("cost", c, "cycles", len(cyc), "by size", dict(sorted(by.items())), "orbits", len(orbits), "distinct trail sets", len(trailsets))
    # second enumeration of the cost-1 cycles: a cost-1 cycle is a simple zero path closed by one arc with e = 1
    zadj = [[b for (b, c) in adj[a] if c == 0] for a in range(N)]
    alt = Counter()
    def zp(path, used):
        if len(path) >= 2 and int(El[path[-1], path[0]]) == 1: alt[len(path)] += 1
        for b in zadj[path[-1]]:
            if Tl[b] in used: continue
            used.add(Tl[b]); path.append(b); zp(path, used); path.pop(); used.discard(Tl[b])
    for o in range(N): zp([o], {Tl[o]})
    out["cost_1_cycles_second_enumeration_zero_path_plus_closing_arc"] = dict(total=sum(alt.values()), by_number_of_vertices=dict(sorted(alt.items())),
                                                                              agrees=(sum(alt.values()) == out["cost_1_cycles"]["total"]))
    json.dump(out, open(sys.argv[3], "w"), indent=1)
    print("zero paths", out["zero_paths_by_number_of_options"], "cost-1 second enumeration", dict(alt))

main()
