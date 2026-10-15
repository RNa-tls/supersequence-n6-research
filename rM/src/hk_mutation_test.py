#!/usr/bin/env python3
"""Round M (section 10) -- tests of the Held-Karp certificate against BOTH 46185 reference words,
and mutation tests of the checker hk_check.py.

1. Every certificate cut S must be satisfied by both reference tours: x(delta+(S)) >= 1 for the
   depot-closed Hamiltonian cycle of each word (the Round J lesson: no cut may be tested only on
   paper).  Degree rows hold trivially.
2. Exact identity for each reference tour x:  c.x = sum_a rc_a x_a + sum u + sum v + sum_S y_S x(delta+(S))
   (checked in exact integer arithmetic with the 2^K-scaled duals); hence bound <= c.x.
3. Mutations (each must be caught or must keep the bound valid):
   a. a cut set containing an index outside 1..N -> rejected by hk_check.py;
   b. duals multiplied by 1.5 / randomly perturbed -> bound stays <= 10897 (weak duality) and
      the negative-reduced-cost correction grows;
   c. the certificate of the 46185 starts applied to the 46187 starts -> still a valid (weaker or
      equal) bound <= 10899, never above the 46187 tour cost.
usage: hk_mutation_test.py CERT.npz"""
import sys, os, json, subprocess, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runatsp as RA

HERE = os.path.dirname(os.path.abspath(__file__))

def tour_checks(word, z, K=20):
    st = RA.starts_of_word(RA.load_word(word)); N = len(st)
    ref = RA.starts_of_word(RA.load_word(os.path.join(HERE, "..", "..", "rL", "records", "superperm8_46185.txt")))
    canon = lambda p: min(p[j:] + p[:j] for j in range(8))
    pos = {canon(s): i for i, s in enumerate(ref)}   # certificate node ids = classes in the 46185 order
    order = [pos[canon(s)] for s in st]              # the word's runs as certificate node ids (0-based)
    same_starts = set(st) == set(ref)
    W = RA.weight_matrix(ref).astype(np.int64)
    cost = int(W[order[:-1], order[1:]].sum())
    # arcs of the depot-closed cycle (node ids 1..N, depot 0)
    tails = [0] + [o + 1 for o in order]; heads = [o + 1 for o in order] + [0]
    ptr, nodes = z["cut_ptr"], z["cut_nodes"]
    inS = np.zeros(N + 1, bool); viol = 0; minx = 10 ** 9
    sc = 1 << K
    U = np.round(z["u"] * sc).astype(np.int64); V = np.round(z["v"] * sc).astype(np.int64)
    Y = np.maximum(np.round(z["y"] * sc).astype(np.int64), 0)
    ysx = 0
    t_arr = np.array(tails); h_arr = np.array(heads)
    for i in range(len(ptr) - 1):
        S = nodes[ptr[i]:ptr[i + 1]]
        inS[:] = False; inS[S] = True
        xS = int((inS[t_arr] & ~inS[h_arr]).sum())
        minx = min(minx, xS); viol += xS < 1
        ysx += int(Y[i]) * xS
    # exact identity: sum_a c_a x_a * sc = sum_a rc_a x_a + sum U + sum V + sum_S Y_S x(delta+(S))
    cut_out = np.zeros((len(ptr) - 1,), np.int64)
    rc_sum = 0
    member = {}
    for i in range(len(ptr) - 1):
        for v_ in nodes[ptr[i]:ptr[i + 1]].tolist(): member.setdefault(v_, []).append(i)
    for a, b in zip(tails, heads):
        c = 0 if (a == 0 or b == 0) else int(W[a - 1, b - 1])
        ys = sum(int(Y[i]) for i in member.get(a, []) if b not in set(nodes[ptr[i]:ptr[i + 1]].tolist())) if a else 0
        rc_sum += c * sc - int(U[a]) - int(V[b]) - ys
    lhs = cost * sc
    rhs = rc_sum + int(U.sum()) + int(V.sum()) + ysx
    return dict(word=os.path.basename(word), same_starts_as_certificate=same_starts,
                tour_cost_in_certificate_model=cost if same_starts else None, cuts=int(len(ptr) - 1),
                violated_cuts=int(viol), min_cut_value=int(minx),
                identity_ok=(lhs == rhs) if same_starts else "n/a (different starts; cuts are class-set statements)")

def run_check(word, cert):
    out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "hk_check.py"), word, cert, "20"],
                         capture_output=True, text=True)
    return out.returncode, (json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 else out.stderr.strip().splitlines()[-1])

def main():
    cert = sys.argv[1]; z = np.load(cert)
    w1 = os.path.join(HERE, "..", "..", "rL", "records", "superperm8_46185.txt")
    w2 = os.path.join(HERE, "..", "..", "rL", "records", "superperm8_46185_b.txt")
    w3 = os.path.join(HERE, "..", "..", "rI", "records", "superperm8_46187.txt")
    res = {"reference_tours": []}
    for w in (w1, w2):
        res["reference_tours"].append(tour_checks(w, z))
    # 46185_b uses other starts for 8 phi-cycles: the certificate (46185 starts) does not apply to
    # its tour; it is checked with its own starts below (mutation c-type): bound for its start set
    tmp = tempfile.mkdtemp()
    def save(**kw):
        p = os.path.join(tmp, "m%d.npz" % len(os.listdir(tmp)))
        d = {k: z[k] for k in z.files}; d.update(kw); np.savez(p, **d); return p
    rc, base = run_check(w1, cert); res["base"] = base
    # a: corrupt a cut with index 0 (the depot) / out of range
    bad = z["cut_nodes"].copy(); bad[0] = 0
    rc_a, out_a = run_check(w1, save(cut_nodes=bad)); res["mut_a_depot_in_cut"] = dict(returncode=rc_a, caught=(rc_a != 0))
    # b: inflate / perturb duals
    rng = np.random.RandomState(7)
    for name, kw in [("u_v_x1.5", dict(u=z["u"] * 1.5, v=z["v"] * 1.5)),
                     ("y_x2", dict(y=z["y"] * 2)),
                     ("noise", dict(u=z["u"] + rng.normal(0, 0.3, len(z["u"])), v=z["v"] + rng.normal(0, 0.3, len(z["v"]))))]:
        rc_b, out_b = run_check(w1, save(**kw))
        res["mut_b_" + name] = dict(returncode=rc_b, bound=out_b["bound"] if rc_b == 0 else None,
                                     valid=(rc_b == 0 and out_b["cost_lb"] <= 10897), neg_rc=out_b.get("negative_rc_total") if rc_b == 0 else None)
    # c: the same duals on other start sets (46185_b, 46187): must stay below their tour costs
    for w, c in ((w2, 10897), (w3, 10899)):
        rc_c, out_c = run_check(w, cert)
        res["mut_c_" + os.path.basename(w)] = dict(returncode=rc_c, bound=out_c["bound"] if rc_c == 0 else None,
                                                    valid=(rc_c == 0 and out_c["cost_lb"] <= c))
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
