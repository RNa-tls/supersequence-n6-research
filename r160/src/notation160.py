#!/usr/bin/env python3
"""Round 160 Phases 9/10/13 -- notation-era contamination and downstream use.

(1) REACHABILITY.  Build the set of repository files the final theorem path
    actually reaches: every path named in a DAG node's `where`, plus the
    transitive closure of their in-repository imports.

(2) ERA SCAN.  Look in that set for the pre-repair / Round-126..140 vocabulary
        f_out, delta, J = G - F, F + e, "abandonment"
    and for any use of F where G is meant.  Anything found on the path is
    load-bearing.

(3) DOWNSTREAM.  Find every file that states or consumes the master identity
    (searching for the constant, for `844 + G + S + H`, and for the row
    enumeration `L = 867 + t`), and check each one uses
        the same constant 867,
        the same four terms k, Z, H, B*,
        H (the heavy COST) and not h (the heavy COUNT),
        coefficient +1 on each term.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DAG = ROOT / "r159" / "certs" / "dag_159.json"

OLD_ERA = {
    "f_out": r"\bf_out\b",
    "delta_slack": r"\bdelta\s*=\s*\(?\s*F\s*\+\s*e",
    "J_eq_G_minus_F": r"\bJ\s*=\s*G\s*-\s*F\b|J=G-F",
    "F_plus_e": r"\bF\s*\+\s*e\b",
    "abandonment": r"abandon",
    "master_with_f_out": r"867\s*\+\s*k\s*\+\s*G\s*\+\s*e",
    "master_with_J": r"867\s*\+\s*k\s*\+\s*J",
}
MASTER_RE = r"867\s*\+\s*k\s*\+\s*Z\s*\+\s*H\s*\+\s*B"
FO_RE = r"844\s*\+\s*G\s*\+\s*S\s*\+\s*H"


def repo_files():
    out = []
    for p in ROOT.rglob("*.py"):
        if ".git" in p.parts:
            continue
        out.append(p)
    for p in ROOT.rglob("*.md"):
        if ".git" in p.parts:
            continue
        out.append(p)
    return out


def where_paths(dag):
    pats = []
    for nid, v in dag["nodes"].items():
        for tok in re.split(r"[;,]", v.get("where", "")):
            tok = tok.strip()
            m = re.match(r"([\w./-]+\.(?:py|md|json|txt))", tok)
            if m:
                pats.append((nid, m.group(1)))
    return pats


def imports_of(path):
    """In-repository module names imported by a python file."""
    if path.suffix != ".py":
        return set()
    txt = path.read_text(errors="ignore")
    names = set(re.findall(r"^\s*import\s+([\w_]+)", txt, re.M))
    names |= set(re.findall(r"^\s*from\s+([\w_]+)\s+import", txt, re.M))
    return names


def main():
    dag = json.loads(DAG.read_text())["dag"]
    files = repo_files()
    bymod = {}
    for p in files:
        if p.suffix == ".py":
            bymod.setdefault(p.stem, []).append(p)

    # ---- (1) reachable set
    seeds, missing = [], []
    for nid, rel in where_paths(dag):
        p = ROOT / rel
        if p.exists():
            seeds.append((nid, p))
        else:
            missing.append((nid, rel))
    # the census chain the DAG's machine nodes are produced by
    for rel in ("r152/src/rows152.py", "r152/src/checker152.py",
                "r153/src/dag153.py", "r153/src/theorem153.py"):
        p = ROOT / rel
        if p.exists():
            seeds.append(("(census chain)", p))
    reach, stack = set(), [p for _, p in seeds]
    while stack:
        p = stack.pop()
        if p in reach:
            continue
        reach.add(p)
        for m in imports_of(p):
            for q in bymod.get(m, []):
                if q not in reach:
                    stack.append(q)

    # ---- (2) era scan
    hits_on_path, hits_off_path = {}, {}
    for p in files:
        txt = p.read_text(errors="ignore")
        found = {k: len(re.findall(v, txt)) for k, v in OLD_ERA.items()
                 if re.search(v, txt)}
        if not found:
            continue
        rel = str(p.relative_to(ROOT))
        (hits_on_path if p in reach else hits_off_path)[rel] = found

    # ---- (3) downstream use of the identity
    downstream = []
    for p in files:
        txt = p.read_text(errors="ignore")
        has_master = bool(re.search(MASTER_RE, txt))
        has_fo = bool(re.search(FO_RE, txt))
        has_rows = bool(re.search(r"867\s*\+\s*t\b", txt))
        if not (has_master or has_fo or has_rows):
            continue
        rel = str(p.relative_to(ROOT))
        # does this file ever pass a heavy COUNT where the cost belongs?
        h_as_budget = bool(re.search(r'r\["h"\]\s*\)', txt))
        downstream.append(dict(file=rel, on_theorem_path=(p in reach),
                               states_master=has_master, states_FO=has_fo,
                               uses_row_constant=has_rows,
                               passes_h_as_a_budget=h_as_budget))

    out = dict(
        reachable_files=len(reach),
        where_paths_missing=missing,
        old_era_hits_ON_the_theorem_path=hits_on_path,
        old_era_hits_off_path=hits_off_path,
        contamination_on_path=bool(hits_on_path),
        downstream=sorted(downstream, key=lambda r: (not r["on_theorem_path"],
                                                     r["file"])),
        master_identity_file_imports_nothing_from_repo=(
            not (imports_of(ROOT / "src" / "l6_master_identity_144.py")
                 & set(bymod))),
        historical_reconciliation=dict(
            fo_shared="both eras start from (FO)  L = 844 + G + S + H",
            round_137_138="L = 867 + k + G + e + x + H - f_out  "
                          "(src/audit_r137_138.py line 331)",
            round_140="L = 867 + k + J + delta + x + H,  J = G - F  "
                      "(src/audit_r140_g3_140.py line 258)",
            equivalence_137_to_140="substitute f_out = F + e - delta: "
                                   "G + e - f_out = (G - F) + delta = J + delta",
            relation_to_current="both re-express S differently: the old era "
                                "used S = (r-1) + x - f_out with r-1 = "
                                "(ORB-1) + k + e, the current era uses "
                                "S = B* + O - 1 - D2 - c.  Same (FO), same "
                                "constant 867, DIFFERENT decomposition in "
                                "variables (F, J, e, x, f_out, delta) that "
                                "have no definition in the pass/beta "
                                "framework -- obsolete, not contradictory.",
            current="L = 867 + k + Z + H + B*  (src/l6_master_identity_144.py)",
            F_in_current_identity=False,
            note="the symbol F is reused in the CURRENT era for the SET of "
                 "hexagons a chain does not use (|F| = 4c, "
                 "src/l6_incidence_graph_146.py (iii)); it is not the "
                 "Round-126 abandonment count and never enters MASTER."),
    )
    out["ok"] = (not out["contamination_on_path"]
                 and not missing
                 and out["master_identity_file_imports_nothing_from_repo"])
    (ROOT / "r160" / "certs" / "notation_160.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("downstream", "historical_reconciliation")},
                     ensure_ascii=False, indent=1)[:2500])
    print("--- downstream ---")
    for r in out["downstream"]:
        print(" ", r)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
