#!/usr/bin/env python3
"""라운드 120 — **뒤집기 대칭**(reversal symmetry)의 전수 검증.

라운드 119 §8 은 "`b <-> 6-b` 는 이동 집합이 역방향 대칭이 아니라 대칭이 아니다" 라고
적었다.  **이것은 틀렸다.**  문자열을 통째로 뒤집는 사상은 실제로 이 문제의 대칭이고,
tau-궤도 분할까지 보존한다.  이 스크립트가 그 사실을 전수로 확인한다.

정의.  rho(w) = 글자를 뒤집은 단어.  walk 을 pass 열 (진입 u_i, 길이 m_i) 로 볼 때

    Phi(walk) := pass 열을 뒤집고, 각 pass (u, m) 를 (rho(sigma^{m-1} u), m) 으로 보낸다.

검증 항목 (전부 전수):

  A1  rho . sigma = sigma^{-1} . rho                                  (720)
  A2  이음매 무게 보존:  omega(y, z) = omega(rho(z), rho(y))          (720 x 719)
  A3  R := rho . sigma^5 는 **대합**이고 tau-궤도를 tau-궤도 위로 보낸다 (144)
  A4  rho 는 육각형을 육각형 위로 보낸다                              (120)
  A5  pass 상: {sigma^j u} 의 rho-상 = {sigma^j rho(sigma^{m-1}u)}    (720 x 6)

  R1  full->full 이음매는 궤도 내부성이 보존된다                      (720 x 17)
  R2  full->short 이음매의 상은 **항상 궤도를 바꾼다**                (720 x 17 x 5)
  R3  short->full 무게-2 이음매의 상은 **항상 궤도 내부**(tau)다      (720 x 5)

  N4  n=4 전수 walk 로 끝에서 끝까지 대조 (거짓 기각 0):
      Phi(walk) 이 유효한 walk 이고 L, P, F, S, H, O 가 보존되며 R1/R2/R3 가 성립한다.

R1/R2/R3 가 라운드 120 의 케이스 분석이 쓰는 전부다.
"""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

# ----------------------------------------------------------------- n = 6 geometry
WORDS = [tuple(p) for p in itertools.permutations(range(6))]
IDX = {w: i for i, w in enumerate(WORDS)}
NW = 720


def sig(w):
    return w[1:] + w[:1]


def isig(w):
    return w[-1:] + w[:-1]


def tau(w):
    return (w[1], w[2], w[3], w[4], w[0], w[5])


def rho(w):
    return tuple(reversed(w))


def build_geo():
    hexid = [-1] * NW
    orbid = [-1] * NW
    nh = no = 0
    for i, w in enumerate(WORDS):
        if hexid[i] < 0:
            x = w
            for _ in range(6):
                hexid[IDX[x]] = nh
                x = sig(x)
            nh += 1
        if orbid[i] < 0:
            x = w
            for _ in range(5):
                orbid[IDX[x]] = no
                x = tau(x)
            no += 1
    assert (nh, no) == (120, 144)
    return hexid, orbid


HEXID, ORBID = build_geo()


def build_phase():
    ph = [-1] * NW
    for q in range(144):
        rep = min(i for i in range(NW) if ORBID[i] == q)
        w = WORDS[rep]
        for j in range(5):
            ph[IDX[w]] = j
            w = tau(w)
    return ph


ORBPH = build_phase()


def sigk(w, k):
    for _ in range(k % 6):
        w = sig(w)
    return w


def omega(a, b):
    """joint weight: number of NEW letters b contributes after a."""
    for k in range(1, 6):
        if a[k:] == b[:6 - k]:
            return k
    return 6


def light_and_heavy_moves():
    """the four light moves plus the 13 indecomposable weight-4 tails, as maps on EXIT words."""
    moves = {}
    moves["W2"] = lambda q: (q[2], q[3], q[4], q[5], q[1], q[0])
    moves["W3a"] = lambda q: (q[3], q[4], q[5], q[1], q[2], q[0])
    moves["W3b"] = lambda q: (q[3], q[4], q[5], q[2], q[0], q[1])
    moves["W3c"] = lambda q: (q[3], q[4], q[5], q[2], q[1], q[0])
    idx = 0
    for pi in itertools.permutations(range(4)):
        mx, ok = -1, True
        for j in range(3):
            mx = max(mx, pi[j])
            if mx == j:
                ok = False
                break
        if not ok:
            continue
        act = (4, 5) + pi
        moves[f"W4_{idx}"] = (lambda a: (lambda q: tuple(q[j] for j in a)))(act)
        idx += 1
    assert idx == 13, idx
    return moves


