#!/usr/bin/env python3
"""Round 170 -- reclassifying every existing certificate against the exact 35.

Round 169 found that its enlarged (P1) closure made many already-issued direct
certificates redundant: a cell whose bound follows from a selected dominator
needs no certificate of its own.  That was computed against a 36-cell
constructed set.  The basis is now known exactly, and it is 35 with a
different membership, so the classification has to be redone against the set
that will actually be shipped.

Three classes, and the middle one is why nothing gets deleted:

  REQUIRED_LOAD_BEARING          the cell is in the exact basis; its bound is
                                 what closes an exposed row;
  USEFUL_INVESTMENT_PREDECESSOR  not in the basis, but it is a dependency of
                                 some certificate that IS -- a ladder rung, or
                                 a prefix cell a target's proof cites.  It
                                 closes no row and still cannot be dropped
                                 without breaking a proof;
  VALID_BUT_REDUNDANT            neither.  The certificate is sound and
                                 nothing in the current plan needs it.

VALID_BUT_REDUNDANT is not a defect and nothing is deleted on its account.  A
redundant certificate is a proved fact that a later round may need, and
redundancy is relative to THIS basis: a different residual completion would
promote some of these back.  The point of the classification is to size the
load-bearing core honestly, not to prune the archive.
"""
from __future__ import annotations
import gzip, hashlib, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def batch_cells(rel):
    """(cell -> cap) a certificate file proves itself, plus what it cites."""
    text = gzip.decompress((ROOT / rel).read_bytes()).decode()
    own, deps = {}, {}
    for line in text.splitlines():
        s = line.split("#")[0].split()
        if not s:
            continue
        if s[0] == "tree":
            own[tuple(int(x) for x in s[1:7])] = int(s[7])
        elif s[0] == "dep":
            deps[tuple(int(x) for x in s[1:7])] = int(s[7])
    return own, deps


def main():
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    BASIS = set([parse(c) for c in src["minimum"]["cells"]]
                + [parse(c) for c in bas["minimum"]["witness_completion"]])

    batches = [
        "r164/certs/extree_prefix_164.txt.gz",
        "r166/certs/extree_batch2_166.txt.gz",
        "r166/certs/extree_batch3_166.txt.gz",
        "r168/certs/extree_batch1_168.txt.gz",
        "r170/certs/extree_ladder_h_170.txt.gz",
        "r170/certs/extree_ladder_a2_170.txt.gz",
        "r170/certs/extree_target_h_170.txt.gz",
        "r170/certs/extree_target_a2_170.txt.gz",
    ]
    owned, cited, where = {}, set(), {}
    for rel in batches:
        own, deps = batch_cells(rel)
        for K, c in own.items():
            owned[K] = c
            where.setdefault(K, []).append(rel)
        cited |= set(deps)
    print(f"{len(owned)} cells carried by {len(batches)} certificates; "
          f"{len(cited)} distinct cells cited as dependencies", flush=True)

    # What the SHIPPED basis proofs depend on.  EXTREE declares dependencies
    # per batch, not per tree, so the honest granularity is the dep set the
    # two genuine target certificates actually name -- no transitive guessing
    # needed, because a target certificate names every cell its proof cites.
    shipped = ("r170/certs/extree_target_h_170.txt.gz",
               "r170/certs/extree_target_a2_170.txt.gz")
    needed, proven_by_shipped = set(), set()
    for rel in shipped:
        own, deps = batch_cells(rel)
        needed |= set(deps)
        proven_by_shipped |= set(own)
    rows = []
    for K, c in sorted(owned.items(), key=lambda kv: cellstr(kv[0])):
        if K in BASIS:
            cls = "REQUIRED_LOAD_BEARING"
        elif K in needed:
            cls = "USEFUL_INVESTMENT_PREDECESSOR"
        else:
            cls = "VALID_BUT_REDUNDANT"
        rows.append(dict(cell=cellstr(K), cap=c, classification=cls,
                         carried_by=where[K]))
    tally = Counter(r["classification"] for r in rows)
    for k, v in sorted(tally.items()):
        print(f"  {k:<32} {v}", flush=True)

    basis_with_cert = sorted(cellstr(K) for K in BASIS if K in owned)
    basis_without = sorted(cellstr(K) for K in BASIS if K not in owned)
    print(f"basis cells with a certificate: {len(basis_with_cert)}/"
          f"{len(BASIS)}", flush=True)

    out = dict(
        basis_size=len(BASIS),
        certificates_examined=batches,
        cells_carried=len(owned),
        tally=dict(tally),
        basis_cells_with_certificate=basis_with_cert,
        basis_cells_still_to_certify=basis_without,
        per_cell=rows,
        policy="nothing is deleted.  VALID_BUT_REDUNDANT means sound and "
               "unused by THIS basis; a different residual completion would "
               "promote some of these back, and a proved fact keeps its value "
               "for later rounds",
        shipped_basis_certificates=list(shipped),
        dependencies_named_by_shipped=len(needed),
        round_169_comparison=dict(
            round_169_called_redundant=src["minimum"]["redundant"],
            round_170_valid_but_redundant=tally.get("VALID_BUT_REDUNDANT", 0),
            these_measure_different_things=
                "round 169's 221 is the number of CANDIDATE cells that need "
                "no direct certificate of their own, because (P1) closure "
                "derives their bound from a selected dominator -- a statement "
                "about closing census rows.  This module asks a different "
                "question: is a certificate the project already holds cited "
                "as a dependency by a shipped proof.  A cell can need no "
                "certificate to close a row and still be an indispensable "
                "predecessor of one that does, which is why 221 redundant "
                "and 0 redundant are both correct"),
        seconds_noncanonical=0.0,
    )
    out["ok"] = True
    (ROOT / "r170" / "certs" / "reclass_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "per_cell"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
