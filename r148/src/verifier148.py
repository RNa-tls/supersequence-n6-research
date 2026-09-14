#!/usr/bin/env python3
"""Round 148 Phase 5/6 -- the FAIL-CLOSED master verifier.

It proves nothing by itself.  It re-reads every committed load-bearing artifact,
checks it against the conditions the proof needs, and REFUSES to certify unless
all of them hold.  Every check is written so that the absence of evidence is a
failure, never a pass:

  C1  cell ledgers: every cell EXACT_UNCAPPED, none capped, none ERROR, and the
      set of cells covers the load-bearing set with nothing missing
  C2  capacity monotonicity in every proved direction, and the analytic bound
  C3  implementation B agrees on every load-bearing cell, with no TIMEOUT
  C4  the pruning-table format is fail-closed (the loader rejects each of the
      malformed families, including the round-144/145 files verbatim)
  C5  rows regenerated from the definitions agree with the independent
      enumeration and the archive profiles
  C6  L <= 869 closed by the piece model alone
  C7  L = 870 has zero non-strict rows
  C8  L = 871 has exactly two equality rows and no other survivor
  C9  both equality rows enumerated exhaustively by BOTH routes, one of them
      with NO pruning table, with identical canonical witness sets
  C10 every equality witness excluded by at least two coexistence solvers,
      each with a positive control
  C11 the length-872 witness is a genuine cover
  C12 source and executable hashes recorded for every searcher used

Usage:  python3 r148/src/verifier148.py [--json]
Exit 0 only when every check passes.
"""
from __future__ import annotations
import hashlib, itertools, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
CHECKS = []


def check(name, ok, detail=None):
    CHECKS.append(dict(check=name, ok=bool(ok), detail=detail))
    return bool(ok)