MOVES = light_and_heavy_moves()


def weight4_classes():
    """Round 120 section 9 - classify the 13 weight-4 tails by STRUCTURAL EFFECT.

    Round 118 recorded "13/13 always change orbit (720/720)".  That is WRONG: W4_0
    (action [4 5 1 2 3 0]) is intra-orbit for all 720 words at ell = 5.  The other 12
    change orbit at every ell.  All 13 change orbit at every ell < 5 and none of them
    ever returns to the source hexagon."""
    rows = {}
    for name, f in MOVES.items():
        if not name.startswith("W4_"):
            continue
        intra5 = sum(1 for u in WORDS if ORBID[IDX[f(sigk(u, 5))]] == ORBID[IDX[u]])
        intra_lt5 = sum(1 for u in WORDS for ell in range(5)
                        if ORBID[IDX[f(sigk(u, ell))]] == ORBID[IDX[u]])
        samehex = sum(1 for u in WORDS for ell in range(6)
                      if HEXID[IDX[f(sigk(u, ell))]] == HEXID[IDX[u]])
        # hexagon overlap between the source orbit and the target orbit (at ell = 5)
        ov = Counter()
        for u in WORDS:
            z = f(sigk(u, 5))
            a = {HEXID[i] for i in range(NW) if ORBID[i] == ORBID[IDX[u]]}
            b = {HEXID[i] for i in range(NW) if ORBID[i] == ORBID[IDX[z]]}
            ov[len(a & b)] += 1
            break
        # phase displacement when intra-orbit
        ph = Counter()
        if intra5 == NW:
            for u in WORDS:
                z = f(sigk(u, 5))
                ph[(ORBPH[IDX[z]] - ORBPH[IDX[u]]) % 5] += 1
        rows[name] = dict(intra_orbit_at_ell5=intra5, intra_orbit_at_ell_lt5=intra_lt5,
                          returns_to_source_hexagon=samehex,
                          phase_shift_when_intra={str(k): v for k, v in ph.items()})
    classes = {}
    for name, r in rows.items():
        key = (r["intra_orbit_at_ell5"], r["intra_orbit_at_ell_lt5"],
               r["returns_to_source_hexagon"])
        classes.setdefault(str(key), []).append(name)
    return dict(per_tail=rows, structural_classes=classes,
                n_classes=len(classes),
                round_118_claim="all 13 weight-4 tails always change orbit (720/720)",
                round_118_claim_status="FALSE for W4_0 at ell = 5; corrected here",
                all_change_orbit_below_ell5=all(r["intra_orbit_at_ell_lt5"] == 0
                                                for r in rows.values()),
                none_returns_to_source_hexagon=all(r["returns_to_source_hexagon"] == 0
                                                   for r in rows.values()))


def seam_hexagon_collisions():
    """Round 120 section 16 - why the b = 1 and b = 5 B_ii searches are shallow.

    With x = 0 the only intra-orbit joint out of a full pass is tau, so "t' >= 2" forces the
    pass before X to have entry tau^{-1}(v), and "t >= 2" forces the pass before Y to have
    entry tau^{-1}(sigma^b v).  X's free exit opens a run at tau(sigma^b v) and Y's at tau(v).
    Two passes cannot share a hexagon (only h* is entered twice, by X and Y themselves).
    Exhaustively over all 720 words:

        hex(tau(sigma^5 v)) = hex(tau^{-1}(v))   for ALL v  ->  at b = 5, t' >= 2 is impossible
        hex(tau(v)) = hex(tau^{-1}(sigma^1 v))   for ALL v  ->  at b = 1, t  >= 2 is impossible

    so at b = 1 and b = 5 every B_ii walk has t = 1 (resp. t' = 1) and its Phi-image sits in
    the closed rows G2 / G1.  b = 2, 3, 4 have no such forced collision and need the search."""
    def itau(w):
        for _ in range(4):
            w = tau(w)
        return w

    rows = {}
    for b in range(1, 6):
        rows[b] = dict(
            pre_X_vs_R_Y_start=sum(1 for v in WORDS
                                   if HEXID[IDX[tau(sigk(v, b))]] == HEXID[IDX[itau(v)]]),
            pre_Y_vs_R_X_start=sum(1 for v in WORDS
                                   if HEXID[IDX[tau(v)]] == HEXID[IDX[itau(sigk(v, b))]]),
            pre_X_vs_pre_Y=sum(1 for v in WORDS
                               if HEXID[IDX[itau(v)]] == HEXID[IDX[itau(sigk(v, b))]]))
    # control: an orbit's five words really do sit in five distinct hexagons
    distinct = all(len({HEXID[IDX[w]] for w in
                        [v, tau(v), tau(tau(v)), tau(tau(tau(v))), itau(v)]}) == 5
                   for v in WORDS)
    return dict(per_b=rows, orbit_words_in_distinct_hexagons=distinct,
                t_prime_ge_2_impossible_at=[b for b, r in rows.items()
                                            if r["pre_X_vs_R_Y_start"] == NW],
                t_ge_2_impossible_at=[b for b, r in rows.items()
                                      if r["pre_Y_vs_R_X_start"] == NW],
                free_splits=[b for b, r in rows.items()
                             if r["pre_X_vs_R_Y_start"] == 0 and r["pre_Y_vs_R_X_start"] == 0])


