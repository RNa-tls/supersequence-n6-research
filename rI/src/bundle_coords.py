#!/usr/bin/env python3
"""Coordinates of the {a,b}-system (here a=0, b=7 for 46188): a class (cyclic word) <-> (C, i, j):
C = cyclic arrangement of the other n-2 symbols (delete a and b), i = slot of b in C, j = slot of a
in C+b.  Every chain of special a (resp. b) has constant C.  For each long trail: the sequence of C's
visited, whether each trail is a union of whole P(C), the 16 C's of a bundle, and the C -> C' moves."""
import sys, os, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, trails = info["S"], info["trails"]
A, B = 0, n - 1
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
F = tuple(list(range(1, n - 1)) + [0, n - 1])
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):                       # cyclic arrangement after deleting A and B
    k = p.index(A); w_ = list(p[k:] + p[:k])
    return cyc_canon([x for x in w_ if x not in (A, B)])
def classes_of_chain(s, l):
    out = []; x = s
    for _ in range(l): out.append(x); x = comp(x, F)
    return out
res = {}
longs = [t for t in trails if len(t) == 104]
allC = {}
for li, t in enumerate(longs):
    seq = []
    Cs = Counter()
    for ch in t:
        s = S[ch[0]]; l = len(ch)
        cs = {Cof(p) for p in classes_of_chain(s, l)}
        assert len(cs) == 1, "chain spans several C"
        C = cs.pop(); Cs[C] += l
        seq.append((s[n - 1], l, C))
    allC[li] = Cs
    Cid = {}
    for _, _, C in seq: Cid.setdefault(C, len(Cid))
    print(f"long trail {li}: distinct C = {len(Cs)}, classes per C = {sorted(set(Cs.values()))}")
    if li == 0:
        for k in range(4):
            part = seq[26 * k: 26 * k + 26]
            print("  period", k, " ".join(f"{'a' if sp == A else 'b'}{l}:C{Cid[C]}" for sp, l, C in part))
        moves = Counter()
        for (sp1, l1, C1), (sp2, l2, C2) in zip(seq, seq[1:] + seq[:1]):
            if C1 != C2:
                # describe C2 relative to C1: which adjacent transposition?
                c1 = list(C1); c2 = list(C2); m_ = len(c1)
                desc = None
                for r in range(m_):
                    rot = c1[r:] + c1[:r]
                    for i in range(m_):
                        t2 = rot[:]; t2[i], t2[(i + 1) % m_] = t2[(i + 1) % m_], t2[i]
                        if cyc_canon(t2) == C2: desc = "adjacent transposition"; break
                    if desc: break
                moves[(f"{'a' if sp1 == A else 'b'}{l1}->{'a' if sp2 == A else 'b'}{l2}", desc)] += 1
        print("  C-changing moves:", dict((str(k), v) for k, v in moves.items()))
# do the 6 bundles + free phi-cycles partition the 120 arrangements?
free = []
for t in trails:
    if len(t) == 6:
        free.append(Cof(S[t[0][0]]))
resid = [t for t in trails if len(t) not in (6, 104)]
rc = {Cof(S[ch[0]]) for t in resid for ch in t}
allbundle = Counter(C for li in allC for C in allC[li])
print("bundle C count", len(allbundle), "free C", len(free), "residual C", rc and len(rc),
      "union size", len(set(allbundle) | set(free) | rc), "disjoint", not (set(allbundle) & (set(free) | rc)))
json.dump(dict((str(li), [list(C) for C in allC[li]]) for li in allC), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", "bundle_C46188.json"), "w"))
