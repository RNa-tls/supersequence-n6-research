#!/usr/bin/env python3
"""Round Q, section 22 (corrected) -- rotated-chain excision moves on a single-opening word, with DEGENERATE moves
removed and every move classified by where the moved block lands.

A move (as in excision_probe.py): trail T (one block of the word), a full chain C of T (7 runs, w2 wrap), a rotation
a of C, X = C rotated at a (C_a .. C_6, C_0 .. C_{a-1}), R = T minus C in version order (N_start .. C_prev_end).
  kind A: X at T's place, R inserted at a gap of the route;   kind B: R at T's place, X inserted at a gap.
A gap is DEGENERATE when one of the two new links is a natural version link of T (then pieces merge and the move is
a different opening of fewer pieces): in kind A the wrap gap C_6 | C_0 inside X (a != 0), and for a = 0 the two gaps
next to X; in kind B for a = 0 the two gaps next to R.  Classes of the non-degenerate gaps:
  boundary  -- between two blocks of other trails or at a word end (the single excision of section 6.4, case E1-E3)
  adjacent  -- next to T's own block (a single 3- or 4-piece visit of T: a re-routing, case E4)
  inside_T  -- inside T's own block (a re-routing of T as one visit)
  inside_other -- inside another trail's block (that trail is split as well: two trails multi-opened)
The change Delta of the word length is exact (run weights).  Prints the best Delta per class.
usage: excision_classes.py WORD FAMILY.json OUT.json [CLASS WITNESS.txt]   (optionally writes the word of the best move of
CLASS, a class name or class_A / class_phi; check the written word's pieces independently, e.g. with pieces.py)"""
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
    st = route[0::n]
    for b, s in enumerate(st):
        for j in range(n): assert route[n * b + j] == s[j:] + s[:j]
    return st
def canon(p): return min(p[i:] + p[:i] for i in range(n))

