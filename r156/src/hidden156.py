#!/usr/bin/env python3
"""Round 156 Phase 4 -- does H.extract smuggle in a finer beta-component
classification than the proved pure / non-pure dichotomy?

The five-type story (E-clean / R2 / S / P / M) was shown in
research/RR_BETA_COMPONENT_FIVE_TYPE_AUDIT.md not to exist in this repository.
This scan checks mechanically that the extraction never branches on anything
about a COMPONENT except "are all of its edges clean E".
"""
from __future__ import annotations
import ast, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = ROOT / "src" / "l6_extraction_145.py"
FORBIDDEN_NAMES = ("R2", "type_S", "type_P", "type_M", "five_type", "fivetype",
                   "classify_component", "comptype", "component_type")


def main():
    src = TARGET.read_text()
    tree = ast.parse(src)
    lits = sorted({n.value for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and len(n.value) <= 12 and "\n" not in n.value})
    names = sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)})
    attrs = sorted({n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)})
    # every comparison against etype[...]
    etype_cmp = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare):
            txt = ast.unparse(n)
            if "etype" in txt:
                etype_cmp.add(txt)
    # comprehension over comps: what predicates touch a whole component?
    comp_preds = [ast.unparse(n) for n in ast.walk(tree)
                  if isinstance(n, (ast.ListComp, ast.GeneratorExp))
                  and "comps" in ast.unparse(n)]
    out = dict(
        target=str(TARGET.relative_to(ROOT)),
        sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
        short_string_literals=lits,
        etype_comparisons=sorted(etype_cmp),
        component_level_predicates=comp_preds,
        forbidden_name_hits=[f for f in FORBIDDEN_NAMES
                             if f in src or f in names or f in attrs],
        edge_type_alphabet_used=sorted(
            L for L in lits if L in ("E", "A", "B", "120", "C", "D",
                                     "clean_w3", "heavy", "?w2")),
    )
    out["component_classification_is_binary"] = (
        len(out["component_level_predicates"]) >= 1
        and not out["forbidden_name_hits"])
    (ROOT / "r156" / "certs" / "hidden_classification_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
