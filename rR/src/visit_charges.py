#!/usr/bin/env python3
"""Round R -- per-visit charges of a word of the 6A+24phi family (charge theorem Q5: G = sum chi - 29).
Run level: the word's route is its sequence of 5040 runs; a piece boundary is a link that is not the natural version
link; a visit boundary is a change of trail.  For a visit v (pieces f_1..f_s):
    first visit: chi = kappa = [cut(f_1) = 2] + sum_jumps E',  E' = w(link) - cut(head)
    later visit: chi = e_in + 1 + sum_jumps E',               e_in = w(link into v) - cut(head) - 1
Prints every visit (trail, pieces, chi, jump terms), the rotational ones (first jump a wrap E' = -1 out of a mid piece),
and checks G = sum chi - 29 against the length.
usage: visit_charges.py WORD FAMILY.json"""
import sys, json
import numpy as np
n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); al = sorted(set(t)); return [al.index(c) for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    return route[0::n]
def canon(p): return min(p[i:] + p[:i] for i in range(n))
def wgt(x, y):
    X = list(x[7:]) + list(x[:7])      # last permutation of the run
    for s in range(1, 8):
        if X[s:] == list(y[:8 - s]): return s
    return 8
def main():
    w = load_word(sys.argv[1]); st = starts(w); fam = json.load(open(sys.argv[2])); N = len(st)
    # exact run (start permutation) -> [(t, v, k)]; a run class sits in both versions of its trail, usually with
    # different entry rotations; the version used by each trail is the one matching most of the word's runs exactly
    exact = {}; vruns = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            runs = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]; vruns[(t, v)] = runs
            for k, r in enumerate(runs): exact.setdefault(r, []).append((t, v, k))
    votes = {}
    for r in st:
        for (t, v, k) in exact.get(tuple(r), []): votes[(t, v)] = votes.get((t, v), 0) + 1
    usev = {t: max((0, 1), key=lambda v: votes.get((t, v), 0)) for t in range(30)}
    T = []; K = []; Vv = []; M = []; R = []
    for r in st:
        c = [x for x in exact.get(tuple(r), []) if x[1] == usev[x[0]]]
        assert len(c) == 1, ("run not in the chosen version", r)
        t, v, k = c[0]; runs = vruns[(t, v)]; T.append(t); Vv.append(v); K.append(k); M.append(len(runs)); R.append(runs)
    def cut(i):          # cut weight of run i of the route: weight of its natural version link
        runs = R[i]; k = K[i]; m = M[i]; return wgt(runs[(k - 1) % m], runs[k])
    L = 8 + 7 * N + sum(wgt(st[i], st[i + 1]) for i in range(N - 1)); G = L - 46162
    natural = lambda i: T[i] == T[i + 1] and Vv[i] == Vv[i + 1] and K[i + 1] == (K[i] + 1) % M[i]
    visits = []; cur = None
    for i in range(N):
        if i == 0 or T[i] != T[i - 1]:
            cur = dict(trail=T[i], start=i, pieces=1, jumps=[], head_cut=cut(i), e_in=None if i == 0 else wgt(st[i - 1], st[i]) - cut(i) - 1); visits.append(cur)
        elif not natural(i - 1):
            cur["pieces"] += 1; cur["jumps"].append(wgt(st[i - 1], st[i]) - cut(i))
    tot = 0; rot = []
    for j, v in enumerate(visits):
        chi = ((v["head_cut"] == 2) if j == 0 else v["e_in"] + 1) + sum(v["jumps"]); v["chi"] = int(chi); tot += chi
        if j > 0 and v["head_cut"] == 2 and v["jumps"] and v["jumps"][0] == -1: rot.append(j)
    out = dict(word=sys.argv[1], length=L, G=G, P=sum(v["pieces"] for v in visits), V=len(visits), sum_chi=int(tot), identity_ok=(G == tot - 29),
               zero_charge_visits=[dict(index=j, trail=visits[j]["trail"], pieces=visits[j]["pieces"], jumps=visits[j]["jumps"], e_in=visits[j]["e_in"]) for j in range(1, len(visits)) if visits[j]["chi"] == 0],
               rotational_visits=rot, multi_piece_visits=[dict(index=j, trail=v["trail"], pieces=v["pieces"], jumps=v["jumps"], chi=v["chi"]) for j, v in enumerate(visits) if v["pieces"] > 1])
    print(json.dumps(out))
main()