def main():
    st = starts(load_word(sys.argv[1])); N = len(st)
    fam = json.load(open(sys.argv[2]))
    cls_trail = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            for k in range(len(s) // 8): cls_trail[canon(tuple(int(c) for c in s[8 * k:8 * k + 8]))] = t
    trail = np.array([cls_trail[canon(s)] for s in st])
    S = np.array(st, np.int64); X = np.concatenate([S[:, 7:], S[:, :7]], 1)
    W = np.full((N, N), 8, np.int64)
    for k in range(7, 0, -1):
        a = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); b = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
        W[a[:, None] == b[None, :]] = k
    np.fill_diagonal(W, 8)
    route = list(range(N)); base = int(W[route[:-1], route[1:]].sum())
    blocks = []; i = 0
    while i < N:
        j = i
        while j + 1 < N and trail[j + 1] == trail[i]: j += 1
        blocks.append((i, j)); i = j + 1
    assert len(blocks) == 30, len(blocks)
    def pathcost(seq): return int(W[seq[:-1], seq[1:]].sum()) if len(seq) > 1 else 0
    classes = ("boundary", "adjacent", "inside_T", "inside_other", "boundary_interior")
    wit = [None]; bt = {}
    best = {c: (10 ** 9, None) for c in classes}; nmoves = 0; ndeg_le0 = 0; hist = {c: {} for c in classes}
    for (i0, j0) in blocks:
        T = route[i0:j0 + 1]; m = len(T); tt = int(trail[i0])
        # T's runs in route order are its version cycle opened at T[0]; chains are the maximal w2 segments of the cycle
        cut = [k for k in range(1, m) if W[T[k - 1], T[k]] != 2]
        segs = []; prev = 0
        for k in cut + [m]: segs.append(T[prev:k]); prev = k
        if W[T[-1], T[0]] == 2 and len(segs) > 1: segs = [segs[-1] + segs[0]] + segs[1:-1]
        vc = [r for sg in segs for r in sg]; mv = len(vc); pos = {r: k for k, r in enumerate(vc)}
        before = route[:i0]; after = route[j0 + 1:]
        for ci, C in enumerate(segs):
            if len(C) != 7 or W[C[-1], C[0]] != 2: continue
            k0 = pos[C[0]]; R = [vc[(k0 + 7 + t) % mv] for t in range(mv - 7)]
            for a in range(7):
                Xr = C[a:] + C[:a]
                for kind in "AB":
                    here, blk = (Xr, R) if kind == "A" else (R, Xr)
                    rest = before + here + after; h0 = len(before); h1 = h0 + len(here)   # here occupies rest[h0:h1]
                    r = np.array(rest); nr = len(r)
                    # gap g lies between rest[g-1] and rest[g], g = 0..nr
                    c = np.zeros(nr + 1, np.int64)
                    c[1:nr] = W[r[:-1], blk[0]] + W[blk[-1], r[1:]] - W[r[:-1], r[1:]]
                    c[0] = W[blk[-1], r[0]]; c[nr] = W[r[-1], blk[0]]
                    tot = pathcost(rest) + pathcost(blk) + c - base
                    g = np.arange(nr + 1)
                    cl = np.full(nr + 1, 3)                                   # inside_other by default
                    # block boundaries of rest (other trails' blocks + T's piece 'here')
                    tr_rest = np.array([trail[x] for x in rest])
                    bnd = np.zeros(nr + 1, bool); bnd[0] = bnd[nr] = True; bnd[1:nr] = tr_rest[:-1] != tr_rest[1:]
                    cl[bnd] = 0
                    cl[(g == h0) | (g == h1)] = 1                             # next to T's own piece
                    cl[(g > h0) & (g < h1)] = 2                               # inside T's own piece
                    deg = np.zeros(nr + 1, bool)
                    if kind == "A":
                        if a != 0: deg[h0 + (7 - a)] = True                   # wrap gap C_6 | C_0 inside X
                        else: deg[h0] = deg[h1] = True
                    else:
                        if a == 0: deg[h0] = deg[h1] = True
                    ndeg_le0 += int(((tot <= 0) & deg).sum())
                    inter = (cl == 0) & (g > 0) & (g < nr)                    # boundary class without the two word ends
                    for ccode, cname in enumerate(classes):
                        msk = ((cl == ccode) if ccode < 4 else inter) & ~deg
                        if not msk.any(): continue
                        k = int(np.argmin(np.where(msk, tot, 10 ** 9))); d = int(tot[k])
                        nmoves += 1
                        hist[cname][d] = hist[cname].get(d, 0) + 1
                        key = cname + ("_A" if m > 100 else "_phi")
                        if key not in bt or d < bt[key][0]:
                            bt[key] = (d, dict(trail=tt, chain=ci, a=a, kind=kind, gap=k))
                            if len(sys.argv) > 5 and sys.argv[4] == key: wit[0] = rest[:k] + blk + rest[k:]
                        if d < best[cname][0]:
                            nb = int(bnd[1:k + 1].sum())                          # blocks of rest before gap k (junction position)
                            best[cname] = (d, dict(trail=tt, chain=ci, a=a, kind=kind, gap=k, R_len=len(R), blocks_before_gap=nb))
                            if len(sys.argv) > 5 and sys.argv[4] == cname: wit[0] = rest[:k] + blk + rest[k:]
    out = dict(word=sys.argv[1], L=35288 + base, degenerate_moves_with_delta_le0=ndeg_le0,
               best_by_class_and_type={k: dict(delta=v[0], move=v[1]) for k, v in sorted(bt.items())},
               best_by_class={c: dict(delta=best[c][0], move=best[c][1]) for c in classes},
               delta_hist_by_class={c: {str(k): hist[c][k] for k in sorted(hist[c])[:8]} for c in classes}, moves=nmoves)
    if wit[0] is not None:
        nr = wit[0]; assert sorted(nr) == list(range(N))
        w = list(st[nr[0]])
        for i, r in enumerate(nr):
            if i > 0: kk = int(W[nr[i - 1], r]); w += list(st[r][8 - kk:])
            w += list(st[r][:7])
        open(sys.argv[5], "w").write("".join(str(c + 1) for c in w) + "\n")
        info = best[sys.argv[4]][1] if sys.argv[4] in best else bt[sys.argv[4]][1]
        out["witness"] = dict(cls=sys.argv[4], file=sys.argv[5], length=len(w), **info)
    json.dump(out, open(sys.argv[3], "w"), indent=1)
    print(json.dumps(out))

main()
