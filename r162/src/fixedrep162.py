#!/usr/bin/env python3
"""Round 162 -- the fixed-representative reduction, rebuilt from definitions.

Nothing is imported from src/l6_fixed_representative_145.py.  Only the
word-level primitives (omega, perm_windows, selected, is_cover) come from the
round-156 independent reconstruction, which imports nothing from src/.

WHAT THE THEOREM ACTUALLY IS (src/l6_fixed_representative_145.py lines 10-78)

  For a cover W let q_1 at i_1 < ... < q_N at i_N (N = n!) be the FIRST
  occurrences of the n! permutations, g_j = i_{j+1} - i_j the actual gaps, and
        omega(a, b) = min{ k in 1..n : a[k:] = b[:n-k] }   (n if none)
  the maximum-overlap gap.  DEFINE

        Phi(W) = q_1  followed, for each j >= 2, by the last
                 omega(q_{j-1}, q_j) letters of q_j.

  L1  Phi(W) is a cover
  L2  |Phi(W)| <= |W_trim| <= |W|,  W_trim := W[i_1 : i_N + n]
  L3  |Phi(W)| = |W|  =>  W = W_trim = Phi(W)
  L4  a fixed point W* exists with |W*| <= |W|, within at most
      |W| - (n! + n - 1) non-fixed iterations
  L5  at a fixed point: (a) the selected sequence used to build Phi(W*) IS
      W*'s own first-occurrence sequence; (b) every selected gap equals omega;
      (c) every non-selected permutation window is a repeat lying strictly
      inside a connector interval

  COROLLARY (the WLOG step): a lower bound proved for all FIXED
  representatives is a lower bound for all covers.

Phi is a REWRITING operator, not a group action: it re-spells the word at
maximum overlap and trims it.  No relabelling, no rotation, no conjugation.
"""
from __future__ import annotations
import json, random, sys, time
from collections import Counter
from math import factorial
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import extract156 as X                                            # noqa: E402

omega, selected, perm_windows, is_cover = (X.omega, X.selected,
                                           X.perm_windows, X.is_cover)


def Phi(W, n):
    sel = selected(W, n)
    out = sel[0][1]
    for j in range(1, len(sel)):
        out += sel[j][1][n - omega(sel[j - 1][1], sel[j][1], n):]
    return out


def trim(W, n):
    sel = selected(W, n)
    return W[sel[0][0]: sel[-1][0] + n]


def step_audit(W, n, alpha):
    """One application of Phi, with L1 / L2 / L3 checked literally."""
    bad = []
    N = factorial(n)
    sel = selected(W, n)
    if len(sel) != N:
        return None, ["not a cover"]
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    oms = [omega(sel[j][1], sel[j + 1][1], n) for j in range(N - 1)]
    # the termwise inequality the whole lemma rests on
    for j in range(N - 1):
        if gaps[j] < oms[j]:
            bad.append(("g_j < omega_j", j, gaps[j], oms[j]))
    V = Phi(W, n)
    Wt = trim(W, n)
    # L1
    if not is_cover(V, n, alpha):
        bad.append("L1 Phi(W) is not a cover")
    # L2
    if len(Wt) != n + sum(gaps):
        bad.append(("L2 |W_trim| != n + sum g", len(Wt), n + sum(gaps)))
    if len(V) != n + sum(oms):
        bad.append(("L2 |Phi(W)| != n + sum omega", len(V), n + sum(oms)))
    if not (len(V) <= len(Wt) <= len(W)):
        bad.append(("L2 chain fails", len(V), len(Wt), len(W)))
    # L3 (rigidity)
    if len(V) == len(W) and V != W:
        bad.append("L3 equal length but a different word")
    if len(V) == len(W):
        if Wt != W:
            bad.append("L3 equal length but the word was trimmed")
        if gaps != oms:
            bad.append("L3 equal length but some gap exceeds omega")
    # trimming loses no permutation window
    if {w for _, w in perm_windows(W, n) if len(set(w)) == n} != \
       {w for _, w in perm_windows(Wt, n)}:
        bad.append("trimming lost a permutation window")
    return V, bad


def iterate(W, n, alpha):
    """Iterate to a fixed point, auditing every step and the L4 bound."""
    N = factorial(n)
    floor = N + n - 1
    lens, steps, bad = [len(W)], 0, []
    cur = W
    budget = len(W) - floor
    if len(W) < floor:
        bad.append(("length below the universal floor", len(W), floor))
    while True:
        V, b = step_audit(cur, n, alpha)
        bad += b
        if V is None:
            break
        if V == cur:
            break
        if len(V) >= len(cur):
            bad.append(("L4 a non-fixed step did not shorten the word",
                        len(cur), len(V)))
            break
        cur, steps = V, steps + 1
        lens.append(len(cur))
        if steps > budget + 1:
            bad.append(("L4 iteration bound exceeded", steps, budget))
            break
    return cur, lens, steps, bad


