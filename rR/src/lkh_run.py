#!/usr/bin/env python3
"""Round R -- adversarial search: LKH-3 (elkai 2.0.1 copy, standalone driver rR/lkh) on the RUN-LEVEL ATSP of a word's
run set (its version vector: every class keeps the entry rotation the word uses).  Node 1 = depot (cost 0 both ways),
nodes 2..5041 = runs; a tour minus the depot is a Hamiltonian path of runs and L = 35288 + path cost (= 8 + 7*5040 +
sum of link weights).  Every returned tour is rebuilt as a word and checked from scratch (all 40320 permutations).
usage: lkh_run.py WORD LKH_BINARY WORKDIR TAG [--time SEC] [--runs R] [--seed S] [--noinit] [--cand K]"""
import sys, os, json, subprocess, argparse, hashlib
import numpy as np
n = 8
def load_word(p):
    t = "".join(ch for ch in open(p).read() if not ch.isspace()); al = sorted(set(t)); return [al.index(c) for c in t]
def starts(w):
    seen = set(); route = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); route.append(p)
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def wmat(st):
    N = len(st); S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    W = np.full((N, N), 8, np.int64)
    from collections import defaultdict
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1).tolist(); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1).tolist()
        d = defaultdict(list)
        for j, key in enumerate(b): d[key].append(j)
        for i, key in enumerate(a):
            for j in d.get(key, ()): W[i, j] = k
    np.fill_diagonal(W, 8); return W
def build(st, W, seq):
    w = list(st[seq[0]])
    for k, r in enumerate(seq):
        if k > 0: kk = int(W[seq[k - 1], r]); w += list(st[r][8 - kk:])
        w += list(st[r][:7])
    return w
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("word"); ap.add_argument("lkh"); ap.add_argument("work"); ap.add_argument("tag")
    ap.add_argument("--time", type=float, default=600); ap.add_argument("--runs", type=int, default=1); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--noinit", action="store_true"); ap.add_argument("--cand", type=int, default=5)
    a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
    st = starts(load_word(a.word)); N = len(st); W = wmat(st)
    base = 8 + 7 * N + int(W[np.arange(N - 1), np.arange(1, N)].sum())
    M = np.zeros((N + 1, N + 1), np.int64); M[1:, 1:] = W
    prob = os.path.join(a.work, a.tag + ".atsp")
    if not os.path.exists(prob):
        with open(prob, "w") as f:
            f.write("NAME : %s\nTYPE : ATSP\nDIMENSION : %d\nEDGE_WEIGHT_TYPE : EXPLICIT\nEDGE_WEIGHT_FORMAT : FULL_MATRIX\nEDGE_WEIGHT_SECTION\n" % (a.tag, N + 1))
            body = (M + 48).astype(np.uint8); sp = np.full((N + 1, 2 * (N + 1)), 32, np.uint8); sp[:, 0::2] = body; sp[:, -1] = 10
            f.write(sp.tobytes().decode()); f.write("EOF\n")
    init = os.path.join(a.work, a.tag + ".init")
    with open(init, "w") as f:
        f.write("TOUR_SECTION\n1\n" + "".join("%d\n" % (i + 2) for i in range(N)) + "-1\nEOF\n")
    par = os.path.join(a.work, a.tag + "_s%d.par" % a.seed); tour = os.path.join(a.work, a.tag + "_s%d.tour" % a.seed)
    lines = ["PROBLEM_FILE = " + prob, "RUNS = %d" % a.runs, "SEED = %d" % a.seed, "TRACE_LEVEL = 1", "MAX_CANDIDATES = %d" % a.cand,
             "MOVE_TYPE = 5", "TIME_LIMIT = %g" % a.time]
    if not a.noinit: lines.append("INITIAL_TOUR_FILE = " + init)
    open(par, "w").write("\n".join(lines) + "\n")
    log = os.path.join(a.work, a.tag + "_s%d.log" % a.seed)
    with open(log, "w") as lf: subprocess.run([a.lkh, par, tour], stdout=lf, stderr=subprocess.STDOUT, check=False)
    t = [int(x) - 1 for x in open(tour).read().split()]
    k = t.index(0); t = t[k + 1:] + t[:k]; seq = [x - 1 for x in t]
    assert sorted(seq) == list(range(N))
    L = 8 + 7 * N + int(W[np.array(seq[:-1]), np.array(seq[1:])].sum())
    w = build(st, W, seq); ok = len({tuple(w[i:i + 8]) for i in range(len(w) - 7) if len(set(w[i:i + 8])) == 8}) == 40320
    res = dict(tag=a.tag, seed=a.seed, base_length=base, lkh_length=L, measured=len(w), all_perms=ok, time=a.time, init=not a.noinit)
    if L < base and ok:
        outw = os.path.join(a.work, a.tag + "_s%d_L%d.txt" % (a.seed, L)); s = "".join(str(c + 1) for c in w) + "\n"; open(outw, "w").write(s)
        res["word"] = outw; res["sha256"] = hashlib.sha256(s.encode()).hexdigest()
    print(json.dumps(res))
main()