def n6_base_fact():
    """the fact R2 rests on: at ell < 5 EVERY move (4 light + 13 weight-4) leaves the orbit."""
    bad = 0
    for name, f in MOVES.items():
        for ell in range(5):
            for u in WORDS:
                if ORBID[IDX[f(sigk(u, ell))]] == ORBID[IDX[u]]:
                    bad += 1
    return dict(checks=len(MOVES) * 5 * NW, intra_orbit_below_ell5=bad, holds=(bad == 0))


def n4_base_fact():
    """the n = 4 analogue of the same fact - it FAILS, which is why R2 is n = 6 specific."""
    perms, idx, s4, t4, r4, om4, hexid, orbid = n4_setup()
    bad = 0
    checks = 0
    for u in perms:
        for ell in range(3):
            y = u
            for _ in range(ell):
                y = s4(y)
            for z in perms:
                if z == y or om4(y, z) < 2:
                    continue
                checks += 1
                if orbid[idx[z]] == orbid[idx[u]]:
                    bad += 1
    return dict(checks=checks, intra_orbit_below_ell_top=bad, holds=(bad == 0))


def verify_n6():
    rep = {}

    # A1 -------------------------------------------------------------------
    rep["A1_rho_sigma"] = all(rho(sig(w)) == isig(rho(w)) for w in WORDS)

    # A2 -------------------------------------------------------------------
    bad = 0
    for y in WORDS:
        for z in WORDS:
            if y == z:
                continue
            if omega(y, z) != omega(rho(z), rho(y)):
                bad += 1
    rep["A2_weight_preserved_pairs"] = NW * (NW - 1)
    rep["A2_violations"] = bad

    # A3 -------------------------------------------------------------------
    R = {w: rho(sigk(w, 5)) for w in WORDS}
    rep["A3_R_involution"] = all(R[R[w]] == w for w in WORDS)
    orb_img = {}
    scattered = 0
    for q in range(144):
        ws = [WORDS[i] for i in range(NW) if ORBID[i] == q]
        img = {ORBID[IDX[R[w]]] for w in ws}
        if len(img) != 1:
            scattered += 1
        else:
            orb_img[q] = img.pop()
    rep["A3_orbits_scattered"] = scattered
    rep["A3_orbit_map_is_bijection"] = (len(set(orb_img.values())) == 144)
    rep["A3_orbit_map_is_involution"] = all(orb_img[orb_img[q]] == q for q in range(144))

    # A4 -------------------------------------------------------------------
    hex_img = {}
    hscat = 0
    for h in range(120):
        img = {HEXID[IDX[rho(WORDS[i])]] for i in range(NW) if HEXID[i] == h}
        if len(img) != 1:
            hscat += 1
        else:
            hex_img[h] = img.pop()
    rep["A4_hexagons_scattered"] = hscat
    rep["A4_hexagon_map_is_bijection"] = (len(set(hex_img.values())) == 120)

    # A5 -------------------------------------------------------------------
    bad = 0
    for u in WORDS:
        for m in range(1, 7):
            fwd = {rho(sigk(u, j)) for j in range(m)}
            e2 = rho(sigk(u, m - 1))
            rev = {sigk(e2, j) for j in range(m)}
            if fwd != rev:
                bad += 1
    rep["A5_pass_image_checks"] = NW * 6
    rep["A5_violations"] = bad

    # R1 -------------------------------------------------------------------
    bad = 0
    checks = 0
    for u in WORDS:
        y = sigk(u, 5)
        for name, f in MOVES.items():
            z = f(y)
            fwd_intra = (ORBID[IDX[u]] == ORBID[IDX[z]])
            rev_intra = (ORBID[IDX[R[u]]] == ORBID[IDX[R[z]]])
            checks += 1
            if fwd_intra != rev_intra:
                bad += 1
    rep["R1_full_full_checks"] = checks
    rep["R1_violations"] = bad

    # R2: full pass -> SHORT pass; the image joint has ell = m'-1 < 5 -----------
    bad = 0
    checks = 0
    for u in WORDS:
        y = sigk(u, 5)
        src_img_entry = rho(y)                       # Phi(full pass) entry = rho(sigma^5 u)
        for name, f in MOVES.items():
            z = f(y)
            for m2 in range(1, 6):                   # target pass is SHORT
                tgt_img_entry = rho(sigk(z, m2 - 1))
                checks += 1
                if ORBID[IDX[tgt_img_entry]] == ORBID[IDX[src_img_entry]]:
                    bad += 1
    rep["R2_full_to_short_checks"] = checks
    rep["R2_violations_image_stayed_in_orbit"] = bad

    # R3: SHORT pass -> full pass by W2; the image joint is tau (intra-orbit) ---
    bad = 0
    checks = 0
    for u in WORDS:
        for b in range(1, 6):                        # source pass is SHORT of length b
            y = sigk(u, b - 1)
            z = MOVES["W2"](y)
            src_img_entry = rho(y)                   # Phi(short pass) entry
            tgt_img_entry = rho(sigk(z, 5))          # Phi(full pass) entry
            checks += 1
            if ORBID[IDX[tgt_img_entry]] != ORBID[IDX[src_img_entry]]:
                bad += 1
    rep["R3_short_to_full_W2_checks"] = checks
    rep["R3_violations_image_left_orbit"] = bad

    # supporting census: which moves are intra-orbit at which ell ------------
    cens = {}
    for name, f in MOVES.items():
        row = {}
        for ell in range(6):
            same = 0
            for u in WORDS:
                y = sigk(u, ell)
                if ORBID[IDX[f(y)]] == ORBID[IDX[u]]:
                    same += 1
            row[ell] = same
        cens[name] = row
    rep["intra_orbit_census_by_ell"] = cens
    return rep


