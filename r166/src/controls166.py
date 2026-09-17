#!/usr/bin/env python3
"""Round 166 phase 14 -- generator-bug controls.

A buggy generator must not be able to manufacture an accepted upper bound.
Each control patches the generator's own state update and requires that the
independent verifier REJECTS the tree it emits.  Cheap cells are used so the
whole suite runs in seconds; the verifier logic does not depend on size.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import routeb164 as R                                             # noqa: E402

GEN = ROOT / "r166" / "src" / "extree_basis_generator.py"

BUGS = {
    "wrong current orbit": (
        "                rec(t, q, ports + 1, tok - c,",
        "                rec(t, corb, ports + 1, tok - c,"),
    "stale histogram (phase not removed on backtrack)": (
        "                    phm[q].discard(R.PHASE[t])",
        "                    pass"),
    "incorrect token update (never charge a token)": (
        "                rec(t, q, ports + 1, tok - c,",
        "                rec(t, q, ports + 1, tok,"),
    "missing used-hexagon update": (
        "                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1",
        "                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0)"),
    "incorrect deficit update (+3 instead of +4)": (
        "                    deficit + (4 if fresh else -1))",
        "                    deficit + (3 if fresh else -1))"),
    "skipped legal branch (drop the last legal move)": (
        "            ms = legal(v, corb, tok, au, bu, eu, hu)",
        "            ms = legal(v, corb, tok, au, bu, eu, hu)[:-1] or "
        "legal(v, corb, tok, au, bu, eu, hu)"),
}

CELLS = 12          # how many cells of the certificate order to generate
# The honest generator needs only a few thousand nodes for these cells.  A bug
# that destroys the pruning can diverge instead, so the cap is set far above
# the honest cost but low enough that divergence is caught quickly; the report
# distinguishes "the verifier rejected the tree" from "the generator diverged".
NODE_CAP = 2_000_000


def load_generator(src):
    ns = {"__file__": str(GEN), "__name__": "gen_mutated"}
    exec(compile(src, "gen_mutated", "exec"), ns)
    return ns["Generator"]


def try_generate(Gen, order, cap):
    """Generate trees for the first CELLS cells, then verify each."""
    certified, bad = {}, None
    for i in range(CELLS):
        cell = order[i]
        C = cap[cell]["cap"]
        g = Gen(certified, NODE_CAP)
        try:
            toks, err = g.build(cell, C)
        except Exception as e:
            return dict(stage="generate", cell="|".join(map(str, cell)),
                        rejected_by="generator crashed",
                        detail=f"{type(e).__name__}: {e}"[:110])
        if toks is None:
            return dict(stage="generate", cell="|".join(map(str, cell)),
                        rejected_by="generator diverged past the node cap",
                        detail=str(err)[:110])
        v = R.TreeVerifier(dict(certified), check_feas_forms=False)
        ok, info = v.validate(cell, C, toks)
        if not ok:
            return dict(stage="verify", cell="|".join(map(str, cell)),
                        rejected_by="independent verifier",
                        detail=str(info)[:130])
        certified[cell] = C
    return None


def main():
    src = GEN.read_text()
    cap, order = R.parse_capcert(ROOT / "r152" / "certs"
                                 / "cap_cert_all_152.txt")
    rows = []
    # control: the unpatched generator must produce accepted trees
    clean = try_generate(load_generator(src), order, cap)
    rows.append(dict(control="unpatched generator (control)",
                     patch_applied=True, rejected=clean is not None,
                     expected_rejected=False,
                     correct=clean is None, detail=clean))
    for name, (old, new) in BUGS.items():
        mutated = src.replace(old, new, 1)
        applied = mutated != src
        res = try_generate(load_generator(mutated), order, cap) if applied \
            else None
        rows.append(dict(control=name, patch_applied=applied,
                         rejected=res is not None, expected_rejected=True,
                         correct=(applied and res is not None),
                         detail=res))
    out = dict(
        generator=str(GEN.relative_to(ROOT)),
        generator_sha256=hashlib.sha256(src.encode()).hexdigest(),
        cells_per_control=CELLS,
        controls=len(BUGS),
        applied=sum(1 for r in rows[1:] if r["patch_applied"]),
        caught=sum(1 for r in rows[1:] if r["correct"]),
        caught_by_the_verifier=sum(
            1 for r in rows[1:]
            if r["correct"] and r["detail"]
            and r["detail"]["rejected_by"] == "independent verifier"),
        caught_by_divergence=sum(
            1 for r in rows[1:]
            if r["correct"] and r["detail"]
            and r["detail"]["rejected_by"] != "independent verifier"),
        missed=[r["control"] for r in rows[1:] if not r["correct"]],
        control_case_passes=rows[0]["correct"],
        rows=rows)
    out["ok"] = (out["control_case_passes"] and not out["missed"]
                 and out["applied"] == len(BUGS))
    (ROOT / "r166" / "certs" / "generator_controls_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    for r in rows:
        print(f"  {r['control']:<52} "
              f"{'rejected' if r['rejected'] else 'accepted':<9} "
              f"{'OK' if r['correct'] else 'MISSED'}"
              + (f"  <- {r['detail']['rejected_by']}" if r['detail'] else ""))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
