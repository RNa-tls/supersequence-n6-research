#!/usr/bin/env python3
"""Second independent checker for chain-ordering certificates (Round J).

Written from scratch: shares no code with chainset_bc.py / chainset_model.py (producer) or with
chainset_check.py / composite_check.py (first checker).  Pure Python integers only (no numpy, no
floating point, no overflow), and it checks a whole composite certificate in one process.

    usage: chainset_check2.py WORD TOP [SUB ...]

What is verified, from first principles:
  W. WORD contains all n! permutations; in order of first occurrence they form (n-1)! runs of n
     cyclic rotations (r = 0).  Runs are grouped into chains: consecutive runs whose junction has
     overlap n-2.  For any ordering c_1..c_q of the chains, gluing with maximal overlaps gives a
     superpermutation of length  BASE + sum_i (cost(c_i, c_{i+1}) - 3),  BASE = n + (n-1)!(n+1) - 3 + q,
     cost = n - overlap(end of c_i, start of c_{i+1}).
  M. The certificate's variable list is exactly: arcs a->b (distinct chains, overlap >= 1, weight
     cost-3), a->H (weight n-3, the no-overlap join), H->b, D->b, a->D (weight 0).  Every ordering
     is a 0/1 point x with out = in = 1 at every chain and at D, out(H) = in(H), and
     x(delta+(S)) >= 1 for every S with D not in S containing a chain (the walk ends at D).
  R. Row list = those degree rows (fixed order) followed by one cut row per pool set; every pool set
     is a legal S.
  B. For each leaf with duals y (y >= 0 on cut rows) and fixings F0 (x=0), F1 (x=1):
        SCALE*w.x = y.Ax + r.x >= y.b + sum_{j in F1} r_j + sum_{j free} min(0, r_j),  r = SCALE*w - A^T y,
     and this must exceed SCALE*(T-1).  Root fixings x_j = 0 need LB_root + r_j > SCALE*(T-1), r_j > 0.
  T. Every certificate's branch tree is a binary split on one unfixed arc per branch node (plus, if
     recorded, node reduced-cost fixings x_a = 0 below a node, each justified by that node's own exact
     bound with x_a forced to 1 exceeding SCALE*(T-1)), every node
     is reachable, no INCUMBENT records; delegated leaves carry exactly the path fixings and are closed
     by exactly one subtree certificate (strictly deeper, same T/BASE/arcs/root fixings); every given
     subtree certificate is used.
Conclusion printed only if everything passes: every ordering has weight >= T, length >= BASE + T."""
import sys, json, gzip, math
from array import array

def load(path):
    f = gzip.open(path, "rt") if path.endswith(".gz") else open(path)
    with f: return json.load(f)

def fail(msg):
    print("REJECT: " + msg); sys.exit(1)

def need(cond, msg):
    if not cond: fail(msg)

def overlap(x, y, n):
    """largest k < n with x[n-k:] == y[:k]"""
    for k in range(n - 1, 0, -1):
        if x[n - k:] == y[:k]: return k
    return 0

