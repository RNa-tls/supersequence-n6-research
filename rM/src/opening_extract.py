#!/usr/bin/env python3
"""Round M -- describe an r = 0 word as an OPENING DESCRIPTION over an exported closed-trail family.

Input: family JSON (family_export.py: per trail, per version, the cyclic list of run starts) and an
r = 0 word over the same class set.  Every run start of the word is located in the family
(trail, version, cyclic index); the route is cut into maximal PIECES, each a cyclic interval of one
trail version.  For every piece the CUT edge (the cyclic edge entering the piece start) is reported
with its weight (3 = cost-3 join, 2 = F-step inside a chain, 1 = inside a run); for every pair of
consecutive pieces the BOUNDARY weight.  Exact identities (checked):
    L = 8 + sum_T (9|T| + k_T) + sum_boundaries w_b - sum_cuts w_c
    J = L - 46085 = E_0 + #(w2 cuts) + sum_boundaries (w_b - 3)       (r = 0, E_0 = sum k_T - 720)
usage: opening_extract.py FAMILY.json WORD OUT.json"""
import sys, json, math, hashlib

n = 8

def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def runs(word):
    seen = set(); route = []
    for i in range(len(word) - n + 1):
        p = tuple(word[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    assert len(route) == math.factorial(n)
    st = route[0::n]
    for b in range(len(st)):
        for j in range(n): assert route[n * b + j] == st[b][j:] + st[b][:j], "not r = 0"
    return st

def main():
    fam = json.load(open(sys.argv[1])); raw = open(sys.argv[2], "rb").read()
    text = "".join(ch for ch in raw.decode() if not ch.isspace())
    al = sorted(set(text)); word = [al.index(c) for c in text]
    F = {}                                 # (t, v) -> list of starts
    loc = {}                               # start -> list of (t, v, i)
    for tr in fam["trails"]:
        for v, s in enumerate(tr["versions"]):
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            F[tr["trail"], v] = st
            for i, p in enumerate(st): loc.setdefault(p, []).append((tr["trail"], v, i))
    S = runs(word)
    assert all(p in loc for p in S), "word not over this family (some run start not in any version)"
    # maximal pieces: greedy extension keeping the set of consistent (t, v, i) alignments
    pieces = []; k = 0
    while k < len(S):
        cand = list(loc[S[k]]); ln = 1
        while k + ln < len(S):
            nxt = [(t, v, i) for (t, v, i) in cand if F[t, v][(i + ln) % len(F[t, v])] == S[k + ln]]
            if not nxt: break
            cand = nxt; ln += 1
        t, v, i = cand[0]
        pieces.append(dict(trail=t, version=v, start=i, runs=ln, alternatives=len(cand)))
        k += ln
    # cut and boundary weights
    def last(p): return p[-1:] + p[:-1]
    K = sum(len(tr["versions"][0]) // 8 for tr in fam["trails"])          # classes
    kT = 0
    for tr in fam["trails"]:
        st = F[tr["trail"], 0]
        kT += sum(1 for i in range(len(st)) if wt(last(st[i - 1]), st[i]) == 3)
    for pc in pieces:
        st = F[pc["trail"], pc["version"]]; i = pc["start"]
        pc["cut_w"] = wt(last(st[i - 1]), st[i])
        e = st[(i + pc["runs"] - 1) % len(st)]
        pc["exit"] = "".join(map(str, last(e))); pc["entry"] = "".join(map(str, st[i]))
    bnd = [wt(last(F[a["trail"], a["version"]][(a["start"] + a["runs"] - 1) % len(F[a["trail"], a["version"]])]),
              F[b["trail"], b["version"]][b["start"]]) for a, b in zip(pieces, pieces[1:])]
    L = len(word); const = 8 + 9 * K + kT
    Lpred = const + sum(bnd) - sum(pc["cut_w"] for pc in pieces)
    E0 = kT - 720
    Jpred = E0 + sum(1 for pc in pieces if pc["cut_w"] == 2) + sum(w - 3 for w in bnd)
    per_trail = {}
    for pc in pieces: per_trail.setdefault(pc["trail"], []).append(pc)
    out = dict(word=sys.argv[2], sha256=hashlib.sha256(raw).hexdigest(), length=L, family=sys.argv[1],
               const=const, E0=E0, pieces=len(pieces), cut_hist={w: sum(1 for pc in pieces if pc["cut_w"] == w) for w in (1, 2, 3)},
               boundary_hist={w: bnd.count(w) for w in sorted(set(bnd))},
               pieces_per_trail={t: len(v) for t, v in sorted(per_trail.items())},
               versions_used={t: sorted({pc["version"] for pc in v}) for t, v in sorted(per_trail.items())},
               L_identity=Lpred, L_ok=(Lpred == L), J=L - 46085, J_identity=Jpred, J_ok=(Jpred == L - 46085),
               description=[[pc["trail"], pc["version"], pc["start"], pc["runs"]] for pc in pieces],
               detail=pieces, boundaries=bnd)
    json.dump(out, open(sys.argv[3], "w"), indent=0)
    print(json.dumps({k: out[k] for k in ("word", "length", "pieces", "cut_hist", "boundary_hist", "L_ok", "J", "J_identity", "J_ok", "E0")}))

if __name__ == "__main__":
    main()
