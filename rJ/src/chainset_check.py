#!/usr/bin/env python3
"""Independent checker for chainset_bc.py certificates (shares no code with the producer or with
chainset_model.py).  Verifies, in exact integer arithmetic:
 1. the chain set re-derived from the word; arc list complete (every ordered pair of distinct chains
    with overlap >= 1, weight cost-3), hub arcs (a->H weight n-3, H->b weight 0), depot arcs (weight 0);
 2. every pool cut S: D not in S, S contains a chain  (=> valid for every route);
 3. row structure: out/in = 1 for chains and D, out(H) = in(H), then cut rows;
 4. root reduced-cost fixings justified by the root dual: LB_root + r_j > (T-1)*SCALE;
 5. the branch tree covers the fixed space (binary splits on one arc each; node reduced-cost fixings
    x_a = 0 below a branch node only when that node's exact bound + r_a > (T-1)*SCALE);
 6. every leaf: exact bound  sum y_k b_k + sum_free min(0, r_j) + sum_fixed1 r_j  > (T-1)*SCALE,
    with y_ge >= 0, r = w*SCALE - A^T y.
Conclusion if all pass: every ordering of the chains has weight >= T, i.e. word length >= BASE + T."""
import sys, os, json, math
import numpy as np
import gzip
def jload(path):
    return json.load(gzip.open(path, 'rt') if path.endswith('.gz') else open(path))

def perms_of_word(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); n = len(al); m = {c: i for i, c in enumerate(al)}
    w = [m[c] for c in w]
    first = []; seen = set()
    for i in range(len(w) - n + 1):
        t = tuple(w[i:i + n])
        if len(set(t)) == n and t not in seen: seen.add(t); first.append(t)
    return first, n

def overlap_cost(x, y, n):
    k = n - 1
    while k > 0:
        if x[n - k:] == y[:k]: return n - k
        k -= 1
    return n