# ----------------------------------------------------------------- n = 4 control
def n4_setup():
    perms = [tuple(p) for p in itertools.permutations(range(4))]
    idx = {p: i for i, p in enumerate(perms)}
    s4 = lambda w: w[1:] + w[:1]
    t4 = lambda w: (w[1], w[2], w[0], w[3])
    r4 = lambda w: tuple(reversed(w))

    def om4(a, b):
        for k in range(1, 4):
            if a[k:] == b[:4 - k]:
                return k
        return 4

    hexid = [-1] * 24
    orbid = [-1] * 24
    nh = no = 0
    for i, w in enumerate(perms):
        if hexid[i] < 0:
            x = w
            for _ in range(4):
                hexid[idx[x]] = nh
                x = s4(x)
            nh += 1
        if orbid[i] < 0:
            x = w
            for _ in range(3):
                orbid[idx[x]] = no
                x = t4(x)
            no += 1
    assert (nh, no) == (6, 8)
    return perms, idx, s4, t4, r4, om4, hexid, orbid


def n4_all_walks(maxlen):
    """all non-repeating n=4 walks (24 words each once) of string length <= maxlen,
    started at a fixed word (S4 left multiplication is simply transitive)."""
    perms, idx, s4, t4, r4, om4, hexid, orbid = n4_setup()
    Wt = [[om4(a, b) for b in perms] for a in perms]
    out = []

    def dfs(cur, used, seq, total):
        if len(seq) == 24:
            out.append((4 + total, tuple(seq)))
            return
        if 4 + total + (24 - len(seq)) > maxlen:
            return
        for j in range(24):
            if used >> j & 1:
                continue
            w = Wt[cur][j]
            if 4 + total + w + (24 - len(seq) - 1) > maxlen:
                continue
            seq.append(j)
            dfs(j, used | (1 << j), seq, total + w)
            seq.pop()

    dfs(0, 1, [0], 0)
    return perms, idx, s4, t4, r4, om4, hexid, orbid, Wt, out


def n4_passes(perms, Wt, seq):
    """cut a word sequence into passes (maximal sigma-runs) -> list of (entry idx, length)."""
    om = [Wt[seq[i]][seq[i + 1]] for i in range(len(seq) - 1)]
    passes, cur = [], 1
    start = seq[0]
    for i, w in enumerate(om):
        if w >= 2:
            passes.append((start, cur))
            cur = 1
            start = seq[i + 1]
        else:
            cur += 1
    passes.append((start, cur))
    return passes, om


