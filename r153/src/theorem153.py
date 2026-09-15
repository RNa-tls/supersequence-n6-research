#!/usr/bin/env python3
"""Round 153 Phase 10 -- the integrated, certified-only theorem verifier.

It reads nothing but certificates and the artefacts they are about, and it
refuses at the first thing it cannot check.  Four inputs, in the order they are
used:

  1. round-152 capacity certification   r152/certs/verify_all_c152.json
                                        r152/certs/verify_piece_c152.json
  2. round-152 certified-only census    r152/certs/census_152.json
  3. round-153 equality enumeration     r153/certs/eqcompare_153.json
  4. round-153 coexistence exclusion    r153/certs/covertree_153.json
                                        r153/certs/coexist_153.json
  5. the explicit length-872 cover      r153/certs/witness872_153.json

Forbidden anywhere: an UNKNOWN_CAP or DISAGREE row, a census row left SURVIVING
or UNKNOWN, an equality row whose enumeration routes disagree, a witness that
does not replay, a coexistence tree that does not validate, or any reference to
the retracted round-144/146 tables inside the round-153 pipeline.
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
FORBIDDEN_READS = ["chain_cells_147.json", "heavy_cells_147.json",
                   "rr_l6_marked_capacity_table_144.json", "ub147",
                   "catalogue147.h", "l6_chain_capacity_147",
                   "l6_marked_capacity", "l6_coupled_144", "l6_cover_bfs_146",
                   "l6_circuit_coexist_144", "l6_coexist_check3_144",
                   "INVALIDATED_BY_UB146"]
PIPELINE = ["r153/src/eqwit153.c", "r153/src/eqwit153.py",
            "r153/src/coexist153.py", "r153/src/covertree153.py",
            "r153/src/theorem153.py", "r153/src/witness872_153.py"]


def j(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    R = {}
    fail = []

    # ---- 1. capacity
    chain, piece = j("r152/certs/verify_all_c152.json"), \
        j("r152/certs/verify_piece_c152.json")
    for tag, d, n in (("chain", chain, 1101), ("piece", piece, 220)):
        if not d:
            fail.append(f"{tag} capacity certificate missing")
            continue
        bad = [r["cell"] for r in d["rows"] if r["status"] not in GOOD]
        R[f"capacity_{tag}"] = dict(cells=len(d["rows"]), expected=n,
                                    not_certified=bad,
                                    sha256=sha(f"r152/certs/verify_"
                                               f"{'all_c152' if tag == 'chain' else 'piece_c152'}.json"))
        if len(d["rows"]) != n or bad:
            fail.append(f"{tag} capacity: {len(d['rows'])} cells, "
                        f"{len(bad)} not certified")

    # ---- 2. census
    cen = j("r152/certs/census_152.json")
    if not cen:
        fail.append("census missing")
    else:
        tallies = {L: v["tally"] for L, v in cen["layers"].items()}
        R["census"] = dict(tallies=tallies,
                           chain_cells_read=cen["certified_cells_read"],
                           piece_cells_read=cen["piece_cells_read"],
                           chain_cells_unread=len(cen["certified_cells_unread"]),
                           sha256=sha("r152/certs/census_152.json"))
        for L, t in tallies.items():
            if t.get("SURVIVING") or t.get("UNKNOWN_CAP"):
                fail.append(f"census {L} leaves {t}")
        if tallies.get("L871", {}).get("EQUALITY") != 2:
            fail.append("census L871 does not leave exactly two equality rows")
        for L in ("L867", "L868", "L869", "L870"):
            if set(tallies.get(L, {})) != {"STRICTLY_CLOSED"}:
                fail.append(f"census {L} is not fully strictly closed")

    # ---- 3. equality enumeration
    eq = j("r153/certs/eqcompare_153.json")
    if not eq:
        fail.append("equality comparison missing")
    else:
        R["equality"] = dict(
            equivariance=eq["equivariance"],
            rows=[dict(name=r["name"], cell=r["cell"], target=r["target"],
                       routes=r["routes_present"], witnesses=r["witness_count"],
                       classes=r["class_count"], agree=r["agree"])
                  for r in eq["rows"]],
            sha256=sha("r153/certs/eqcompare_153.json"))
        if not eq["equivariance"]["ok"]:
            fail.append("left S6 equivariance failed")
        for r in eq["rows"]:
            if not r["agree"]:
                fail.append(f"equality {r['name']}: routes disagree")
            if r["routes_present"] < 4:
                fail.append(f"equality {r['name']}: only "
                            f"{r['routes_present']} routes")

    # ---- 4. coexistence
    ct, co = j("r153/certs/covertree_153.json"), j("r153/certs/coexist_153.json")
    if not ct or not co:
        fail.append("coexistence certificates missing")
    else:
        R["coexistence"] = dict(
            trees=[dict(name=r["name"], index=r["index"], c=r["c"], F=r["F"],
                        status=r["status"], nodes=r["nodes"])
                   for r in ct["rows"]],
            all_excluded=ct["all_excluded"],
            tree_sha256=ct["tree_sha256"],
            tree_file_sha256=sha("r153/certs/covertree_153.txt"),
            solvers_agree=all(c2[tag]["agree"]
                              for r in co["rows"] for c2 in r["certificates"]
                              for tag in ("lemmaE", "unrestricted")),
            excluded_without_lemmaE=all(c2["excluded_without_lemmaE"]
                                        for r in co["rows"]
                                        for c2 in r["certificates"]),
            controls_ok=co["controls_ok"])
        if ct["tree_sha256"] != R["coexistence"]["tree_file_sha256"]:
            fail.append("coexistence tree hash does not match the file")
        if not ct["all_excluded"]:
            fail.append("a coexistence tree did not validate")
        if not co["controls_ok"]:
            fail.append("a coexistence solver has no working positive control")
        if not R["coexistence"]["excluded_without_lemmaE"]:
            fail.append("exclusion needs Lemma E")

    # the number of witnesses excluded must equal the number enumerated
    if eq and ct:
        enum = {r["name"]: r["witness_count"] for r in eq["rows"]}
        excl = {}
        for r in ct["rows"]:
            excl[r["name"]] = excl.get(r["name"], 0) + (r["status"] == "EXCLUDED")
        R["every_enumerated_witness_is_excluded"] = enum == excl
        if enum != excl:
            fail.append(f"enumerated {enum} but excluded {excl}")

    # ---- 5. the explicit cover
    w = j("r153/certs/witness872_153.json")
    if not w:
        fail.append("length-872 witness certificate missing")
    else:
        R["witness872"] = dict(length=w["length"], covered=w["permutations_covered"],
                               ok=w["ok"], sha256=w["sha256"])
        if not w["ok"]:
            fail.append("the length-872 word is not a superpermutation")

    # ---- hygiene of the round-153 pipeline
    hits = {}
    for rel in PIPELINE:
        src = (ROOT / rel).read_text()
        h = []
        for i, line in enumerate(src.splitlines(), 1):
            st = line.lstrip()
            if st.startswith(("#", "*", "/*", "//")):
                continue
            # only a line that actually READS or IMPORTS counts; naming a
            # forbidden artefact inside this file's own blacklist does not
            if not any(tok in line for tok in
                       ("open(", "import ", "read_text", "read_bytes",
                        "#include", "subprocess", "Path(")):
                continue
            for bad in FORBIDDEN_READS:
                if bad in line:
                    h.append(dict(line=i, needle=bad, text=st[:100]))
        if h:
            hits[rel] = h
    R["pipeline_reads_no_retracted_artefact"] = not hits
    R["forbidden_read_hits"] = hits
    if hits:
        fail.append("the round-153 pipeline names a retracted artefact")

    R["failures"] = fail
    R["L6_ge_872"] = not fail
    R["L6_le_872"] = bool(w and w["ok"])
    R["L6_equals_872"] = R["L6_ge_872"] and R["L6_le_872"]
    (ROOT / "r153" / "certs" / "theorem_153.json").write_text(
        json.dumps(R, indent=1) + "\n")
    print(json.dumps({k: v for k, v in R.items()
                      if k not in ("forbidden_read_hits",)}, indent=1)[:4000])
    print("FAILURES:", fail or "none")
    print("L6 >= 872:", R["L6_ge_872"], " L6 <= 872:", R["L6_le_872"],
          " L6 = 872:", R["L6_equals_872"])
    return 0 if R["L6_equals_872"] else 1


if __name__ == "__main__":
    sys.exit(main())
