#!/usr/bin/env python3
"""Round T -- checker B for the fixed-selection single-opening optimum.  Independent of csrc/hk_exact.c and of
src/options.py: it enumerates the arcs itself from the cyclic trail words (forward scan from the arc's end) and runs a
BACKWARD dynamic programme in numpy:
    h[U][o] = least J of a sequence of arcs that starts with arc o and uses exactly the trails of U.
J = sum of arc costs + sum over joins (5 - overlap);  length = 46149 + J.
usage: hk_check_b.py SEL TSV BASE OUT.json [--maxcost C] [--ovcap K] [--plant "t1 s1 d1 t2 s2 d2 v"] [--plans P1 P2 ..]"""
import sys, os, json, time, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_from_selection import read_sel, trails, canon
a = sys.argv[1:]; selp, tsvp, basep, outp = a[:4]
maxcost = int(a[a.index("--maxcost") + 1]) if "--maxcost" in a else 2
ovcap = int(a[a.index("--ovcap") + 1]) if "--ovcap" in a else 7
plant = [int(x) for x in a[a.index("--plant") + 1].split()] if "--plant" in a else None
plans = a[a.index("--plans") + 1:] if "--plans" in a else []
mine = {canon(c) for c, _ in trails(read_sel(selp))}; base = open(basep).read().strip()
cyc = []
for l in open(tsvp):
    p = l.split("\t"); c = base[int(p[3]):int(p[3]) + int(p[2])]; assert canon(c) in mine; cyc.append(c)
T = len(cyc); assert T == 16
# ---- arcs: (trail, start s, dropped d); enumerated from the END e of the arc going forward
arcs = []
for t, c in enumerate(cyc):
    R = len(c); d3 = c * 3; win = [d3[i:i + 8] for i in range(R)]; perm = np.array([len(set(x)) == 8 for x in win])
    mult = {}
    for x, p in zip(win, perm):
        if p: mult[x] = mult.get(x, 0) + 1
    for e in np.nonzero(perm)[0]:
        gone = {}; q = 1
        while q < R:
            j = (e + q) % R
            if perm[j]:
                if 2 - (q - 1) <= maxcost: arcs.append((t, int(j), q - 1))
                x = win[j]
                if mult[x] - gone.get(x, 0) <= 1: break
                gone[x] = gone.get(x, 0) + 1
            q += 1
arcs.sort(); no = len(arcs)
tr = np.array([x[0] for x in arcs]); cost = np.array([2 - x[2] for x in arcs], np.int16)
head = []; tail = []
for t, s, d in arcs:
    c = cyc[t]; R = len(c); piece = (c[s:] + c + c)[:R + 7 - d]; head.append(piece[:7]); tail.append(piece[-7:])
def codes(strs, k, pre): return np.array([int(x[:k] if pre else x[7 - k:], 8) for x in strs], np.int64)
order = {}; starts = {}; look = {}
for k in range(1, ovcap + 1):
    hc = codes(head, k, True); tc = codes(tail, k, False); o = np.argsort(hc, kind="stable"); keys, st = np.unique(hc[o], return_index=True)
    order[k] = o; starts[k] = st; pos = np.searchsorted(keys, tc); pos[pos >= len(keys)] = 0; hit = keys[pos] == tc
    look[k] = (pos, hit)                           # for a tail: index of the matching head key, and whether it exists
INF = 10 ** 4
pl = None
if plant:
    i = arcs.index(tuple(plant[0:3])); j = arcs.index(tuple(plant[3:6])); pl = (i, j, plant[6])
t0 = time.time(); bytrail = [np.nonzero(tr == t)[0] for t in range(T)]
prev = {}                                          # U -> (min over all arcs, {k: per-key minima}, value at the planted arc j)
full = (1 << T) - 1; hfull = None; nstate = 0; dig = hashlib.sha256()
for size in range(1, T + 1):
    cur = {}
    for U in range(1, 1 << T):
        if bin(U).count("1") != size: continue
        h = np.full(no, INF, np.int16)
        for t in range(T):
            if not U >> t & 1: continue
            idx = bytrail[t]
            if size == 1: h[idx] = cost[idx]; continue
            m0, mk, hj = prev[U & ~(1 << t)]
            best = np.full(len(idx), m0 + 5, np.int16)
            for k in range(1, ovcap + 1):
                pos, hit = look[k]; v = mk[k][pos[idx]] + (5 - k); best = np.where(hit[idx] & (v < best), v, best)
            if pl and tr[pl[0]] == t and hj < INF:
                q = np.nonzero(idx == pl[0])[0][0]; best[q] = min(best[q], pl[2] + hj)
            h[idx] = np.minimum(best + cost[idx], INF)
        nstate += int((h < INF).sum())
        cur[U] = (int(h.min()), {k: np.minimum.reduceat(h[order[k]], starts[k]) for k in range(1, ovcap + 1)}, int(h[pl[1]]) if pl else INF)
        if U == full: hfull = h
    prev = cur
    print("size", size, "sets", len(cur), "%.0fs" % (time.time() - t0), file=sys.stderr, flush=True)
J = int(hfull.min()); res = dict(checker="hk_check_b (backward DP, numpy, own arc enumeration)", arcs=no, arcs_by_cost={str(c): int((cost == c).sum()) for c in sorted(set(cost.tolist()))},
    max_arc_cost=maxcost, overlap_cap=ovcap, plant=plant, optimal_J=J, optimal_length=46149 + J, first_arcs_by_J={str(v): int((hfull == v).sum()) for v in range(J, J + 4)}, states=nstate, sec=round(time.time() - t0, 1))
# ---- direct evaluation of given plans in the same arc table
ev = []
for p in plans:
    seq = [(int(x.split()[1]), int(x.split()[2]), int(x.split()[3]) - 1) for x in open(p).read().split("\n")[1:] if x.strip()]
    tot = 0; prevtail = None
    for t, s, d in seq:
        i = arcs.index((t, s, d)); tot += int(cost[i])
        if prevtail is not None:
            k = next((k for k in range(7, 0, -1) if prevtail[-k:] == head[i][:k]), 0); tot += 5 - k
        prevtail = tail[i]
    ev.append(dict(plan=os.path.basename(p), J=tot, length=46149 + tot))
res["plans"] = ev
json.dump(res, open(outp, "w"), indent=1); print(json.dumps(res))
