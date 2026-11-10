#!/usr/bin/env python3
"""Round S -- end-to-end tests of the Monge reduction (Theorems S1, S2, S3) on generated routes.

Every test route is a Hamiltonian path of the 5040 runs of one version vector.  For each route
  * reduce_to_bracket_tree deletes cuts step by step (checks the Monge side condition and that every step has weight
    change <= 0), rebuilds the reduced route and checks: permutation of the runs, weight = old weight + sum of the step
    changes, bracket tree (V = P, c = P - 30, no jump);
  * direct_tree realizes the bracket tree of several random spanning trees directly (no deletion order) and the weight
    change is checked to be <= 0 (for wrap-free routes and routes whose wrap blocks are skip cycles this is the statement
    "every spanning tree works").

Families of test routes
  A  random pieces in random order (many cuts, huge weights), wrap-free ones only;
  B  record words (bracket trees) perturbed by random segment moves, wrap-free ones only;
  C  forced ladders (m = 2; singleton / wrap steps on either side);
  D  rotations with a skip: k consecutive full chains in natural position are removed (one skip junction) and every
     chain is re-inserted as a rotated block (optionally cut into two parts) at random places  -> skip cycles (S2);
  E  open gaps: as D, then a random segment of the route is moved into the gap  -> open wrap blocks; statistics of
     reducible / irreducible cases (bridge = the gap cut is needed by the tree, light neighbour).

usage: monge_reduce_test.py RUNS.bin OUT.json SEED N_A N_B N_C N_D N_E [WORD ...]
"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monge_reduce as MR

def natural_full_runs(F, route):
    """positions p such that route[p-1], route[p..p+6], route[p+7] is  Q_end, a full chain in natural order, N_0."""
    pos = {r: i for i, r in enumerate(route)}; out = []
    for c in F.chains:
        if not c["full"]: continue
        D = c["runs"]; p = pos.get(D[0])
        if p is None or p == 0 or p + 7 >= len(route): continue
        if route[p:p + 7] != D: continue
        if route[p - 1] != int(F.pred[D[0]]) or route[p + 7] != int(F.succ[D[-1]]): continue
        out.append((p, c))
    return out

def rotation_move(F, route, rng, k=1, split=False):
    """remove k consecutive natural full chains (one skip junction) and re-insert each as a rotated block."""
    cand = natural_full_runs(F, route)
    if not cand: return None
    starts = {p: c for p, c in cand}
    opts = [p for p in starts if all((p + 7 * j) in starts for j in range(k)) and p + 7 * k < len(route)]
    if not opts: return None
    p = rng.choice(opts); chains_ = [starts[p + 7 * j]["runs"] for j in range(k)]
    rest = route[:p] + route[p + 7 * k:]
    for D in chains_:
        a = rng.randint(1, 6); block = D[a:] + D[:a]
        if split:
            cutp = rng.randint(1, 6); parts = [block[:cutp], block[cutp:]]
        else: parts = [block]
        for part in parts:
            j = rng.randint(0, len(rest)); rest = rest[:j] + part + rest[j:]
    return rest

def gap_fill_move(F, route, rng):
    """after a rotation move: move a random segment of the route into a gap (between Q_end and N_0 of a wrapped chain)."""
    pos = {r: i for i, r in enumerate(route)}
    gaps = []
    for c in F.chains:
        if not c["full"]: continue
        D = c["runs"]; q = int(F.pred[D[0]]); nn = int(F.succ[D[-1]])
        if D[0] not in pos: continue                         # chain of the other version
        if pos[nn] == pos[q] + 1 and pos[D[0]] == pos[D[-1]] + 1: gaps.append(pos[q])     # skip junction + wrap used
    if not gaps: return None
    g = rng.choice(gaps); N = len(route)
    for _ in range(50):
        i = rng.randrange(N - 1); Lseg = rng.choice([1, 7, 42, 84, 200, 672, 1000]); j = min(N, i + Lseg)
        if i <= g < j or i <= g + 1 < j: continue
        seg = route[i:j]; rest = route[:i] + route[j:]
        gp = rest.index(route[g]) + 1
        return rest[:gp] + seg + rest[gp:]
    return None

def main():
    F = MR.Family(sys.argv[1], cache=os.environ.get("W_CACHE")); outp = sys.argv[2]; seed = int(sys.argv[3])
    nA, nB, nC, nD, nE = [int(x) for x in sys.argv[4:9]]; words = sys.argv[9:]
    rng = random.Random(seed); t0 = time.time()
    base = [MR.word_route(F, w, None) for w in words]
    res = dict(seed=seed, base_words=words)
    def run_reducible(route, tag, st, ntrees=3):
        new_route, info = MR.reduce_to_bracket_tree(F, route, rng)
        st["routes"] += 1; st["deleted"] += info["deleted"]; st["delta_sum"] += info["delta"]; st["max_P"] = max(st["max_P"], info["P"])
        st["ladders"] += len(info["ladders"]); st["tight_steps"] += info["tight_steps"]; st["max_cycles_after"] = max(st["max_cycles_after"], info["cycles_after"])
        st["whole_cycles"] += len(info["whole_cycles"]); st["bypassed_blocks"] += len(info["bypassed"])
        st["max_delta"] = max(st["max_delta"], info["delta"])
        for _ in range(ntrees):
            nr2, d2 = MR.direct_tree(F, route, rng)
            st["direct_trees"] += 1; st["direct_max_delta"] = max(st["direct_max_delta"], d2)
            if d2 > 0: st["direct_violations"] += 1
    def fresh(): return dict(routes=0, deleted=0, delta_sum=0, max_P=0, ladders=0, tight_steps=0, max_cycles_after=0, whole_cycles=0, bypassed_blocks=0,
                             max_delta=-10 ** 9, direct_trees=0, direct_max_delta=-10 ** 9, direct_violations=0)
    # A: random pieces
    st = fresh(); skipped = 0
    while st["routes"] < nA:
        route = MR.random_route(F, rng, extra_cuts=(0, rng.choice([1, 2, 4, 8, 16])))
        if MR.Cover(F, route).has_wrap(): skipped += 1; continue
        run_reducible(route, "A", st)
    st["skipped_with_wrap"] = skipped; res["A_random_pieces_wrap_free"] = st
    # B: perturbed record words
    st = fresh(); skipped = 0
    while st["routes"] < nB and base:
        route = MR.perturb(F, rng.choice(base), rng, rng.randint(1, 25))
        if MR.Cover(F, route).has_wrap(): skipped += 1; continue
        run_reducible(route, "B", st)
    st["skipped_with_wrap"] = skipped; res["B_perturbed_words_wrap_free"] = st
    # C: forced ladders
    lad = {}
    for tT in "sw":
        for tS in "sw":
            n = 0; nl = 0; worst = -10 ** 9
            while n < nC:
                route, prefer = MR.ladder_route(F, rng, tT, tS)
                if MR.Cover(F, route).has_wrap(): continue
                new_route, info = MR.reduce_to_bracket_tree(F, route, rng, prefer=prefer)
                n += 1; l2 = [x for x in info["ladders"] if x[0] == "ladder"]; nl += len(l2)
                for x in l2: worst = max(worst, x[2])
            lad[tT + tS] = dict(routes=n, ladders_deleted=nl, max_ladder_delta=worst if nl else None)
    res["C_forced_ladders"] = lad
    # D: rotations with a skip (skip cycles)
    st = fresh(); kinds = {}; notclosed = 0; tries = 0
    while st["routes"] < nD and base and tries < 40 * nD:
        tries += 1
        route = list(rng.choice(base))
        if rng.random() < 0.5: route = MR.perturb(F, route, rng, rng.randint(1, 6))
        nm = rng.randint(1, 4); ok = True
        for _ in range(nm):
            r2 = rotation_move(F, route, rng, k=rng.choice([1, 1, 1, 2, 2, 3, 4]), split=rng.random() < 0.3)
            if r2 is None: ok = False; break
            route = r2
        if not ok: continue
        cls, bl = MR.classify(F, route)
        if cls != "closed": notclosed += 1; continue
        run_reducible(route, "D", st)
        for b in bl: kinds[b["k"]] = kinds.get(b["k"], 0) + 1
    st["blocks_by_k"] = kinds; st["generated_not_closed"] = notclosed; res["D_rotations_with_skip"] = st
    # E: open gaps
    st = dict(routes=0, reduced=0, failed=0, reasons={}, direct_min_delta_hist={}, direct_trees=0, some_tree_nonpositive=0, all_trees_positive=0, examples=[])
    tries = 0
    while st["routes"] < nE and base and tries < 60 * nE:
        tries += 1
        route = list(rng.choice(base))
        r2 = rotation_move(F, route, rng, k=rng.choice([1, 1, 2]), split=False)
        if r2 is None: continue
        r3 = gap_fill_move(F, r2, rng)
        if r3 is None: continue
        cls, bl = MR.classify(F, r3)
        if cls != "open": continue
        st["routes"] += 1
        try:
            new_route, info = MR.reduce_to_bracket_tree(F, r3, rng); st["reduced"] += 1
        except MR.ReductionError as e:
            st["failed"] += 1; key = str(e).split(":")[0].split(" k=")[0]; st["reasons"][key] = st["reasons"].get(key, 0) + 1
        best = 10 ** 9
        for _ in range(8):
            try:
                nr2, d2 = MR.direct_tree(F, r3, rng); best = min(best, d2); st["direct_trees"] += 1
            except MR.ReductionError: pass
        if best <= 0: st["some_tree_nonpositive"] += 1
        else:
            st["all_trees_positive"] += 1
            if len(st["examples"]) < 5: st["examples"].append(dict(min_delta=best, G=F.weight(r3) - 10874, blocks=[(b["k"], b["s"], b["r"]) for b in bl]))
        st["direct_min_delta_hist"][str(min(best, 9))] = st["direct_min_delta_hist"].get(str(min(best, 9)), 0) + 1
    res["E_open_gaps"] = st
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(outp, "w"), indent=1)
    print(json.dumps(res)[:3000])

if __name__ == "__main__": main()
