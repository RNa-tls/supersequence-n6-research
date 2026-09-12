#!/usr/bin/env python3
"""Round 145 — the FIXED REPRESENTATIVE reduction, proved and verified here.

Round 142 B1 asserts it; this module proves it from scratch and checks every
step of the proof computationally on real covering words, including the
length-872 witness at n = 6.

-------------------------------------------------------------------------------
SETTING

Fix n.  A word W over an n-letter alphabet is a COVER if every one of the n!
permutations occurs as a window W[i:i+n].  For each permutation p let
first(p) be the least such i.  Order the permutations by first occurrence:

    q_1 at i_1 < q_2 at i_2 < ... < q_N at i_N,       N = n!

(the i_j are distinct because two different permutations cannot start at the
same position).  Write g_j = i_{j+1} - i_j >= 1 for the ACTUAL gaps and

    omega(a, b) = min { k in 1..n : a[k:] == b[:n-k] }      (n if none)

for the maximum-overlap gap.  Necessarily g_j >= omega(q_j, q_{j+1}), because
the window at i_{j+1} is q_{j+1} and the two windows overlap in n - g_j letters
when g_j < n.

DEFINE  Phi(W) = the word obtained by writing q_1 and then, for each j >= 2,
appending the last omega(q_{j-1}, q_j) letters of q_j.

-------------------------------------------------------------------------------
LEMMA 1 (Phi is a cover).  q_1, ..., q_N all occur as windows of Phi(W), at the
positions of the partial sums of the omegas, by construction.  Hence Phi(W) is
a cover.

LEMMA 2 (Phi does not lengthen).  Let W_trim = W[i_1 : i_N + n], so that
|W_trim| = n + sum_j g_j <= |W| and |Phi(W)| = n + sum_j omega(q_j, q_{j+1}).
Since g_j >= omega_j termwise, |Phi(W)| <= |W_trim| <= |W|.

LEMMA 3 (equality is rigidity).  If |Phi(W)| = |W| then |W_trim| = |W| (no
trimming) and g_j = omega_j for every j.  A word is determined by its window
sequence and gaps, so W = W_trim = Phi(W).

LEMMA 4 (a fixed point exists, no longer than W).  |Phi^{m}(W)| is a
non-increasing sequence of integers bounded below by n, so it is eventually
constant; at the first index m with |Phi^{m+1}(W)| = |Phi^{m}(W)| Lemma 3 gives
Phi^{m+1}(W) = Phi^{m}(W).  Put W* = Phi^m(W); then W* is a cover,
|W*| <= |W| and Phi(W*) = W*.

LEMMA 5 (what a fixed point looks like).  Let W* = Phi(W*).  Then

  (a) the selected sequence used to build Phi(W*) IS the first-occurrence
      sequence of W*, so "selected" is unambiguous;
  (b) every selected gap equals omega, i.e. every selected connector is a
      SHORTEST connector;
  (c) every window of W* is either one of the selected q_j or lies strictly
      inside a connector interval [i_j, i_{j+1} + n - 1]; in the latter case it
      is a repeat, because the first occurrences are exactly the i_j.  So all
      repeats are hidden windows of selected connectors.

  Proof.  (a) holds because Phi(W*) is by definition built from W*'s own first
  occurrences and equals W*.  (b) is Lemma 3 applied to W*.  For (c): a window
  starts at some position q with i_1 <= q <= i_N (the word is trimmed), so
  i_j <= q < i_{j+1} for some j, or q = i_N.  If q is one of the i_j it is
  selected; otherwise the window starts strictly between two consecutive
  selected starts, so it lies inside that connector, and it is not a first
  occurrence, hence a repeat.

COROLLARY.  min over covers of |W| is attained at a fixed point.  So a lower
bound proved for all FIXED representatives is a lower bound for all covers.
This is the only thing the rest of the proof needs from B1.
-------------------------------------------------------------------------------

The checks below verify Lemmas 1-5 literally, and in particular that no step
ever lengthens a word and that the fixed points really do satisfy (a)-(c).
"""
from __future__ import annotations
import itertools, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def omega(a, b, n):
    for k in range(1, n):
        if a[k:] == b[:n - k]:
            return k
    return n


def perm_windows(W, n):
    """(position, window) for every window whose n letters are distinct."""
    return [(i, W[i:i + n]) for i in range(len(W) - n + 1)
            if len(set(W[i:i + n])) == n]


def selected(W, n):
    """First occurrences in chronological order: list of (position, window)."""
    seen, out = set(), []
    for i, w in perm_windows(W, n):
        if w not in seen:
            seen.add(w)
            out.append((i, w))
    return out


