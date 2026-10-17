#!/usr/bin/env python3
"""Round O (section 2) -- exact value F(pi) of a fixed trail order, single-opening model.

Model SO (as Round M/N): every trail T picks one option o = (version v, opening edge k): the word runs
through T's runs st[k], st[k+1], ..., st[k-1] (one piece).  Boundary o -> o' costs
    e(o, o') = w(exit(o), entry(o')) - cut(o') - 1 >= 0,
and with P = 30 pieces the audited identity (Round N section 1, form (E)) is
    J = E0 + (P - 1) + [c0 = 2] + sum e = 48 + 29 + [cut(o_first) = 2] + sum e = 77 + cost.
For an order pi = (pi_1, ..., pi_30):
    F(pi) = min over options of  [cut(o_1) = 2] + sum_{i<30} e(o_i, o_{i+1}),
exactly computed by the layered shortest-path recurrence (the only state is the option of the
previous trail, i.e. its version and opening edge -- its exit run):
    D_1(o)     = [cut(o) = 2]                                  (o an option of pi_1)
    D_{i+1}(o') = min_{o in pi_i} D_i(o) + e(o, o')            (o' an option of pi_{i+1})
    F(pi)      = min_o D_30(o).
Implementation A (this file): numpy min-plus on the excess matrix E.  Implementation B is
fixed_order_b.py (independent excess computation from the family JSON, pure-python loops).
usage: fixed_order.py FAMILY.json E.npy [ORDER as comma list | audit.json]"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rN", "src"))
import options as OP


class FixedOrder:
    def __init__(self, fam_path, E_path):
        self.fam, self.opts = OP.load(fam_path)
        self.E = np.load(E_path).astype(np.int64)
        self.T = np.array([o["t"] for o in self.opts])
        self.cut = np.array([o["cut"] for o in self.opts])
        self.NT = int(self.T.max()) + 1
        self.topts = [np.nonzero(self.T == t)[0] for t in range(self.NT)]

    def F(self, order, want_options=False):
        D = (self.cut[self.topts[order[0]]] == 2).astype(np.int64)
        back = []
        for a, b in zip(order, order[1:]):
            M = D[:, None] + self.E[np.ix_(self.topts[a], self.topts[b])]
            arg = M.argmin(0); D = M[arg, np.arange(M.shape[1])]; back.append(arg)
        val = int(D.min())
        if not want_options: return val
        j = int(D.argmin()); ch = [int(self.topts[order[-1]][j])]
        for i in range(len(order) - 2, -1, -1):
            j = int(back[i][j]); ch.append(int(self.topts[order[i]][j]))
        return val, ch[::-1]

    def cost(self, opts_seq):
        c = int(self.cut[opts_seq[0]] == 2)
        return c + int(sum(self.E[a, b] for a, b in zip(opts_seq, opts_seq[1:])))


def order_from_audit(path):
    d = json.load(open(path))
    return [r["trail"] for r in d["table"]], d


def main():
    fam_p, E_p = sys.argv[1], sys.argv[2]
    fo = FixedOrder(fam_p, E_p)
    arg = sys.argv[3]
    if arg.endswith(".json"):
        order, d = order_from_audit(arg)
        key = {(o["t"], o["v"], o["k"]): i for i, o in enumerate(fo.opts)}
        word_opts = [key[(r["trail"], r["version"], r["start"])] for r in d["table"]]
        val, ch = fo.F(order, True)
        print(json.dumps(dict(order=order, F=val, J=77 + val, word_cost=fo.cost(word_opts), argmin_cost=fo.cost(ch))))
    else:
        order = [int(x) for x in arg.split(",")]
        print(json.dumps(dict(order=order, F=fo.F(order))))


if __name__ == "__main__":
    main()
