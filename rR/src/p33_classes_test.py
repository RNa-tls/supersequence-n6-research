#!/usr/bin/env python3
"""Round S -- the routes with exactly one wrapped chain and P <= 33: which are reducible by Theorems S1-S3?
Builds routes of every structural class (random trail order, random cuts, random full chain C of a random trail T,
random rotation a, random places) and runs the Monge reduction (rR/src/monge_reduce.py).
Classes (T' = T - C is the remainder; h = gap cut (entry N_0, exit Q_end); R = rotated block of C):
  E1      T' one piece at the gap (hybrid main), R elsewhere on the path                 P = 32   expected: reducible
  1a      hybrid main, C in two pieces at two places                                      P = 33   expected: reducible
  G1p     T' cut at m and at the gap, bracket at the gap, R on the path                   P = 33   expected: NOT reducible (gap cut)
  G1c     the same, R inside the bracket                                                  P = 33   expected: reducible
  G1''    T' cut at the gap (on the path) and at m, bracket at m, R inside the bracket    P = 33   expected: NOT reducible
  G1''p   the same, R on the path                                                         P = 33   expected: reducible
  2s      hybrid main + bracket of another trail S, R and h in the same component         P = 33   expected: reducible
  2d      the same, R and h in different components                                       P = 33   expected: reducible
usage: p33_classes_test.py RUNS.bin N SEED OUT.json"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monge_reduce as MR

def cyc_from(F, o):
    r = [o]; x = int(F.succ[o])
    while x != o: r.append(x); x = int(F.succ[x])
    return r
def seg(F, a, b):            # runs a .. b along the version cycle (inclusive)
    r = [a]
    while r[-1] != b: r.append(int(F.succ[r[-1]]))
    return r

def build(F, rng, cls):
    vers = {t: rng.randrange(2) for t in range(30)}
    order = list(range(30)); rng.shuffle(order)
    T = rng.choice(order)
    fulls = [c for c in F.chains if c["t"] == T and c["v"] == vers[T] and c["full"]]
    C = rng.choice(fulls)["runs"]; N0 = int(F.succ[C[-1]]); Q = int(F.pred[C[0]]); a = rng.randint(1, 6)
    R = C[a:] + C[:a]
    def std(t):
        b = F.base(t, vers[t]); return cyc_from(F, b + rng.randrange(F.mlen[t]))
    others = [t for t in order if t != T]
    hyb = seg(F, N0, Q)                                     # T' in one piece: N_0 .. Q_end
    def pick_m():
        while True:
            m = F.base(T, vers[T]) + rng.randrange(F.mlen[T])
            if m not in C and m != N0: return m
    items = None
    if cls == "E1":
        items = [std(t) if t != T else hyb for t in order]; items.insert(rng.randint(0, len(items)), R)
    elif cls == "1a":
        j = rng.randint(1, 6); items = [std(t) if t != T else hyb for t in order]
        for part in (R[:j], R[j:]): items.insert(rng.randint(0, len(items)), part)
    elif cls in ("G1p", "G1c", "G1''", "G1''p"):
        m = pick_m(); k = rng.randint(1, 6); zin = rng.sample(others, k); pout = [t for t in order if t not in zin]
        p1 = seg(F, m, Q); p2 = seg(F, N0, int(F.pred[m]))                 # [m .. Q_end], [N_0 .. pred m]
        Z = [std(t) for t in zin]
        if cls in ("G1c", "G1''"): Z.insert(rng.randint(0, len(Z)), R)
        groups = []
        for t in pout:
            if t != T: groups.append([std(t)]); continue
            if cls in ("G1p", "G1c"): groups.append([p1] + Z + [p2])       # bracket at the gap
            else: groups.append([p2] + Z + [p1])                           # bracket at m; the path piece is [N_0 .. pred m] ... [m .. Q_end]
        if cls in ("G1p", "G1''p"): groups.insert(rng.randint(0, len(groups)), [R])     # R on the path: outside the bracket
        items = [x for g in groups for x in g]
    elif cls in ("2s", "2d"):
        S = rng.choice(others); k = rng.randint(1, 5); zin = rng.sample([t for t in others if t != S], k)
        bS = F.base(S, vers[S]); mS = F.mlen[S]; a1, b1 = sorted(rng.sample(range(mS), 2))
        s1 = seg(F, bS + a1, bS + b1 - 1); s2 = seg(F, bS + b1, bS + (a1 - 1) % mS)
        hyb_in_cycle = rng.random() < 0.5; Rin = hyb_in_cycle if cls == "2s" else (not hyb_in_cycle)
        Z = [std(t) for t in zin]
        if hyb_in_cycle: Z.insert(rng.randint(0, len(Z)), hyb)
        if Rin: Z.insert(rng.randint(0, len(Z)), R)
        groups = []
        for t in order:
            if t in zin: continue
            if t == S: groups.append([s1] + Z + [s2])
            elif t == T:
                if not hyb_in_cycle: groups.append([hyb])
            else: groups.append([std(t)])
        if not Rin: groups.insert(rng.randint(0, len(groups)), [R])        # R on the path: outside the bracket
        items = [x for g in groups for x in g]
    route = [r for it in items for r in it]
    assert len(route) == 5040 and len(set(route)) == 5040, (cls, len(route), len(set(route)))
    return route

def main():
    F = MR.Family(sys.argv[1], cache=os.environ.get("W_CACHE")); n = int(sys.argv[2]); rng = random.Random(int(sys.argv[3]))
    expect = {"E1": True, "1a": True, "G1p": False, "G1c": True, "G1''": False, "G1''p": True, "2s": True, "2d": True}
    out = {}; allok = True
    for cls in expect:
        st = dict(routes=0, P=set(), wraps=set(), reduced=0, not_reduced=0, reasons={}, max_delta=None, cycles_after=set(), degenerate=0)
        while st["routes"] < n:
            route = build(F, rng, cls); C = MR.Cover(F, route); wc, bl = MR.classify(F, route)
            if len(bl) != 1 or bl[0]["k"] != 1 or bl[0]["closed"]: st["degenerate"] += 1; continue     # e.g. the block landed in its own gap
            st["routes"] += 1; st["P"].add(C.P); st["wraps"].add(wc)
            ok = False
            for attempt in range(4):
                try:
                    nr, info = MR.reduce_to_bracket_tree(F, route, rng); ok = True
                    st["max_delta"] = info["delta"] if st["max_delta"] is None else max(st["max_delta"], info["delta"]); st["cycles_after"].add(info["cycles_after"]); break
                except MR.ReductionError as e: msg = str(e).split(":")[0].split(" k=")[0]
            if ok: st["reduced"] += 1
            else: st["not_reduced"] += 1; st["reasons"][msg] = st["reasons"].get(msg, 0) + 1
        st["P"] = sorted(st["P"]); st["wraps"] = sorted(st["wraps"]); st["cycles_after"] = sorted(st["cycles_after"])
        st["expected_reducible"] = expect[cls]; st["as_expected"] = (st["reduced"] == n) if expect[cls] else (st["not_reduced"] == n)
        allok = allok and st["as_expected"]; out[cls] = st
        print(cls, json.dumps(st))
    out["all_as_expected"] = allok
    json.dump(out, open(sys.argv[4], "w"), indent=1)
main()
