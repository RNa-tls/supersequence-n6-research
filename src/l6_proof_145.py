#!/usr/bin/env python3
"""L6 = 872 — the end-to-end verifier for the complete proof chain.

Runs every step and prints one verdict.  Each step is either an identity check,
a hand lemma verified literally, or an exhaustive (uncapped) search.  Nothing
is imported as an unverified fact, and NR6 is not used anywhere.

  STEP 1  Upper bound: the stored witness is a cover of length 872.
  STEP 2  Fixed representative: every cover has one, no longer (l6_fixed_representative_145).
  STEP 3  (FO)  L = 844 + G + S + H, by counting, checked on real words.
  STEP 4  Successor splicing: nu, beta, the catalogue (l6_splicing_145).
  STEP 5  Incidence:  K + R_int <= G+1,  K = G+1 (mod 2)  (l6_incidence_144).
  STEP 6  SAME-HEX:  D2 + Qs <= R_int, hence Z >= Qs >= 0 (l6_same_hex_145).
  STEP 7  Bookkeeping and MASTER-142  L = 867 + k + Z + H + B*  (l6_bookkeeping_144),
          and the CHAIN-level budgets derived and extracted literally
          (l6_extraction_145): sum P_i, sum D_i, sum tok_i = B* - sigma,
          blocks_i = O_i + tok_i, hex repeats <= R_int, chains <= d+1+h.
  STEP 8  Geometry: joint catalogue, companion hexagon, left S6 (l6_marked_capacity_144).
  STEP 9  Rows: every coordinate row with t <= 4 is strict, except two at t = 4
          (l6_rows_final_144), with no fallback and no unproved capacity cell.
  STEP 10 Those two rows: exhaustive equality-witness enumeration plus the
          pure-E-circuit coexistence test (l6_circuit_coexist_144, ..._check3_144).
  VERDICT L6 >= 872 from steps 2-10, L6 <= 872 from step 1.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
WIT = ROOT / "outputs" / "witness_144"
FULL = "--full" in sys.argv


def step1():
    W = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    alpha = sorted(set(W))
    need = {"".join(p) for p in itertools.permutations(alpha)}
    got = {W[i:i + 6] for i in range(len(W) - 5) if len(set(W[i:i + 6])) == 6}
    return dict(length=len(W), alphabet=len(alpha), windows=len(got),
                covers_all=got == need,
                ok=(len(W) == 872 and got == need and len(alpha) == 6))


def table_guard():
    """REFUSE to certify while the chain capacity tables stand refuted.

    ROUND 146.  This verifier's row step reads the cached capacity tables and
    believes them, so it happily reported `L6 = 872` after round 146 proved the
    chain table is NOT a valid upper bound (its pruning table collapsed
    per-split capacities under a combined-budget key and the loader took the
    minimum, so recorded capacities sit BELOW the truth).  A verifier that
    cannot fail on refuted input is not a check, so the guard below is now the
    first step: any cell whose table-free recheck beat the recorded value, or
    any recheck still missing, blocks the certificate.
    See research/ERRATA_146_CHAIN_UB.md.
    """
    rp = ROOT / "outputs" / "rr_l6_chain_recheck_146.json"
    hp = ROOT / "outputs" / "rr_l6_heavy_recheck_146.json"
    dp = ROOT / "outputs" / "rr_l6_chain_dependency_146.json"
    if not rp.exists():
        return dict(ok=False, reason="chain recheck has not been run at all")
    ch = json.loads(rp.read_text())
    hv = json.loads(hp.read_text()) if hp.exists() else {}
    need = {"%d|%d|%d|%d|%d" % tuple(c)
            for c in json.loads(dp.read_text())["cells"]} if dp.exists() else set()
    too_small = sorted(k for k, v in ch.items() if v.get("verdict") == "TOO_SMALL")
    too_small += sorted("heavy " + k for k, v in hv.items()
                        if v.get("verdict") == "TOO_SMALL")
    unresolved = sorted(k for k in need
                        if ch.get(k, {}).get("status") not in ("exact", "bound_below"))
    return dict(ok=not too_small and not unresolved,
                too_small=len(too_small), too_small_keys=too_small[:20],
                unresolved=len(unresolved), unresolved_keys=unresolved[:20],
                reason=("the chain capacity table is refuted: recorded "
                        "capacities are below the table-free truth"
                        if too_small else
                        "some load-bearing cell has no conclusive recheck"
                        if unresolved else "tables clear"))


def main():
    import l6_fixed_representative_145 as FR
    import l6_splicing_145 as SP
    import l6_same_hex_145 as SH
    import l6_incidence_144 as IN
    import l6_bookkeeping_144 as BK
    import l6_extraction_145 as EX
    import l6_marked_capacity_144 as MC
    import l6_coupled_144 as PIECE
    import l6_chain_rows_144 as CR
    import l6_871_analysis_144 as AN
    import l6_rows_final_144 as RF
    import l6_circuit_coexist_144 as CO
    import l6_coexist_check3_144 as CO3

    out = {}
    out["step0_tables_not_refuted"] = table_guard()
    out["step1_upper_bound"] = step1()

    fr = FR.run(n4=120 if not FULL else 400)
    out["step2_fixed_representative"] = dict(
        n4=fr["n4"], n5={k: fr["n5"][k] for k in ("minima", "failures",
                                                 "all_minima_already_fixed")},
        n6_witness_already_fixed=fr["n6_witness"]["already_fixed"],
        n6_witness_repeats=fr["n6_witness"]["audit"]["repeats"],
        ok=fr["all_ok"])

    out["step3_FO"] = dict(
        witness=fr["n6_witness_FO"],
        symbolic=(__import__("l6_master_identity_144")
                  .fo_identity_from_word_level()["mismatches"] == 0),
        ok=fr["n6_witness_FO"]["identity_holds"])

    sp = SP.run()
    out["step4_splicing"] = dict(
        n4=dict(ok=sp["n4_optimum"]["ok"], FO=sp["n4_optimum"]["FO_holds"]),
        n5=dict(count=sp["n5_minima"]["count"], ok=sp["n5_minima"]["all_ok"]),
        n6_witness={k: sp["n6_witness_872"][k] for k in
                    ("length", "P", "G", "O", "k", "S", "H", "D2", "Qs", "K",
                     "R_int", "c", "d", "g", "Z", "Bstar", "MASTER",
                     "MASTER_holds", "types")},
        ok=sp["all_ok"])

    inc = IN.check(3000 if not FULL else 8000)
    out["step5_incidence"] = dict(trials=inc["trials"],
                                 bound_violations=inc["bound_violations"],
                                 parity_violations=inc["parity_violations"],
                                 witness_tight=(sp["n6_witness_872"]["K"] +
                                                sp["n6_witness_872"]["R_int"] ==
                                                sp["n6_witness_872"]["G"] + 1),
                                 ok=inc["holds"])

    sh = SH.run(tries4=200 if not FULL else 600)
    out["step6_same_hex"] = dict(n4=sh["n4"], n5=sh["n5"], nfail=sh["nfail"],
                                ok=sh["ok"])

    bk = BK.check(50000 if not FULL else 200000)
    ex = EX.run(tries4=80 if not FULL else 300, tries5=40 if not FULL else 150)
    out["step7_bookkeeping"] = dict(
        symbolic=dict(trials=bk["trials"], violations=bk["violations"],
                      holds=bk["holds"]),
        extraction=dict(
            n6_witness={k: ex["n6_witness_872"][k] for k in
                        ("chains", "sum_P", "sum_D", "sum_tok", "sigma",
                         "blocks", "Bstar", "hex_repeats", "chain_sizes")},
            n5_minima_ok=ex["n5_minima"]["all_ok"],
            n4_sweep=ex["n4_sweep"], n5_sweep=ex["n5_sweep"], ok=ex["ok"]),
        ok=bk["holds"] and ex["ok"])

    out["step8_geometry"] = dict(
        joint_catalogue=MC.catalogue_check()["holds"],
        companion_hex=MC.companion_lemma()["holds"],
        left_S6=MC.s6_symmetry()["holds"],
        ok=all([MC.catalogue_check()["holds"], MC.companion_lemma()["holds"],
                MC.s6_symmetry()["holds"]]))

    PIECE.load_caps()
    CR.load_cache()
    AN.load_h()
    rows, survivors = {}, []
    for t in range(0, 5):
        r = RF.run(t, allow_compute=False)
        rows[f"L{867 + t}"] = dict(coordinate_rows=r["coordinate_rows"],
                                   strict=r["strict"], surviving=r["surviving"],
                                   fallback=r["surviving_with_fallback"])
        if t == 4:
            survivors = r["survivors"]
    out["step9_rows"] = dict(
        table=rows,
        t_le_3_all_strict=all(rows[f"L{867 + t}"]["surviving"] == 0
                              for t in range(0, 4)),
        t4_surviving=rows["L871"]["surviving"],
        t4_no_fallback=rows["L871"]["fallback"] == 0,
        survivors=[{k: x[k] for k in ("k", "Z", "H", "Bstar", "G", "c", "d",
                                      "D2", "h", "required", "bound")}
                   for x in survivors],
        ok=(all(rows[f"L{867 + t}"]["surviving"] == 0 for t in range(0, 4))
            and rows["L871"]["surviving"] == 2
            and rows["L871"]["fallback"] == 0))

    eq = {}
    for tag, c in (("wit_Q1.jsonl", 6), ("wit_Q2.jsonl", 7)):
        chains = [json.loads(l)["ports"]
                  for l in (WIT / tag).read_text().splitlines() if l.strip()]
        d1 = [CO.coexist(ch, c) for ch in chains]
        d3 = [CO3.solve(ch, c) for ch in chains]
        nub = WIT / tag.replace(".jsonl", "_noub.jsonl")
        same = None
        if nub.exists():
            other = [json.loads(l)["ports"]
                     for l in nub.read_text().splitlines() if l.strip()]
            same = sorted(map(tuple, chains)) == sorted(map(tuple, other))
        eq[tag] = dict(c=c, witnesses=len(chains),
                       independent_enumeration_agrees=same,
                       dfs_solver_finds_any=any(x["ok"] for x in d1),
                       subset_solver_finds_any=any(x["ok"] for x in d3),
                       excluded=not (any(x["ok"] for x in d1)
                                     or any(x["ok"] for x in d3)))
    out["step10_equality_rows"] = dict(
        detail=eq, ok=all(v["excluded"] for v in eq.values()))

    lower = all(out[k]["ok"] for k in
                ("step0_tables_not_refuted",
                 "step2_fixed_representative", "step3_FO", "step4_splicing",
                 "step5_incidence", "step6_same_hex", "step7_bookkeeping",
                 "step8_geometry", "step9_rows", "step10_equality_rows"))
    upper = out["step1_upper_bound"]["ok"]
    out["verdict"] = dict(
        lower_bound_L6_ge_872=lower, upper_bound_L6_le_872=upper,
        L6_equals_872=(lower and upper),
        uses_NR6=False,
        statement=("Every n=6 covering word has length at least 872, and a "
                   "covering word of length 872 exists; hence L6 = 872.")
        if (lower and upper) else
        ("NOT ESTABLISHED -- the chain capacity tables step 9 reads are "
         "refuted (research/ERRATA_146_CHAIN_UB.md).  What survives: "
         "L6 >= 870 by the piece model alone and L6 <= 872 by the witness, "
         "so L6 is in {870, 871, 872}."
         if not out["step0_tables_not_refuted"]["ok"] else "NOT ESTABLISHED"))
    return out


if __name__ == "__main__":
    r = main()
    (ROOT / "outputs" / "rr_l6_proof_145.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=1))
    for k, v in r.items():
        if k == "verdict":
            continue
        print(k, "->", "OK" if v.get("ok") else "FAIL")
    print()
    print(json.dumps(r["verdict"], ensure_ascii=False, indent=1))
