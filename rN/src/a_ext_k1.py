#!/usr/bin/env python3
"""Round N (section 4) -- kappa = 1 single-visit options of an A bundle that are NOT single-piece
openings, by structural enumeration, and their effect on single-A bridges between phi options.

A visit of internal cost 1 without a split is two zero-excess segments joined by one w = 4 jump.
Inside one A the zero-excess segments are standard intervals of the trail cycle and rotated pieces;
the rotated pieces whose removal leaves ONE interval are (a) one full chain K entered at position i
(i = 2..7), (b) the reverse-alternative pair K (entered at p7) -> K-1 (entered at p2).  Hence the
candidates are  [rotated piece] -> jump -> [interval]  and  [interval] -> jump -> [rotated piece].
(Split-based kappa = 1 visits are the F-step openings, already single-piece, or use the 24 special
F7p7 -> S5p2 arcs; those are enumerated too.)  Every candidate path is rebuilt run by run and its
internal cost recomputed exactly; only paths covering all runs once with cost 1 are kept.
Output: options (t, v, y, x) and the bridge comparison tau1_ext vs tau1 on phi option pairs.
usage: a_ext_k1.py FAMILY.json E.npy TAU1.npy OUT.json"""
import sys, os, json
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import options as OP
from famstruct import Fam

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def internal_cost(runs_seq):
    """sum (w - 2) over the path minus (k - 1) for k chains is computed by caller; here sum(w-2)"""
    return sum(wt(last(a), b) - 2 for a, b in zip(runs_seq, runs_seq[1:]))

def main():
    fam, opts = OP.load(sys.argv[1]); E = np.load(sys.argv[2]); tau = np.load(sys.argv[3])
    T = len(fam["trails"])
    res_opts = []
    for v in (0, 1):
        fm = Fam(sys.argv[1], [v] * T)
        for t in range(T):
            if len(fm.trail_runs[t]) != 672: continue
            chs = fm.trail_chains[t]; nc = len(chs)
            runs = fm.runs
            kT = nc
            def chain_runs(ci, start_pos=1):
                rr = fm.chains[chs[ci % nc]]["runs"]
                j = start_pos - 1
                return rr[j:] + rr[:j]
            def interval(a, b):          # chains a..b (cyclic, inclusive) standard
                seq = []; i = a
                while True:
                    seq += fm.chains[chs[i % nc]]["runs"]
                    if i % nc == b % nc: break
                    i += 1
                return seq
            cands = []
            for K in range(nc):
                ch = fm.chains[chs[K]]
                if not ch["full"]: continue
                for i in range(2, 8):
                    R = chain_runs(K, i)
                    rest = interval(K + 1, K - 1)
                    cands.append(R + rest); cands.append(rest + R)
                # reverse-alternative pair: K at p7, then K-1 at p2
                prev = fm.chains[chs[(K - 1) % nc]]
                if prev["full"]:
                    R = chain_runs(K, 7) + chain_runs(K - 1, 2)
                    rest = interval(K + 1, K - 2)
                    cands.append(R + rest); cands.append(rest + R)
            seen = set()
            for seq in cands:
                if len(seq) != 672 or len(set(seq)) != 672: continue
                st = [runs[r] for r in seq]
                kap = internal_cost(st) - (kT - 1)
                if kap != 1: continue
                key = (seq[0], seq[-1])
                if key in seen: continue
                seen.add(key)
                res_opts.append(dict(t=t, v=v, y=runs[seq[0]], x=runs[seq[-1]], kappa=1))
    # single-piece pairs (to exclude duplicates)
    sp = {(o["entry"], last(o["exit"])[1:] + last(o["exit"])[:1] if False else None) for o in opts}
    print(json.dumps(dict(extended_A_k1=len(res_opts), by_trail_version=dict(Counter("%d/%d" % (o["t"], o["v"]) for o in res_opts)))), flush=True)
    # bridge comparison: tau1_ext(o, o') = min over ext options of (w(exit(o), y) - 3) + (w(last(x), entry(o')) - cut(o') - 1)
    phi = [i for i, o in enumerate(opts) if o["m"] == 42]
    ex_phi = [opts[i]["exit"] for i in phi]; en_phi = [opts[i]["entry"] for i in phi]
    cut_phi = np.array([opts[i]["cut"] for i in phi])
    Y = [o["y"] for o in res_opts]; Xl = [last(o["x"]) for o in res_opts]
    Win = OP.weight_block(ex_phi, Y).astype(np.int16)                 # phi exit -> ext entry
    Wout = OP.weight_block(Xl, en_phi).astype(np.int16)               # ext exit -> phi entry
    e_in = Win - 4 + 1
    e_out = Wout - cut_phi[None, :] - 1
    best = np.full((len(phi), len(phi)), 99, np.int16)
    for v in range(0, 4):
        M = np.zeros_like(best, dtype=bool)
        for a in range(0, v + 1):
            L = (e_in == a).astype(np.float32); Rm = (e_out <= v - a).astype(np.float32)
            M |= (L @ Rm) > 0
        best[(best == 99) & M] = v
    tp = np.array([opts[i]["t"] for i in phi])
    same = tp[:, None] == tp[None, :]
    best[same] = 99
    T1 = tau.astype(np.int16).copy(); T1[same] = 99
    improved = (best < T1)
    out = dict(extended_A_k1=len(res_opts),
               tau1_ext_hist=dict(sorted(Counter(best[~same].ravel().tolist()).items())),
               pairs_where_ext_beats_single_piece=int(improved.sum()),
               improvement_hist=dict(sorted(Counter((T1[improved] - best[improved]).tolist()).items())),
               min_tau_overall=int(np.minimum(best, T1)[~same].min()))
    json.dump(dict(summary=out, options=[dict(t=o["t"], v=o["v"], y="".join(map(str, o["y"])), x="".join(map(str, o["x"])), kappa=1) for o in res_opts]),
              open(sys.argv[4], "w"))
    print(json.dumps(out))

if __name__ == "__main__":
    main()
