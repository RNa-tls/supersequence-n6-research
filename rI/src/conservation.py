#!/usr/bin/env python3
"""Conservation law for two-special r = 0 routes ({a,b} = {0,n-1}): every chain lies in one
P({a,b},C); e_C = #chains in P(C) - (n-2) = (sum of deficiencies n-1-l in C)/(n-1).
Checks  L = CONST + sum_C e_C + (tau - 1) + sum_{c>=4}(c - 4)  and reports the e_C histogram."""
import sys, os, json, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r0verifyA import load, analyse
w, n = load(sys.argv[1]); out, info = analyse(w, n)
S, chains, J, trails = info["S"], info["chains"], info["J"], info["trails"]
A, B = 0, n - 1
def cyc_canon(seq):
    k = seq.index(min(seq)); return tuple(seq[k:] + seq[:k])
def Cof(p):
    k = p.index(A); w_ = list(p[k:] + p[:k]); return cyc_canon([x for x in w_ if x not in (A, B)])
assert all(S[ch[0]][n - 1] in (A, B) for ch in chains), "not a two-special route"
cnt = defaultdict(int); defi = defaultdict(int)
for ch in chains:
    C = Cof(S[ch[0]]); cnt[C] += 1; defi[C] += (n - 1) - len(ch)
e = {C: cnt[C] - (n - 2) for C in cnt}
assert all(defi[C] == (n - 1) * e[C] for C in cnt)
HEX = math.factorial(n - 1); ORB = math.factorial(n - 2); CONST = math.factorial(n) + HEX + ORB + n - 3
tau = len(trails); ex4 = sum(c - 4 for c in J if c >= 4)
L = CONST + sum(e.values()) + (tau - 1) + ex4
specials = sum(1 for i in range(len(S) - 1) if S[i][n - 1] != S[i + 1][n - 1])
print(json.dumps(dict(file=os.path.basename(sys.argv[1]), length=len(w), arrangements=len(cnt), sum_e=sum(e.values()),
                      e_hist=dict(Counter(e.values())), tau=tau, sum_c_minus_4=ex4, L_identity=L, ok=(L == len(w)),
                      special_switches=specials)))
