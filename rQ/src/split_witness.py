#!/usr/bin/env python3
"""Round Q, section 3 -- independent reconstruction of a single-split witness (no code shared with ckT*/split_eval).
Input: trail sequence SIGMA (30 trail ids), junction j (P = SIGMA[:j], Z' = SIGMA[j:]), anchor position s < j and the
anchor's cycle option b (local index).  Minimises over all other options (exact DP, numpy), rebuilds the route
    A, f1 = [a, b), B = Z', f2 = [b, a), C    (P = A + S + C),
writes the word, and checks it: every permutation of 8 symbols appears, length = 46085 + 77 + G.
usage: split_witness.py FAMILY.json SIGMA(comma) j s b OUT.txt"""
import sys, json, math, itertools
import numpy as np
n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
def main():
    fam = json.load(open(sys.argv[1])); sig = [int(x) for x in sys.argv[2].split(",")]; j = int(sys.argv[3]); s = int(sys.argv[4]); bq = int(sys.argv[5])
    V = []   # V[t][v] = list of run starts
    for tr in fam["trails"]: V.append([[tuple(int(c) for c in st[8 * k:8 * k + 8]) for k in range(len(st) // 8)] for st in tr["versions"]])
    def opts(t): return [(v, k) for v in range(2) for k in range(len(V[t][v]))]
    def entry(t, o): v, k = o; return V[t][v][k]
    def exitp(t, o): v, k = o; R = V[t][v]; return last(R[(k - 1) % len(R)])
    def cut(t, o): return wt(exitp(t, o), entry(t, o))
    def e(t1, o1, t2, o2): return wt(exitp(t1, o1), entry(t2, o2)) - cut(t2, o2) - 1
    O = {t: opts(t) for t in set(sig)}
    def emat(t1, t2): return np.array([[e(t1, a, t2, b) for b in O[t2]] for a in O[t1]], np.int64)
    S = sig[s]; ob = O[S][bq]
    # P part: positions 0..j-1, anchor at s with option a != b, same version
    P = sig[:j]; Z = sig[j:]
    f = np.array([cut(P[0], o) == 2 for o in O[P[0]]], np.int64); fw = [f]; arg = []
    for i in range(1, j):
        M = emat(P[i - 1], P[i]); tot = fw[-1][:, None] + M; arg.append(tot.argmin(0)); fw.append(tot.min(0))
    bw = [None] * j; bw[j - 1] = np.zeros(len(O[P[j - 1]]), np.int64); barg = [None] * j
    for i in range(j - 2, -1, -1):
        M = emat(P[i], P[i + 1]); tot = M + bw[i + 1][None, :]; barg[i] = tot.argmin(1); bw[i] = tot.min(1)
    pc = fw[s] + bw[s]
    for qa, o in enumerate(O[S]):
        if o == ob or o[0] != ob[0]: pc[qa] = 10 ** 6
    qa = int(pc.argmin()); Pbest = int(pc[qa])
    # Z cycle: S(b) -> Z[0] -> ... -> Z[-1] -> S(b)
    d = np.array([e(S, ob, Z[0], o) for o in O[Z[0]]], np.int64); zarg = []
    for i in range(1, len(Z)):
        M = emat(Z[i - 1], Z[i]); tot = d[:, None] + M; zarg.append(tot.argmin(0)); d = tot.min(0)
    close = np.array([e(Z[-1], o, S, ob) for o in O[Z[-1]]], np.int64); tot = d + close; ql = int(tot.argmin()); Zbest = int(tot[ql])
    G = 1 + Pbest + Zbest
    # reconstruct options: P (anchor fixed at qa)
    popt = [None] * j; popt[s] = qa
    for i in range(s, 0, -1):    # backwards from s through fw argmins
        popt[i - 1] = int(arg[i - 1][popt[i]])
    for i in range(s, j - 1): popt[i + 1] = int(barg[i][popt[i]])
    zopt = [None] * len(Z); zopt[-1] = ql
    for i in range(len(Z) - 1, 0, -1): zopt[i - 1] = int(zarg[i - 1][zopt[i]])
    # route pieces: (trail, version, start index, length in runs)
    def piece(t, o_in, o_out):   # runs from entry of o_in up to the exit of o_out (same version)
        v, k1 = o_in; v2, k2 = o_out; assert v == v2; m = len(V[t][v]); L = (k2 - k1) % m or m; return [V[t][v][(k1 + u) % m] for u in range(L)]
    oa = O[S][qa]
    route = []
    for i in range(s): t = P[i]; o = O[t][popt[i]]; route += piece(t, o, o)
    route += piece(S, oa, ob)
    for i in range(len(Z)): t = Z[i]; o = O[t][zopt[i]]; route += piece(t, o, o)
    route += piece(S, ob, oa)
    for i in range(s + 1, j): t = P[i]; o = O[t][popt[i]]; route += piece(t, o, o)
    assert len(route) == 5040 and len(set(route)) == 5040
    # word
    # each run: its start s, then s[0..6] appended (the 7 further left rotations); the last window is last(s)
    w = list(route[0])
    for r_i, r in enumerate(route):
        if r_i > 0:
            k = wt(last(route[r_i - 1]), r); w += list(r[8 - k:])
        w += list(r[:7])
    seen = set(tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8)
    ok = len(seen) == math.factorial(8)
    open(sys.argv[6], "w").write("".join(str(c + 1) for c in w) + "\n")
    res = dict(G=G, J=77 + G, L_formula=46085 + 77 + G, L_word=len(w), all_perms=ok, P=Pbest, Z=Zbest, anchor_trail=S, a=list(oa), b=list(ob))
    print(json.dumps(res))
main()
