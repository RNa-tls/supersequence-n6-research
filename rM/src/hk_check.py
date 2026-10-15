#!/usr/bin/env python3
"""Round M -- independent checker for a Held-Karp dual certificate (hk_bound.py) of the run-level ATSP.
Shares no code with hk_bound.py / runatsp.py.

Claim checked: for EVERY Hamiltonian path of the 5040 runs (fixed starts of WORD) with arc costs
w(last(s), t), the cost is >= B, hence L >= 35288 + ceil(B) and J >= ceil(B) - 10797.
Proof (weak duality with 0/1 variables): close the path through a depot d (arcs of cost 0) to a
Hamiltonian cycle x on V = runs + {d}.  For duals u_v, v_v (free) and y_S >= 0 (S = nonempty set of
runs), rc_a = c_a - u_tail - v_head - sum_{S : a leaves S} y_S, and
   c.x = sum_a rc_a x_a + sum_v u_v + sum_v v_v + sum_S y_S x(delta+(S))
       >= sum_a min(rc_a, 0) + sum u + sum v + sum y,
because x(delta+(v)) = x(delta-(v)) = 1, x(delta+(S)) >= 1 and x_a in {0, 1}.
All arithmetic is exact: the duals are rounded to integers / 2^K first (any dual vector is
admissible), then everything is computed in int64.
usage: hk_check.py WORD CERT.npz [K]"""
import sys, math, json
import numpy as np

def main():
    word_path, cert = sys.argv[1], sys.argv[2]; K = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    text = "".join(ch for ch in open(word_path).read() if not ch.isspace())
    al = sorted(set(text)); w = [al.index(c) for c in text]; n = len(al)
    # runs: first occurrences, blocks of n rotations
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        t = tuple(w[i:i + n])
        if len(set(t)) == n and t not in seen: seen.add(t); route.append(t)
    assert len(route) == math.factorial(n)
    st = route[::n]
    assert all(route[n * b + j] == s[j:] + s[:j] for b, s in enumerate(st) for j in range(n))
    N = len(st)
    # cost matrix c[i][j] = smallest k >= 1 with last(s_i)[k:] == s_j[:n-k], last(s) = s[n-1] s[0..n-2]
    S = np.array(st, dtype=np.int64); X = np.concatenate([S[:, n - 1:], S[:, :n - 1]], axis=1)
    C = np.full((N, N), n, dtype=np.int64)
    for k in range(n - 1, 0, -1):                 # descending k: smaller k overwrites
        m = n - k
        a = np.zeros(N, np.int64); b = np.zeros(N, np.int64)
        for t in range(m): a = a * n + X[:, k + t]; b = b * n + S[:, t]
        eq = a[:, None] == b[None, :]
        C[eq] = k
    np.fill_diagonal(C, 0)                        # diagonal arcs do not exist (excluded below)
    z = np.load(cert)
    u, v, y = z["u"], z["v"], z["y"]; ptr, nodes = z["cut_ptr"], z["cut_nodes"]
    V = N + 1
    assert len(u) == V and len(v) == V and len(y) == len(ptr) - 1
    sc = 1 << K
    U = np.round(u * sc).astype(np.int64); Vv = np.round(v * sc).astype(np.int64)
    Y = np.maximum(np.round(y * sc).astype(np.int64), 0)
    cuts = [nodes[ptr[i]:ptr[i + 1]] for i in range(len(Y))]
    for Sx in cuts:
        assert len(Sx) >= 1 and Sx.min() >= 1 and Sx.max() <= N and len(set(Sx.tolist())) == len(Sx), "bad cut set"
    # reduced costs (scaled) of run -> run arcs
    RC = C * sc - U[1:, None] - Vv[None, 1:]
    ysum_out = np.zeros(N, np.int64)               # for arcs j -> depot: crosses delta+(S) iff j in S
    for Sx, ys in zip(cuts, Y):
        if ys == 0: continue
        mk = np.zeros(N, bool); mk[Sx - 1] = True
        RC[np.ix_(mk, ~mk)] -= ys
        ysum_out[Sx - 1] += ys
    np.fill_diagonal(RC, 0)                       # no loops
    neg = int(np.minimum(RC, 0).sum())
    rc_dep_out = -U[0] - Vv[1:]                   # depot -> j (depot in no S: crosses no delta+(S))
    rc_dep_in = -U[1:] - Vv[0] - ysum_out         # j -> depot
    neg += int(np.minimum(rc_dep_out, 0).sum()) + int(np.minimum(rc_dep_in, 0).sum())
    total = int(U.sum()) + int(Vv.sum()) + int(Y.sum()) + neg
    # bound B = total / 2^K (exact rational); integer path cost >= ceil(B)
    Bceil = -((-total) // sc)
    res = dict(word=word_path, cert=cert, scale_bits=K, cuts=len(cuts), positive_y=int((Y > 0).sum()),
               bound_scaled=total, bound=total / sc, cost_lb=Bceil, L_lb=35288 + Bceil, J_lb=Bceil - 10797,
               negative_rc_total=neg / sc)
    print(json.dumps(res))

if __name__ == "__main__":
    main()
