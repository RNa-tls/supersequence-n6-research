#!/usr/bin/env python3
"""Round 164 -- check the manufactured proof object with TWO validators.

The tree written by gentree164.py is checked

  (1) by this round's own verifier, r164/src/routeb164.py, which rebuilt the
      geometry from string algebra and maintains the feasibility histogram
      both incrementally and from scratch at every node; and

  (2) by round 152's validator, r152/src/extree152.py, which was written
      independently, years of rounds earlier, against the same format.

Neither validator searches.  A cell whose tree passes both has an upper bound
that two independent programs have confirmed from a stored proof object, which
is exactly what the target cells lacked.
"""
from __future__ import annotations
import gzip, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import routeb164 as R                                             # noqa: E402

CERTS = ROOT / "r152" / "certs"
SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")


def read_tree(rel):
    p = ROOT / rel
    if str(p).endswith(".gz"):
        return gzip.open(p, "rt").read()
    return p.read_text()


def main():
    t0 = time.time()
    gen = json.loads((ROOT / "r164" / "certs" / "gentree_164.json").read_text())
    rel = gen["stored"]
    text = read_tree(rel)
    plain = SCRATCH / "extree_prefix_164.txt"
    plain.parent.mkdir(parents=True, exist_ok=True)
    plain.write_text(text)

    cap, order = R.parse_capcert(CERTS / "cap_cert_all_152.txt")
    tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
    targets = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]}
    trees = R.parse_extree(plain)

    # ---- validator 1: this round's
    certified, rows = {}, []
    nodes = hist = forms = subset = 0
    for cell, capv, toks in trees:
        v = R.TreeVerifier(dict(certified))
        ok, info = v.validate(cell, capv, toks)
        nodes += v.nodes
        hist += v.hist_checks
        forms += v.feas_form_checks
        subset += v.feas_subset_checks
        row = dict(cell="|".join(map(str, cell)), cap=capv,
                   is_target=cell in targets, nodes=v.nodes,
                   r164_validator=bool(ok), detail=None if ok else info)
        if ok:
            certified[cell] = capv
        # does the claimed cap agree with the round-152 certificate?
        row["matches_route_a_cap"] = (cap.get(cell, {}).get("cap") == capv)
        rows.append(row)

    # ---- validator 2: round 152's, as a separate process
    rep2 = SCRATCH / "extree_r152_report.json"
    r = subprocess.run(
        [sys.executable, str(ROOT / "r152" / "src" / "extree152.py"),
         "--tree", str(plain), "--report", str(rep2)],
        capture_output=True, text=True, cwd=str(ROOT))
    second = None
    if rep2.exists():
        d = json.loads(rep2.read_text())
        second = dict(cells=d["cells"], certified=d["certified"],
                      all_valid=d["all_valid"], total_nodes=d["total_nodes"],
                      exit_code=r.returncode)
    out = dict(
        tree_file=rel,
        tree_sha256=__import__("hashlib").sha256(
            (ROOT / rel).read_bytes()).hexdigest(),
        cells=len(trees),
        targets_in_the_file=sum(1 for x in rows if x["is_target"]),
        r164_validator=dict(
            all_valid=all(x["r164_validator"] for x in rows),
            proof_nodes=nodes, histogram_assertions=hist,
            histogram_discrepancies=sum(
                1 for x in rows if not x["r164_validator"]
                and "histogram" in str(x["detail"])),
            feas_form_checks=forms, feas_subset_checks=subset),
        r152_validator=second,
        caps_match_route_a=all(x["matches_route_a_cap"] for x in rows),
        cells_upper_certified_by_two_validators=[
            x["cell"] for x in rows if x["r164_validator"]],
        targets_upper_certified_by_two_validators=[
            x["cell"] for x in rows if x["r164_validator"] and x["is_target"]],
        rows=rows)
    out["ok"] = (out["r164_validator"]["all_valid"] and out["caps_match_route_a"]
                 and second is not None and second["all_valid"])
    (ROOT / "r164" / "certs" / "verifygen_164.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows",
                                   "cells_upper_certified_by_two_validators")},
                     ensure_ascii=False, indent=1))
    print("seconds:", round(time.time() - t0, 1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
