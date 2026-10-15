#!/usr/bin/env python3
"""Round M (sections 11, 14, 20) -- LKH on the FULL r = 0 problem of n = 8 (any start / world per
class), as a GTSP: cluster = cyclic class, nodes = its allowed run starts (default: all 8
rotations, i.e. every world), arc s -> t = w(last(s), t).  Noon-Bean + ATSP->STSP doubling are done
inside the standalone binary (rM/lkh_r0, Distance_SPECIAL), candidates = all arcs of weight <= WC
(+ cluster cycle + depot), initial tour = INITWORD.  The decoded tour is rebuilt as a word and
measured from scratch.
usage: lkh_full8.py BINARY INITWORD [--worlds 0,1,...] [--wc 4] [--M 1000] [--trials T] [--chunks K]
                    [--seed S] [--time SEC] [--tag TAG] [--scratch DIR] [--move 5] [--kicks K]"""
import sys, os, json, time, argparse, itertools, struct, subprocess, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("binary"); ap.add_argument("init")
    ap.add_argument("--worlds", default="0,1,2,3,4,5,6,7"); ap.add_argument("--wc", type=int, default=4)
    ap.add_argument("--M", type=int, default=1000); ap.add_argument("--trials", type=int, default=1000)
    ap.add_argument("--runs", type=int, default=1); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--time", type=float, default=0); ap.add_argument("--tag", default="f8")
    ap.add_argument("--move", type=int, default=5); ap.add_argument("--kicks", type=int, default=1)
    ap.add_argument("--maxcand", type=int, default=60); ap.add_argument("--chunks", type=int, default=1)
    ap.add_argument("--scratch", default="."); ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs"))
    a = ap.parse_args()
    t0 = time.time()
    ws = [int(x) for x in a.worlds.split(",")]
    init = RA.starts_of_word(RA.load_word(a.init))
    # ATSP nodes: 0 = depot; then per class (init order) its allowed starts in rotation order
    start = [None]; cluster = [-1]; succ = [0]; members = []
    for ci, s0 in enumerate(init):
        rots = [s0[j:] + s0[:j] for j in range(8)]
        allowed = [r for r in rots if r[7] in ws]
        if s0 not in allowed: allowed = [s0] + allowed      # keep the initial start available
        first = len(start); mem = []
        for r in allowed: mem.append(len(start)); start.append(r); cluster.append(ci); succ.append(0)
        for k, x in enumerate(mem): succ[x] = mem[(k + 1) % len(mem)]
        members.append(mem)
    n0 = len(start); depot = 0
    succ[0] = 0; cluster[0] = len(members)
    exitp = [None] * n0
    for x in range(1, n0): exitp[x] = RA.last(start[succ[x]])
    pred = [0] * n0
    for x in range(1, n0): pred[succ[x]] = x
    idx = {s: x for x, s in enumerate(start) if s is not None}
    # node data
    nd = os.path.join(a.scratch, "f8_%s_%d.nodes" % (a.tag, os.getpid()))
    with open(nd, "wb") as f:
        f.write(struct.pack("<4i", n0, depot, a.M, 100000))
        for x in range(n0):
            s = start[x] if x else (0,) * 8; e = exitp[x] if x else (0,) * 8
            f.write(struct.pack("<2i", cluster[x], succ[x])); f.write(bytes(s)); f.write(bytes(e))
    # candidate arcs i -> j (ATSP), weight <= WC
    outc = [[] for _ in range(n0)]; inc = [[] for _ in range(n0)]
    for x in range(1, n0):
        e = exitp[x]
        for k in range(2, a.wc + 1):
            for perm in itertools.permutations(e[:k]):
                y = e[k:] + perm
                if RA.wt(e, y) != k: continue
                j = idx.get(y)
                if j is None or cluster[j] == cluster[x]: continue
                outc[x].append((j, k)); inc[j].append((x, k))
    rnd = random.Random(a.seed)
    dep_targets = set([members[0][0]] + [x for x in rnd.sample(range(1, n0), min(200, n0 - 1))])
    # STSP ids: in(x) = x + 1, out(x) = n0 + x + 1
    cf = os.path.join(a.scratch, "f8_%s_%d.cand" % (a.tag, os.getpid()))
    ncand = 0
    with open(cf, "w") as f:
        f.write("%d\n" % (2 * n0))
        for x in range(n0):
            # in(x): twin out(x), out(pred(x)), out(i) for arcs i -> x, out(depot)
            L = [(n0 + x + 1, 0)]
            if x: L.append((n0 + pred[x] + 1, 0))
            L += [(n0 + i + 1, k) for (i, k) in inc[x]]
            if x: L.append((n0 + depot + 1, 9))
            else: L += [(n0 + t + 1, 9) for t in dep_targets]
            f.write("%d 0 %d %s\n" % (x + 1, len(L), " ".join("%d %d" % c for c in L))); ncand += len(L)
        for x in range(n0):
            L = [(x + 1, 0)]
            if x: L.append((succ[x] + 1, 0))
            L += [(j + 1, k) for (j, k) in outc[x]]
            if x: L.append((depot + 1, 9))
            else: L += [(t + 1, 9) for t in dep_targets]
            f.write("%d 0 %d %s\n" % (n0 + x + 1, len(L), " ".join("%d %d" % c for c in L))); ncand += len(L)
        f.write("-1\nEOF\n")
    # initial tour: depot, then every class entered at its initial start, cluster cycle order
    atsp = [0]
    for ci, s0 in enumerate(init):
        x = idx[s0]; mem = members[ci]
        for _ in range(len(mem)): atsp.append(x); x = succ[x]
    tf = os.path.join(a.scratch, "f8_%s_%d.tour" % (a.tag, os.getpid()))
    with open(tf, "w") as f:
        f.write("TYPE : TOUR\nDIMENSION : %d\nTOUR_SECTION\n" % (2 * n0))
        for x in atsp: f.write("%d\n%d\n" % (x + 1, n0 + x + 1))
        f.write("-1\nEOF\n")
    pf = os.path.join(a.scratch, "f8_%s_%d.prob" % (a.tag, os.getpid()))
    with open(pf, "w") as f:
        f.write("TYPE : TSP\nDIMENSION : %d\nEDGE_WEIGHT_TYPE : SPECIAL\nFIXED_EDGES_SECTION\n" % (2 * n0))
        for x in range(n0): f.write("%d %d\n" % (x + 1, n0 + x + 1))
        f.write("-1\nEOF\n")
    print(json.dumps(dict(n0=n0, stsp=2 * n0, worlds=ws, wc=a.wc, candidates=ncand, build_sec=round(time.time() - t0, 1),
                          init_cost=sum(RA.wt(RA.last(x), y) for x, y in zip(init, init[1:])))), flush=True)
    # CHECKPOINTED search: CHUNKS calls of the binary, each MAX_TRIALS = TRIALS from the current best
    # tour with a new seed; the best word is saved after every chunk (scratch) and kept if < 46185.
    best_sts = list(init); best_cost = sum(RA.wt(RA.last(x), y) for x, y in zip(init, init[1:]))
    ckpt = os.path.join(a.scratch, "f8_%s_best.txt" % a.tag)
    for chunk in range(a.chunks):
        seed = a.seed * 1000 + chunk
        with open(tf, "w") as f:
            f.write("TYPE : TOUR\nDIMENSION : %d\nTOUR_SECTION\n" % (2 * n0))
            seqa = [0]
            for s0 in best_sts:
                x = idx[s0]; c = cluster[x]
                for _ in range(len(members[c])): seqa.append(x); x = succ[x]
            for x in seqa: f.write("%d\n%d\n" % (x + 1, n0 + x + 1))
            f.write("-1\nEOF\n")
        par = os.path.join(a.scratch, "f8_%s_%d.par" % (a.tag, os.getpid()))
        params = ["PROBLEM_FILE = %s" % pf, "CANDIDATE_FILE = %s" % cf, "CANDIDATE_SET_TYPE = NEAREST-NEIGHBOR",
                  "MAX_CANDIDATES = %d" % a.maxcand, "INITIAL_TOUR_FILE = %s" % tf, "MOVE_TYPE = %d" % a.move,
                  "MAX_TRIALS = %d" % a.trials, "RUNS = 1", "SEED = %d" % seed, "TRACE_LEVEL = 1",
                  "PRECISION = 1", "SUBGRADIENT = NO", "KICKS = %d" % a.kicks]
        if a.time: params.append("TIME_LIMIT = %g" % a.time)
        open(par, "w").write("\n".join(params) + "\n")
        ot = os.path.join(a.scratch, "f8_%s_%d.out" % (a.tag, os.getpid()))
        lk = os.path.join(a.scratch, "f8_%s_lkh.log" % a.tag)
        with open(lk, "a") as lf:
            subprocess.run(["stdbuf", "-oL", a.binary, par, pf, nd, ot], check=True, stdout=lf, stderr=subprocess.STDOUT)
        tour = [int(l) for l in open(ot) if l.strip()]
        assert len(tour) == 2 * n0, ("tour size", len(tour))
        k = tour.index(1)
        seq = tour[k:] + tour[:k]
        if seq[1] != n0 + 1: seq = [seq[0]] + seq[1:][::-1]
        assert seq[1] == n0 + 1
        at = [seq[i] - 1 for i in range(0, len(seq), 2)]
        assert all(seq[i + 1] == n0 + at[i // 2] + 1 for i in range(0, len(seq), 2)), "not alternating"
        assert at[0] == 0
        sts = []; i = 1; proper = True
        while i < len(at):
            c = cluster[at[i]]; m = len(members[c])
            if sorted(at[i:i + m]) != sorted(members[c]): proper = False; break
            sts.append(start[at[i]]); i += m
        res = dict(tag=a.tag, chunk=chunk, seed=seed, proper=proper, sec=round(time.time() - t0, 1))
        if proper:
            cost = sum(RA.wt(RA.last(x), y) for x, y in zip(sts, sts[1:]))
            res.update(cost=cost, L=35288 + cost, J=cost - 10797, worlds_used=sorted(set(s[7] for s in sts)),
                       changed_starts=sum(1 for s in sts if s not in set(init)))
            if cost <= best_cost:
                best_cost, best_sts = cost, sts
                route = []
                for s in sts: route += [s[j:] + s[:j] for j in range(8)]
                w = list(route[0])
                for x, y in zip(route, route[1:]): kk = RA.wt(x, y); w += list(y[8 - kk:])
                res["measured"] = len(w); RA.write_word(w, ckpt)
                if len(w) < 46185:
                    pth = os.path.join(a.out, "lkh_full8_%d_%s_c%d.txt" % (len(w), a.tag, chunk)); RA.write_word(w, pth); res["file"] = pth
        res["best_L"] = 35288 + best_cost
        print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
