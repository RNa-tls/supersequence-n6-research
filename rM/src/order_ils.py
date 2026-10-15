#!/usr/bin/env python3
"""Round M (section 20) -- iterated local search over TRAIL ORDERS in the single-opening model, with
the exact (all weights 2..8) layered shortest path of trail_order_exact.py, vectorised with numpy.
Local search: first-improvement over relocations and swaps (plateau moves accepted with
probability PLATEAU); perturbation: random double bridge on the order.  Starts from a given
description or from random orders (--random).  Every new best order is rebuilt and measured.
usage: order_ils.py FAMILY.json DESC.json [--iters N] [--seed S] [--random] [--plateau P]"""
import sys, os, json, time, random, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def encoder(layers):
    """per layer: entry codes and exit suffix codes for every overlap length m = 1..6"""
    data = []
    for L in layers:
        E = np.array([o[0] for o in L], dtype=np.int64); X = np.array([o[1] for o in L], dtype=np.int64)
        cut = np.array([o[2] for o in L], dtype=np.int64)
        pre = {}; suf = {}
        for m in range(1, 7):
            pc = np.zeros(len(L), np.int64); sc = np.zeros(len(L), np.int64)
            for t in range(m):
                pc = pc * 8 + E[:, t]; sc = sc * 8 + X[:, 8 - m + t]
            pre[m] = pc; suf[m] = sc
        data.append((pre, suf, cut))
    return data

def make_eval(layers, const):
    data = encoder(layers)
    BIG = 10 ** 6
    def evaluate(order):
        pre0, suf0, cut0 = data[order[0]]
        lab = -cut0
        prev = order[0]
        for t in order[1:]:
            pre, suf, cut = data[t]; psuf = data[prev][1]
            best = np.full(len(cut), lab.min() + 8, np.int64)
            for m in range(1, 7):                    # overlap m <-> weight k = 8 - m
                k = 8 - m
                sc = psuf[m]; idx = np.argsort(sc, kind="stable"); ss = sc[idx]
                starts = np.flatnonzero(np.r_[True, ss[1:] != ss[:-1]])
                keys = ss[starts]; mins = np.minimum.reduceat(lab[idx], starts)
                pos = np.searchsorted(keys, pre[m]); pos[pos >= len(keys)] = 0
                hit = keys[pos] == pre[m]
                cand = np.where(hit, mins[pos] + k, BIG)
                best = np.minimum(best, cand)
            lab = best - cut; prev = t
        return int(const + lab.min())
    return evaluate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family"); ap.add_argument("desc")
    ap.add_argument("--iters", type=int, default=200); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--random", action="store_true"); ap.add_argument("--plateau", type=float, default=0.3)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs"))
    a = ap.parse_args()
    fam = json.load(open(a.family)); desc = json.load(open(a.desc))
    layers, const = TOE.load_layers(fam)
    ev = make_eval(layers, const)
    rnd = random.Random(a.seed)
    T = len(layers)
    order = [d[0] for d in desc["description"]]
    if a.random: rnd.shuffle(order)
    t0 = time.time()
    assert ev([d[0] for d in desc["description"]]) == TOE.evaluate(layers, const, [d[0] for d in desc["description"]])
    cur = ev(order); best = (cur, list(order))
    print(json.dumps(dict(start=cur, random=a.random, seed=a.seed)), flush=True)
    def local_search(order, cur):
        improved = True
        while improved:
            improved = False
            moves = [("r", i, j) for i in range(T) for j in range(T) if i != j] + [("s", i, j) for i in range(T) for j in range(i + 1, T)]
            rnd.shuffle(moves)
            for kind, i, j in moves:
                if kind == "r":
                    r = order[:i] + order[i + 1:]; r.insert(j, order[i])
                else:
                    r = list(order); r[i], r[j] = r[j], r[i]
                v = ev(r)
                if v < cur or (v == cur and rnd.random() < a.plateau * 0.01):
                    if v < cur: improved = True
                    order, cur = r, v
                    if improved: break
        return order, cur
    for it in range(a.iters):
        order, cur = local_search(order, cur)
        if cur < best[0]:
            best = (cur, list(order))
            v, pth = TOE.evaluate(layers, const, order, True); meas = TOE.build(fam, pth)
            print(json.dumps(dict(iter=it, new_best=cur, measured=meas, sec=round(time.time() - t0, 1))), flush=True)
            if meas < 46185:
                p = os.path.join(a.out, "order_ils_%d_s%d.txt" % (meas, a.seed))
                open(p, "w").write(json.dumps(dict(order=order, value=v)) + "\n")
        # perturbation: double bridge on the best order
        o = list(best[1])
        i, j, k = sorted(rnd.sample(range(1, T), 3))
        order = o[:i] + o[j:k] + o[i:j] + o[k:]
        cur = ev(order)
        if it % 10 == 0:
            print(json.dumps(dict(iter=it, current=cur, best=best[0], sec=round(time.time() - t0, 1))), flush=True)
    print(json.dumps(dict(final_best=best[0], order=best[1], sec=round(time.time() - t0, 1))), flush=True)

if __name__ == "__main__":
    main()
