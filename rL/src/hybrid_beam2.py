#!/usr/bin/env python3
"""Round L -- beam search for hybrid relinking with TWO-PIECE visits of bundles (heuristic).

Extends hybrid_beam.py: a large closed trail (bundle) may be entered at a cut e1, left early at a
second cut e2 (a cost-3 join of the trail), and its remaining arc (head(e2) .. tail(e1)) visited
later, entered exactly at head(e2).  Exact length:
     L = const + sum boundary weights - sum of ALL cut weights.
At most MAXPEND pieces may be pending at a time.  Every complete route is rebuilt and measured.
usage: hybrid_beam2.py WORD [EXC] [BEAM] [MAXPEND] [--both|--allver]"""
import sys, os, json, time, itertools
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hybrid_relink as H

def main():
    path = sys.argv[1]; EXC = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    BEAM = int(sys.argv[3]) if len(sys.argv) > 3 else 50000
    MAXPEND = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    BOTH = "--both" in sys.argv; ALLV = "--allver" in sys.argv
    t0 = time.time()
    seqs, L0, K, alt = H.closed_trails(path)
    if ALLV:
        cache = os.path.join(os.environ.get("RL_CACHE", "."), "versions_" + os.path.basename(path) + ".pkl")
        V = H.all_versions(seqs, cache)
    T = len(seqs)
    const = 8 + sum(9 * (len(s) // 8) for s in seqs) + K
    nodes = []; nid = {}; versions = []
    for ti, s in enumerate(seqs):
        vs = V[ti] if ALLV else [s] + ([alt[ti]] if BOTH and alt[ti] is not None else [])
        for s_ in vs:
            vi = len(versions); versions.append((ti, s_))
            for i in range(len(s_)):
                nid.setdefault(s_[i], []).append(len(nodes))
                nodes.append((ti, s_[i], s_[i - 1], H.wt(s_[i - 1], s_[i]), vi, i))
    # arcs indexed by EXIT perm: list of (w, target node)
    out = defaultdict(list)
    exits = {nd[2] for nd in nodes}
    for u in exits:
        for w_ in range(2, 5 + EXC):
            for perm in itertools.permutations(u[:w_]):
                v = u[w_:] + perm
                if H.wt(u, v) != w_: continue
                for b in nid.get(v, []):
                    if w_ - nodes[b][3] - 1 <= EXC or (w_ <= 4 + EXC and nodes[b][3] == 3): out[u].append((w_, b))
    big = {ti for ti, s in enumerate(seqs) if len(s) > 400}
    print(json.dumps(dict(nodes=len(nodes), exits=len(exits), arcs=sum(len(v) for v in out.values()),
                          build_sec=round(time.time() - t0, 1))), flush=True)
    # state: key (exit perm, done mask, pending tuple) -> (cost, path)
    # path items: (node, piece_end_index) meaning: visit versions[node.vi] from node.i up to (excl.) end index
    beam = {}
    for b, nd in enumerate(nodes):
        ti, entry, exitp, cut, vi, i = nd
        m0 = len(versions[vi][1])
        key = (exitp, 1 << ti, ())
        if key not in beam or beam[key][0] > -cut: beam[key] = (-cut, ((vi, i, m0),))
        if ti in big and MAXPEND > 0:
            s_ = versions[vi][1]; m = len(s_)
            for d in range(8, m - 8):
                j = (i + d) % m
                if H.wt(s_[j - 1], s_[j]) != 3: continue
                key = (s_[j - 1], 1 << ti, ((ti, s_[j], exitp, vi, j, i),))
                val = (-cut - 3, ((vi, i, d),))
                if key not in beam or beam[key][0] > val[0]: beam[key] = val
    items = sorted(beam.items(), key=lambda kv: kv[1][0])[:BEAM * 4]
    best_full = None
    for depth in range(1, 2 * T + 2):
        nxt = {}
        for (u, mask, pend), (cost, pth) in items:
            pend_entry = {p[1]: p for p in pend}
            for w_, b in out[u]:
                ti, entry, exitp, cut, vi, i = nodes[b]
                if entry in pend_entry:
                    p = pend_entry[entry]
                    if p[3] != vi: continue
                    npend = tuple(q for q in pend if q is not p)
                    mm = len(versions[vi][1])
                    key = (p[2], mask, npend); val = (cost + w_, pth + ((vi, p[4], (p[5] - p[4]) % mm),))
                    if key not in nxt or nxt[key][0] > val[0]: nxt[key] = val
                    continue
                if mask >> ti & 1: continue
                if w_ - cut - 1 > EXC: continue
                key = (exitp, mask | (1 << ti), pend); val = (cost + w_ - cut, pth + ((vi, i, len(versions[vi][1])),))
                if key not in nxt or nxt[key][0] > val[0]: nxt[key] = val
                if ti in big and len(pend) < MAXPEND:
                    s_ = versions[vi][1]; m = len(s_)
                    for d in range(8, m - 8):
                        j = (i + d) % m
                        if H.wt(s_[j - 1], s_[j]) != 3: continue
                        key = (s_[j - 1], mask | (1 << ti), tuple(sorted(pend + ((ti, s_[j], exitp, vi, j, i),))))
                        val = (cost + w_ - cut - 3, pth + ((vi, i, d),))
                        if key not in nxt or nxt[key][0] > val[0]: nxt[key] = val
        if not nxt: break
        items = sorted(nxt.items(), key=lambda kv: kv[1][0])[:BEAM]
        done = [(k, v) for k, v in items if k[1] == (1 << T) - 1 and not k[2]]
        if done:
            c = done[0][1][0]
            if best_full is None or c < best_full[0]: best_full = (c, done[0][1][1])
        print(json.dumps(dict(depth=depth, states=len(nxt), best_cost=items[0][1][0],
                              complete_best=None if best_full is None else const + best_full[0], sec=round(time.time() - t0, 1))), flush=True)
        if all(k[1] == (1 << T) - 1 and not k[2] for k, v in items): break
    if best_full is None: print(json.dumps(dict(result="no complete route"))); return
    cost, pth = best_full
    route = []
    for vi, st, ln in pth:
        s_ = versions[vi][1]; m = len(s_)
        route += [s_[(st + t) % m] for t in range(ln)]
    assert len(route) == 40320 and len(set(route)) == 40320, ("rebuild", len(route), len(set(route)))
    Lm = 8 + sum(H.wt(route[i], route[i + 1]) for i in range(len(route) - 1))
    res = dict(predicted=const + cost, measured=Lm, exc=EXC, beam=BEAM, maxpend=MAXPEND, both=BOTH, allver=ALLV,
               sec=round(time.time() - t0, 1))
    if Lm <= 46185:
        word = list(route[0])
        for p_, q_ in zip(route, route[1:]):
            c = H.wt(p_, q_); word += list(q_[8 - c:])
        tag = os.path.basename(path).replace("superperm8_", "").replace(".txt", "")
        outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"hybrid_beam2_{Lm}_from_{tag}.txt")
        open(outp, "w").write("".join(str(c + 1) for c in word) + "\n"); res["file"] = outp
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