def audit_fixed_point(Ws, n, alpha):
    """Lemma 5 (a), (b), (c) and the trimming, checked literally."""
    bad = []
    N = factorial(n)
    sel = selected(Ws, n)
    if len(sel) != N:
        return ["not a cover"]
    # (a) the fixed point IS its own maximum-overlap spelling
    if Phi(Ws, n) != Ws:
        bad.append("L5a not a fixed point of Phi")
    # (b) every selected gap equals omega
    gaps = [sel[j + 1][0] - sel[j][0] for j in range(N - 1)]
    oms = [omega(sel[j][1], sel[j + 1][1], n) for j in range(N - 1)]
    if gaps != oms:
        bad.append("L5b a selected gap exceeds omega")
    if max(gaps) > n:
        bad.append(("L5b a gap exceeds n", max(gaps)))
    # (c) every non-selected permutation window is a repeat inside a connector
    starts = {i for i, _ in sel}
    pos = sorted(starts)
    reps = 0
    for i, w in perm_windows(Ws, n):
        if i in starts:
            continue
        reps += 1
        lo = max((p for p in pos if p < i), default=None)
        hi = min((p for p in pos if p > i), default=None)
        if lo is None or hi is None or not (lo < i < hi):
            bad.append(("L5c a repeat is not inside a connector", i))
        if w not in {x for _, x in sel}:
            bad.append(("L5c a repeat is not a selected permutation", i))
    # trimmed
    if sel[0][0] != 0 or sel[-1][0] + n != len(Ws):
        bad.append("not trimmed")
    return bad


# ------------------------------------------------------------------ corpus
def inflate(W, n, rng, prob=0.3):
    """Re-spell some selected connectors at the FULL gap n (always legal)."""
    sel = selected(W, n)
    out, widened = sel[0][1], 0
    for j in range(1, len(sel)):
        k = omega(sel[j - 1][1], sel[j][1], n)
        if rng.random() < prob and k < n:
            k, widened = n, widened + 1
        out += sel[j][1][n - k:]
    return out, widened


def pad(W, n, rng, alpha):
    """Junk letters inserted, and junk prefixes/suffixes (to exercise trim)."""
    w = W
    for _ in range(rng.randint(1, 3)):
        p = rng.randrange(len(w) + 1)
        w = w[:p] + "".join(rng.choice(alpha)
                            for _ in range(rng.randint(1, n))) + w[p:]
    if rng.random() < 0.5:
        w = "".join(rng.choice(alpha) for _ in range(rng.randint(1, 2 * n))) + w
    if rng.random() < 0.5:
        w = w + "".join(rng.choice(alpha) for _ in range(rng.randint(1, 2 * n)))
    return w


def main():
    t0 = time.time()
    rng = random.Random(162162)
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import run156 as R                                            # noqa: E402
    import passes156 as P3                                        # noqa: E402
    seeds = [(4, "1234", R.W4)]
    raw = json.loads((ROOT / "outputs" /
                      "rr_nr6_n5_minima_142.json").read_text())
    w5 = sorted({e["word"] for e in raw if isinstance(e, dict) and "word" in e})
    seeds += [(5, "01234", w) for w in w5]
    seeds += [(3, "123", w) for w in P3.n3_family()[:20]]
    W6 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    seeds += [(6, "123456", W6)]

    st, bad, traces = Counter(), [], []
    pool = []
    for n, alpha, W in seeds:
        pool.append((n, alpha, W, "seed"))
        for _ in range(60):
            V, wid = inflate(W, n, rng)
            if is_cover(V, n, alpha) and wid:
                pool.append((n, alpha, V, f"inflate{wid}"))
        for _ in range(60):
            V = pad(W, n, rng, alpha)
            if is_cover(V, n, alpha):
                pool.append((n, alpha, V, "pad"))
    for n, alpha, W, kind in pool:
        st["words"] += 1
        st[f"n{n}"] += 1
        st[f"kind_{kind[:7]}"] += 1
        Ws, lens, steps, b = iterate(W, n, alpha)
        b += audit_fixed_point(Ws, n, alpha)
        if not is_cover(Ws, n, alpha):
            b.append("the fixed point is not a cover")
        if len(Ws) > len(W):
            b.append("the fixed point is LONGER than the input")
        if b:
            st["failures"] += 1
            if len(bad) < 8:
                bad.append(dict(n=n, kind=kind, failures=[str(x)
                                                          for x in b][:4]))
        st["total_iterations"] += steps
        st["max_iterations"] = max(st["max_iterations"], steps)
        if steps:
            st["needed_iterations"] += 1
        if len(Ws) < len(W):
            st["strictly_shortened"] += 1
        if steps > 1:
            st["multi_step"] += 1
        if len(traces) < 6 and steps > 1:
            traces.append(dict(n=n, kind=kind, lengths=lens))
        # Phase 6: does one step change the SELECTED sequence?
        if kind != "seed":
            s0 = [w for _, w in selected(W, n)]
            V = Phi(W, n)
            if is_cover(V, n, alpha):
                s1 = [w for _, w in selected(V, n)]
                if s0 != s1:
                    st["one_step_changes_selected_sequence"] += 1
    out = dict(seconds=round(time.time() - t0, 1), stats=dict(st),
               traces=traces, failures=bad, ok=(st["failures"] == 0))
    (ROOT / "r162" / "certs" / "real_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "traces"},
                     ensure_ascii=False, indent=1)[:1800])
    for t in traces[:3]:
        print("  trace", json.dumps(t, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
