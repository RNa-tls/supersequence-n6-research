#!/usr/bin/env python3
"""Round 152 -- drive the C checker in PASSES until it reaches a fixpoint.

Why passes.  The checker may only prune with values it has PROVED, and in a
single ascending sweep a cell with tokens to spend looks up budget vectors that
no earlier cell dominates, so its tree stays huge.  The fix is to iterate:

  pass 1   ascending order, a small node cap.  Cheap cells get certified.
  pass n   retry only the cells still UNKNOWN_CAP, this time pruning with
           everything PROVED so far (r152/src/checker152.c's third argument),
           with the cell itself excluded from its own table.

This is still (P1) and still acyclic: a value used to certify cell K was proved
in a run where K was not certified, so nothing can depend on K.  The node cap
grows each pass.  Cells that never certify stay UNKNOWN_CAP and are reported as
such -- they are never promoted.

usage: passes152.py --cert <cert.txt> --out <verify.json> [--caps 1e8,1e9,...]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, time
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from mutate152 import parse, render                                # noqa: E402

GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")


def run_checker(exe, cert_text, node_cap, prune_path):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(cert_text)
        p = f.name
    cmd = [str(exe), p, str(node_cap)] + ([prune_path] if prune_path else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    Path(p).unlink()
    try:
        doc = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"checker produced no JSON (exit {r.returncode}):\n"
                         f"{r.stderr[-800:]}")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exe", default=str(SRC / "checker152.exe"))
    ap.add_argument("--caps", default="150000000,2000000000,20000000000,"
                                      "80000000000")
    a = ap.parse_args()
    caps = [int(float(x)) for x in a.caps.split(",")]
    cells = parse(Path(a.cert).read_text())
    key = lambda c: "|".join(map(str, c[0]))                       # noqa: E731
    done, rows = {}, {}
    t0 = time.time()

    for i, cap in enumerate(caps):
        todo = [c for c in cells if key(c) not in done]
        if not todo:
            break
        prune = None
        if i:
            with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                             delete=False) as f:
                for k, v in done.items():
                    f.write(" ".join(k.split("|")) + f" {v}\n")
                prune = f.name
        print(f"== pass {i + 1}: {len(todo)} cells, node cap {cap:,}, "
              f"prune list {len(done)} cells", flush=True)
        doc = run_checker(a.exe, render(todo), cap, prune)
        if prune:
            Path(prune).unlink()
        new = 0
        for r in doc["rows"]:
            rows[r["cell"]] = r
            if r["status"] in GOOD:
                if r["cell"] not in done:
                    new += 1
                done[r["cell"]] = r["cap"]
            elif r["status"] == "DISAGREE":
                print(f"  DISAGREE on {r['cell']}: {r.get('detail')}",
                      flush=True)
        print(f"   certified so far {len(done)}/{len(cells)} (+{new} this pass)"
              f"  {round(time.time() - t0)}s", flush=True)
        if not new and i:
            print("   no progress; stopping", flush=True)
            break

    ordered = [rows[key(c)] for c in cells if key(c) in rows]
    out = dict(checker="C152-passes", cert=a.cert, caps=caps,
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
    print(f"unverified: {out['unverified'][:20]}"
          f"{' ...' if len(out['unverified']) > 20 else ''}")
    return 0 if out["all_certified"] else 1


if __name__ == "__main__":
    sys.exit(main())
