#!/usr/bin/env python3
"""Round P, section 27 probe -- two-piece splits of a single-opening word.
The word is the greedy overlap concatenation of its permutation route (pieces of runs; a run = the 8 left
rotations of its first permutation).  length = 8 + sum of overlap weights w over the 40319 route transitions.
For every trail T of the word (piece = runs k1, k1+1, ..., k1-1 of one version) and every second cut d
(1 <= d < m) the trail is split into HEAD = runs k1..k1+d-1 and TAIL = runs k1+d..k1-1; one of the two pieces
stays at T's place, the other is inserted at any other boundary of the piece sequence (also before the first or
after the last piece).  The exact length change is computed from the changed transitions only, and the best
candidates are rebuilt and re-measured from scratch.
usage: split_probe.py FAMILY.json DESCRIPTION.json [DESCRIPTION.json ...]"""
import sys, json

def w(x, y):
    for s in range(1, 8):
        if x[s:] == y[:8 - s]: return s
    return 8

def main():
    fam = json.load(open(sys.argv[1])); RUNS = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]): RUNS[t, v] = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
    first = lambda t, v, k: RUNS[t, v][k % len(RUNS[t, v])]
    last = lambda t, v, k: (lambda p: p[7:] + p[:7])(first(t, v, k))
    def length(pieces):
        route_w = 0; prev = None
        for (t, v, k0, n) in pieces:
            for i in range(n):
                p = first(t, v, k0 + i)
                if prev is not None: route_w += w(prev, p)
                route_w += 7; prev = last(t, v, k0 + i)
        return 8 + route_w
    out = []
    for dp in sys.argv[2:]:
        desc = [tuple(x) for x in json.load(open(dp))["description"]]   # (t, v, k, m)
        base = [(t, v, k, m) for (t, v, k, m) in desc]
        L0 = length(base); P = len(base)
        entry = lambda pc: first(pc[0], pc[1], pc[2]); exitp = lambda pc: last(pc[0], pc[1], pc[2] + pc[3] - 1)
        best = []; nev = 0
        for i, (t, v, k1, m) in enumerate(base):
            prv = base[i - 1] if i > 0 else None; nxt = base[i + 1] if i + 1 < P else None
            for d in range(1, m):
                head = (t, v, k1, d); tail = (t, v, k1 + d, m - d)
                for stay, move in ((head, tail), (tail, head)):
                    rest = base[:i] + [stay] + base[i + 1:]
                    # cost of the sequence with T replaced by `stay`, relative to the base
                    dstay = 0
                    if prv is not None: dstay += w(exitp(prv), entry(stay)) - w(exitp(prv), entry(base[i]))
                    if nxt is not None: dstay += w(exitp(stay), entry(nxt)) - w(exitp(base[i]), entry(nxt))
                    # the internal transition lost at the split point (head's last run -> tail's first run)
                    dint = -w(last(t, v, k1 + d - 1), first(t, v, k1 + d))
                    if stay is tail:   # the base word's internal transition at the cut k1 is unchanged (still a piece boundary)
                        pass
                    for j in range(P + 1):          # insert `move` before rest[j] (j = P: at the end)
                        if j == i or j == i + 1: continue
                        a = rest[j - 1] if j > 0 else None; b = rest[j] if j < P else None
                        dins = 0
                        if a is not None: dins += w(exitp(a), entry(move))
                        if b is not None: dins += w(exitp(move), entry(b))
                        if a is not None and b is not None: dins -= w(exitp(a), entry(b))
                        if a is None or b is None:
                            # at the word start/end: the move piece adds only one transition
                            pass
                        delta = dstay + dint + dins + 0   # the moved piece keeps its runs' internal transitions
                        nev += 1
                        best.append((delta, i, d, stay is head, j))
        best.sort(); top = best[:20]
        checked = []
        for (delta, i, d, head_stays, j) in top[:5]:
            t, v, k1, m = base[i]; head = (t, v, k1, d); tail = (t, v, k1 + d, m - d)
            stay, move = (head, tail) if head_stays else (tail, head)
            rest = base[:i] + [stay] + base[i + 1:]; seq = rest[:j] + [move] + rest[j:]
            checked.append(dict(delta_formula=delta, length_rebuilt=length(seq), trail=t, at=i, d=d, head_stays=head_stays, insert_before=j))
        out.append(dict(description=dp, base_length=L0, evaluated=nev, best_delta=top[0][0] if top else None,
                        n_delta_le_0=sum(1 for b in best if b[0] <= 0), checked_top5=checked))
    print(json.dumps(out, indent=1))

main()
