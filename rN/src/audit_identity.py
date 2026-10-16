#!/usr/bin/env python3
"""Round N section 1 -- first-principles audit of the J identity on an r = 0 word, against the
6A+24phi family.  Self-contained: reads only the word and the family JSON.

Checked forms (all must give the same J):
 (R)  run level        J = sum_t (w_t - 2) - 719                     over the 5039 run transitions
 (Q)  4chan form       J = (q - 720) + #(w >= 4) + sum_{w>=4} (w - 4),  q = #word chains (w = 2 runs)
 (C)  chain form       J = 48 + (q - 768) + sum_{non-F transitions} (w - 3)
 (P)  piece form       J = 48 + [c0 = 2] + sum_{k>=1} beta_k,  beta_k = w_k - c_k  (pieces of trails)
 (E)  excess form      J = 48 + (P - 1) + [c0 = 2] + sum_k e_k,  e_k = beta_k - 1
 (V)  visit form       J = 48 + kappa(v_1) + sum_{v >= 2} (w_in(v) - 3 + kappa(v))
 (S)  segment form     J = 48 + (S - 1) + splits + sum_{connections} (w - 4)
       (segment = maximal run of the word whose non-F transitions all have w = 3)
Also: Delta E per opening (F-step cut +1, w = 2 boundary -1, link cut 0), per-piece table.
usage: audit_identity.py WORD FAMILY.json [OUT.json]"""
import sys, json, math, hashlib
from collections import Counter

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def F(s): return s[1:7] + (s[0], s[7])