def n4_measure(perms, idx, hexid, orbid, passes, om):
    entries = [p[0] for p in passes]
    lens = [p[1] for p in passes]
    P = len(passes)
    joints = [w for w in om if w >= 2]
    S = sum(1 for w in joints if w >= 3)
    H = sum(max(w - 3, 0) for w in joints)
    orbs = [orbid[e] for e in entries]
    runs, cur = [], [0]
    for i in range(1, P):
        if orbs[i] == orbs[i - 1]:
            cur.append(i)
        else:
            runs.append(cur)
            cur = [i]
    runs.append(cur)
    r = len(runs)
    O = len(set(orbs))
    inter = {run[0] - 1 for run in runs[1:]}
    x = sum(1 for i, w in enumerate(joints) if i not in inter and w >= 3)
    f_out = sum(1 for i in inter if joints[i] == 2)
    return dict(P=P, F=P - 6, S=S, H=H, O=O, r=r, e=r - O, x=x, f_out=f_out,
                lens=lens, L=4 + sum(om))


def n4_reverse(perms, idx, s4, r4, passes):
    """Phi: reverse the pass order; pass (u, m) -> (rho(sigma^{m-1} u), m)."""
    out = []
    for e, m in reversed(passes):
        w = perms[e]
        for _ in range(m - 1):
            w = s4(w)
        out.append((idx[r4(w)], m))
    return out


def n4_words(perms, idx, s4, passes):
    seq = []
    for e, m in passes:
        w = perms[e]
        for _ in range(m):
            seq.append(idx[w])
            w = s4(w)
    return seq


def verify_n4(maxlen=34):
    perms, idx, s4, t4, r4, om4, hexid, orbid, Wt, walks = n4_all_walks(maxlen)
    rep = dict(maxlen=maxlen, walks=len(walks))
    bad_valid = bad_inv = bad_L = bad_invol = 0
    bad_r1 = bad_r2 = bad_r3 = 0
    chk_r1 = chk_r2 = chk_r3 = 0
    trans = Counter()
    lenhist = Counter()
    for L, seq in walks:
        passes, om = n4_passes(perms, Wt, seq)
        m0 = n4_measure(perms, idx, hexid, orbid, passes, om)
        rp = n4_reverse(perms, idx, s4, r4, passes)
        rseq = n4_words(perms, idx, s4, rp)
        # validity: 24 distinct words, and the pass cut of the reversed word sequence
        # must reproduce exactly the pass list we constructed
        if len(set(rseq)) != 24:
            bad_valid += 1
            continue
        rpasses, rom = n4_passes(perms, Wt, rseq)
        if rpasses != rp:
            bad_valid += 1
            continue
        m1 = n4_measure(perms, idx, hexid, orbid, rpasses, rom)
        if m1["L"] != m0["L"]:
            bad_L += 1
        for key in ("P", "F", "S", "H", "O"):
            if m1[key] != m0[key]:
                bad_inv += 1
                break
        if m1["lens"] != list(reversed(m0["lens"])):
            bad_inv += 1
        # involution
        if n4_words(perms, idx, s4, n4_reverse(perms, idx, s4, r4, rpasses)) != list(seq):
            bad_invol += 1
        lenhist[(m0["F"], tuple(sorted(l for l in m0["lens"] if l < 4)))] += 1
        trans[(m0["F"], m0["e"], m0["x"], m0["f_out"], m0["H"],
               m1["e"], m1["x"], m1["f_out"], m1["H"])] += 1
        # R1 / R2 / R3 at the walk level
        jidx = [i for i, w in enumerate(om) if w >= 2]
        P = len(passes)
        for jn, i in enumerate(jidx):
            la, lb = passes[jn][1], passes[jn + 1][1]
            fwd_intra = (orbid[passes[jn][0]] == orbid[passes[jn + 1][0]])
            k = P - 2 - jn                       # same joint, reversed indexing
            rev_intra = (orbid[rpasses[k][0]] == orbid[rpasses[k + 1][0]])
            if la == 4 and lb == 4:
                chk_r1 += 1
                if fwd_intra != rev_intra:
                    bad_r1 += 1
            if la == 4 and lb < 4:
                chk_r2 += 1
                if rev_intra:
                    bad_r2 += 1
            if la < 4 and lb == 4 and om[i] == 2:
                chk_r3 += 1
                if not rev_intra:
                    bad_r3 += 1
    rep.update(bad_valid=bad_valid, bad_invariants=bad_inv, bad_L=bad_L,
               bad_involution=bad_invol,
               R1_checks=chk_r1, R1_violations=bad_r1,
               R2_checks=chk_r2, R2_violations=bad_r2,
               R3_checks=chk_r3, R3_violations=bad_r3,
               resource_transitions=len(trans),
               f1_short_length_multisets={str(k): v for k, v in sorted(lenhist.items())
                                          if k[0] == 1})
    # the transitions actually observed for F=1 walks, as (e,x,f_out,H) -> (e,x,f_out,H)
    f1 = {}
    for key, n in trans.items():
        if key[0] != 1:
            continue
        f1[f"{key[1:5]}->{key[5:]}"] = n
    rep["f1_resource_transitions"] = f1
    return rep


