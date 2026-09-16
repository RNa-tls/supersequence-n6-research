#!/usr/bin/env python3
"""Round 163 phases 3 and 8 -- audit-evidence table and verdict reconciliation.

Phase 3 builds, for every hand-proof node, the list of audits that actually
exist in the repository: the round, the commit that introduced the artefact,
the artefact path and hash, the proof type, and the verdict token READ OUT OF
THE ARTEFACT rather than remembered.

Phase 8 then checks each FULLY_CERTIFIED verdict against what later rounds
discovered.  A later discovery matters only if it makes a statement that is
still certified FALSE.  Each reconciliation names a regex that must be present
in the CURRENT DAG text for the correction to count as recorded.
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DAG = ROOT / "r163" / "certs" / "dag_163.json"
TOKEN = re.compile(r"\bH_[A-Z]+_(?:FULLY_CERTIFIED|PARTIAL|REFUTED)\b")

# node -> list of (round, artefact, proof type, scope of the statement audited)
AUDITS = {
    "H.models": [(149, "r149/PROOF.md", "paper + exhaustive finite check",
                  "(O1)-(O6), Claims 1-5, Lemmas 1.1-1.2, t <= 4 in range"),
                 (149, "r149/AUDIT.md", "provenance-only", "audit summary"),
                 (163, "r163/certs/hidden_163.json",
                  "exhaustive finite check",
                  "all three models load-bearing; Lemma 1.1 load-bearing")],
    "H.feas": [(149, "r149/PROOF.md", "paper",
                "section 9.5 lemma; turn-it-off audit UNAVAILABLE"),
               (150, "r150/PROOF.md",
                "paper + exhaustive finite check + independent reimplementation",
                "Token-Touched-Orbit theorem, dual certificate, "
                "clause-by-clause conformance of five C bodies"),
               (163, "r163/certs/recheck_163.json",
                "exhaustive finite check",
                "dual bound = subset optimum on all 7,722 multisets")],
    "H.catalogue": [(149, "r149/PROOF.md", "paper + exhaustive finite check",
                     "sections 2.1-2.3, all 518,400 ordered pairs"),
                    (163, "r163/certs/recheck_163.json",
                     "independent reimplementation + exhaustive finite check",
                     "catalogue recomputed from the definitions")],
    "H.wlog": [(149, "r149/PROOF.md", "paper + exhaustive finite check",
                "section 2.4, 518,400 equivariance pairs"),
               (153, "r153/src/eqwit153.py", "machine certificate",
                "node E.equivariance, the search-level check"),
               (163, "r163/certs/recheck_163.json",
                "independent reimplementation + exhaustive finite check",
                "transitivity + generator-exhaustive equivariance")],
    "H.tight": [(155, "research/RR_L6_H_TIGHT_AUDIT.md",
                 "paper + exhaustive finite check",
                 "the four equality-row conclusions from g = d = 0")],
    "H.extract": [(156, "r156/THEOREM.md", "paper",
                   "the CORRECTED extraction theorem (0)-(7)"),
                  (156, "research/RR_L6_H_EXTRACT_AUDIT.md",
                   "independent reimplementation + exhaustive finite check",
                   "the theorem on 20,327,589 exhaustive cases")],
    "H.incidence": [(157, "research/RR_L6_H_INCIDENCE_AUDIT.md",
                     "paper + exhaustive finite check",
                     "2g = mu(B) + R_int, K + R_int <= G+1, parity, tree")],
    "H.envelope": [(158, "research/RR_L6_H_ENVELOPE_AUDIT.md",
                    "paper + exhaustive finite check",
                    "four upper bounds + two piece-model lower bounds")],
    "H.samehex": [(159, "research/RR_L6_H_SAMEHEX_AUDIT.md",
                   "paper + exhaustive finite check",
                   "D2 + Qs <= R_int (the lower half only)")],
    "H.master": [(160, "research/RR_L6_H_MASTER_AUDIT.md",
                  "paper + exhaustive finite check",
                  "L = 867 + k + Z + H + B* as an identity; general n")],
    "H.splice": [(161, "research/RR_L6_H_SPLICE_AUDIT.md",
                  "paper + exhaustive finite check",
                  "Lemmas A-F split into 23 clauses")],
    "H.fixedrep": [(162, "research/RR_L6_H_FIXEDREP_AUDIT.md",
                    "paper + exhaustive finite check",
                    "L1-L5 and the WLOG corollary")],
}

# later discovery -> (node it lands on, what it invalidates, regex that must
# appear in the CURRENT DAG text for the correction to be recorded)
RECONCILE = {
    "R156: the written extraction cut recipe is wrong": (
        "H.extract",
        "the node's own `where` document; the IMPLEMENTATION is correct and "
        "the corrected statement is r156/THEOREM.md.  Round 156 therefore "
        "returned PARTIAL, so nothing false was ever certified",
        r"r156/THEOREM\.md"),
    "R158: the census consumes two piece-model LOWER bounds": (
        "H.envelope",
        "the node's `what`, which listed only the four upper bounds",
        r"a >= D2 - d"),
    "R159: R_int <= 2g is not H.samehex's": (
        "H.samehex",
        "the bundled statement D2 + Qs <= R_int <= 2g; the upper half belongs "
        "to H.incidence and SAME-HEX is not a corollary of the extraction "
        "theorem",
        r"upper half R_int <= 2g is H\.incidence"),
    "R160: the nonnegativity of k, Z, B* is not H.master's": (
        "H.master",
        "the bundled claim that MASTER-142 also supplies nonnegativity",
        r"NONNEGATIVITY of the four terms is imported, not proved here"),
    "R161: the converse of Lemma E is false": (
        "H.splice",
        "any use of the converse; round 161 showed it fails on 324/646 covers "
        "and that no downstream step uses it",
        r"CONVERSE of Lemma E is false and is not used"),
    "R162: the fixed representative is not unique": (
        "H.fixedrep",
        "any appeal to uniqueness; the corollary needs existence only",
        r"a lower bound for all fixed representatives is a lower bound for "
        r"all covers"),
    "R155: section 9's ground for 'all 120 hexagons' is not a derivation": (
        "H.tight",
        "the justification, not the claim: the claim is true and follows from "
        "splice Lemma A",
        r"correct ground is splice Lemma A"),
    "R163: G = 2g + c + d was in no node's text": (
        "H.extract / H.incidence / H.tight",
        "nothing certified was false; the assumption was simply unrecorded "
        "while being the strongest measured (7,848 rows re-open without it)",
        r"G = 2g \+ c \+ d"),
    "R163: G <= 5k was owned by nobody": (
        "H.models",
        "nothing certified was false; it appeared only as '(n-1)O >= P' "
        "inside H.master's derived_from (332 rows re-open without it)",
        r"G <= 5k"),
    "R163: Claim 1 (required = 120 + G - 5c) was in no node's text": (
        "H.extract",
        "nothing certified was false; H.extract's `what` was the placeholder "
        "'the extraction bookkeeping' (8 rows re-open if it is weakened)",
        r"120 \+ G - 5c"),
}


def sha(p):
    q = ROOT / p
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def commit_of(rel):
    # This round's own artefacts are not yet committed when this runs, so
    # their "last commit" is a moving target that would make the certificate
    # non-reproducible.  They are labelled instead of dated.
    if rel.startswith("r163/"):
        return "(this round, round 163)"
    try:
        out = subprocess.run(["git", "log", "--format=%h %ad %s",
                              "--date=short", "-1", "--", rel],
                             cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.strip()
        return out or None
    except Exception:
        return None


def verdict_of(rel):
    p = ROOT / rel
    if not p.exists() or p.suffix != ".md":
        return None
    toks = TOKEN.findall(p.read_text(errors="ignore"))
    body = p.read_text(errors="ignore")
    # the node's OWN verdict is the token matching the file name
    stem = re.search(r"H_([A-Z]+)_AUDIT", rel)
    own = None
    if stem:
        want = re.compile(rf"\bH_{stem.group(1)}_"
                          r"(FULLY_CERTIFIED|PARTIAL|REFUTED)\b")
        m = want.findall(body)
        own = f"H_{stem.group(1)}_{m[-1]}" if m else None
    return dict(own_verdict=own,
                all_tokens_in_file=sorted(set(
                    TOKEN.findall(body))) or None)


def main():
    dag = json.loads(DAG.read_text())["dag"]["nodes"]
    blob = " || ".join(f"{v.get('what')} {v.get('derived_from')} "
                       f"{v.get('where')}" for v in dag.values())
    table = {}
    for node, entries in AUDITS.items():
        rows = []
        for rnd, rel, kind, scope in entries:
            rows.append(dict(round=rnd, artefact=rel, exists=(ROOT / rel).exists(),
                             sha256=sha(rel), commit=commit_of(rel),
                             proof_type=kind, statement_audited=scope,
                             verdict=verdict_of(rel)))
        table[node] = rows
    rec = {}
    for name, (node, what, rx) in RECONCILE.items():
        rec[name] = dict(lands_on=node, invalidates=what,
                         pattern=rx,
                         recorded_in_current_dag=bool(re.search(rx, blob)))
    # every audit document's own verdict, read out of the file
    verdicts = {}
    for p in sorted(ROOT.glob("research/RR_L6_H_*_AUDIT.md")):
        rel = str(p.relative_to(ROOT))
        verdicts[rel] = verdict_of(rel)["own_verdict"]
    out = dict(dag_source=str(DAG.relative_to(ROOT)),
               audits=table, verdict_tokens=verdicts,
               # a DEDICATED round is one whose single target was that node:
               # rounds 155-162.  Round 163 is an inventory, not a dedicated
               # audit, so its re-derivations do not make a node "audited".
               nodes_with_a_dedicated_audit_round=sorted(
                   n for n, e in AUDITS.items()
                   if any(155 <= r <= 162 for r, *_ in e)),
               nodes_without_a_dedicated_audit_round=sorted(
                   n for n, e in AUDITS.items()
                   if not any(155 <= r <= 162 for r, *_ in e)),
               reconciliation=rec,
               unrecorded_corrections=sorted(
                   k for k, v in rec.items()
                   if not v["recorded_in_current_dag"]),
               missing_artefacts=sorted(
                   r["artefact"] for rows in table.values() for r in rows
                   if not r["exists"]))
    out["ok"] = not out["unrecorded_corrections"] and not out["missing_artefacts"]
    (ROOT / "r163" / "certs" / "evidence_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("verdict_tokens", "nodes_without_a_dedicated_audit_round",
                       "unrecorded_corrections", "missing_artefacts", "ok")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