def main():
    raw = open(sys.argv[1]).read(); text = "".join(ch for ch in raw if not ch.isspace())
    al = sorted(set(text)); word = [al.index(c) for c in text]
    fam = json.load(open(sys.argv[2]))
    sha = hashlib.sha256(raw.encode()).hexdigest()
    # perms and r = 0 run structure
    seen = set(); route = []
    for i in range(len(word) - n + 1):
        p = tuple(word[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    assert len(route) == math.factorial(n), "not a superpermutation"
    steps = [wt(x, y) for x, y in zip(route, route[1:])]
    assert len(word) == n + sum(steps), "word is not tight"
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j], "not r = 0"
    tw = [wt(last(a), b) for a, b in zip(st, st[1:])]          # run transitions
    L = len(word)
    JR = sum(w - 2 for w in tw) - 719
    q = 1 + sum(1 for w in tw if w >= 3)
    JQ = (q - 720) + sum(1 for w in tw if w >= 4) + sum(w - 4 for w in tw if w >= 4)
    JC = 48 + (q - 768) + sum(w - 3 for w in tw if w >= 3)
    # family membership: run start -> (trail, version, cyclic index)
    where = {}
    cyc = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            ss = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            cyc[(t, v)] = ss
            for k, p in enumerate(ss): where.setdefault(p, []).append((t, v, k))
    loc = []
    for s in st:
        assert s in where, "run start not in family"
        loc.append(where[s])
    # choose consistent version per trail (each trail must use one version)
    ver = {}
    for cand in loc:
        ts = {c[0] for c in cand}
        assert len(ts) == 1
    for b, cand in enumerate(loc):
        t = cand[0][0]
        vs = {c[1] for c in cand}
        ver.setdefault(t, set()); ver[t] = vs if not ver[t] else ver[t] & vs
    assert all(len(v) >= 1 for v in ver.values()), "inconsistent versions"
    vsel = {t: min(v) for t, v in ver.items()}
    pos = []
    for b, cand in enumerate(loc):
        t = cand[0][0]; k = [c[2] for c in cand if c[1] == vsel[t]][0]; pos.append((t, vsel[t], k))
    # pieces: maximal segments following trail edges
    pieces = []; cur = [0]
    for b in range(1, len(st)):
        (t0, v0, k0), (t1, v1, k1) = pos[b - 1], pos[b]
        if t0 == t1 and k1 == (k0 + 1) % len(cyc[(t0, v0)]): cur.append(b)
        else: pieces.append(cur); cur = [b]
    pieces.append(cur)
    P = len(pieces)
    def cutw(b):
        t, v, k = pos[b]; ss = cyc[(t, v)]
        return wt(last(ss[k - 1]), ss[k])
    rows = []; beta = []
    for i, pc in enumerate(pieces):
        t, v, k = pos[pc[0]]; c = cutw(pc[0]); m = len(cyc[(t, v)])
        win = tw[pc[0] - 1] if i > 0 else None
        b_ = (win - c) if i > 0 else None
        if i > 0: beta.append(b_)
        rows.append(dict(i=i, trail=t, version=v, start=k, runs=len(pc), trail_runs=m, cut=c, w_in=win, beta=b_,
                         e=(b_ - 1) if b_ is not None else None,
                         intra=(i > 0 and pos[pieces[i - 1][-1]][0] == t)))
    c0 = cutw(pieces[0][0])
    JP = 48 + (1 if c0 == 2 else 0) + sum(beta)
    JE = 48 + (P - 1) + (1 if c0 == 2 else 0) + sum(b - 1 for b in beta)
    # Delta E accounting: E0 = sum_T k_T - 720
    kT = {}
    for (t, v), ss in cyc.items():
        if v == vsel.get(t, 0): kT[t] = sum(1 for k in range(len(ss)) if wt(last(ss[k - 1]), ss[k]) == 3)
    E0 = sum(kT.values()) - 720
    nF = sum(1 for r in rows if r["cut"] == 2); n2 = sum(1 for r in rows if r["w_in"] == 2)
    E = q - 720
    # visits: maximal groups of consecutive pieces of one trail
    visits = []; cv = [0]
    for i in range(1, P):
        if rows[i]["trail"] == rows[i - 1]["trail"]: cv.append(i)
        else: visits.append(cv); cv = [i]
    visits.append(cv)
    def kappa(vi):
        return (3 - rows[vi[0]]["cut"]) + sum(rows[i]["beta"] for i in vi[1:])
    JV = 48 + kappa(visits[0]) + sum(rows[v[0]]["w_in"] - 3 + kappa(v) for v in visits[1:])
    # segments (maximal w <= 3 stretches) and splits
    conn = [w for w in tw if w >= 4]
    S = len(conn) + 1
    # splits = q - 768 (each family chain split adds one word chain)
    JS = 48 + (S - 1) + (q - 768) + sum(w - 4 for w in conn)
    res = dict(word=sys.argv[1], sha256=sha, length=L, runs=len(st), q=q, E=E, tau_minus_1=sum(1 for w in tw if w >= 4),
               lam=sum(w - 4 for w in tw if w >= 4), run_weight_hist=dict(sorted(Counter(tw).items())),
               J_run=JR, J_4chan=JQ, J_chain=JC, J_piece=JP, J_excess=JE, J_visit=JV, J_segment=JS,
               all_equal=len({JR, JQ, JC, JP, JE, JV, JS, L - 46085}) == 1, J_from_length=L - 46085,
               pieces=P, visits=len(visits), segments=S, splits=q - 768, E0=E0, F_cuts=nF, w2_boundaries=n2,
               dE_check=(E == E0 + nF - n2), versions=vsel, cut_hist=dict(Counter(r["cut"] for r in rows)),
               boundary_hist=dict(sorted(Counter(r["w_in"] for r in rows[1:]).items())),
               e_hist=dict(sorted(Counter(r["e"] for r in rows[1:]).items())), sum_e=sum(r["e"] for r in rows[1:]),
               intra_boundaries=sum(1 for r in rows if r["intra"]), c0=c0, table=rows)
    out = sys.argv[3] if len(sys.argv) > 3 else None
    if out: json.dump(res, open(out, "w"), indent=1)
    res.pop("table")
    print(json.dumps(res))

if __name__ == "__main__":
    main()
