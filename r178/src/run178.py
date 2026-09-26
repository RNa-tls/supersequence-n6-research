#!/usr/bin/env python3
"""Round 178 -- falsification run of the generic coarsening map (bridge178.coarsen).

Routes: (1) archive superpermutations (n = 5, 6, 7), (2) random perturbations of those
routes (segment reversal / vertex moves) followed by normalization, (3) random greedy
routes.  For each route: build the coarsened instance, check it with checkers A and B
(r176), check L_c = CONST(n) + D and word length >= L_c, record the trichotomy case.
For unperturbed archive routes also compare with the R174 MASTER dictionary
(r = G, q = S+1, eta = h, M = O, m = k_master, a+b = Z+B*, t = D + (H-h)).
Mutation tests on produced instances.
usage: run178.py [--quick]"""
import glob, gzip, json, math, os, random, re, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "r176", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "r160", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "r156", "src"))
from bridge178 import coarsen, check_instance, normalize, route_of_word, cost, BridgeError
from checkA176 import CheckerA
from checkB176 import CheckerB
SPL = "/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/sp_lit/superpermutations"
QUICK = "--quick" in sys.argv


def words(n, limit):
    out = []
    for f in sorted(glob.glob(f"{SPL}/{n}/*")):
        if not os.path.isfile(f): continue
        raw = open(f, "rb").read()
        if raw[:2] == b"\x1f\x8b": raw = gzip.decompress(raw)
        for t in re.findall(r"[1-9]+", raw.decode("utf-8", "replace")):
            if len(t) >= math.factorial(n) and len(set(t)) == n and t not in out:
                out.append(t)
                if len(out) >= limit: return out
    return out


def to_route(w, n):
    return [tuple(int(ch) - 1 for ch in t) for t in route_of_word(w, n)]


def word_of_route(route, n):
    w = "".join(str(v + 1) for v in route[0])
    for x, y in zip(route, route[1:]):
        d = cost(x, y, n); w += "".join(str(v + 1) for v in y[n - d:])
    return w


def perturb(route, n, rng, ops):
    route = list(route)
    for _ in range(ops):
        i, j = sorted(rng.sample(range(len(route)), 2))
        if rng.random() < 0.5:
            route[i:j + 1] = route[i:j + 1][::-1]
        else:
            v = route.pop(i); route.insert(rng.randrange(len(route) + 1), v)
    return normalize(route, n)


def greedy(n, rng, jump):
    from itertools import permutations
    perms = list(permutations(range(n)))
    left = set(perms); x = rng.choice(perms); route = [x]; left.discard(x)
    while left:
        cands = [y for y in (x[1:] + x[:1], x[2:] + (x[1], x[0]), x[2:] + x[:2]) if y in left]
        if not cands or rng.random() < jump:
            best = None
            for d in range(3, n + 1):
                pre = x[d:]
                opts = [y for y in left if y[:n - d] == pre] if d < n else list(left)
                if opts: best = rng.choice(opts); break
            y = best
        else:
            y = cands[0]
        route.append(y); left.discard(y); x = y
    return normalize(route, n)


def case_of(res):
    flat = [x for t in res["instance"] for x in t]
    runs = sum(1 for x in flat for i in x[2] if i - 1 not in x[2])
    ch = sum((res["n"] - 1 - x[1]) + len(x[2]) for x in flat)
    if runs > 0: return "(i) omitted run"
    if ch <= res["u"] - 1: return "(ii) charge <= u-1"
    return "(iii) forest"


def master_compare(w, n, res):
    try:
        import extract156 as X, master160 as M160
    except Exception as e:
        return None
    st = X.structure(w, n); mm = M160.master(st)
    H, h = mm["H"], mm["h"]
    return dict(r_eq_G=res["r"] == mm["G"], q_eq_S1=res["q"] == mm["S"] + 1, eta_eq_h=res["eta"] == h,
                M_eq_O=res["M"] == mm["O"], m_eq_k=res["m"] == mm["k"],
                ab_eq_ZB=res["a"] + res["b"] == mm["Z"] + mm["Bstar"],
                t_eq=mm["t"] == res["D"] + (H - h), Z=mm["Z"], Bstar=mm["Bstar"], a=res["a"], b=res["b"])


def mutations(res, n):
    A = CheckerA(n)
    inst = res["instance"]; flat = [x for t in inst for x in t]
    muts = []
    base = dict(res)
    def with_inst(new): d = dict(res); d["instance"] = new; return d
    # missing row
    t0 = next(i for i, t in enumerate(inst) if t)
    muts.append(("missing row", with_inst([t if i != t0 else t[1:] for i, t in enumerate(inst)]), None))
    # duplicated class: copy a row into a new trail
    muts.append(("duplicated row/class", with_inst(inst + [[flat[0]]]), {"k": len(flat) + 1, "tau": len(inst) + 1}))
    # incorrect charge claim
    ch = sum(A.charge(x) for x in flat)
    if ch >= 1: muts.append(("charge claim total-1", res, {"u": ch - 1}))
    # omitted endpoint (position 0)
    x = flat[0]
    muts.append(("omitted endpoint", with_inst([[(x[0], x[1], (0,) + x[2])] + inst[0][1:]] + inst[1:] if inst[0] and inst[0][0] == x else inst), None))
    # illegal transition: reverse a trail of length >= 2 when that is incompatible
    for i, t in enumerate(inst):
        if len(t) >= 2 and not A.compatible(t[1], t[0]):
            muts.append(("illegal transition (reversed trail)", with_inst(inst[:i] + [t[::-1]] + inst[i + 1:]), None)); break
    # incorrect trail count: split all trails into singletons, claim tau
    if len(flat) > res["eta"] + 1 + res["b"]:
        muts.append(("trail count exceeds tau", with_inst([[x] for x in flat]), None))
    # altered defect count: claim a+1 (row count must be ORB+m-r+a)
    muts.append(("altered defect a+1", res, {"k": math.factorial(n - 2) + res["m"] - res["r"] + res["a"] + 1}))
    if len(inst) >= 1:
        muts.append(("trail budget one below actual", res, {"tau": len(inst) - 1}))
    return muts


