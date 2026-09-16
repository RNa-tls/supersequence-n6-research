#!/usr/bin/env python3
"""Round 164 phase 0 -- recover the Route-B target set from the artefacts.

Round 163 reported 247 single-implementation chain cells and 109 piece cells.
Nothing here trusts those numbers.  The census-read sets are recovered by
RE-RUNNING an independent reimplementation of the census (round 163's
hidden163, which reproduces the stored census exactly) with the capacity
lookups instrumented, so the read set comes from execution, not from a field
in census_152.json.  Coverage is then computed from the four verification
reports.

It also parses the two text certificates and the exhaustion-tree file, so the
next phase knows exactly which proof objects exist for the targets.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CERTS = ROOT / "r152" / "certs"
sys.path.insert(0, str(ROOT / "r163" / "src"))
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def sha(p):
    q = ROOT / p if not str(p).startswith("/") else Path(p)
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


# ------------------------------------------------- certificate text parsing
def parse_capcert(rel):
    """L6-CAPCERT-2: `cell b d a bb e h cap nports` then one port line."""
    lines = (ROOT / rel).read_text().splitlines()
    assert lines[0] == "L6-CAPCERT-2", lines[0]
    out, i, bad = {}, 1, []
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        if f[0] != "cell":
            bad.append((i + 1, s[:60]))
            i += 1
            continue
        b, d, a, bb, e, h, cap, np_ = (int(x) for x in f[1:9])
        ports = [int(x) for x in lines[i + 1].split()] if i + 1 < len(lines) else []
        if len(ports) != np_:
            bad.append((i + 2, f"nports {np_} but {len(ports)} listed"))
        out[(b, d, a, bb, e, h)] = dict(cap=cap, nports=np_, ports=ports)
        i += 2
    return out, bad


def parse_pcert(rel):
    """L6-PIECECERT-1: `pcell b d fp lp cap nports` then one port line."""
    lines = (ROOT / rel).read_text().splitlines()
    assert lines[0] == "L6-PIECECERT-1", lines[0]
    out, i, bad = {}, 1, []
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        if f[0] != "pcell":
            bad.append((i + 1, s[:60]))
            i += 1
            continue
        b, d, fp, lp, cap, np_ = (int(x) for x in f[1:7])
        ports = [int(x) for x in lines[i + 1].split()] if i + 1 < len(lines) else []
        if len(ports) != np_:
            bad.append((i + 2, f"nports {np_} but {len(ports)} listed"))
        out[(b, d, fp, lp)] = dict(cap=cap, nports=np_, ports=ports)
        i += 2
    return out, bad


def parse_extree_cells(rel):
    """Which cells have a serialised exhaustion tree at all."""
    cells = []
    for s in (ROOT / rel).read_text().splitlines():
        if s.startswith("tree "):
            f = [int(x) for x in s.split()[1:]]
            cells.append((tuple(f[:6]), f[6]))
    return cells


# ------------------------------------------------------- census read set
def census_read_sets():
    """Run the round-163 independent census with the lookups instrumented."""
    import hidden163 as H
    H.load()
    chain_reads, piece_reads = set(), set()
    orig_CC, orig_PC = H.CC, H.PC

    def CC(b, d, a, bb, e, h=0):
        chain_reads.add((b, d, a, bb, e, h))
        return orig_CC(b, d, a, bb, e, h)

    def PC(b, d, fp, lp):
        if b >= 0 and d >= 0:
            piece_reads.add((b, d, fp, lp))
        return orig_PC(b, d, fp, lp)

    H.CC, H.PC = CC, PC
    res = H.run()
    H.CC, H.PC = orig_CC, orig_PC
    return chain_reads, piece_reads, res["totals"]


def main():
    cap, cap_bad = parse_capcert("r152/certs/cap_cert_all_152.txt")
    pc, pc_bad = parse_pcert("r152/certs/pcert_all_152.txt")
    extree = parse_extree_cells("r152/certs/extree_pilot_152.txt")

    vC = json.loads((CERTS / "verify_all_c152.json").read_text())
    vP = json.loads((CERTS / "verify_subset_152.json").read_text())
    pC = json.loads((CERTS / "verify_piece_c152.json").read_text())
    pP = json.loads((CERTS / "verify_piece_152.json").read_text())

    key6 = lambda s: tuple(int(x) for x in s.split("|"))
    C_chain = {key6(r["cell"]): r for r in vC["rows"] if r["status"] in GOOD}
    P_chain = {key6(r["cell"]): r for r in vP["rows"] if r["status"] in GOOD}
    pkey = lambda r: (r["b"], r["d"], r["fp"], r["lp"])
    C_piece = {pkey(r): r for r in pC["rows"] if r["status"] in GOOD}
    P_piece = {pkey(r): r for r in pP["rows"] if r["status"] in GOOD}

    chain_reads, piece_reads, totals = census_read_sets()

    # a read that no certificate covers falls back to the analytic bound
    chain_certified_reads = sorted(c for c in chain_reads if c in C_chain)
    chain_fallback_reads = sorted(c for c in chain_reads if c not in C_chain)
    piece_certified_reads = sorted(c for c in piece_reads if c in C_piece)
    piece_fallback_reads = sorted(c for c in piece_reads if c not in C_piece)

    CHAIN_SINGLE = sorted(c for c in chain_certified_reads if c not in P_chain)
    PIECE_SINGLE = sorted(c for c in piece_certified_reads if c not in P_piece)

    # do the targets have a serialised exhaustion proof?
    extree_cells = {c for c, _ in extree}
    targets_with_extree = sorted(set(CHAIN_SINGLE) & extree_cells)

    def prof(cells, src):
        from collections import Counter
        st = Counter(src[c]["status"] for c in cells)
        return dict(st)

    out = dict(
        inputs={p: sha(p) for p in (
            "r152/certs/cap_cert_all_152.txt", "r152/certs/pcert_all_152.txt",
            "r152/certs/extree_pilot_152.txt",
            "r152/certs/verify_all_c152.json",
            "r152/certs/verify_subset_152.json",
            "r152/certs/verify_piece_c152.json",
            "r152/certs/verify_piece_152.json",
            "r152/certs/census_152.json")},
        census_totals=totals,
        census_reproduces_stored=(totals.get("STRICTLY_CLOSED") == 1607
                                  and totals.get("EQUALITY") == 2
                                  and totals.get("SURVIVING", 0) == 0),
        chain=dict(
            certificate_records=len(cap), parse_errors=cap_bad,
            certified_by_C=len(C_chain), certified_by_python=len(P_chain),
            python_subset_of_C=set(P_chain) <= set(C_chain),
            census_reads=len(chain_reads),
            census_reads_certified=len(chain_certified_reads),
            census_reads_analytic_fallback=len(chain_fallback_reads),
            single_implementation=len(CHAIN_SINGLE),
            status_profile_of_targets=prof(CHAIN_SINGLE, C_chain)),
        piece=dict(
            certificate_records=len(pc), parse_errors=pc_bad,
            certified_by_C=len(C_piece), certified_by_python=len(P_piece),
            python_subset_of_C=set(P_piece) <= set(C_piece),
            census_reads=len(piece_reads),
            census_reads_certified=len(piece_certified_reads),
            census_reads_no_certificate=len(piece_fallback_reads),
            single_implementation=len(PIECE_SINGLE),
            status_profile_of_targets=prof(PIECE_SINGLE, C_piece)),
        total_targets=len(CHAIN_SINGLE) + len(PIECE_SINGLE),
        exhaustion_trees=dict(
            file="r152/certs/extree_pilot_152.txt",
            trees=len(extree), cells=[list(c) for c, _ in extree],
            targets_with_a_serialised_exhaustion_tree=len(targets_with_extree),
            note="L6-EXTREE-1 is the only serialised upper-bound proof object "
                 "in the repository and it is a PILOT: 24 cheap cells"),
        CHAIN_SINGLE_IMPL=[list(c) for c in CHAIN_SINGLE],
        PIECE_SINGLE_IMPL=[list(c) for c in PIECE_SINGLE],
    )
    out["matches_round_163_expectation"] = dict(
        chain_expected=247, chain_recovered=len(CHAIN_SINGLE),
        piece_expected=109, piece_recovered=len(PIECE_SINGLE),
        total_expected=356, total_recovered=out["total_targets"],
        agree=(len(CHAIN_SINGLE) == 247 and len(PIECE_SINGLE) == 109))
    out["ok"] = (out["census_reproduces_stored"] and not cap_bad and not pc_bad
                 and out["chain"]["python_subset_of_C"]
                 and out["piece"]["python_subset_of_C"])
    (ROOT / "r164" / "certs" / "targets_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    brief = {k: v for k, v in out.items()
             if k not in ("CHAIN_SINGLE_IMPL", "PIECE_SINGLE_IMPL", "inputs")}
    brief["exhaustion_trees"] = {k: v for k, v
                                 in out["exhaustion_trees"].items()
                                 if k != "cells"}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
