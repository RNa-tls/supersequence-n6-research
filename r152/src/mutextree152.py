#!/usr/bin/env python3
"""Round 152 -- mutation tests for the explicit-exhaustion-tree validator.

Two kinds of test, because "the validator rejects broken files" and "the
validator's checks are what does the rejecting" are different claims.

  A. CERTIFICATE mutations.  The tree file is damaged in one specific way and
     the unmutated validator must report TREE_INVALID (non-zero exit).
  B. SOURCE mutations.  One check is removed from a COPY of the validator, and
     that copy must then ACCEPT the very file the real validator rejected.
     A source mutation that changes nothing means the check was not doing the
     work its comment claims.
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
VAL = SRC / "extree152.py"


def tokens(text):
    return [t for line in text.splitlines()
            for t in line.split("#")[0].split()
            if not t.startswith("L6-EXTREE")]


def render(toks):
    out, i = ["L6-EXTREE-1"], 0
    while i < len(toks):
        if toks[i] == "tree":
            out.append(" ".join(toks[i:i + 8]))
            i += 8
            continue
        out.append(toks[i])
        i += 1
    return "\n".join(out) + "\n"


def run(val, tree):
    with tempfile.NamedTemporaryFile("w", suffix=".extree", delete=False) as f:
        f.write(tree)
        p = f.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        rep = f.name
    r = subprocess.run([sys.executable, str(val), "--tree", p,
                        "--report", rep], capture_output=True, text=True)
    Path(p).unlink()
    Path(rep).unlink(missing_ok=True)
    return r.returncode, (r.stdout + r.stderr)[-400:]


def mutant(edits):
    src = VAL.read_text()
    for old, new in edits:
        if old not in src:
            raise SystemExit(f"pattern not found: {old[:60]}")
        src = src.replace(old, new, 1)
    d = Path(tempfile.mkdtemp())
    (d / "extree152.py").write_text(src)
    # the mutant must still import the real catalogue module
    (d / "checker152.py").write_text((SRC / "checker152.py").read_text())
    return d / "extree152.py"


def span(toks, i):
    """End index of the subtree whose preorder starts at token i."""
    if toks[i] == "L":
        return i + 1
    j = i + 1
    for _ in range(int(toks[i][1:])):
        j = span(toks, j)
    return j


def first_internal(toks):
    for i, t in enumerate(toks):
        if t.startswith("N") and t != "N0" and int(t[1:]) > 0:
            return i
    raise SystemExit("no internal node found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default="r152/certs/extree_pilot_152.txt")
    ap.add_argument("--report", default="r152/certs/mutations_extree_152.json")
    a = ap.parse_args()
    base = Path(a.tree).read_text()
    toks = tokens(base)
    res, allok = [], True

    rc, out = run(VAL, base)
    print(f"baseline exit {rc}")
    allok &= rc == 0

    # ---- A. certificate mutations
    def damaged(name, newtoks):
        nonlocal allok
        text = render(newtoks)
        rc, out = run(VAL, text)
        caught = rc != 0
        res.append(dict(kind="certificate", mutation=name, exit=rc,
                        caught=caught, tail=out.strip().splitlines()[-1][:160]
                        if out.strip() else ""))
        print(f"  {'CAUGHT ' if caught else 'ESCAPED'} {name} (exit {rc})")
        allok &= caught
        return text

    j = first_internal(toks)
    m = list(toks); m[j] = "N" + str(int(m[j][1:]) - 1)
    t_childcount = damaged("A1_child_count_reduced", m)

    m = list(toks); m[j] = "L"
    t_leafswap = damaged("A2_internal_node_replaced_by_leaf", m)

    m = list(toks); del m[j + 1]
    damaged("A3_token_deleted", m)

    m = list(toks)
    k = next(i for i, t in enumerate(m) if t == "tree")
    m[k + 7] = str(int(m[k + 7]) - 1)
    t_caplow = damaged("A4_cap_lowered", m)

    m = list(toks); m[j] = "N99"
    damaged("A5_child_count_inflated", m)

    # a whole subtree replaced by an unjustified leaf: the stream stays
    # well-formed, so only the leaf justification can catch this one
    sys.setrecursionlimit(100000)
    end = span(toks, j)
    m = toks[:j] + ["L"] + toks[end:]
    t_subtree = damaged("A6_subtree_dropped_stream_still_well_formed", m)

    # ---- B. source mutations: the check must be what catches it
    checks = [
        ("B1_child_count_check_removed",
         [("            if k != len(ms):", "            if False:")],
         t_childcount),
        ("B2_leaf_justification_removed",
         [('                state["err"] = (f"unjustified leaf at token {i}: '
           'ports={ports} "\n                                f"deficit={deficit} '
           'r1={r1} r2={r2}")\n                return',
           "                return")],
         t_subtree),
        ("B3_reach_check_removed",
         [('            if ports >= cap + 1 and deficit <= dmax:',
           "            if False:")],
         t_caplow),
    ]
    for name, edits, broken in checks:
        mv = mutant(edits)
        rc, out = run(mv, broken)
        accepts = rc == 0
        res.append(dict(kind="source", mutation=name, exit=rc,
                        check_is_load_bearing=accepts))
        print(f"  {'LOAD-BEARING' if accepts else 'NOT LOAD-BEARING'} {name} "
              f"(mutant exit {rc})")
        allok &= accepts

    out = dict(tree=a.tree, results=res,
               all_certificate_mutations_caught=all(
                   r["caught"] for r in res if r["kind"] == "certificate"),
               all_checks_load_bearing=all(
                   r["check_is_load_bearing"] for r in res
                   if r["kind"] == "source"),
               ok=allok)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
