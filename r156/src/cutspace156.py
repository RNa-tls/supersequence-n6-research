#!/usr/bin/env python3
"""Round 156 Phase 5 -- the CUT is the load-bearing step, so enumerate it.

Three things are established here, on real fixed representatives:

 (A) EXHAUSTIVE over opening choices.  For every cover whose extraction has
     d >= 1 non-pure, non-dummy beta components, every combination of
     admissible (= non clean-E) opening edges is tried, in both heavy modes.
     Claims 1-5, the chain count and the whole model feed must hold for ALL
     of them -- the theorem may not depend on which edge the cycle is cut at.

 (B) NEGATIVE CONTROL.  Opening a cycle at a clean-E edge instead is tried on
     the same covers.  The audit records exactly which claim then breaks; if
     nothing broke, the "no clean E edge is ever cut" hypothesis would be
     decorative rather than load-bearing.

 (C) ARBITRARY EXTRA CUTS.  Claim 5 (within-chain hexagon repeats <= R_int) is
     claimed for the specific cut.  Here it is tested against arbitrary extra
     cut sets, to see whether it is a property of the cut or of subpaths.
"""
from __future__ import annotations
import itertools, json, random, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract156 as X                                            # noqa: E402
import corpus156 as C                                             # noqa: E402
import run156 as R                                                # noqa: E402

CAP = 4096          # per-word ceiling on enumerated opening combinations


def opening_candidates(st):
    comps = X.components(st["beta"])
    dummy, etype = st["dummy"], st["etype"]
    pure = [c for c in comps if dummy not in c
            and all(etype.get(x) == "E" for x in c)]
    cand, ecand = [], []
    for c in comps:
        if dummy in c or c in pure:
            continue
        cand.append([x for x in c if etype.get(x) not in (None, "E")])
        ecand.append([x for x in c if etype.get(x) == "E"])
    return cand, ecand


def exhaustive(st, stats, bad):
    cand, _ = opening_candidates(st)
    if not cand:
        return 0
    total = 1
    for c in cand:
        total *= len(c)
    combos = itertools.product(*cand)
    if total > CAP:
        rng = random.Random(7)
        combos = (tuple(rng.choice(c) for c in cand) for _ in range(CAP))
        stats["words_sampled"] += 1
    else:
        stats["words_exhaustive"] += 1
    stats["combination_space"] += total
    done = 0
    for combo in combos:
        for kh in (False, True):
            r = X.extract(st, keep_heavy=kh, forced_openings=list(combo))
            stats["runs"] += 1
            done += 1
            if not r["ok"]:
                stats["failures"] += 1
                if len(bad) < 10:
                    bad.append(dict(keep_heavy=kh, failures=r["failures"][:6]))
    return done


def negative_control(st, stats, tally):
    """Open at a clean-E edge and record which claim breaks."""
    cand, ecand = opening_candidates(st)
    if not cand or not all(ecand):
        return
    for kh in (False, True):
        combo = [c[0] for c in ecand]
        r = X.extract(st, keep_heavy=kh, forced_openings=combo)
        stats["neg_runs"] += 1
        if r["ok"]:
            stats["neg_undetected"] += 1
        else:
            stats["neg_detected"] += 1
            for f in r["failures"]:
                tally[f[0] if isinstance(f, tuple) else str(f)] += 1


def arbitrary_cuts(st, rng, stats):
    """Claim 5 against arbitrary extra cut sets (subpath monotonicity)."""
    beta, dummy, P = st["beta"], st["dummy"], st["P"]
    hexr = st["hexr"]
    comps = X.components(beta)
    R_int = 0
    for c in comps:
        cnt = Counter(hexr[x] for x in c if x != dummy)
        R_int += sum(v - 1 for v in cnt.values())
    for _ in range(12):
        cut = {x for x in range(P) if rng.random() < rng.choice((.1, .3, .6))}
        succ = {}
        for x in range(P):
            if x in cut:
                continue
            y = beta[x]
            if y != dummy:
                succ[x] = y
        indeg = Counter(succ.values())
        starts = [x for x in range(P) if not indeg.get(x)]
        seen, rep = set(), 0
        for s in starts:
            ch, x = [], s
            while True:
                ch.append(x)
                seen.add(x)
                if x not in succ:
                    break
                x = succ[x]
            rep += len(ch) - len({hexr[y] for y in ch})
        stats["arb_runs"] += 1
        if len(seen) != P:                      # a beta cycle survived uncut
            stats["arb_cycle_left"] += 1
            continue
        if rep > R_int:
            stats["arb_failures"] += 1


def main():
    t0 = time.time()
    rng = random.Random(4242)
    stats, bad, tally = Counter(), [], Counter()
    ws, w5 = R.words()
    pool = [(n, W) for _, n, W in ws]
    pool += [(4, w) for w in C.corpus(4, "1234", [R.W4], rng, 700)]
    pool += [(5, w) for w in C.corpus(5, "01234", w5, rng, 300)]
    for n, W in pool:
        st = X.structure(W, n)
        exhaustive(st, stats, bad)
        negative_control(st, stats, tally)
        arbitrary_cuts(st, rng, stats)
    out = dict(seconds=round(time.time() - t0, 1), words=len(pool),
               cap_per_word=CAP, stats=dict(stats), bad=bad,
               negative_control_breaks=dict(tally.most_common()),
               ok=(stats["failures"] == 0 and stats["arb_failures"] == 0
                   and stats["neg_undetected"] == 0))
    (ROOT / "r156" / "certs" / "cutspace_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2500])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
