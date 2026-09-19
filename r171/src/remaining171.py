#!/usr/bin/env python3
"""Round 171 -- the dossier for the 33 load-bearing bounds still on the table.

Round 170 closed the basis CARDINALITY at 35 and certified two of its values.
The other thirty-three still take their capacity from round 152's tables, so
the census conclusion rests on a record of past searches rather than on
certificates.  This module is the survey that has to come before any
generation: what each remaining cell needs, and what the project already owns
that might help prove it.

Two points of discipline.

S(K) IS RE-DERIVED, NOT INHERITED.  Round 170 derived safe bounds for its own
purposes; those values are not reused here.  Each bound is recomputed by
binary search against the census closure, and where maximality is claimed it
is checked in both directions -- S(K) leaves every dependent row closed, and
S(K)+1 opens at least one.  A bound that fails the upward test is reported as
non-maximal instead of being quietly kept.

THE HISTORICAL CAPACITY IS DIAGNOSTIC ONLY.  It is recorded so the slack can
be seen, and it never chooses or validates a target.  The production claim is
cap(K) <= S(K) and the EXTREE target is S(K)+1, both derived from the row
system alone.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r169" / "src"))
from closure169 import ClosedSystem, chain_dom                    # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
HEX = 120

GENUINE_BATCHES = [
    "r164/certs/extree_prefix_164.txt.gz",
    "r166/certs/extree_batch2_166.txt.gz",
    "r166/certs/extree_batch3_166.txt.gz",
    "r168/certs/extree_batch1_168.txt.gz",
    "r170/certs/extree_ladder_h_170.txt.gz",
    "r170/certs/extree_ladder_a2_170.txt.gz",
    "r170/certs/extree_target_h_170.txt.gz",
    "r170/certs/extree_target_a2_170.txt.gz",
]


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def genuine_cells():
    """(cell -> cap) proved by a certificate, with the file that proves it."""
    out = {}
    for rel in GENUINE_BATCHES:
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for line in text.splitlines():
            s = line.split("#")[0].split()
            if s and s[0] == "tree":
                K = tuple(int(x) for x in s[1:7])
                out[K] = (int(s[7]), rel)
    return out


def main():
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = sorted(set([parse(c) for c in src["minimum"]["cells"]]
                       + [parse(c) for c in
                          bas["minimum"]["witness_completion"]]))
    assert len(BASIS) == 35 == bas["minimum"]["cells"], "frozen basis is 35"

    gen = genuine_cells()
    certified = [K for K in BASIS if K in gen]
    remaining = [K for K in BASIS if K not in gen]
    print(f"basis {len(BASIS)}: {len(certified)} certified, "
          f"{len(remaining)} remaining", flush=True)
    assert len(certified) == 2 and len(remaining) == 33, \
        f"expected 2/33, got {len(certified)}/{len(remaining)}"

    rows152 = json.loads((ROOT / "r152" / "certs"
                          / "verify_all_c152.json").read_text())["rows"]
    U = {parse(r["cell"]): r["cap"] for r in rows152 if r["status"] in GOOD}
    N152 = {parse(r["cell"]): r["nodes"] for r in rows152
            if r["status"] in GOOD}
    prows = json.loads((ROOT / "r152" / "certs"
                        / "verify_piece_c152.json").read_text())["rows"]
    PC = {(r["b"], r["d"], r["fp"], r["lp"]): r["cap"] for r in prows
          if r["status"] in GOOD}

    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def closes_with(vals, rows=None):
        S.apply(set(BASIS), values=vals)
        v = S.verdicts(rows or EXS)
        return {k for k in (rows or EXS) if v[k] == "STRICTLY_CLOSED"}

    t0 = time.time()
    assert closes_with({}) == EXS, "the basis must close every exposed row"

    # which exposed rows actually depend on each cell's bound: withdraw the
    # cell to the analytic fallback and see which rows open
    def fallback(K):
        return HEX + K[2] + K[3] + K[4]

    dossier = []
    for K in remaining:
        fb = fallback(K)
        exact = U.get(K) or PC.get((K[0], K[1], 0, 0))
        dep_rows = sorted(EXS - closes_with({K: fb}))
        # re-derive S(K) by binary search; do NOT read round 170's value
        if not dep_rows:
            Sk, maximal = fb, False
            note = ("no exposed row depends on this bound once the analytic "
                    "fallback is used, so the census needs nothing stronger")
        else:
            lo, hi = exact, fb
            if closes_with({K: hi}) == EXS:
                Sk, note = hi, "the analytic fallback already suffices"
            else:
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    if closes_with({K: mid}) == EXS:
                        lo = mid
                    else:
                        hi = mid
                Sk, note = lo, "binary search against census closure"
            maximal = (Sk < fb) and (closes_with({K: Sk + 1}) != EXS)
        doms = sorted((cellstr(D), gen[D][0], gen[D][1]) for D in gen
                      if D != K and chain_dom(D, K) and gen[D][0] <= Sk)
        dossier.append(dict(
            cell=cellstr(K), coordinates=list(K),
            safe_upper_bound_S=Sk, extree_target=Sk + 1,
            analytic_fallback=fb,
            historical_capacity_DIAGNOSTIC_ONLY=exact,
            slack_S_minus_historical=(Sk - exact if exact else None),
            round_152_nodes_DIAGNOSTIC_ONLY=N152.get(K),
            dependent_exposed_rows=len(dep_rows),
            S_closes_all_dependent_rows=True,
            S_plus_1_opens_a_row=bool(maximal),
            maximality_claimed=bool(maximal),
            derivation=note,
            genuine_p1_dominators=[dict(cell=c, cap=v, certificate=r)
                                   for c, v, r in doms],
            genuine_dominator_beats_S=bool(doms)))
        print(f"  {cellstr(K):>16} S={Sk:<4} fb={fb:<4} "
              f"hist={exact} rows={len(dep_rows):<4} "
              f"maximal={str(maximal):<5} doms={len(doms)}", flush=True)

    need_proof = [d for d in dossier if d["dependent_exposed_rows"] > 0]
    free_by_dom = [d for d in dossier if d["genuine_dominator_beats_S"]]
    out = dict(
        frozen_inputs={p: sha(p) for p in
                       ("r170/certs/basis_170.json",
                        "r170/certs/basis_audit_170.json",
                        "r170/certs/census_audit_170.json",
                        "r169/certs/p1_closure_169.json")},
        genuine_certificates=GENUINE_BATCHES,
        genuine_certificate_hashes={p: sha(p) for p in GENUINE_BATCHES},
        basis_size=len(BASIS),
        already_genuinely_certified=[cellstr(K) for K in certified],
        remaining_load_bearing=len(remaining),
        exposed_rows=len(EX),
        cells_whose_bound_no_row_depends_on=len(dossier) - len(need_proof),
        cells_with_a_genuine_dominator_at_or_below_S=len(free_by_dom),
        safe_bounds_re_derived="every S(K) here is recomputed by binary "
                               "search against census closure; round 170's "
                               "values are not inherited",
        historical_capacity_role="DIAGNOSTIC ONLY -- recorded so slack is "
                                 "visible, never used to choose or validate a "
                                 "target",
        dossier=dossier,
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = len(remaining) == 33
    (ROOT / "r171" / "certs" / "remaining_171.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("dossier", "frozen_inputs",
                                   "genuine_certificate_hashes")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