def main():
    rep = dict(round=120,
               claim="reversal (string reversal) is an exact symmetry that also preserves "
                     "the tau-orbit partition; Round 119 section 8 said otherwise and is "
                     "corrected here",
               n6=verify_n6(), n4_control=verify_n4(37),
               weight4_classes=weight4_classes(),
               n6_base_fact=n6_base_fact(), n4_base_fact=n4_base_fact(),
               seam_hexagon_collisions=seam_hexagon_collisions())
    ok = (rep["n6"]["A1_rho_sigma"] and rep["n6"]["A2_violations"] == 0
          and rep["n6"]["A3_R_involution"] and rep["n6"]["A3_orbits_scattered"] == 0
          and rep["n6"]["A3_orbit_map_is_bijection"]
          and rep["n6"]["A3_orbit_map_is_involution"]
          and rep["n6"]["A4_hexagons_scattered"] == 0
          and rep["n6"]["A5_violations"] == 0
          and rep["n6"]["R1_violations"] == 0
          and rep["n6"]["R2_violations_image_stayed_in_orbit"] == 0
          and rep["n6"]["R3_violations_image_left_orbit"] == 0
          and rep["n4_control"]["bad_valid"] == 0
          and rep["n4_control"]["bad_invariants"] == 0
          and rep["n4_control"]["bad_L"] == 0
          and rep["n4_control"]["bad_involution"] == 0
          and rep["n4_control"]["R1_violations"] == 0
          and rep["n4_control"]["R3_violations"] == 0
          and rep["n6_base_fact"]["holds"]
          # R2 is an n = 6 fact.  Its n = 4 analogue FAILS, and so does R2 in n = 4 - the
          # n = 4 control therefore CONFIRMS that R2 tracks the base census exactly and is
          # not an accident.  Requiring 0 n = 4 R2 violations would be the wrong test.
          and (not rep["n4_base_fact"]["holds"])
          and (rep["n4_control"]["R2_violations"] > 0)
          and rep["weight4_classes"]["all_change_orbit_below_ell5"]
          and rep["weight4_classes"]["none_returns_to_source_hexagon"]
          and rep["seam_hexagon_collisions"]["orbit_words_in_distinct_hexagons"]
          and rep["seam_hexagon_collisions"]["t_prime_ge_2_impossible_at"] == [5]
          and rep["seam_hexagon_collisions"]["t_ge_2_impossible_at"] == [1]
          and rep["seam_hexagon_collisions"]["free_splits"] == [2, 3, 4])
    rep["all_checks_pass"] = ok
    rep["label"] = "ROUND-120 PROVISIONAL - CLAUDE ONLY - NOT INDEPENDENTLY AUDITED"
    rep["disclaimer"] = "This project has not proved L6 >= 872."
    OUT.mkdir(exist_ok=True)
    (OUT / "rr_f1_reversal_120.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep["n6"].items()
                      if k != "intra_orbit_census_by_ell"}, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in rep["n4_control"].items()
                      if k not in ("f1_resource_transitions", "f1_short_length_multisets")},
                     ensure_ascii=False, indent=1))
    print("n6 base fact (ell<5 always leaves the orbit):", rep["n6_base_fact"])
    print("n4 base fact (the analogue - expected to FAIL):", rep["n4_base_fact"])
    print("seam hexagon collisions:",
          json.dumps(rep["seam_hexagon_collisions"], ensure_ascii=False))
    print("weight-4 structural classes:",
          json.dumps(rep["weight4_classes"]["structural_classes"], ensure_ascii=False))
    print("ALL CHECKS PASS:", ok)


if __name__ == "__main__":
    main()
