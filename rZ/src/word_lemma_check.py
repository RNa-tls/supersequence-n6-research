#!/usr/bin/env python3
"""Round Z -- check the new global lemmas on a real word (exact, deterministic).
For the rows/seams/chains of rZ/src/word_anatomy.py it checks:
  Z1 (6-row lemma):  every 6-row is (i) entered and left by d with the rows before and after in one 2-cycle, or
       (ii) next to a non-d seam (b, c, e, f) or a chain end;  and  P6 <= M + E + 2L + 2n  (E = e-seams).
  Z2 (runs):  maximal runs of full rows inside chains have <= 6 rows; a 6-run has a b/f seam or the chain start before
       it and a c/f seam or the chain end after it;  F7 <= 5 (P + n) + #6-runs.
  Z6 (b-seam entry):  the entry class of every b-seam is the class that follows the exit class in the previous row's
       2-cycle (so the previous row is not full, and that class is foreign to the previous 2-cycle).
  priced lines:  every chain has 4r - 9d + 4L <= 56 and 4r - 9d + 5L <= C5, 17r - 38d + LAM L <= C (given).
usage: word_lemma_check.py WORD.txt [C5 LAM2 C2]"""
import sys, collections, json
w = open(sys.argv[1]).read().strip()
C5 = int(sys.argv[2]) if len(sys.argv) > 2 else None
LAM2 = int(sys.argv[3]) if len(sys.argv) > 3 else None
C2 = int(sys.argv[4]) if len(sys.argv) > 4 else None
n = 8; syms = sorted(set(w))
first = {}
for i in range(len(w) - n + 1):
    s = w[i:i + n]
    if len(set(s)) == n and s not in first: first[s] = i
seq = sorted(first.items(), key=lambda t: t[1]); perm = [p for p, _ in seq]; pos = [q for _, q in seq]
def cls(p): k = p.index(syms[0]); return p[k:] + p[:k]
def cyc(s): k = s.index(min(s)); return s[k:] + s[:k]
steps = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
blocks = []; cur = [0]
for i, st in enumerate(steps):
    if st == 1 and cls(perm[i]) == cls(perm[i + 1]): cur.append(i + 1)
    else: blocks.append(cur); cur = [i + 1]
blocks.append(cur)
after = [steps[b[-1]] if b[-1] < len(steps) else None for b in blocks]
rows = []; cur = [0]
for bi in range(len(blocks) - 1):
    if after[bi] == 2: cur.append(bi + 1)
    else: rows.append(cur); cur = [bi + 1]
rows.append(cur)
R = len(rows)
full_ok = all(len(blocks[b]) == 8 for r in rows for b in r)
rz, rG, rs = [], [], []
for r in rows:
    fb = [b for b in r if len(blocks[b]) == 8] or r
    e = perm[blocks[fb[0]][0]]; rz.append(e[-1]); rG.append((e[-1], cyc(e[:-1]))); rs.append(len(r))
def stype(y, e):
    if e[:5] != y[3:]: return None
    a, b, c = y[0], y[1], y[2]
    return {a + c + b: 'c', b + a + c: 'b', b + c + a: 'e', c + a + b: 'f', c + b + a: 'd'}.get(e[5:])
seam = []
for i in range(R - 1):
    y = perm[blocks[rows[i][-1]][-1]]; e = perm[blocks[rows[i + 1][0]][0]]
    wt = pos[blocks[rows[i + 1][0]][0]] - pos[blocks[rows[i][-1]][-1]]
    seam.append(stype(y, e) if wt == 3 else 'X')
chains = []; cur = [0]
for i in range(R - 1):
    if seam[i] != 'X': cur.append(i + 1)
    else: chains.append(cur); cur = [i + 1]
chains.append(cur)
usedG = collections.Counter(rG); M = sum(t - 1 for t in usedG.values())
E = seam.count('e'); L = sum(1 for s in seam if s in ('b', 'c', 'f')); nch = len(chains)
# Z1
P6 = 0; typ = collections.Counter(); viol = 0
for ch in chains:
    for k, ri in enumerate(ch):
        if rs[ri] != 6: continue
        P6 += 1
        bef = seam[ri - 1] if k > 0 else None; aft = seam[ri] if k < len(ch) - 1 else None
        if bef == 'd' and aft == 'd':
            if rG[ch[k - 1]] == rG[ch[k + 1]]: typ['(i) d/d, sandwich in one 2-cycle'] += 1
            else: viol += 1
        else: typ['(ii) next to %s/%s' % (bef or 'end', aft or 'end')] += 1
z1 = dict(P6=P6, M=M, E=E, L=L, chains=nch, bound=M + E + 2 * L + 2 * nch, holds=P6 <= M + E + 2 * L + 2 * nch and viol == 0, types=dict(typ), violations=viol)
# Z2
runs = collections.Counter(); bad = 0; six = 0; F7 = sum(1 for x in rs if x == 7); P = R - F7
for ch in chains:
    i = 0
    while i < len(ch):
        if rs[ch[i]] == 7:
            j = i
            while j + 1 < len(ch) and rs[ch[j + 1]] == 7: j += 1
            Lr = j - i + 1; runs[Lr] += 1
            if Lr > 6: bad += 1
            if Lr == 6:
                six += 1
                bef = 'start' if i == 0 else seam[ch[i] - 1]; aft = 'end' if j == len(ch) - 1 else seam[ch[j]]
                if bef not in ('start', 'b', 'f') or aft not in ('end', 'c', 'f'): bad += 1
            i = j + 1
        else: i += 1
z2 = dict(F7=F7, P=P, chains=nch, six_runs=six, runs=dict(sorted(runs.items())), bound=5 * (P + nch) + six, holds=bad == 0 and F7 <= 5 * (P + nch) + six)
# Z6
def g_next(G, X):          # the class after X in 2-cycle G: z moves past its right neighbour
    z = G[0]; k = X.index(z); t = X[k + 1:] + X[:k]            # the other 7 after z
    return cls(t[0] + z + t[1:])
b_ok = 0; b_bad = 0
for i in range(R - 1):
    if seam[i] == 'b':
        y = perm[blocks[rows[i][-1]][-1]]; X = cls(y); e = perm[blocks[rows[i + 1][0]][0]]
        if cls(e) == g_next(rG[i], X) and rs[i] < 7: b_ok += 1
        else: b_bad += 1
z6 = dict(b_seams=b_ok + b_bad, ok=b_ok, bad=b_bad)
# priced lines per chain
pl = []
for ch in chains:
    r = len(ch); d = sum(7 - rs[i] for i in ch); lc = sum(1 for a in ch[:-1] if seam[a] in ('b', 'c', 'f'))
    pl.append((4 * r - 9 * d + 4 * lc, 4 * r - 9 * d + 5 * lc, (17 * r - 38 * d + LAM2 * lc) if LAM2 is not None else None))
pr = dict(max_line1_price4=max(x[0] for x in pl), holds4=max(x[0] for x in pl) <= 56)
if C5 is not None: pr.update(max_line1_price5=max(x[1] for x in pl), holds5=max(x[1] for x in pl) <= C5)
if LAM2 is not None: pr.update(max_line2_price=max(x[2] for x in pl), holds2=max(x[2] for x in pl) <= C2)
print(json.dumps(dict(word=sys.argv[1], full_blocks_only=full_ok, Z1=z1, Z2=z2, Z6=z6, priced_lines=pr)))
