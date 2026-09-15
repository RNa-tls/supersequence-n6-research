#!/usr/bin/env python3
"""Round 152 -- do the two independent checkers agree, cell by cell?

Runs r152/src/checker152.exe and r152/src/checker152.py on the SAME certificate
bytes and compares status, cap and node count per cell.  Node counts agreeing is
not required for soundness -- the two only have to reach the same verdict -- but
when they do agree it says the two searches explored the same tree, which is a
much stronger statement than "both said yes".
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    ap.add_argument("--out", default="r152/certs/agreement_152.json")
    a = ap.parse_args()

    c = subprocess.run([str(SRC / "checker152.exe"), a.cert, str(a.node_cap)],
                       capture_output=True, text=True)
    cdoc = json.loads(c.stdout)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        rep = f.name
    p = subprocess.run([sys.executable, str(SRC / "checker152.py"),
                        "--cert", a.cert, "--node-cap", str(a.node_cap),
                        "--report", rep], capture_output=True, text=True)
    pdoc = json.loads(Path(rep).read_text())
    Path(rep).unlink()

    crows = {r["cell"]: r for r in cdoc["rows"]}
    prows = {r["cell"]: r for r in pdoc["rows"]}
    diffs = []
    for k in sorted(set(crows) | set(prows)):
        x, y = crows.get(k), prows.get(k)
        if x is None or y is None:
            diffs.append(dict(cell=k, issue="missing from one checker"))
            continue
        if x["status"] != y["status"] or x["cap"] != y["cap"]:
            diffs.append(dict(cell=k, c=x["status"], py=y["status"],
                              c_cap=x["cap"], py_cap=y["cap"]))
    nodes_differ = [k for k in crows
                    if k in prows and crows[k].get("nodes") != prows[k].get("nodes")]
    out = dict(cert=a.cert, node_cap=a.node_cap,
               c_exit=c.returncode, python_exit=p.returncode,
               cells=len(crows), verdict_differences=diffs,
               cells_with_different_node_counts=len(nodes_differ),
               examples=nodes_differ[:10],
               agree=(not diffs and c.returncode == p.returncode))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k != "verdict_differences"}, indent=1))
    if diffs:
        print(json.dumps(diffs[:20], indent=1))
    return 0 if out["agree"] else 1


if __name__ == "__main__":
    sys.exit(main())
