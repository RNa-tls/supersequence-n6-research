#!/usr/bin/env python3
"""Round R -- rebuild the word of a bracket-tree configuration and measure it (independent of the C search/evaluator).
Input: a JSON line as written by ckM_eval.c (stage C): P (trail order), cycles (trail orders, each opened at its
anchor), anchor_trails (trail of the anchor of every cycle), nested_inner (-1: every anchor main is in P; i: cycle i
is anchored at a trail of the other cycle, which is anchored in P).
The exact optimum over all options is recomputed here by dynamic programming with back-pointers (numpy, options and
excess rebuilt from runs.bin), the word is assembled run by run:
    trail with main cut a and anchor cut b (same version):  pieces [a, b) and [b, a);  the cycle sits between them,
    every other trail is a single piece [a, a);
its length is measured from the run links (8 + 7 N + sum w) and every permutation is checked.
usage: bracket_witness.py RUNS.bin CONFIG.json(line) OUT_WORD.txt"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io

def main():
    runs, tv, tofs, mlen = runs_io.load(sys.argv[1]); N = len(runs)
    W = runs_io.weight_matrix(runs).astype(np.int64)
    T = np.array([x[0] for x in tv]); V = np.array([x[1] for x in tv]); K = np.array([x[2] for x in tv])
    def opt_idx(t): return np.arange(tofs[t], tofs[t] + 2 * mlen[t])
    pred = np.empty(N, np.int64)
    for t in range(30):
        for v in range(2):
            o0 = tofs[t] + v * mlen[t]
            for k in range(mlen[t]): pred[o0 + k] = o0 + (k - 1) % mlen[t]
    cut = W[pred, np.arange(N)]
    def e(a, b): return W[pred[a]][:, b] - cut[b][None, :] - 1 if np.ndim(a) else W[pred[a], b] - cut[b] - 1
    def E(oa, ob): return W[np.ix_(pred[oa], ob)] - cut[ob][None, :] - 1      # matrix e(oa_i -> ob_j)
    cfg = json.loads(open(sys.argv[2]).read().strip().splitlines()[0])
    P = cfg["P"]; Z = cfg["cycles"]; c = len(Z); AT = cfg["anchor_trails"][:c]; nest = cfg.get("nested_inner", -1)
    BIG = 10 ** 6
    def path_dp(seq, start_vec, node=None):
        """forward DP over seq (trail list); start_vec over options of seq[0]; node[t] = vector of extra costs per option.
        returns list of value vectors and back-pointers"""
        vals = [start_vec + (node[seq[0]] if node and seq[0] in node else 0)]; bps = [None]
        for i in range(1, len(seq)):
            M = vals[-1][:, None] + E(opt_idx(seq[i - 1]), opt_idx(seq[i]))
            bp = M.argmin(0); v = M[bp, np.arange(M.shape[1])]
            if node and seq[i] in node: v = v + node[seq[i]]
            vals.append(v); bps.append(bp)
        return vals, bps
    def back(seq, vals, bps, endq):
        qs = [endq]
        for i in range(len(seq) - 1, 0, -1): qs.append(int(bps[i][qs[-1]]))
        return [opt_idx(seq[i])[q] for i, q in enumerate(reversed(qs))]
    def cycle_close(seq, anchor_trail, node=None):
        """for every option u of anchor_trail: least e(u -> z1) + path + e(zl -> u) and the options used"""
        U = opt_idx(anchor_trail); best = np.full(len(U), BIG); arg = [None] * len(U)
        o1 = opt_idx(seq[0])
        for ui, u in enumerate(U):
            st = W[pred[u], o1] - cut[o1] - 1
            vals, bps = path_dp(seq, st.astype(np.int64), node)
            ol = opt_idx(seq[-1]); tot = vals[-1] + (W[pred[ol], u] - cut[u] - 1)
            q = int(tot.argmin()); best[ui] = tot[q]; arg[ui] = (vals, bps, q)
        return U, best, arg
    def node_from(U, best, main_trail):
        """node cost on main_trail's options o: least closing over anchors of the same version and a different run"""
        Om = opt_idx(main_trail); nc = np.full(len(Om), BIG); ch = np.full(len(Om), -1)
        for qi, o in enumerate(Om):
            ok = (V[U] == V[o]) & (K[U] != K[o]); cand = np.where(ok, best, BIG); j = int(cand.argmin()); nc[qi] = cand[j]; ch[qi] = j
        return nc, ch
    o_first = opt_idx(P[0]); st0 = (cut[o_first] == 2).astype(np.int64)
    choice = {}
    if nest == -1:
        node = {}; info = {}
        for i in range(c):
            U, best, arg = cycle_close(Z[i], AT[i]); nc, ch = node_from(U, best, AT[i])
            node[AT[i]] = node.get(AT[i], 0) + nc; info[i] = (U, best, arg, ch)
        if c == 2 and AT[0] == AT[1]: print(json.dumps({"warning": "both anchors on one trail: anchors may coincide; check"}))
        vals, bps = path_dp(P, st0, node); q = int(vals[-1].argmin()); G = int(vals[-1][q]) + c
        popts = back(P, vals, bps, q)
        for i in range(c):
            U, best, arg, ch = info[i]; mo = popts[P.index(AT[i])]; j = ch[mo - opt_idx(AT[i])[0]]
            vals_c, bps_c, qc = arg[j]; choice[i] = (int(U[j]), back(Z[i], vals_c, bps_c, qc))
    else:
        inner = nest; outer = 1 - inner; Tin, Tout = AT[inner], AT[outer]
        U, best, arg = cycle_close(Z[inner], Tin); nc, ch = node_from(U, best, Tin)
        Uo, besto, argo = cycle_close(Z[outer], Tout, {Tin: nc}); nco, cho = node_from(Uo, besto, Tout)
        vals, bps = path_dp(P, st0, {Tout: nco}); q = int(vals[-1].argmin()); G = int(vals[-1][q]) + c
        popts = back(P, vals, bps, q)
        mo = popts[P.index(Tout)]; jo = cho[mo - opt_idx(Tout)[0]]; vals_c, bps_c, qc = argo[jo]; zo = back(Z[outer], vals_c, bps_c, qc)
        choice[outer] = (int(Uo[jo]), zo)
        mi = zo[Z[outer].index(Tin)]; ji = ch[mi - opt_idx(Tin)[0]]; vals_i, bps_i, qi = arg[ji]; choice[inner] = (int(U[ji]), back(Z[inner], vals_i, bps_i, qi))
    # assemble: pieces of a trail given its cut set; P order with each cycle spliced after its anchor trail's first piece
    def pieces_single(o):
        t, v, k = tv[o]; m = mlen[t]; o0 = tofs[t] + v * m; return [o0 + (k + j) % m for j in range(m)]
    def piece(o_from, o_to):     # runs [o_from, o_to) of one version (cyclic), o_to == o_from means the whole cycle
        t, v, k = tv[o_from]; m = mlen[t]; o0 = tofs[t] + v * m; k2 = tv[o_to][2]; L = (k2 - k) % m or m; return [o0 + (k + j) % m for j in range(L)]
    def emit(seq, opts, spl):
        out = []
        for t, o in zip(seq, opts):
            if t in spl: u, inner_runs = spl[t]; out += piece(o, u) + inner_runs + piece(u, o)
            else: out += pieces_single(o)
        return out
    spl_P = {}; spl_Z = {}
    if nest == -1:
        for i in range(c): u, zop = choice[i]; spl_P.setdefault(AT[i], [])
        # (two anchors on the same trail are not assembled here)
        for i in range(c): u, zop = choice[i]; spl_P[AT[i]] = (u, emit(Z[i], zop, {}))
        seq = emit(P, popts, spl_P)
    else:
        ui, zi = choice[inner]; inner_runs = emit(Z[inner], zi, {})
        uo, zo = choice[outer]; outer_runs = emit(Z[outer], zo, {Tin: (ui, inner_runs)})
        seq = emit(P, popts, {Tout: (uo, outer_runs)})
    assert sorted(seq) != None
    classes = set()
    for r in seq: rr = runs[r]; classes.add(min(tuple(rr[i:] + rr[:i]) for i in range(8)))
    assert len(seq) == 5040 and len(classes) == 5040, (len(seq), len(classes))
    Lw = 8 + 7 * len(seq) + int(W[np.array(seq[:-1]), np.array(seq[1:])].sum())
    w = list(runs[seq[0]])
    for i, r in enumerate(seq):
        if i > 0: kk = int(W[seq[i - 1], r]); w += list(runs[r][8 - kk:])
        w += list(runs[r][:7])
    assert len(w) == Lw
    perms = {tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8}
    s = "".join(str(x + 1) for x in w) + "\n"; open(sys.argv[3], "w").write(s)
    print(json.dumps(dict(G_dp=G, length=Lw, G_word=Lw - 46162, all_perms=len(perms) == 40320, sha256=hashlib.sha256(s.encode()).hexdigest(),
                          P_options=[int(x) for x in popts], anchors=[choice[i][0] for i in range(c)])))

main()
