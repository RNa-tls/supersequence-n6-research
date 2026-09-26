#!/usr/bin/env python3
"""Round 175 -- falsification tests for the symbolic lemmas of
r175/ROW_RUN_LEMMA_REPORT.md (they are proved there for all n; this only re-checks).

Part 1 (frame rules, Lemma 4).  Frame: (n-2)-cycle E = (e_0 .. e_{m-1}), m = n-2,
pair {P, Q}.  A frame row (g, s) has start e_g e_{g+1} .. e_{g-1} a s, where
{a, s} = {P, Q}; it is long (length n-1, omitted set Om, |Om| <= 1, Om in 1..n-3) or
a loop (length n-2).  Predicted:
  long/long, g1 != g2 : conflict  <=>  s1 != s2 and (g2-g1)%m not in Om1 and (g1-g2)%m not in Om2
  loop(h)/long(g), h != g : conflict <=> s != sigma and (h-g)%m not in Om
  loop/loop, h1 != h2 : conflict <=> s1 != s2
  same gap: same special => same block;  different special => conflict, except
            loop/loop of the same phase (disjoint).
  Loops are checked in both phases: forward (start e_h..e_{h-1} a s, omits "s a") and
  backward (start F(forward) = e_{h+1}..e_{h-1} a e_h s, omits "a s").
Part 2 (structure, Lemmas 5-6).  Every all-charge<=1 ModelTrail from the identity
start (exhaustive, marked model) has type pattern  L^{c0} Long^k L^{c1},
c0, c1 <= 2, all long rows in ONE frame (same E, same pair) on consecutive gaps.
usage: framecheck175.py n [rulesonly]"""
import sys
from itertools import permutations
sys.setrecursionlimit(100000)
n = int(sys.argv[1]); m = n - 2
def F(s): return s[1:n - 1] + (s[0], s[n - 1])
def Rinv(s): return (s[n - 1],) + s[:n - 1]
def hexrep(s): return min(s[i:] + s[:i] for i in range(n))
def states(p):
    st = [p]
    for _ in range(n - 2): st.append(F(st[-1]))
    return st
def row(p, l, om):
    st = states(p)
    return dict(block=min(st), beta=Rinv(st[l - 1])[3:],
                vis=frozenset(hexrep(st[i]) for i in range(l) if i != om))
E = tuple(range(m)); P, Q = m, m + 1
def start(g, s):
    a = P if s == Q else Q
    return tuple(E[(g + i) % m] for i in range(m)) + (a, s)
longs = [(g, s, om) for g in range(m) for s in (P, Q) for om in [None] + list(range(1, n - 2))]
loops = [(h, s) for h in range(m) for s in (P, Q)]
R = {("L",) + x: row(start(x[0], x[1]), n - 1, x[2]) for x in longs}
R.update({("O",) + x + ("fwd",): row(start(x[0], x[1]), n - 2, None) for x in loops})
R.update({("O",) + x + ("bwd",): row(F(start(x[0], x[1])), n - 2, None) for x in loops})   # backward phase
bad = 0; checked = 0
def status(x, y):
    if R[x]["block"] == R[y]["block"]: return "block"
    return "conflict" if R[x]["vis"] & R[y]["vis"] else "ok"
keys = list(R)
for i, x in enumerate(keys):
    for y in keys[i + 1:]:
        st = status(x, y); checked += 1
        kx, ky = x[0], y[0]
        gx, sx = x[1], x[2]; gy, sy = y[1], y[2]
        if gx == gy:
            if sx == sy:
                pred = "block"   # same gap & special: same W and special, hence same block
            else:
                pred = ("ok" if x[3] == y[3] else "conflict") if (kx == "O" and ky == "O") else "conflict"
        else:
            if kx == "L" and ky == "L":
                ox = set() if x[3] is None else {x[3]}; oy = set() if y[3] is None else {y[3]}
                c = sx != sy and (gy - gx) % m not in ox and (gx - gy) % m not in oy
            elif kx == "O" and ky == "O":
                c = sx != sy
            else:
                (h, sig), (g, s, om) = ((gx, sx), y[1:]) if kx == "O" else ((gy, sy), x[1:])
                c = s != sig and (h - g) % m not in ({om} if om is not None else set())
            pred = "conflict" if c else "ok"
        if (pred == "block") != (st == "block") or (pred != "block" and pred != st):
            bad += 1
            if bad < 5: print("MISMATCH", x, y, "pred", pred, "actual", st)
print(f"n={n} part1 frame rules: {checked} pairs, mismatches {bad}")
if "rulesonly" in sys.argv:
    sys.exit(0)

