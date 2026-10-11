#!/usr/bin/env python3
"""Exact bundle packing in the {a,b}-system (sec. 11-12, orbit-reduced): the ground set is the
(n-3)! cyclic arrangements C of the n-2 symbols other than a, b.  A bundle shape (closed trail whose
class set is a union of whole P({a,b},C)) is moved by all relabellings of those n-2 symbols; each
image is a subset of arrangements.  Partition all arrangements into bundle images and singletons
(free phi-cycles), maximizing total saving  sum_B [k_B (n-1) - (q_B + 1)].
Then Phi_core = (n-3)! (n-1) - saving  and  L >= CONST - ORB - 1 + Phi_core (cost-4 links)."""
import sys, os, json, itertools, math, time
from ortools.sat.python import cp_model
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])

def bundle_Cset(n, word, pair):
    """C-set (arrangements of the non-pair symbols, as tuples of those symbols) of the closed trail
    of `word` started at the identity."""
    from bundle_scan_lib import closed_classes
    cl = closed_classes(n, word)
    u, v = pair
    return frozenset(cyc_canon([x for x in c if x not in (u, v)]) for c in cl), len(cl)

if __name__ == "__main__":
    n = int(sys.argv[1]); tl = float(sys.argv[2]); bfile = sys.argv[3]; topk = int(sys.argv[4]) if len(sys.argv) > 4 else 50
    shapes = json.load(open(bfile))
    shapes = [s for s in shapes if s["saving"] > 0][:topk]
    others = list(range(1, n - 1))                    # target system {0, n-1}; arrangements of 1..n-2
    ground = sorted({cyc_canon(list(p)) for p in itertools.permutations(others)})
    gid = {C: i for i, C in enumerate(ground)}
    t0 = time.time(); cands = {}
    for si, sh in enumerate(shapes):
        Cset, ncl = bundle_Cset(n, sh["word"], tuple(sh["pair"]))
        src = [x for x in range(n) if x not in sh["pair"]]
        for img in itertools.permutations(others):
            mp = dict(zip(src, img))
            key = frozenset(gid[cyc_canon([mp[x] for x in C])] for C in Cset)
            if key not in cands or cands[key][0] < sh["saving"]: cands[key] = (sh["saving"], si, img)
    m = cp_model.CpModel(); keys = list(cands)
    x = [m.NewBoolVar("") for _ in keys]
    cover = [[] for _ in ground]
    for i, k in enumerate(keys):
        for c in k: cover[c].append(x[i])
    for c in range(len(ground)): m.Add(sum(cover[c]) <= 1)       # remaining arrangements = free phi-cycles
    m.Maximize(sum(cands[k][0] * x[i] for i, k in enumerate(keys)))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = 4
    st = sv.Solve(m)
    ORB = math.factorial(n - 2); HEX = math.factorial(n - 1); CONST = math.factorial(n) + HEX + ORB + n - 3
    nfree = math.factorial(n - 3)
    sol = [keys[i] for i in range(len(keys)) if sv.Value(x[i])] if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else []
    best = sv.ObjectiveValue() if sol else None
    out = dict(n=n, shapes=[s["word"] for s in shapes], candidates=len(cands), ground=len(ground), status=sv.StatusName(st),
               max_saving=best, bound=sv.BestObjectiveBound(),
               Phi_core=None if best is None else nfree * (n - 1) - int(best),
               L_if_cost4_links=None if best is None else CONST - ORB - 1 + nfree * (n - 1) - int(best),
               used=None if not sol else [shapes[cands[k][1]]["word"] for k in sol], sec=round(time.time() - t0, 1))
    print(json.dumps(out))
    if sol:
        json.dump(dict(n=n, bundles=[dict(word=shapes[cands[k][1]]["word"], pair=shapes[cands[k][1]]["pair"], img=cands[k][2]) for k in sol]),
                  open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"bundle_pack_n{n}_{int(best)}.json"), "w"))
