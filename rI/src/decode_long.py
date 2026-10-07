#!/usr/bin/env python3
"""Decode trails of an r=0 word as words in position permutations.
State = chain start s (tuple of symbols by position).  Chain of length l occupies the classes of
s, sF, ..., sF^(l-1) (F = position cycle on 0..n-2, fixing n-1).  The cost-3 successor of a chain
with last start x is t = (x[2..n-2], then a permutation of (x[0], x[1], x[n-1])); we record which
one as a triple over {0,1,n-1}.  Every step is s_{j+1} = s_j o pi_j with pi_j a POSITION permutation
(right action), so after a word w the start is s_0 o Pi(w): the trail is determined by s_0 and the
symbol-free word ((l_j, sigma_j))_j."""
import sys, os, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse

def compose(p, q):            # (p o q)[i] = p[q[i]]  : first apply q's position selection
    return tuple(p[q[i]] for i in range(len(p)))
def ident(n): return tuple(range(n))
def Fpos(n): return tuple(list(range(1, n - 1)) + [0, n - 1])
def powp(p, k):
    r = ident(len(p))
    for _ in range(k): r = compose(r, p)
    return r
def step_perm(n, l, sig):
    """position perm pi with s_next = s o pi for a chain of length l followed by cost-3 choice sig."""
    f = powp(Fpos(n), l - 1)          # x = s o f
    tail = tuple(list(range(2, n - 1)) + list(sig))   # t = x o tail
    return compose(f, tail)
def cycle_type(p):
    seen = set(); ct = []
    for i in range(len(p)):
        if i in seen: continue
        j = i; L = 0
        while j not in seen: seen.add(j); j = p[j]; L += 1
        ct.append(L)
    return sorted(ct, reverse=True)
def order(p):
    from math import lcm
    o = 1
    for c in cycle_type(p): o = lcm(o, c)
    return o

def decode_trail(route_info, trail, n):
    S = route_info["S"]
    rows = []
    for ci, ch in enumerate(trail):
        s = S[ch[0]]; l = len(ch); x = S[ch[-1]]
        sig = None; pi = None
        if ci + 1 < len(trail):
            t = S[trail[ci + 1][0]]
            assert t[:n - 3] == x[2:n - 1]
            idx = {x[0]: 0, x[1]: 1, x[n - 1]: n - 1}
            sig = tuple(idx[c] for c in t[n - 3:])
            pi = step_perm(n, l, sig)
            assert compose(s, pi) == t
        rows.append(dict(start=s, special=s[n - 1], l=l, sigma=sig, pi=pi))
    return rows

if __name__ == "__main__":
    w, n = load(sys.argv[1]); out, info = analyse(w, n)
    trails = info["trails"]
    longs = [t for t in trails if len(t) > 20]
    res = []
    for k, t in enumerate(longs):
        rows = decode_trail(info, t, n)
        word = [(r["l"], r["sigma"]) for r in rows]
        sig_hist = Counter(r["sigma"] for r in rows if r["sigma"])
        # period of the symbol-free word (last row has no successor)
        body = word[:-1]
        per = next(p for p in range(1, len(body) + 1) if all(body[i] == body[i % p] for i in range(len(body))))
        Pi = ident(n)
        for r in rows[:per]: Pi = compose(Pi, r["pi"])
        s0 = rows[0]["start"]; s26 = rows[per]["start"]
        tau = {s0[i]: s26[i] for i in range(n)}      # value relabelling: s26 = tau o s0
        res.append(dict(trail=k, rows=len(rows), word_period=per, Pi=Pi, Pi_cycle_type=cycle_type(Pi), Pi_order=order(Pi),
                        tau=[tau[i] for i in range(n)], tau_cycle_type=cycle_type(tuple(tau[i] for i in range(n))),
                        start=s0, specials="".join(str(r["special"]) for r in rows),
                        word="".join(f"{r['l']}" + ("" if r["sigma"] is None else "".join("abc"[[0, 1, n - 1].index(z)] for z in r["sigma"])) + " " for r in rows[:per]),
                        sigma_hist={"".join(map(str, k)): v for k, v in sig_hist.items()}))
    for r in res: print(json.dumps(r))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "decode_long46188.json"), "w"), indent=1)