# Part 2: structure of all runs (marked model), exhaustive from the identity start
kinds = [("F", n - 1, None), ("O", n - 2, None)] + [("M", n - 1, j) for j in range(1, n - 2)]
info = {}
for p in permutations(range(n)):
    st = states(p)
    info[p] = (min(st), [(k, l, om, Rinv(st[l - 1])[3:],
                          frozenset(hexrep(st[i]) for i in range(l) if i != om)) for k, l, om in kinds])
def frame(p):   # (E as cycle rep, pair) of a length-(n-1) row start
    Ec = p[:n - 2]; r = min(Ec[i:] + Ec[:i] for i in range(n - 2))
    return (r, frozenset(p[n - 2:]))
viol = 0; runs = 0; path = []; path_om = []
def check():
    global viol, runs
    runs += 1
    t = "".join("O" if k == "O" else "L" for k, p in path)
    import re
    mm = re.fullmatch(r"(O{0,2})(L*)(O{0,2})", t)
    ok = mm is not None
    if ok and mm.group(2):
        fr = {frame(p) for k, p in path if k != "O"}
        ok = len(fr) == 1
    if ok and mm.group(2):
        ok = lemmas(mm, t)
    if not ok:
        viol += 1
        if viol < 5: print("STRUCTURE VIOLATION", [(k, "".join(map(str, p))) for k, p in path])
LEMMA_STATS = {}
def lemmas(mm, t):
    """Lemmas 5-7 for a run with k >= 1 long rows (gap id = E-element following a)."""
    c0, k, c1 = len(mm.group(1)), len(mm.group(2)), len(mm.group(3))
    longs = [(kk, p) for kk, p in path[c0:c0 + k]]
    p0 = longs[0][1]; Ec = p0[:n - 2]; pair = set(p0[n - 2:])
    succ = {Ec[i]: Ec[(i + 1) % (n - 2)] for i in range(n - 2)}
    pred = {v: u for u, v in succ.items()}
    gaps = [p[0] for _, p in longs]
    if any(gaps[i + 1] != succ[gaps[i]] for i in range(k - 1)): return False
    def floop(q):   # frame-loop coordinates (gap, special, dir) or None if off-frame
        W = q[:n - 1]; sp = q[n - 1]
        if sp not in pair: return None
        a = (pair - {sp}).pop(); i = W.index(a)
        rest = W[i + 1:] + W[:i]                  # E read after a
        if frame(rest + (a, sp)) != frame(p0): return None
        d = "fwd" if i == n - 2 else "bwd" if i == n - 3 else "other"
        return (rest[0], sp, d)
    st = LEMMA_STATS
    if c1 >= 1:
        mu1 = floop(path[c0 + k][1])
        if mu1 is None or mu1[0] != succ[gaps[-1]] or mu1[2] != "fwd": return False
        if c1 == 2:
            mu2 = floop(path[c0 + k + 1][1])
            if mu2 is not None:
                if not (mu2[0] == mu1[0] and mu2[1] != mu1[1] and mu2[2] == "fwd"): return False
                st["mu2_S"] = st.get("mu2_S", 0) + 1
            else:
                return False            # Lemma 7: no off-frame second loop when k >= 1
    if c0 >= 1:
        lam = floop(path[c0 - 1][1])
        if lam is None or lam[0] != pred[gaps[0]] or lam[2] != "bwd": return False
        if c0 == 2:
            lam2 = floop(path[0][1])
            if lam2 is None or not (lam2[0] == lam[0] and lam2[1] != lam[1] and lam2[2] == "bwd"):
                return False
            st["lam2_S"] = st.get("lam2_S", 0) + 1
    if c0 == 2 and c1 == 2: return False
    return True
def rec(beta, blocks, hexes):
    rest = [c for c in range(n) if c not in beta]
    for q in permutations(rest):
        p = beta + q; b, rows = info[p]
        if b in blocks: continue
        for k, l, om, nb, vis in rows:
            if vis & hexes: continue
            path.append((k, p)); path_om.append(om); check()
            blocks.add(b); rec(nb, blocks, hexes | vis); blocks.discard(b); path.pop(); path_om.pop()
p0 = tuple(range(n)); b0, rows0 = info[p0]
for k, l, om, nb, vis in rows0:
    path.append((k, p0)); path_om.append(om); check(); rec(nb, {b0}, set(vis)); path.pop(); path_om.pop()
print(f"n={n} part2 structure + Lemmas 5-7: {runs} runs checked, violations {viol}; second-loop types seen {LEMMA_STATS}")
