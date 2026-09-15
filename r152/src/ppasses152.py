#!/usr/bin/env python3
"""Round 152 -- drive the PIECE checker in passes until it reaches a fixpoint.

The twin of r152/src/passes152.py.  A cell that cannot be exhausted with the
bounds available in the ascending sweep is retried with the bounds the earlier
passes PROVED, with the cell excluded from its own table.  Cells that never
certify stay UNKNOWN_CAP; nothing is ever promoted.

usage: ppasses152.py --cert <pcert.txt> --out <verify.json> [--caps a,b,c]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, time
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from pmutate152 import parse, render                              # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exe", default=str(SRC / "piece152.exe"))
    ap.add_argument("--caps", default="30000000,300000000,3000000000,40000000000")
    a = ap.parse_args()
    caps = [int(float(x)) for x in a.caps.split(",")]
    cells = parse(Path(a.cert).read_text())
    key = lambda c: f"{c[0]}|{c[1]}|{c[2]}{c[3]}"                  # noqa: E731
    done, rows, mask00 = {}, {}, {}
    t0 = time.time()

    for i, cap in enumerate(caps):
        todo = [c for c in cells if key(c) not in done]
        if not todo:
            break
        prune = None
        if i:
            with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                             delete=False) as f:
                for (b, d), v in mask00.items():
                    f.write(f"{b} {d} {v}\n")
                prune = f.name
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(render(todo))
            cpath = f.name
        print(f"== pass {i + 1}: {len(todo)} cells, node cap {cap:,}, "
              f"prune list {len(mask00)} (b,d)", flush=True)
        cmd = [str(a.exe), "check", cpath, str(cap)] + ([prune] if prune else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        Path(cpath).unlink()
        if prune:
            Path(prune).unlink()
        try:
            doc = json.loads(r.stdout)
        except json.JSONDecodeError:
            raise SystemExit(f"checker produced no JSON (exit {r.returncode}):\n"
                             f"{r.stderr[-800:]}")
        new = 0
        for row in doc["rows"]:
            rows[row["cell"]] = row
            if row["status"] in GOOD:
                if row["cell"] not in done:
                    new += 1
                done[row["cell"]] = row["cap"]
                if row["fp"] == 0 and row["lp"] == 0 and row["cap"] >= 0:
                    mask00[(row["b"], row["d"])] = row["cap"]
            elif row["status"] == "DISAGREE":
                print(f"  DISAGREE on {row['cell']}", flush=True)
        print(f"   certified {len(done)}/{len(cells)} (+{new})  "
              f"{round(time.time() - t0)}s", flush=True)
        if not new and i:
            print("   no progress; stopping", flush=True)
            break

    ordered = [rows[key(c)] for c in cells if key(c) in rows]
    out = dict(checker="P152-passes", cert=a.cert, caps=caps,
               cells=len(cells), rows=ordered,
               certified=sum(r["status"] in GOOD for r in ordered),
               exact=sum(r["status"] == "EXACT_CERTIFIED" for r in ordered),
               unverified=[r["cell"] for r in ordered
                           if r["status"] not in GOOD],
               total_nodes=sum(r.get("nodes", 0) for r in ordered),
               seconds=round(time.time() - t0, 1))
    out["all_certified"] = not out["unverified"]
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows", "unverified")}, indent=1))
    print("unverified:", out["unverified"][:20])
    return 0 if out["all_certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
