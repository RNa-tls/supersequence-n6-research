#!/usr/bin/env python3
"""Round S -- independent reconstruction of gap-anchored single brackets (checks rR/csrc/gap_eval.c on real words).

A gap-anchored bracket (see gap_eval.c): trail S (version v) with a full chain C detached; S - C is cut at its main m and
at the gap (entry N_0, exit Q_end); the cycle Z' = z_1 .. z_k hangs at the gap; C is traversed as one rotated block
C_a .. C_6 C_0 .. C_{a-1} somewhere else (in the path or in the cycle).  For a configuration
    (order of the 30 trails, junction position j, anchor position s, version, C_0, place of the block)
this program recomputes the optimal options by its own dynamic programming (numpy, no code shared with gap_eval.c),
ASSEMBLES THE ROUTE run by run, and measures its weight directly:  G = (sum of the link weights) - 10874.
It prints the measured G next to the value of gap_eval.c, the piece / cover structure of the route (monge_reduce.Cover)
and what the Monge reduction says about it (the gap cut is the irreducible structure of Theorem S3).

usage: gap_witness.py RUNS.bin WITNESSES.jsonl [MAX] [OUT_WORD_PREFIX]
       gap_witness.py RUNS.bin --config ORDER(comma) J S VERSION C0_LOCAL SITE
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import monge_reduce as MR

BIG = 10 ** 6

def opts_of_trail(F, t): return np.arange(F.tofs[t], F.tofs[t] + 2 * F.mlen[t])

def Emat(F, A, B):
    """e(a -> b) = w(exit run of a, entry run of b) - cut(b) - 1 for option arrays A, B."""
    return F.W[np.ix_(F.pred[A], B)].astype(np.int64) - F.cut[B][None, :] - 1

def chain_of(F, c0):
    c = F.chains[int(F.cid[c0])]; assert c["full"] and c["runs"][0] == c0, "C_0 is not the start of a full chain"
    return c["runs"]

def solve(F, order, jj, s, ver, c0, site):
    """optimal options and G of the configuration; returns (G, route)."""
    S = order[s]; C = chain_of(F, c0); N0 = int(F.succ[C[-1]]); Qend = int(F.pred[c0])
    assert int(F.T[c0]) == S and int(F.V[c0]) == ver
    block = np.array(C[1:], np.int64)                       # options S(C_a), a = 1..6: entry C_a, exit C_{a-1}
    excl = set(C) | {N0}
    # vertex lists: P part and cycle part; ("t", trail) or ("b",)
    Pv = [("t", t) for t in order[:jj]]; Zv = [("t", t) for t in order[jj:]]
    if site < 100: Pv.insert(site, ("b",)); spos = s + (1 if site <= s else 0)
    else: Zv.insert(site - 100 - jj, ("b",)); spos = s
    def olist(v): return block if v[0] == "b" else opts_of_trail(F, v[1])
    PL = [olist(v) for v in Pv]; ZL = [olist(v) for v in Zv]
    # P part: forward and backward with back pointers
    n = len(PL); fw = [None] * n; fb = [None] * n; bw = [None] * n; bb = [None] * n
    fw[0] = (F.cut[PL[0]] == 2).astype(np.int64)
    for i in range(1, n):
        M = fw[i - 1][:, None] + Emat(F, PL[i - 1], PL[i]); fb[i] = M.argmin(0); fw[i] = M.min(0)
    bw[n - 1] = np.zeros(len(PL[n - 1]), np.int64)
    for i in range(n - 2, -1, -1):
        M = Emat(F, PL[i], PL[i + 1]) + bw[i + 1][None, :]; bb[i] = M.argmin(1); bw[i] = M.min(1)
    tot = fw[spos] + bw[spos]
    ok = np.array([(F.V[o] == ver) and (int(o) not in excl) for o in PL[spos]])
    tot = np.where(ok, tot, BIG); q = int(tot.argmin()); pa = int(tot[q])
    choice = [None] * n; choice[spos] = q
    for i in range(spos, 0, -1): choice[i - 1] = int(fb[i][choice[i]])
    for i in range(spos, n - 1): choice[i + 1] = int(bb[i][choice[i]])
    Popt = [int(PL[i][choice[i]]) for i in range(n)]
    # closing walk: S(C_0) [exit Q_end] -> Z lists -> S(N_0) [entry N_0]
    oC = np.array([c0]); oN = np.array([N0]); m = len(ZL)
    d = Emat(F, oC, ZL[0])[0]; back = [None] * m
    for i in range(1, m):
        M = d[:, None] + Emat(F, ZL[i - 1], ZL[i]); back[i] = M.argmin(0); d = M.min(0)
    fin = d + Emat(F, ZL[m - 1], oN)[:, 0]; qz = int(fin.argmin()); cz = int(fin[qz])
    zch = [None] * m; zch[m - 1] = qz
    for i in range(m - 1, 0, -1): zch[i - 1] = int(back[i][zch[i]])
    Zopt = [int(ZL[i][zch[i]]) for i in range(m)]
    G = 1 + pa + cz
    # assemble the route
    def full_cycle(o):
        r = [o]; x = int(F.succ[o])
        while x != o: r.append(x); x = int(F.succ[x])
        return r
    def block_runs(o):                                         # o = C_a: C_a .. C_6 C_0 .. C_{a-1}
        a = C.index(o); return C[a:] + C[:a]
    def vertex_runs(v, o): return block_runs(o) if v[0] == "b" else full_cycle(o)
    route = []
    for i, v in enumerate(Pv):
        o = Popt[i]
        if i == spos:
            mrun = o; part1 = [mrun]; x = int(F.succ[mrun])
            while part1[-1] != Qend: part1.append(x); x = int(F.succ[x])
            part2 = [N0]; x = int(F.succ[N0])
            while x != mrun: part2.append(x); x = int(F.succ[x])
            route += part1
            for k, vz in enumerate(Zv): route += vertex_runs(vz, Zopt[k])
            route += part2
        else: route += vertex_runs(v, o)
    return G, route, dict(pa=pa, cz=cz, main=Popt[spos] - F.tofs[S])

def check(F, cfg, tag=""):
    order = cfg["order"]; jj = cfg["junction_after"]; s = cfg["anchor_pos"]; ver = cfg["version"]
    S = order[s]; c0 = F.tofs[S] + cfg["gap_C0_option"]; site = cfg["block_site"]
    G, route, info = solve(F, order, jj, s, ver, c0, site)
    assert sorted(route) == sorted(set(route)) and len(route) == 5040, "assembled route is not a Hamiltonian path"
    Gm = F.weight(route) - 10874
    C = MR.Cover(F, route); comps, comp = C.components(); cls, bl = MR.classify(F, route)
    try:
        nr, inf = MR.reduce_to_bracket_tree(F, route); red = "reduced to a bracket tree, weight change %d" % inf["delta"]
    except MR.ReductionError as e: red = "not reducible: " + str(e)
    out = dict(tag=tag, G_dp=G, G_measured=Gm, G_gap_eval=cfg.get("G_exact_one_block"), LB_gap_eval=cfg.get("LB"), P=C.P, cover_cycles=len(comps) - 1,
               wrap_class=cls, wrap_blocks=[(b["k"], b["s"], b["r"], b["closed"]) for b in bl], monge=red, **info)
    return out, route

def main():
    F = MR.Family(sys.argv[1], cache=os.environ.get("W_CACHE"))
    if sys.argv[2] == "--config":
        order = [int(x) for x in sys.argv[3].split(",")]
        cfg = dict(order=order, junction_after=int(sys.argv[4]), anchor_pos=int(sys.argv[5]), version=int(sys.argv[6]), gap_C0_option=int(sys.argv[7]), block_site=int(sys.argv[8]))
        out, route = check(F, cfg); print(json.dumps(out)); return
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9; pref = sys.argv[4] if len(sys.argv) > 4 else None
    n = 0; bad = 0; best = None
    for line in open(sys.argv[2]):
        if n >= mx: break
        cfg = json.loads(line)
        if "gap_C0_option" not in cfg: continue
        out, route = check(F, cfg, tag=str(n)); n += 1
        okk = (out["G_dp"] == out["G_measured"]) and (cfg.get("G_exact_one_block") in (None, out["G_dp"]))
        if not okk: bad += 1
        if best is None or out["G_measured"] < best[0]["G_measured"]: best = (out, route)
        print(json.dumps(out))
    print(json.dumps(dict(checked=n, mismatches=bad, least_measured_G=best[0]["G_measured"] if best else None)))
    if pref and best:
        w = MR.build_word(F, best[1]); open(pref + "_G%d.txt" % best[0]["G_measured"], "w").write("".join(str(c + 1) for c in w) + "\n")

if __name__ == "__main__": main()