def main():
    word, certf = sys.argv[1], sys.argv[2]
    C = jload(certf)
    perms, n = perms_of_word(word)
    assert len(perms) == math.factorial(n), "word is not a superpermutation"
    # runs of n consecutive rotations, chains of F-steps (independent re-derivation)
    runs = [perms[i] for i in range(0, len(perms), n)]
    for i in range(0, len(perms), n):
        for k in range(1, n): assert perms[i + k] == perms[i + k - 1][1:] + perms[i + k - 1][:1], "not r=0"
    chains = []
    for s in runs:
        if chains and s == chains[-1][-1][1:n - 1] + (chains[-1][-1][0], chains[-1][-1][n - 1]): chains[-1].append(s)
        else: chains.append([s])
    q = len(chains); D, H = q, q + 1
    st = [c[0] for c in chains]; en = [c[-1][-1:] + c[-1][:-1] for c in chains]
    HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
    assert C["BASE"] == CONST - ORB + q
    # 1. arcs
    arcs = [tuple(a) for a in C["arcs"]]; A = len(arcs)
    aset = {}
    for i, (a, b, wgt) in enumerate(arcs):
        assert (a, b) not in aset; aset[(a, b)] = i
        if a < q and b < q:
            c = overlap_cost(en[a], st[b], n); assert a != b and c <= n - 1 and wgt == c - 3
        elif b == H: assert a < q and wgt == n - 3
        elif a == H: assert b < q and wgt == 0
        elif a == D: assert b < q and wgt == 0
        elif b == D: assert a < q and wgt == 0
        else: raise AssertionError("bad arc")
    need = 0
    for a in range(q):
        for b in range(q):
            if a != b and overlap_cost(en[a], st[b], n) <= n - 1:
                assert (a, b) in aset, "missing arc"; need += 1
        for pair in ((a, H), (H, a), (D, a), (a, D)): assert pair in aset
    assert A == need + 4 * q
    tail = np.array([a for a, _, _ in arcs]); head = np.array([b for _, b, _ in arcs]); w = np.array([c for _, _, c in arcs], dtype=np.int64)
    # 2. cuts
    pool = [frozenset(S) for S in C["pool"]]
    for S in pool: assert D not in S and any(v < q for v in S), "invalid cut"
    # 3. rows
    rows = C["rows"]; k = 0
    assert len(rows) < 2 ** 12, "too many rows for the int64 accumulation bound"
    for v in range(q + 2):
        if v == H: assert rows[k][0] == "eq" and rows[k][2][0] == "H"; k += 1
        else:
            assert rows[k][0] == "eq" and rows[k][1] == 1.0 and rows[k][2] == ["out", v]; k += 1
            assert rows[k][0] == "eq" and rows[k][1] == 1.0 and rows[k][2] == ["in", v]; k += 1
    ndeg = k
    for j in range(k, len(rows)): assert rows[j][0] == "ge" and rows[j][1] == 1.0 and rows[j][2] == ["cut", j - ndeg]
    out_of = [[] for _ in range(q + 2)]; in_of = [[] for _ in range(q + 2)]
    for i, (a, b, _) in enumerate(arcs): out_of[a].append(i); in_of[b].append(i)
    def row_vec(k):
        kind, b, tag = rows[k]
        if tag[0] == "H": return [(np.array(out_of[H]), 1), (np.array(in_of[H]), -1)], 0
        if tag[0] == "out": return [(np.array(out_of[tag[1]]), 1)], 1
        if tag[0] == "in": return [(np.array(in_of[tag[1]]), 1)], 1
        S = pool[tag[1]]; inS = np.zeros(q + 2, dtype=bool); inS[list(S)] = True
        return [(np.nonzero(inS[tail] & ~inS[head])[0], 1)], 1
    cache = {}
    SC = C["SCALE"]; THR = (C["T"] - 1) * SC
    def bound(ysparse, fix0, fix1):
        aty = np.zeros(A, dtype=object); yb = 0
        aty = np.zeros(A, dtype=np.int64)
        for k, v in ysparse:
            assert abs(v) < 2 ** 50
            if rows[k][0] == "ge" and v < 0: v = 0
            if v == 0: continue
            if k not in cache: cache[k] = row_vec(k)
            parts, b = cache[k]
            for idx, coef in parts: aty[idx] += coef * v
            yb += v * b
        r = w * SC - aty
        assert int(np.max(np.abs(r))) < (2 ** 62) // A, "magnitudes too large for exact int64 sums"
        free = np.ones(A, dtype=bool)
        if fix0: free[list(fix0)] = False
        if fix1: free[list(fix1)] = False
        lb = yb + int(np.sum(np.minimum(0, r[free]))) + (int(np.sum(r[list(fix1)])) if fix1 else 0)
        return lb, r
    # 4. root fixings (validated only in a top-level certificate; subtrees inherit them)
    fixed0 = set(C["root"]["fixed0"])
    if not C.get("init_fix"):
        lb_root, r_root = bound(C["root"]["y"], [], [])
        for j in fixed0: assert r_root[j] > 0 and lb_root + int(r_root[j]) > THR, "unjustified fixing"
    # 5./6. tree
    nodes = {nd["id"]: nd for nd in C["nodes"]}
    assert 0 in nodes and nodes[0]["parent"] is None
    children = {}
    for nd in C["nodes"]:
        if nd["parent"] is not None: children.setdefault(nd["parent"], []).append(nd)
    assert all(nd["kind"] != "INCUMBENT" for nd in C["nodes"])
    assert C["complete"] or C.get("frontier"), "incomplete certificate"
    leaves = 0; worst = None
    init = C.get("init_fix", [])
    if init:                                    # subtree certificate: root fixings must come from the caller
        global_fixed0 = set(jload(sys.argv[3])["root"]["fixed0"]) if len(sys.argv) > 3 else None
        assert global_fixed0 is not None and fixed0 == global_fixed0, "subtree must use the top certificate's validated fixings"
    i0 = [a for a, v in init if v == 0]; i1 = [a for a, v in init if v == 1]
    delegated = []
    stack = [(0, i0, i1)]
    while stack:
        i, f0, f1 = stack.pop(); nd = nodes[i]
        if nd["kind"] == "branch":
            ch = children.get(i, []); assert len(ch) == 2
            j = nd["branch_var"]; assert {c["val"] for c in ch} == {0, 1} and all(c["var"] == j for c in ch)
            assert j not in fixed0 and j not in f0 and j not in f1
            rcf = nd.get("rcfix", [])
            if rcf:
                # node reduced-cost fixing: x_a = 0 below this node, justified by this node's dual
                assert len(set(rcf)) == len(rcf) and j not in rcf
                lb, r = bound(nd["y"], sorted(fixed0 | set(f0)), f1)
                for a in rcf:
                    assert a not in fixed0 and a not in f0 and a not in f1, "node fixing of an already fixed arc"
                    assert r[a] > 0 and lb + int(r[a]) > THR, "unjustified node fixing"
                f0 = f0 + list(rcf)
            for c in ch: stack.append((c["id"], f0 + [j] if c["val"] == 0 else f0, f1 + [j] if c["val"] == 1 else f1))
        elif nd["kind"] == "delegated":
            assert sorted(map(tuple, nd["fix"])) == sorted([(a, 0) for a in f0] + [(a, 1) for a in f1]), "delegated fixings mismatch"
            delegated.append(sorted(map(tuple, nd["fix"])))
        else:
            assert nd["kind"] in ("pruned", "infeasible_lp")
            lb, _ = bound(nd["y"], sorted(fixed0 | set(f0)), f1)
            assert lb > THR, f"leaf {i} bound {lb / SC} not > {C['T'] - 1}"
            leaves += 1; worst = lb if worst is None else min(worst, lb)
    res = dict(ok=True, n=n, chains=q, arcs=A, cuts=len(pool), root_fixed=len(fixed0), leaves=leaves,
               min_leaf_bound=None if worst is None else worst / SC, delegated=len(delegated), T=C["T"])
    if not delegated and not C.get("init_fix"):
        res["theorem"] = f"every route on this chain set has weight >= {C['T']}, length >= {C['BASE'] + C['T']}"
    if os.environ.get("DELEG_OUT"): json.dump(delegated, open(os.environ["DELEG_OUT"], "w"))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
