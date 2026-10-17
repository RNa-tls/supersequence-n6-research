#!/usr/bin/env python3
"""Round O -- near-optimal trail orders: breadth-first plateau search from the 46185 order over
relocations (one trail, or a block of 2-3 consecutive trails) and swaps, keeping every order with
exact F(pi) <= FMAX.  Also reports whether any order with F <= 22 is met (it would be a J <= 99 word).
usage: near_orders.py FAMILY.json E.npy AUDIT.json FMAX MAX_EXPAND OUT.json"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order as FA

def neighbours(p):
    n = len(p)
    for L in (1, 2, 3):
        for i in range(n - L + 1):
            seg = p[i:i + L]; rest = p[:i] + p[i + L:]
            for j in range(len(rest) + 1):
                if j != i: yield tuple(rest[:j] + seg + rest[j:])
    for i in range(n):
        for j in range(i + 1, n):
            q = list(p); q[i], q[j] = q[j], q[i]; yield tuple(q)

def main():
    fam, E_p, audit, fmax, maxexp, out = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    fo = FA.FixedOrder(fam, E_p)
    base = tuple(r["trail"] for r in json.load(open(audit))["table"])
    val = {base: fo.F(list(base))}; frontier = [base]; expanded = 0; t0 = time.time(); best = val[base]
    while frontier and expanded < maxexp:
        frontier.sort(key=lambda p: val[p]); p = frontier.pop(0); expanded += 1
        for q in neighbours(list(p)):
            if q in val: continue
            v = fo.F(list(q)); val[q] = v
            if v <= fmax: frontier.append(q)
            best = min(best, v)
        if expanded % 10 == 0:
            print(json.dumps(dict(expanded=expanded, kept=sum(1 for v in val.values() if v <= fmax), evaluated=len(val), best=best, t=round(time.time() - t0, 1))), flush=True)
    kept = sorted(((v, list(p)) for p, v in val.items() if v <= fmax))
    from collections import Counter
    json.dump(dict(fmax=fmax, expanded=expanded, evaluated=len(val), best=best, hist=dict(Counter(v for v, _ in kept)), orders=[dict(F=v, order=p) for v, p in kept]), open(out, "w"))
    print(json.dumps(dict(evaluated=len(val), best=best, hist=dict(Counter(v for v, _ in kept)))))

main()
