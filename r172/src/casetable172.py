#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- the finite case table behind the R1 accounting
identities (r172/THEOREM_R1.md, Lemma 2).

Part 1 (the proof object).  Every suffix move of a walk W, split at port
w_m, is compared with the same move read in the standalone suffix S.  A move
is determined, for accounting purposes, by

    kind     in {E, A, B, P, H}
    orbit    fresh in W? fresh in S?      (S's history is a sub-history of W's)
    hexagon  new in W?   new in S?
    current  is the target orbit the current orbit?   (E is legal only then)

The charging rules of the model (r149/PROOF.md 2.2-2.3, repeated in every
generator and verifier) are the only input:

    token  c  = 0 if kind == E or orbit fresh, else 1
    deficit   = +4 if orbit fresh, else -1
    e charge  = 1 if hexagon not new and kind not in {A, B}, else 0
    a, bb, h  = [kind == A], [kind == B], cost * [kind == H]

The table lists every combination, marks the impossible ones with the reason,
and for every possible one checks, per move,

    (c_W - c_S, def_S - def_W) == (1, 5) if the row is a FIRST RE-ENTRY into
                                          a non-current prefix orbit
                                  (0, 0) otherwise
    e_W - e_S in {0, 1}          a, bb, h equal in W and S.

Part 2 (regression, not proof).  Random legal walks over the Round 164
geometry; every suffix move is classified into a row, and the engine's own
flags (fresh / new hexagon / c / se, as computed by the move rules used by
gen168 and both verifiers) must match that row's deltas.  Per-row coverage is
reported.  The Round-172 randomized split-point identity check is re-run too.
"""
from __future__ import annotations
import itertools, json, random, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "r172" / "certs" / "case_table_R1.json"

KINDS = ("E", "A", "B", "P", "H")
# orbit status: (fresh_W, fresh_S, current, label)
ORBIT = [
    (True, True, False, "fresh-orbit entry (orbit untouched by W so far)"),
    (False, False, True, "current-orbit continuation (target orbit = current orbit)"),
    (False, False, False, "return to an orbit already touched in the suffix "
                          "(incl. c0, and repeated re-entry of a prefix orbit)"),
    (False, True, False, "FIRST re-entry of a non-current prefix orbit"),
    (True, False, False, "IMPOSSIBLE: S's history is contained in W's"),
    (True, True, True, "IMPOSSIBLE: the current orbit is touched in S"),
    (False, True, True, "IMPOSSIBLE: the current orbit is touched in S"),
    (True, False, True, "IMPOSSIBLE: S's history is contained in W's"),
]
HEXS = [(True, True), (False, False), (False, True), (True, False)]


def charge(kind, fresh, newhex, cost=1):
    c = 0 if (kind == "E" or fresh) else 1
    dd = 4 if fresh else -1
    e = 1 if (not newhex and kind not in ("A", "B")) else 0
    return dict(c=c, deficit=dd, e=e, a=int(kind == "A"), bb=int(kind == "B"),
                h=cost if kind == "H" else 0)


def table():
    rows = []
    for kind, (fw, fs, cur, olab), (hw, hs) in itertools.product(
            KINDS, ORBIT, HEXS):
        row = dict(kind=kind, orbit=olab, fresh_W=fw, fresh_S=fs,
                   current=cur, newhex_W=hw, newhex_S=hs)
        why = None
        if olab.startswith("IMPOSSIBLE"):
            why = olab
        elif hw and not hs:
            why = "IMPOSSIBLE: a hexagon new to W is new to S (S's history is contained in W's)"
        elif kind == "E" and not cur:
            why = "IMPOSSIBLE: an E move stays in the current orbit (legality rule)"
        if why:
            row.update(possible=False, reason=why)
            rows.append(row)
            continue
        w, s = charge(kind, fw, hw), charge(kind, fs, hs)
        first = (not fw) and fs
        row.update(possible=True, W=w, S=s, first_reentry=first,
                   dtok=w["c"] - s["c"], ddef=s["deficit"] - w["deficit"],
                   de=w["e"] - s["e"])
        ok = ((row["dtok"], row["ddef"]) == ((1, 5) if first else (0, 0))
              and row["de"] in (0, 1)
              and all(w[k] == s[k] for k in ("a", "bb", "h")))
        row["identity_holds"] = ok
        rows.append(row)
    return rows


# ------------------------------------------------------------- part 2
def regression(trials=3000, seed=172):
    sys.path.insert(0, str(ROOT / "r164" / "src"))
    import routeb164 as R
    rng = random.Random(seed)
    rows = [r for r in table() if r["possible"]]
    idx = {(r["kind"], r["fresh_W"], r["fresh_S"], r["current"],
            r["newhex_W"], r["newhex_S"]): i for i, r in enumerate(rows)}
    cover = Counter()
    mismatch = 0
    split_points = split_rp = ident_viol = 0
    for _ in range(trials):
        b = rng.choice([1, 2, 3])
        amax, bmax, emax, hmax = (rng.randint(0, 4), rng.randint(0, 2),
                                  rng.randint(0, 3), rng.randint(0, 3))
        v = 0
        phm = {R.ORB[0]: {R.PHASE[0]}}
        hexc = {R.HEX[0]}
        corb, tok, au, bu, eu, hu, deficit = R.ORB[0], b, 0, 0, 0, 0, 4
        walk = [dict(t=0, kind=None, c=0, se=0, fresh=True, newhex=True)]
        for _step in range(rng.randint(20, 90)):
            ms = []
            for t, kind, cost in R.MOVES[v]:
                q = R.ORB[t]
                ph = phm.get(q)
                if ph is not None and R.PHASE[t] in ph:
                    continue
                if kind == "E" and q != corb:
                    continue
                if kind == "A" and au >= amax:
                    continue
                if kind == "B" and bu >= bmax:
                    continue
                if kind == "H" and hu + cost > hmax:
                    continue
                newhex = R.HEX[t] not in hexc
                se = 0
                if not newhex and kind not in ("A", "B"):
                    if eu >= emax:
                        continue
                    se = 1
                fresh = ph is None
                c = 0 if (kind == "E" or fresh) else 1
                if c > tok:
                    continue
                ms.append((t, kind, cost, fresh, newhex, se, c))
            if not ms:
                break
            t, kind, cost, fresh, newhex, se, c = rng.choice(ms)
            q = R.ORB[t]
            phm.setdefault(q, set()).add(R.PHASE[t])
            hexc.add(R.HEX[t])
            tok -= c
            au += kind == "A"
            bu += kind == "B"
            eu += se
            hu += cost if kind == "H" else 0
            deficit += 4 if fresh else -1
            walk.append(dict(t=t, kind=kind, c=c, se=se, fresh=fresh,
                             newhex=newhex, cur=(q == corb)))
            v, corb = t, q
        final = deficit
        n = len(walk)
        for m in range(n):
            # prefix state at w_m
            porb, phex, D = set(), set(), 0
            for i in range(m + 1):
                q = R.ORB[walk[i]["t"]]
                D += -1 if q in porb else 4
                porb.add(q)
                phex.add(R.HEX[walk[i]["t"]])
            c0 = R.ORB[walk[m]["t"]]
            s_orb, s_hex = {c0}, {R.HEX[walk[m]["t"]]}
            s_tok = s_e = 0
            s_def = 4
            w_tok = w_e = 0
            reentered = set()
            for i in range(m + 1, n):
                st = walk[i]
                q, hx = R.ORB[st["t"]], R.HEX[st["t"]]
                fs = q not in s_orb
                hs = hx not in s_hex
                key = (st["kind"], st["fresh"], fs, st["cur"], st["newhex"], hs)
                if key not in idx:
                    mismatch += 1
                else:
                    row = rows[idx[key]]
                    cover[idx[key]] += 1
                    sc = charge(st["kind"], fs, hs)
                    if (row["W"]["c"], row["W"]["e"]) != (st["c"], st["se"]) \
                            or (row["S"]["c"], row["S"]["e"]) != (sc["c"], sc["e"]):
                        mismatch += 1
                if (not st["fresh"]) and fs and q != c0:
                    reentered.add(q)
                s_tok += 0 if (st["kind"] == "E" or fs) else 1
                s_e += 1 if (not hs and st["kind"] not in ("A", "B")) else 0
                s_def += 4 if fs else -1
                s_orb.add(q)
                s_hex.add(hx)
                w_tok += st["c"]
                w_e += st["se"]
            rp = len(reentered)
            split_points += 1
            split_rp += rp > 0
            if not (s_def == final - D + 4 + 5 * rp and s_tok + rp == w_tok
                    and s_e <= w_e):
                ident_viol += 1
    return dict(trials=trials, seed=seed,
                row_coverage={i: cover[i] for i in range(len(rows))},
                rows_never_realised=[i for i in range(len(rows)) if not cover[i]],
                classification_or_flag_mismatches=mismatch,
                split_points=split_points, split_points_with_r_ge_1=split_rp,
                identity_violations=ident_viol)


def main():
    rows = table()
    poss = [r for r in rows if r["possible"]]
    reg = regression()
    out = dict(title="R1 per-move accounting case table (THEOREM_R1 Lemma 2)",
               rows_total=len(rows), rows_possible=len(poss),
               rows_impossible=len(rows) - len(poss),
               all_possible_rows_satisfy_identity=all(r["identity_holds"] for r in poss),
               first_reentry_rows=sum(r["first_reentry"] for r in poss),
               table=rows, regression_not_proof=reg)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "table"}, indent=1))
    return 0 if out["all_possible_rows_satisfy_identity"] and \
        reg["identity_violations"] == 0 and \
        reg["classification_or_flag_mismatches"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