# ---------------------------------------------------------------- W: word -> chains
def chains_from(word_path):
    txt = "".join(open(word_path).read().split())
    syms = sorted(set(txt)); n = len(syms); code = {c: i for i, c in enumerate(syms)}
    s = [code[c] for c in txt]
    seen = set(); order = []
    for i in range(len(s) - n + 1):
        win = tuple(s[i:i + n])
        if len(set(win)) == n and win not in seen:
            seen.add(win); order.append(win)
    need(len(seen) == math.factorial(n), "word is not a superpermutation")
    # r = 0: the first-occurrence order is a concatenation of runs p, Rp, ..., R^{n-1}p
    need(len(order) % n == 0, "not r=0")
    runs = []
    for i in range(0, len(order), n):
        p = order[i]
        for k in range(n):
            need(order[i + k] == p[k:] + p[:k], "not r=0 (run %d)" % (i // n))
        runs.append((order[i], order[i + n - 1]))            # (first perm, last perm) of the run
    classes = set(min(p[k:] + p[:k] for k in range(n)) for p, _ in runs)
    need(len(classes) == len(runs) == math.factorial(n - 1), "classes not covered exactly once")
    chains = []                                               # (start perm, end perm)
    for first, last in runs:
        if chains and overlap(chains[-1][1], first, n) == n - 2: chains[-1][1] = last
        else: chains.append([first, last])
    return n, [tuple(c) for c in chains], len(txt)

# ---------------------------------------------------------------- M, R: model
class Model:
    def __init__(self, n, chains):
        self.n = n; self.q = q = len(chains); self.D = q; self.H = q + 1; self.V = q + 2
        self.start = [c[0] for c in chains]; self.end = [c[1] for c in chains]
        self.base = n + math.factorial(n - 1) * (n + 1) - 3 + q
        exp = {}
        for a in range(q):
            ea = self.end[a]
            for b in range(q):
                if a != b:
                    ov = overlap(ea, self.start[b], n)
                    if ov >= 1: exp[(a, b)] = (n - ov) - 3
            exp[(a, self.H)] = n - 3; exp[(self.H, a)] = 0; exp[(self.D, a)] = 0; exp[(a, self.D)] = 0
        self.expected = exp

    def bind(self, arcs):
        """check the certificate's arc list against the model; keep tails/heads/weights"""
        need(len(arcs) == len(self.expected), "arc count %d != %d" % (len(arcs), len(self.expected)))
        seen = set()
        for a, b, wt in arcs:
            need((a, b) not in seen, "duplicate arc"); seen.add((a, b))
            need((a, b) in self.expected and self.expected[(a, b)] == wt, "wrong or extra arc %r" % ((a, b, wt),))
        self.tail = [a for a, _, _ in arcs]; self.head = [b for _, b, _ in arcs]; self.w = [wt for _, _, wt in arcs]
        self.A = len(arcs)

    def word_order_weight(self):
        """weight of the input word's own chain order (D -> 0 -> 1 -> ... -> q-1 -> D)"""
        tot = 0
        for a in range(self.q - 1):
            ov = overlap(self.end[a], self.start[a + 1], self.n)
            tot += (self.n - ov) - 3
        return tot

    def degree_rows(self):
        rows = []
        for v in range(self.V):
            if v == self.H: rows.append(["eq", 0.0, ["H"]])
            else: rows.append(["eq", 1.0, ["out", v]]); rows.append(["eq", 1.0, ["in", v]])
        return rows

# ---------------------------------------------------------------- B: exact bounds
class Bounder:
    def __init__(self, M, cert):
        self.M = M; self.SC = cert["SCALE"]; self.T = cert["T"]
        need(isinstance(self.SC, int) and self.SC > 0, "bad SCALE")
        deg = M.degree_rows(); rows = cert["rows"]; nd = len(deg)
        need(len(rows) == nd + len(cert["pool"]), "row count mismatch")
        for k in range(nd):
            need(rows[k][0] == deg[k][0] and float(rows[k][1]) == deg[k][1] and list(rows[k][2]) == deg[k][2], "degree row %d differs" % k)
        self.meaning = []                       # per row: ('out', v) / ('in', v) / ('H',) / ('cut', frozenset)
        for k in range(nd): self.meaning.append(tuple(deg[k][2]))
        for i, S in enumerate(cert["pool"]):
            need(rows[nd + i][0] == "ge" and float(rows[nd + i][1]) == 1.0 and list(rows[nd + i][2]) == ["cut", i], "cut row %d differs" % i)
            fs = frozenset(S)
            need(len(fs) == len(S) and all(isinstance(v, int) and 0 <= v < M.V for v in fs), "malformed cut set")
            need(M.D not in fs and any(v < M.q for v in fs), "illegal cut set (contains D or no chain)")
            self.meaning.append(("cut", fs))
    CUT_ARCS = {}                               # shared by all certificates (same arc list)

    def leaving(self, fs):
        if fs not in Bounder.CUT_ARCS:
            M = self.M
            Bounder.CUT_ARCS[fs] = array("i", [j for j in range(M.A) if M.tail[j] in fs and M.head[j] not in fs])
        return Bounder.CUT_ARCS[fs]

    def bound(self, ysparse, fix0, fix1, want_r=False):
        """exact integer: SCALE * (lower bound on w.x over the region)  [and the reduced costs]"""
        M = self.M
        yout = [0] * M.V; yin = [0] * M.V; yH = 0; yb = 0; aty = [0] * M.A; cuts = []
        seen = set()
        for k, v in ysparse:
            need(isinstance(k, int) and isinstance(v, int) and 0 <= k < len(self.meaning) and k not in seen, "malformed dual")
            seen.add(k)
            m = self.meaning[k]
            if m[0] == "out": yout[m[1]] += v; yb += v
            elif m[0] == "in": yin[m[1]] += v; yb += v
            elif m[0] == "H": yH += v
            else:
                need(v >= 0, "negative dual on a >= row"); yb += v; cuts.append((m[1], v))
        for fs, v in cuts:
            if v:
                for j in self.leaving(fs): aty[j] += v
        H = M.H; SC = self.SC
        f0 = set(fix0); f1 = set(fix1)
        need(not (f0 & f1), "arc fixed to both 0 and 1")
        lb = yb; rr = [] if want_r else None
        for j in range(M.A):
            a, b = M.tail[j], M.head[j]
            t = yout[a] + yin[b] + aty[j]
            if a == H: t += yH
            if b == H: t -= yH
            r = M.w[j] * SC - t
            if want_r: rr.append(r)
            if j in f1: lb += r
            elif j not in f0 and r < 0: lb += r
        return (lb, rr) if want_r else lb

# ---------------------------------------------------------------- T: trees
def check_tree(B, cert, init0, init1, fixed0):
    """returns (#pruned leaves, min leaf bound, list of delegated fixing keys)"""
    THR = (B.T - 1) * B.SC
    nodes = {}
    for nd in cert["nodes"]:
        need(nd["id"] not in nodes, "duplicate node id"); nodes[nd["id"]] = nd
        need(nd["kind"] in ("branch", "pruned", "infeasible_lp", "delegated"), "node kind %r not allowed" % nd["kind"])
    need(0 in nodes and nodes[0]["parent"] is None, "no root node")
    kids = {}
    for nd in cert["nodes"]:
        if nd["parent"] is not None: kids.setdefault(nd["parent"], []).append(nd)
    leaves = 0; worst = None; deleg = []; visited = set()
    todo = [(0, list(init0), list(init1))]
    while todo:
        i, f0, f1 = todo.pop(); nd = nodes[i]
        need(i not in visited, "node visited twice"); visited.add(i)
        if nd["kind"] == "branch":
            j = nd["branch_var"]; ch = kids.get(i, [])
            need(isinstance(j, int) and 0 <= j < B.M.A, "bad branch variable")
            need(len(ch) == 2 and sorted(c["val"] for c in ch) == [0, 1] and all(c["var"] == j for c in ch), "bad split at node %d" % i)
            need(j not in fixed0 and j not in f0 and j not in f1, "branch on a fixed arc")
            rcf = nd.get("rcfix") or []
            if rcf:
                # node reduced-cost fixing x_a = 0 below this node: the node's own exact bound with
                # x_a forced to 1 must already exceed SCALE*(T-1)
                need(len(set(rcf)) == len(rcf) and j not in rcf, "malformed node fixing list")
                fz = set(fixed0) | set(f0)
                lbn, rn = B.bound(nd["y"], sorted(fz), f1, want_r=True)
                for a in rcf:
                    need(isinstance(a, int) and 0 <= a < B.M.A and a not in fz and a not in f1, "node fixing of a fixed/bad arc")
                    need(lbn - min(0, rn[a]) + rn[a] > THR, "unjustified node fixing of arc %d at node %d" % (a, i))
                f0 = f0 + list(rcf)
            for c in ch:
                todo.append((c["id"], f0 + [j], f1) if c["val"] == 0 else (c["id"], f0, f1 + [j]))
        elif nd["kind"] == "delegated":
            key = tuple(sorted([(a, 0) for a in f0] + [(a, 1) for a in f1]))
            need(tuple(sorted(tuple(x) for x in nd["fix"])) == key, "delegated fixings differ from the path")
            need(not kids.get(i), "delegated node has children"); deleg.append(key)
        else:
            need(not kids.get(i), "leaf has children")
            lb = B.bound(nd["y"], sorted(set(fixed0) | set(f0)), f1)
            need(lb > THR, "leaf %d: bound %.6f not > %d" % (i, lb / B.SC, B.T - 1))
            leaves += 1; worst = lb if worst is None else min(worst, lb)
    need(len(visited) == len(nodes), "unreachable nodes in the tree")
    return leaves, worst, deleg

def main():
    word, top, subs = sys.argv[1], sys.argv[2], sys.argv[3:]
    n, chains, wlen = chains_from(word)
    M = Model(n, chains)
    C = load(top)
    need(C["n"] == n and C["BASE"] == M.base, "n/BASE mismatch")
    need(not C.get("init_fix"), "top certificate must start from the empty fixing")
    M.bind([tuple(a) for a in C["arcs"]])
    ww = M.word_order_weight()
    need(wlen >= M.base + ww, "length formula violated by the input word")
    B = Bounder(M, C); THR = (B.T - 1) * B.SC
    fixed0 = sorted(set(C["root"]["fixed0"]))
    if fixed0:
        # root reduced-cost fixing, recomputed: LB_root + r_j > THR with r_j > 0
        lb_root, r_root = B.bound(C["root"]["y"], [], [], want_r=True)
        for j in fixed0:
            need(0 <= j < M.A, "bad fixed arc")
            lb_j = lb_root - min(0, r_root[j]) + r_root[j]     # the same bound with x_j forced to 1
            need(lb_j > THR, "unjustified root fixing of arc %d" % j)
    leaves, worst, open_keys = check_tree(B, C, [], [], fixed0)
    total = leaves; level = {k: 1 for k in open_keys}; depth = 0
    certs = {}
    for sf in subs:
        S = load(sf)
        need(S["T"] == C["T"] and S["BASE"] == C["BASE"] and S["SCALE"] == C["SCALE"] and S["n"] == n, sf + ": T/BASE/SCALE mismatch")
        need(S["arcs"] == C["arcs"], sf + ": arc list differs")
        need(sorted(set(S["root"]["fixed0"])) == fixed0, sf + ": root fixings differ from the top's")
        need(S.get("init_fix"), sf + ": no initial fixings")
        key = tuple(sorted(tuple(x) for x in S["init_fix"]))
        need(key not in certs, sf + ": second certificate for the same leaf")
        certs[key] = (sf, S)
    used = set(); queue = list(open_keys)
    while queue:
        key = queue.pop()
        need(key in certs, "delegated leaf %r is not closed" % (list(key),))
        sf, S = certs[key]; need(sf not in used, sf + " used twice"); used.add(sf)
        BS = Bounder(M, S)
        i0 = [a for a, v in key if v == 0]; i1 = [a for a, v in key if v == 1]
        lv, wv, ks = check_tree(BS, S, i0, i1, fixed0)
        total += lv
        if wv is not None: worst = wv if worst is None else min(worst, wv)
        depth = max(depth, level[key])
        for k2 in ks:
            need(set(key) < set(k2), sf + ": delegated leaf not strictly below its root")
            need(k2 not in level, "leaf delegated twice"); level[k2] = level[key] + 1; queue.append(k2)
        certs[key] = (sf, None)                                 # free memory
    need(len(used) == len(subs), "unused subtree certificates: %r" % sorted(set(subs) - used))
    print(json.dumps(dict(ok=True, checker="chainset_check2", n=n, chains=M.q, arcs=M.A, BASE=M.base,
                          word_length=wlen, word_order_weight=ww, root_fixed=len(fixed0),
                          certificates=1 + len(subs), nesting_depth=depth, pruned_leaves=total,
                          min_leaf_bound=None if worst is None else worst / B.SC, T=B.T,
                          theorem="every ordering of this chain set has weight >= %d, i.e. length >= %d" % (B.T, M.base + B.T))))

if __name__ == "__main__":
    main()