def is_cover(W, n, alphabet=None):
    alpha = sorted(set(alphabet or W))
    need = {"".join(p) for p in itertools.permutations(alpha)}
    return {w for _, w in perm_windows(W, n)} == need


def Phi(W, n):
    sel = selected(W, n)
    out = sel[0][1]
    for j in range(1, len(sel)):
        k = omega(sel[j - 1][1], sel[j][1], n)
        out += sel[j][1][n - k:]
    return out


def fixed_representative(W, n, max_iter=200):
    """Iterate Phi to a fixed point, recording that length never increases."""
    lens = [len(W)]
    cur = W
    for _ in range(max_iter):
        nxt = Phi(cur, n)
        lens.append(len(nxt))
        if len(nxt) > len(cur):
            raise AssertionError("Phi lengthened the word (Lemma 2 violated)")
        if nxt == cur:
            return cur, lens
        if len(nxt) == len(cur) and nxt != cur:
            raise AssertionError("equal length but different word "
                                 "(Lemma 3 violated)")
        cur = nxt
    raise AssertionError("no fixed point within max_iter")


def audit_fixed_point(Ws, n):
    """Verify Lemma 5 (a), (b), (c) literally on a fixed point."""
    sel = selected(Ws, n)
    if len(sel) != __import__("math").factorial(n):
        return dict(ok=False, why="not a cover")
    # (a) the reconstruction from the selected sequence is the word itself
    rebuilt = sel[0][1]
    for j in range(1, len(sel)):
        rebuilt += sel[j][1][n - omega(sel[j - 1][1], sel[j][1], n):]
    if rebuilt != Ws:
        return dict(ok=False, why="fixed point is not its own max-overlap spelling")
    # (b) every selected gap equals omega
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(len(sel) - 1)]
    oms = [omega(sel[j][1], sel[j + 1][1], n) for j in range(len(sel) - 1)]
    if gaps != oms:
        return dict(ok=False, why="a selected gap exceeds omega")
    # (c) every repeat lies strictly inside a connector interval
    starts = {i for i, _ in sel}
    pos = sorted(starts)
    repeats, inside = 0, 0
    for i, _w in perm_windows(Ws, n):
        if i in starts:
            continue
        repeats += 1
        # find j with pos[j] < i < pos[j+1]
        lo = max(p for p in pos if p < i)
        hi = min(p for p in pos if p > i)
        if lo < i < hi and i + n - 1 <= hi + n - 1:
            inside += 1
    if repeats != inside:
        return dict(ok=False, why="a repeat is not a hidden connector window")
    # the trimming is already done: the word starts at the first selected window
    if sel[0][0] != 0 or sel[-1][0] + n != len(Ws):
        return dict(ok=False, why="fixed point is not trimmed")
    return dict(ok=True, length=len(Ws), passes=None, repeats=repeats,
                gaps_all_shortest=True, selected=len(sel),
                max_gap=max(gaps), gap_histogram={str(k): gaps.count(k)
                                                 for k in sorted(set(gaps))})


# ----------------------------------------------------------------- test corpus
def inflate(W, n, rng, prob=0.25):
    """Rebuild a cover with SOME selected gaps widened to the full n.

    Writing q_j in full and then q_{j+1} in full is always legal, so the result
    is guaranteed to still be a cover while being a NON-fixed word: exactly the
    situation Phi has to repair.  Overlaps strictly between omega and n are not
    available, so the only alternative to omega is n.
    """
    sel = selected(W, n)
    out, widened = sel[0][1], 0
    for j in range(1, len(sel)):
        k = omega(sel[j - 1][1], sel[j][1], n)
        if rng.random() < prob and k < n:
            k = n
            widened += 1
        out += sel[j][1][n - k:]
    return out, widened


def pad(W, n, rng, alpha):
    """Junk before and after: still a cover, and Phi must trim it."""
    pre = "".join(rng.choice(alpha) for _ in range(rng.randint(1, 2 * n)))
    post = "".join(rng.choice(alpha) for _ in range(rng.randint(1, 2 * n)))
    return pre + W + post


def corpus(W, n, rng, alpha, count):
    """Guaranteed covers: the word itself, gap-inflated and junk-padded forms,
    plus random insertions kept ONLY when they remain covers."""
    out = [(W, "base")]
    for _ in range(count):
        w, k = inflate(W, n, rng)
        out.append((w, f"inflate+{k}"))
        out.append((pad(w, n, rng, alpha), f"inflate+{k}+pad"))
    out.append((pad(W, n, rng, alpha), "pad"))
    tries = 0
    while tries < count:
        tries += 1
        w = W
        for _ in range(rng.randint(1, 3)):
            p = rng.randrange(len(w))
            w = w[:p] + "".join(rng.choice(alpha)
                                for _ in range(rng.randint(1, n + 2))) + w[p:]
        if is_cover(w, n, alpha):
            out.append((w, "insert"))
    return out


