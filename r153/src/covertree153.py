#!/usr/bin/env python3
"""Round 153 -- EXPLICIT exhaustion trees for the coexistence exclusions.

"No c tau-orbits cover F" is a complete case analysis over a small tree, so the
tree is written down rather than re-searched.  Format L6-COVERTREE-1, a preorder
token stream per witness:

    cover <name> <index> <c> <restricted> <|F|> <f0 f1 ... >
    <tokens>

    N<j>   an internal node: the j children are EXACTLY the candidate orbits
           whose hexagon set contains the LOWEST hexagon of F still uncovered,
           listed in increasing orbit id
    L      a leaf, justified by one of two PROVED facts:
             (k) the budget is spent: c orbits are already chosen
             (w) what is left cannot be covered: more than 5*(c-k) hexagons of
                 F are still uncovered and a tau-orbit meets five hexagons

The validator performs NO SEARCH.  At each node it recomputes the lowest
uncovered hexagon and the candidate list from the geometry itself, insists the
file lists exactly those children, checks every leaf's justification, and checks
that no node ever reaches a full cover.  Reaching a full cover would be a
counterexample, and the validator says so.

The branching rule loses nothing: any cover must cover the lowest uncovered
hexagon, so some chosen orbit contains it.

produce:  covertree153.py produce --out r153/certs/covertree_153.txt
validate: covertree153.py validate --tree r153/certs/covertree_153.txt
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
sys.path.insert(0, str(ROOT / "r153" / "src"))
from checker152 import HEX, ORB, N                                  # noqa: E402

NH, NQ = 120, 144
ORBHEX = [frozenset() for _ in range(NQ)]
_tmp = [set() for _ in range(NQ)]
for _v in range(N):
    _tmp[ORB[_v]].add(HEX[_v])
ORBHEX = [frozenset(s) for s in _tmp]


def instance(ports, c, restricted):
    Hc = {HEX[v] for v in ports}
    Oc = {ORB[v] for v in ports}
    F = sorted(set(range(NH)) - Hc)
    idx = {h: i for i, h in enumerate(F)}
    cands = []
    for q in range(NQ):
        if restricted and q in Oc:
            continue
        m = 0
        for h in ORBHEX[q]:
            if h in idx:
                m |= 1 << idx[h]
        if m:
            cands.append((q, m))
    return F, cands, (1 << len(F)) - 1


def children(cands, mask, n):
    low = min(i for i in range(n) if not mask >> i & 1)
    return low, sorted((q, m) for q, m in cands if m >> low & 1)


def produce(witnesses, out_path):
    lines = ["L6-COVERTREE-1",
             "# cover <name> <index> <c> <restricted> <|F|> <hexagons of F>",
             "# then a preorder stream: N<j> internal, L leaf (budget spent or",
             "# more than 5*(c-k) hexagons of F still uncovered)"]
    stats = []
    for name, index, ports, c, restricted in witnesses:
        F, cands, FULL = instance(ports, c, restricted)
        n = len(F)
        toks, nodes = [], 0

        def rec(mask, k):
            nonlocal nodes
            nodes += 1
            if mask == FULL:
                raise SystemExit(f"{name}#{index}: a cover EXISTS -- refuted")
            if k == c or bin(FULL ^ mask).count("1") > 5 * (c - k):
                toks.append("L")
                return
            low, ch = children(cands, mask, n)
            toks.append(f"N{len(ch)}")
            for q, m in ch:
                rec(mask | m, k + 1)

        rec(0, 0)
        lines.append(f"cover {name} {index} {c} {int(restricted)} {n} "
                     + " ".join(map(str, F)))
        lines.append(" ".join(toks))
        stats.append(dict(name=name, index=index, c=c, restricted=restricted,
                          F=n, nodes=nodes, tokens=len(toks)))
    Path(out_path).write_text("\n".join(lines) + "\n")
    return stats


def validate(path):
    text = Path(path).read_text()
    if not text.startswith("L6-COVERTREE-1"):
        raise SystemExit("not an L6-COVERTREE-1 file")
    rows, ok = [], True
    lines = [l for l in text.splitlines()
             if l.strip() and not l.lstrip().startswith("#")
             and not l.startswith("L6-COVERTREE")]
    i = 0
    while i < len(lines):
        hd = lines[i].split()
        if hd[0] != "cover":
            raise SystemExit(f"expected 'cover', saw {hd[0]!r}")
        name, index, c, restricted, n = hd[1], int(hd[2]), int(hd[3]), \
            int(hd[4]), int(hd[5])
        F = [int(x) for x in hd[6:]]
        toks = lines[i + 1].split()
        i += 2
        if len(F) != n:
            raise SystemExit("|F| does not match the listed hexagons")
        idx = {h: j for j, h in enumerate(F)}
        FULL = (1 << n) - 1
        cands = []
        for q in range(NQ):
            m = 0
            for h in ORBHEX[q]:
                if h in idx:
                    m |= 1 << idx[h]
            if m:
                cands.append((q, m))
        # the validator cannot know which orbits the chain used unless it is
        # told; a RESTRICTED tree therefore has to name them, so restricted
        # trees are only accepted when they also validate UNRESTRICTED.
        state = dict(pos=0, err=None, nodes=0)

        def walk(mask, k):
            if state["err"]:
                return
            state["nodes"] += 1
            j = state["pos"]
            if j >= len(toks):
                state["err"] = "token stream ended early"
                return
            tk = toks[j]
            state["pos"] = j + 1
            if mask == FULL:
                state["err"] = f"the tree reaches a FULL cover at token {j}"
                return
            if tk == "L":
                if k == c:
                    return
                if bin(FULL ^ mask).count("1") > 5 * (c - k):
                    return
                state["err"] = (f"unjustified leaf at token {j}: k={k}, "
                                f"{bin(FULL ^ mask).count('1')} hexagons left, "
                                f"budget {c - k}")
                return
            if not tk.startswith("N"):
                state["err"] = f"bad token {tk!r} at {j}"
                return
            want = int(tk[1:])
            low, ch = children(cands, mask, n)
            if want != len(ch):
                state["err"] = (f"token {j} says {want} children, the state has "
                                f"{len(ch)} orbits containing hexagon {F[low]}")
                return
            for q, m in ch:
                walk(mask | m, k + 1)
                if state["err"]:
                    return

        sys.setrecursionlimit(10000)
        walk(0, 0)
        row = dict(name=name, index=index, c=c, restricted=bool(restricted),
                   F=n, nodes=state["nodes"], tokens=len(toks))
        if state["err"]:
            row.update(status="TREE_INVALID", detail=state["err"])
            ok = False
        elif state["pos"] != len(toks):
            row.update(status="TREE_INVALID",
                       detail=f"{len(toks) - state['pos']} tokens left over")
            ok = False
        else:
            row["status"] = "EXCLUDED"
        rows.append(row)
    return dict(tree=str(path),
                tree_sha256=hashlib.sha256(text.encode()).hexdigest(),
                rows=rows, all_excluded=ok)


def load(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("produce", "validate"))
    ap.add_argument("--tree", default="r153/certs/covertree_153.txt")
    ap.add_argument("--report", default="r153/certs/covertree_153.json")
    a = ap.parse_args()
    if a.mode == "produce":
        wits = []
        for name, path, c in (("E1", "r153/certs/E1_table.jsonl", 6),
                              ("E2", "r153/certs/E2_table.jsonl", 7)):
            p = ROOT / path
            if not p.exists():
                print(f"  missing {path}, skipped")
                continue
            for i, w in enumerate(load(p)):
                wits.append((name, i, w["ports"], c, False))
        st = produce(wits, a.tree)
        print(json.dumps(st, indent=1))
        return 0
    r = validate(a.tree)
    Path(a.report).write_text(json.dumps(r, indent=1) + "\n")
    for row in r["rows"]:
        print(f"  {row['name']}#{row['index']} c={row['c']} |F|={row['F']} "
              f"{row['status']} nodes={row['nodes']}"
              + (f"  {row.get('detail')}" if row.get("detail") else ""))
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
    return 0 if r["all_excluded"] else 1


if __name__ == "__main__":
    sys.exit(main())