def main():
    rng = random.Random(178)
    log = dict(routes=[], mutations=[], failures=[])
    plan = []
    for n, lim, npert in ((5, 60 if not QUICK else 10, 40 if not QUICK else 5),
                          (6, 12 if not QUICK else 3, 12 if not QUICK else 2),
                          (7, 3 if not QUICK else 1, 2 if not QUICK else 0)):
        ws = words(n, lim)
        for w in ws: plan.append((n, "archive", w, None))
        for j in range(npert):
            w = rng.choice(ws); plan.append((n, "perturbed", w, 1 + rng.randrange(6)))
        if n <= 6:
            for j in range(10 if not QUICK else 2):
                plan.append((n, "greedy", None, rng.choice([0.0, 0.05, 0.2])))
    cases = {}
    for n, kind, w, param in plan:
        A, B = CheckerA(n), CheckerB(n)
        try:
            if kind == "archive":
                route0 = to_route(w, n); route = normalize(route0, n)
            elif kind == "perturbed":
                route = perturb(to_route(w, n), n, rng, param)
            else:
                route = greedy(n, rng, param)
            res = coarsen(route, n, rng)
        except BridgeError as e:
            log["failures"].append(dict(n=n, kind=kind, err=str(e))); print("FAIL", n, kind, e); continue
        okA, okB = check_instance(res, A), check_instance(res, B)
        CONST = math.factorial(n) + math.factorial(n - 1) + math.factorial(n - 2) + n - 3
        Lc = n + sum(min(cost(route[i], route[i + 1], n), 4) for i in range(len(route) - 1)) + 0
        Lc_formula = CONST + res["D"]
        Lc_direct = n + sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1) if cost(route[i], route[i + 1], n) <= 3) + 4 * (res["p"] - 1)
        entry = dict(n=n, kind=kind, param=param, r=res["r"], q=res["q"], p=res["p"], M=res["M"], k=res["k"],
                     m=res["m"], a=res["a"], b=res["b"], eta=res["eta"], D=res["D"], cycles=res["cycles"],
                     trails=len(res["instance"]), rows=sum(len(t) for t in res["instance"]),
                     A=okA, B=okB, Lc_ok=Lc_direct == Lc_formula,
                     word_ge_Lc=(len(w) >= Lc_formula) if (kind == "archive") else None, case=case_of(res))
        if kind == "archive" and route == route0:
            entry["master"] = master_compare(w, n, res)
        elif kind != "archive":
            w2 = word_of_route(route, n)
            if [tuple(int(ch) - 1 for ch in t) for t in route_of_word(w2, n)] == route:
                entry["master"] = master_compare(w2, n, res)
                entry["word_ge_Lc"] = len(w2) >= Lc_formula
        cases[(n, entry["case"])] = cases.get((n, entry["case"]), 0) + 1
        log["routes"].append(entry)
        if not (okA[0] and okB[0] and entry["Lc_ok"] and entry["word_ge_Lc"] in (None, True)):
            log["failures"].append(entry); print("FAIL", entry)
        # mutations on a subset
        if len(log["mutations"]) < 400:
            for name, rr, claims in mutations(res, n):
                ra, rb = check_instance(rr, A, claims), check_instance(rr, B, claims)
                log["mutations"].append(dict(n=n, name=name, A=ra, B=rb))
                if ra[0] or rb[0]:
                    log["failures"].append(dict(n=n, mutation=name, A=ra, B=rb)); print("MUTANT ACCEPTED", n, name)
    # summary
    by = {}
    for e in log["routes"]:
        key = (e["n"], e["kind"]); s = by.setdefault(key, dict(count=0, a_pos=0, b_pos=0, D_max=0, okA=0, okB=0))
        s["count"] += 1; s["a_pos"] += e["a"] > 0; s["b_pos"] += e["b"] > 0; s["D_max"] = max(s["D_max"], e["D"])
        s["okA"] += e["A"][0]; s["okB"] += e["B"][0]
    for key, s in sorted(by.items()): print(key, s)
    print("trichotomy cases:", {f"n={k[0]} {k[1]}": v for k, v in sorted(cases.items())})
    mm = [e["master"] for e in log["routes"] if e.get("master")]
    if mm:
        keys = ["r_eq_G", "q_eq_S1", "eta_eq_h", "M_eq_O", "m_eq_k", "ab_eq_ZB", "t_eq"]
        print("dictionary on unperturbed archive routes:", {k: sum(x[k] for x in mm) for k in keys}, "of", len(mm),
              "; with Z>0:", sum(x["Z"] > 0 for x in mm), "B*>0:", sum(x["Bstar"] > 0 for x in mm),
              "a != Z:", sum(x["a"] != x["Z"] for x in mm))
    nm = len(log["mutations"]); rej = sum(not x["A"][0] and not x["B"][0] for x in log["mutations"])
    print(f"mutations: {nm}, rejected by both: {rej}")
    print("FAILURES:", len(log["failures"]))
    json.dump(log, open(os.path.join(HERE, "..", "certs", "run178.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
