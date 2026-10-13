#!/usr/bin/env python3
"""Round L -- local search over the CLUSTER ORDER of the hybrid relinking GTSP, with exact
re-optimisation of the cut choices for every order (layered shortest path / Viterbi).

For a fixed order T_1..T_m of the closed trails the best choice of cut nodes is a shortest path in a
layered graph: layer i = nodes of T_i (versions included), arc o -> o' (o in T_i, o' in T_{i+1}) of
cost w(exit(o), entry(o')) - cut(o'), first layer cost -cut(o).  Arcs: every boundary weight
w <= WMAX (exact: all perms reachable from exit(o) with weight <= WMAX are enumerated).
Moves: relocate one cluster (all positions), swap two clusters, reverse a segment; first
improvement; restarts from the order given by a seed word (its trail order) or from a file.
Every improved route is rebuilt and measured from scratch; words <= 46186 are written out.
usage: hybrid_order_ls.py FAMILY_WORD [SEED_WORD] [WMAX] [iters] [--both]"""
import sys, os, json, time, itertools, random
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hybrid_relink as H
import r0_decompose as RD

def main():
    fam = sys.argv[1]; seed = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else fam
    WMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    ITERS = int(sys.argv[4]) if len(sys.argv) > 4 else 50
    BOTH = "--both" in sys.argv
    t0 = time.time()
    seqs, L0, K, alt = H.closed_trails(fam)
    T = len(seqs)
    const = 8 + sum(9 * (len(s) // 8) for s in seqs) + K
    nodes = []; nid = {}; versions = []; by_cl = defaultdict(list)
    for ti, s in enumerate(seqs):
        vs = [s] + ([alt[ti]] if BOTH and alt[ti] is not None else [])
        for s_ in vs:
            vi = len(versions); versions.append((ti, s_))
            for i in range(len(s_)):
                j = len(nodes)
                nid.setdefault(s_[i], []).append(j); by_cl[ti].append(j)
                nodes.append((ti, s_[i], s_[i - 1], H.wt(s_[i - 1], s_[i]), vi, i))
    # out-arcs per node grouped by target cluster: arcs[o][T'] = list of (cost, o')
    out = [defaultdict(list) for _ in nodes]
    for a, (ta, entry, exitp, ca, va, ia) in enumerate(nodes):
        u = exitp
        for w_ in range(2, WMAX + 1):
            for perm in itertools.permutations(u[:w_]):
                v = u[w_:] + perm
                if H.wt(u, v) != w_: continue
                for b in nid.get(v, []):
                    tb = nodes[b][0]
                    if tb != ta: out[a][tb].append((w_ - nodes[b][3], b))
    print(json.dumps(dict(nodes=len(nodes), build_sec=round(time.time() - t0, 1))), flush=True)
    INF = 10 ** 9
    def evaluate(order):
        best = {o: -nodes[o][3] for o in by_cl[order[0]]}
        back = [dict()]
        for i in range(1, len(order)):
            nb = {}; bk = {}
            tgt = order[i]
            for o, c in best.items():
                for cc, o2 in out[o].get(tgt, ()):
                    v = c + cc
                    if v < nb.get(o2, INF): nb[o2] = v; bk[o2] = o
            if not nb: return INF, None
            best = nb; back.append(bk)
        o = min(best, key=best.get); cost = best[o]
        path = [o]
        for i in range(len(order) - 1, 0, -1):
            o = back[i][o]; path.append(o)
        return cost, path[::-1]
    # seed order: the trail order of the seed word mapped to clusters
    cl_of = {}
    for ti, s in enumerate(seqs):
        for p in s: cl_of[p] = ti
    w = RD.load(seed); st = RD.runs_of(w)
    order = []
    for p in st:
        c = cl_of[p]
        if not order or order[-1] != c:
            if c not in order: order.append(c)
    assert sorted(order) == list(range(T)), "seed word does not visit the family's trails"
    cost, path = evaluate(order)
    print(json.dumps(dict(start_L=const + cost if cost < INF else None, sec=round(time.time() - t0, 1))), flush=True)
    rng = random.Random(1)
    best_cost, best_order, best_path = cost, order, path
    for it in range(ITERS):
        improved = False
        moves = []
        for i in range(T):
            for j in range(T):
                if i != j: moves.append(("rel", i, j))
        for i in range(T):
            for j in range(i + 1, T): moves.append(("swap", i, j))
        for i in range(T):
            for j in range(i + 2, T + 1): moves.append(("rev", i, j))
        rng.shuffle(moves)
        for mv in moves:
            o = list(best_order)
            if mv[0] == "rel":
                c = o.pop(mv[1]); o.insert(mv[2], c)
            elif mv[0] == "swap":
                o[mv[1]], o[mv[2]] = o[mv[2]], o[mv[1]]
            else:
                o[mv[1]:mv[2]] = o[mv[1]:mv[2]][::-1]
            c, p = evaluate(o)
            if c < best_cost:
                best_cost, best_order, best_path = c, o, p; improved = True
                print(json.dumps(dict(iter=it, move=mv[0], L=const + c, sec=round(time.time() - t0, 1))), flush=True)
                break
        if not improved: break
    # rebuild and measure
    route = []
    for j in best_path:
        ti, entry, exitp, c, vi, i0 = nodes[j]
        s_ = versions[vi][1]; route += s_[i0:] + s_[:i0]
    assert len(route) == 40320 and len(set(route)) == 40320
    Lm = 8 + sum(H.wt(route[i], route[i + 1]) for i in range(len(route) - 1))
    res = dict(predicted=const + best_cost, measured=Lm, cuts={str(k): sum(1 for j in best_path if nodes[j][3] == k) for k in (1, 2, 3)},
               wmax=WMAX, both=BOTH, sec=round(time.time() - t0, 1))
    if Lm <= 46186:
        word = list(route[0])
        for p_, q_ in zip(route, route[1:]):
            c = H.wt(p_, q_); word += list(q_[8 - c:])
        tag = os.path.basename(fam).replace("superperm8_", "").replace(".txt", "")
        outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_ls_{Lm}_from_{tag}.txt")
        open(outp, "w").write("".join(str(c + 1) for c in word) + "\n"); res["file"] = outp
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
