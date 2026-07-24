#!/usr/bin/env python3
"""Computational cross-check of UNIQUE_WEIGHT2_MOVE_THEOREM.md's proof:
tail_permutations(2) has exactly one element, and the 6 A2 candidate
targets (ell=0..5) are literally p_0 composed with 6 FIXED group
elements independent of p_0 -- verified against several different p_0
values directly, not just asserted.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "legacy_research" / "work"


def _load(name: str, filename: str):
    path = WORK / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


macro = _load("auwm_macro", "superperm_partial_f1_macro.py")
exact = macro.exact
core = exact.core


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "outputs" / "unique_weight2_move_verification.json"))
    args = parser.parse_args()

    w1 = core.tail_permutations(1)
    w2 = core.tail_permutations(2)
    w3 = core.tail_permutations(3)

    action = core.tail_action(2, w2[0])
    sigma_powers = [core.power(core.SIGMA, ell) for ell in range(6)]
    fixed_elements = [core.compose(s, action) for s in sigma_powers]

    # verify: for several different p0, target(ell) == compose(p0, fixed_elements[ell])
    import random
    random.seed(0)
    sample_p0s = [core.IDENTITY] + [tuple(random.sample(range(6), 6)) for _ in range(10)]
    checks = []
    all_match = True
    for p0 in sample_p0s:
        for ell in range(6):
            p_ell = core.compose(p0, sigma_powers[ell])
            target_direct = core.word_after(p_ell, action)
            target_via_fixed = core.compose(p0, fixed_elements[ell])
            match = target_direct == target_via_fixed
            all_match = all_match and match
            checks.append({"p0": p0, "ell": ell, "match": match})

    report = {
        "schema": "unique-weight2-move-verification-v1",
        "tail_permutations_1_count": len(w1),
        "tail_permutations_2_count": len(w2),
        "tail_permutations_2_elements": list(w2),
        "tail_permutations_3_count": len(w3),
        "unique_weight2_action": list(action),
        "fixed_elements_sigma_ell_times_action": [list(e) for e in fixed_elements],
        "formula_verified_over_sample": {
            "sample_p0_count": len(sample_p0s),
            "total_checks": len(checks),
            "all_match": all_match,
        },
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({
        "wrote": args.output,
        "tail_permutations_2_count": len(w2),
        "formula_verified": all_match,
    }, indent=2))


if __name__ == "__main__":
    main()
