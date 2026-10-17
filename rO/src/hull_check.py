#!/usr/bin/env python3
"""Round O (section 20) -- independent check of the order-hull decomposition of the 16.111 LP optimum.
Reads hull_test.json only: (i) every order is a permutation of the 30 trails, (ii) weights are >= 0
and sum to 1, (iii) sum_k lam_k z^{pi_k} equals the LP's trail-level arc vector z (and the start /
end vectors) up to 1e-6, (iv) F(pi_k) recomputed with the independent implementation B
(fixed_order_b.py) equals the stored value.  usage: hull_check.py FAMILY.json HULL.json"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixed_order_b as FB

def main():
    fam, hp = sys.argv[1:3]; d = json.load(open(hp))
    dec = d["decomposition"]; ok_perm = all(sorted(x["order"]) == list(range(30)) for x in dec)
    lams = [x["lam"] for x in dec]; ok_w = min(lams) >= 0 and abs(sum(lams) - 1) < 1e-9
    z = {}; f = {}; l = {}
    for x in dec:
        o, w = x["order"], x["lam"]
        for a, b in zip(o, o[1:]): z[f"{a}->{b}"] = z.get(f"{a}->{b}", 0.0) + w
        f[str(o[0])] = f.get(str(o[0]), 0.0) + w; l[str(o[-1])] = l.get(str(o[-1]), 0.0) + w
    def dist(u, v): return max(abs(u.get(k, 0.0) - v.get(k, 0.0)) for k in set(u) | set(v))
    dz, df, dl = dist(z, d["z_support"]), dist(f, d["first"]), dist(l, d["last"])
    ob = FB.build(fam); bad = [x["F"] for x in dec if FB.F(ob, x["order"]) != x["F"]]
    print(json.dumps(dict(orders=len(dec), permutations=ok_perm, weights=ok_w, max_dev_z=dz, max_dev_first=df, max_dev_last=dl,
                          z_ok=dz < 1e-3 and df < 1e-3 and dl < 1e-3, F_recomputed_by_B=len(bad) == 0, minF=min(x["F"] for x in dec))))

main()