def run(seed=20260912, n4=400, n5=60):
    rng = random.Random(seed)
    res = {}

    def sweep(W, n, alpha, count, lower):
        bad, tested, shortened = [], 0, 0
        for w, tag in corpus(W, n, rng, alpha, count):
            assert is_cover(w, n, alpha), ("corpus produced a non-cover", tag)
            tested += 1
            Ws, lens = fixed_representative(w, n)
            if len(Ws) < len(w):
                shortened += 1
            if not is_cover(Ws, n, alpha):
                bad.append((tag, "fixed point is not a cover"))
            if len(Ws) > len(w):
                bad.append((tag, "Phi lengthened"))
            if len(Ws) < lower:
                bad.append((tag, "below the known optimum", len(Ws)))
            a = audit_fixed_point(Ws, n)
            if not a["ok"]:
                bad.append((tag, a))
        return dict(tested=tested, shortened=shortened, failures=len(bad),
                    examples=bad[:3], ok=not bad)

    # ---- n = 4
    base4 = "123412314231243121342132413214321"
    assert is_cover(base4, 4, "1234") and len(base4) == 33
    res["n4"] = sweep(base4, 4, "1234", n4, 33)

    # ---- n = 5: the eight minimal covers preserved in round 142
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    if p5.exists():
        raw = json.loads(p5.read_text())
        words = sorted({e["word"] for e in raw if isinstance(e, dict)
                        and "word" in e})
        alpha5 = "".join(sorted(set(words[0]))) if words else "01234"
        bad5, sub = [], {}
        for idx, W in enumerate(words):
            assert is_cover(W, 5, alpha5) and len(W) == 153
            Ws, _ = fixed_representative(W, 5)
            if Ws != W:
                bad5.append(("a 153-minimum is not already fixed", idx, len(Ws)))
            a = audit_fixed_point(Ws, 5)
            if not a["ok"]:
                bad5.append((idx, a))
        sub = sweep(words[0], 5, alpha5, n5, 153) if words else {}
        res["n5"] = dict(minima=len(words), all_minima_already_fixed=not bad5,
                         failures=len(bad5), examples=bad5[:3],
                         perturbation_sweep=sub,
                         ok=(not bad5) and sub.get("ok", True))

    # ---- n = 6: the verified 872 witness
    p6 = ROOT / "data" / "verified_872_witness.txt"
    if p6.exists():
        W = p6.read_text().strip()
        assert is_cover(W, 6, "123456") and len(W) == 872
        Ws, lens = fixed_representative(W, 6)
        a = audit_fixed_point(Ws, 6)
        res["n6_witness"] = dict(input_length=len(W), fixed_length=len(Ws),
                                 iterations=len(lens) - 1, lengths=lens,
                                 already_fixed=(Ws == W), audit=a,
                                 ok=a["ok"] and len(Ws) <= len(W))
        res["n6_perturbations"] = sweep(W, 6, "123456", 4, 872)
        # the (FO) identity read off the real witness
        sel = selected(W, 6)
        gaps = [sel[j + 1][0] - sel[j][0] for j in range(len(sel) - 1)]
        P = 1 + sum(1 for g in gaps if g >= 2)
        S = sum(1 for g in gaps if g >= 3)
        Hh = sum(max(g - 3, 0) for g in gaps)
        res["n6_witness_FO"] = dict(
            passes=P, G=P - 120, S=S, H=Hh,
            L_from_identity=844 + (P - 120) + S + Hh, L_actual=len(W),
            identity_holds=(844 + (P - 120) + S + Hh == len(W)),
            t=len(W) - 867)

    res["conclusion"] = ("Every cover has a fixed representative that is no "
                        "longer, is itself a cover, spells every selected "
                        "connector at maximum overlap, and whose repeats are "
                        "exactly hidden connector windows.  A lower bound for "
                        "fixed representatives is therefore a lower bound for "
                        "all covers.")
    res["all_ok"] = all(v.get("ok", True) for v in res.values()
                        if isinstance(v, dict))
    return res


if __name__ == "__main__":
    r = run(n4=int(sys.argv[1]) if len(sys.argv) > 1 else 400)
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "rr_l6_fixed_representative_145.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])