def jload(p):
    p = Path(p)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return dict(__unparseable__=repr(e)[:120])


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main(argv):
    # ---- C1 cell ledgers
    ch = jload(R147 / "tables" / "chain_cells_147.json")
    hv = jload(R147 / "tables" / "heavy_cells_147.json")
    lb = jload(R147 / "tables" / "loadbearing_cells_147.json")
    if ch is None or hv is None or lb is None:
        check("C1_ledgers_present", False, "a ledger file is missing")
    else:
        bad = {k: v.get("status") for d in (ch, hv) for k, v in d.items()
               if v.get("status") != "EXACT_UNCAPPED"}
        capped = [k for d in (ch, hv) for k, v in d.items() if v.get("capped")]
        have = set(ch) | set(hv)
        need = {"|".join(map(str, c)) for c in lb["cells"]}
        missing = sorted(need - have)
        check("C1_all_cells_exact_uncapped", not bad and not capped,
              dict(non_exact=bad, capped=capped,
                   chain=len(ch), heavy=len(hv)))
        check("C1_no_load_bearing_cell_missing", not missing,
              dict(load_bearing=len(need), missing=missing[:8]))
    # ---- C2 monotonicity, RECOMPUTED here from the ledgers.
    # Reading the stored certificate would make the verifier blind to a
    # mutation of the underlying data, so the invariant is re-derived.
    cells = {}
    for d in (ch or {}), (hv or {}):
        for k, v in d.items():
            if v.get("status") == "EXACT_UNCAPPED":
                cells[tuple(int(x) for x in k.split("|"))] = v["cc"]
    viol, anal = [], []
    for K, cc in cells.items():
        if cc > 120 + K[2] + K[3] + K[4]:
            anal.append(dict(cell=list(K), cc=cc))
        for i in range(6):
            lo = list(K)
            lo[i] -= 1
            lo = tuple(lo)
            if lo in cells and cells[lo] > cc:
                viol.append(dict(lower=list(lo), upper=list(K),
                                 cc_lower=cells[lo], cc_upper=cc))
    check("C2_monotonicity_and_analytic_bound_recomputed",
          not viol and not anal and len(cells) == 1101,
          dict(cells=len(cells), monotonicity_violations=len(viol),
               analytic_violations=len(anal), examples=(viol + anal)[:4]))
    stored_mono = jload(R147 / "certs" / "monotonicity_147.json")
    check("C2b_stored_monotonicity_certificate_agrees",
          bool(stored_mono) and stored_mono.get("ok")
          and stored_mono.get("cells") == len(cells),
          {k: v for k, v in (stored_mono or {}).items() if k != "examples"})
    # ---- C3 implementation B
    b = jload(R147 / "certs" / "second_impl_147.json")
    check("C3_implementation_B_agrees_everywhere",
          bool(b) and b.get("ok") and not b.get("disagreeing")
          and not b.get("timeouts")
          and b.get("agreeing") == b.get("cells_total"),
          {k: v for k, v in (b or {}).items() if k != "cells"})
    # ---- C4 fail-closed loader
    fc = jload(R147 / "certs" / "failclosed_147.json")
    check("C4_loader_fails_closed", bool(fc) and fc.get("ok"),
          {k: v for k, v in (fc or {}).items() if k != "cases"})
    # ---- C5 rows from definitions
    rg = jload(R147 / "rows" / "rows_regenerated_147.json")
    ar = jload(R147 / "certs" / "rows_vs_archive_147.json")
    check("C5_rows_from_definitions", bool(rg) and rg.get("all_agree")
          and bool(ar) and ar.get("all_ok"),
          dict(layers={k: v.get("coordinate_groups")
                       for k, v in (rg or {}).get("layers", {}).items()},
               archive_profiles=(ar or {}).get("profiles"),
               archive_words=(ar or {}).get("words")))
    # ---- C6 L <= 869 by the piece model alone
    p870 = jload(R147 / "certs" / "piece_only_870_147.json")
    check("C6_L869_closed_by_piece_model_alone", bool(p870) and p870.get("ok"),
          {k: dict(rows=v["rows"], closed=v["closed_by_piece"])
           for k, v in (p870 or {}).get("layers", {}).items()})
    # ---- C7/C8 fresh censuses
    cen = jload(R148 / "rows" / "census_148.json")
    lay = (cen or {}).get("layers", {})
    t870 = lay.get("L870", {}).get("tally", {})
    t871 = lay.get("L871", {}).get("tally", {})
    check("C7_L870_zero_non_strict",
          bool(t870) and set(t870) == {"STRICTLY_CLOSED"}
          and t870["STRICTLY_CLOSED"] == lay["L870"]["rows"] == 353,
          dict(tally=t870, rows=lay.get("L870", {}).get("rows"),
               closed_by=lay.get("L870", {}).get("closed_by")))
    check("C8_L871_exactly_two_equality_rows",
          bool(t871) and set(t871) == {"STRICTLY_CLOSED", "EQUALITY"}
          and t871.get("EQUALITY") == 2
          and t871.get("STRICTLY_CLOSED") == 1154
          and lay["L871"]["rows"] == 1156,
          dict(tally=t871, rows=lay.get("L871", {}).get("rows"),
               closed_by=lay.get("L871", {}).get("closed_by")))
    # ---- C9/C10 equality witnesses
    w = jload(R148 / "certs" / "witnesses_148.json")
    rows = (w or {}).get("rows", [])
    routes_ok = bool(rows) and all(
        r["route_table"]["status"] == "EXHAUSTIVE"
        and r["route_notable"]["status"] == "EXHAUSTIVE"
        and not r["route_table"]["capped"] and not r["route_notable"]["capped"]
        and r["routes_agree"] for r in rows)
    check("C9_equality_witnesses_enumerated_both_routes_one_without_table",
          routes_ok,
          [dict(row=r["name"], table=dict(w=r["route_table"]["witnesses"],
                                          cls=r["route_table"]["classes"],
                                          nodes=r["route_table"]["nodes"]),
                notable=dict(w=r["route_notable"]["witnesses"],
                             cls=r["route_notable"]["classes"],
                             nodes=r["route_notable"]["nodes"]),
                same_sha=r["routes_agree"]) for r in rows])
    have_certs = bool(rows) and all(r.get("certificates") for r in rows)
    excl = have_certs and all(r.get("all_excluded") for r in rows)
    ctrl = have_certs and all(r.get("controls_ok") for r in rows)
    check("C10_coexistence_certificates_present", have_certs,
          dict(rows=len(rows),
               with_certificates=sum(1 for r in rows if r.get("certificates"))))
    check("C10_all_equality_witnesses_excluded", excl,
          [dict(row=r["name"],
                verdicts=[dict(bfs=c["solver_bfs"]["coverable"],
                               dfs=c["solver_dfs"]["ok"],
                               subset=c["solver_subset"]["ok"],
                               min_orbits=c["solver_bfs"]["min_orbits"])
                          for c in r.get("certificates", [])]) for r in rows])
    check("C10_positive_controls_present", ctrl,
          [dict(row=r["name"], controls=r.get("controls")) for r in rows])
    # ---- C13 the equality cells carry exactly the required port count, read
    # straight out of the ledger (a mutated capacity breaks this immediately)
    eq = {(0, 14, 0, 0, 0, 0): 96, (0, 8, 0, 0, 0, 1): 92}
    got = {k: cells.get(k) for k in eq}
    check("C13_equality_cell_capacities_equal_required_ports",
          all(got[k] == v for k, v in eq.items()),
          dict(expected=       {"|".join(map(str, k)): v for k, v in eq.items()},
               ledger={"|".join(map(str, k)): v for k, v in got.items()}))

    # ---- C14 the committed witness files really are the excluded objects:
    # recanonicalise them here and re-run the coexistence test, rather than
    # believing the stored certificate
    sys.path.insert(0, str(ROOT / "src"))
    try:
        import l6_cover_bfs_146 as CB
        PERMS = ["".join(q) for q in itertools.permutations("123456")]
        IDX = {q: i for i, q in enumerate(PERMS)}

        def canon(ports):
            words = [PERMS[v] for v in ports]
            best = None
            for g in itertools.permutations("123456"):
                m = dict(zip("123456", g))
                seq = tuple(IDX["".join(m[c] for c in wd)] for wd in words)
                if best is None or seq < best:
                    best = seq
            return best
        recheck = []
        for name, c in (("row96", 6), ("row92", 7)):
            shas = {}
            for route in ("table", "notable"):
                f = R148 / "witnesses" / f"{name}_{route}.jsonl"
                if not f.exists():
                    shas[route] = None
                    continue
                raw = [json.loads(x)["ports"]
                       for x in f.read_text().splitlines() if x.strip()]
                cls = sorted({canon(p) for p in raw})
                shas[route] = dict(
                    witnesses=len(raw), classes=len(cls),
                    sha256=hashlib.sha256(json.dumps(cls).encode()).hexdigest(),
                    excluded=[not CB.decide(list(x), c)["coverable_by_c_orbits"]
                              for x in cls],
                    min_orbits=[CB.decide(list(x), c)["min_orbits_to_cover_F"]
                                for x in cls])
            recheck.append(dict(row=name, routes=shas,
                                routes_agree=(shas.get("table") is not None
                                              and shas.get("notable") is not None
                                              and shas["table"]["sha256"]
                                              == shas["notable"]["sha256"])))
        ok14 = all(r["routes_agree"]
                   and all(r["routes"]["table"]["excluded"])
                   and all(m is not None for m in r["routes"]["table"]["min_orbits"])
                   for r in recheck)
        check("C14_witness_files_recanonicalised_and_reexcluded", ok14, recheck)
    except Exception as e:
        check("C14_witness_files_recanonicalised_and_reexcluded", False,
              repr(e)[:200])

    # ---- C11 the 872 witness
    wit = ROOT / "data" / "verified_872_witness.txt"
    ok872 = False
    detail872 = "missing"
    if wit.exists():
        W = wit.read_text().split()[0]
        wins = {W[i:i + 6] for i in range(len(W) - 5)
                if len(set(W[i:i + 6])) == 6}
        allp = {"".join(p) for p in itertools.permutations("123456")}
        ok872 = len(W) == 872 and wins >= allp
        detail872 = dict(length=len(W), distinct_permutation_windows=len(wins),
                         covers_all_720=wins >= allp)
    check("C11_length_872_witness_is_a_cover", ok872, detail872)
    # ---- C12 provenance, VERIFIED rather than merely recorded.
    # Recording a hash and never comparing it is not provenance: a mutated
    # hash escaped this check until round 148's mutation run caught it.
    # The build is bit-reproducible (gcc -O2 on the same source gives the same
    # SHA-256), so both source and executable hashes are compared to disk.
    bins = jload(R147 / "certs" / "binaries_147.json") or {}
    prov, mism = {}, []
    for tag in ("phase2_build", "rebuilt_build"):
        b = bins.get(tag) or {}
        exe = b.get("exe")
        rec = b.get("exe_sha256")
        got = sha(ROOT / exe) if exe else None
        prov[tag] = dict(exe=exe, recorded=rec, on_disk=got,
                         matches=(rec is not None and got == rec))
        if exe and rec and got is not None and got != rec:
            mism.append(f"{tag}: recorded {rec[:12]} but {exe} hashes {got[:12]}")
        if exe and rec and got is None:
            mism.append(f"{tag}: {exe} is missing, cannot verify its hash")
    srcsrc = bins.get("rebuilt_build", {}).get("source_sha256")
    src_file = R147 / "src" / "l6_chain_capacity_147.c"
    src_now = sha(src_file)
    if srcsrc and src_now != srcsrc:
        mism.append(f"source: recorded {srcsrc[:12]} but file hashes "
                    f"{(src_now or '')[:12]}")
    srcs = {q.name: sha(q) for q in [
        src_file, R147 / "src" / "chain2_147.c", R147 / "src" / "ub147.py",
        ROOT / "src" / "l6_marked_capacity_pruned_144.c"]}
    check("C12_provenance_hashes_match_disk",
          bool(bins) and all(srcs.values()) and not mism
          and any(v["matches"] for v in prov.values()),
          dict(builds=prov, mismatches=mism, source_sha256=srcs))

    ok = all(c["ok"] for c in CHECKS)
    out = dict(verdict=("L6 >= 872 (and with the witness, L6 = 872)" if ok
                        else "NOT CERTIFIED"),
               certified=ok, checks=CHECKS,
               failed=[c["check"] for c in CHECKS if not c["ok"]])
    (R148 / "certs" / "master_verifier_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    if "--json" in argv:
        print(json.dumps(out, indent=1))
    else:
        for c in CHECKS:
            print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']}")
        print()
        print("CERTIFIED:", ok, "|", out["verdict"])
        if not ok:
            print("failed:", out["failed"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
