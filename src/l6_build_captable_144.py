#!/usr/bin/env python3
"""Build the marked-capacity table C(b,D,mask) with the two C searchers.

Runs `outputs/l6cap_p_144.exe` once per (b,D) cell, feeding every cell already
proved back in as the suffix upper bound, so deep deficits become reachable.
Each cell records its own node count, whether it was capped, and the
unpruned cross-check where one was run.

Usage: l6_build_captable_144.py [--model AB|ABS|A] b:dmax [b:dmax ...]
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE_P = ROOT / "outputs" / "l6cap_p_144.exe"
EXE = ROOT / "outputs" / "l6cap_144.exe"
MODEL = "AB"
OUT = ROOT / "outputs" / "rr_l6_marked_capacity_table_144.json"
UB = ROOT / "outputs" / "rr_l6_capacity_ub_144.txt"


def load():
    if OUT.exists():
        return json.loads(OUT.read_text())
    return dict(tables={}, cells={}, bmax={}, dmax=0,
                note="C(b,D,mask); mask=fp lp, 1 means that endpoint clean-E "
                     "block is REQUIRED partial (<5 ports). -1 = infeasible.")


def write_ub(st):
    lines = []
    for b, tab in st["tables"].items():
        for key, val in tab.items():
            d, mask = key.split("|")
            if mask == "00" and val >= 0:
                lines.append(f"{b} {d} {val}")
    UB.write_text("\n".join(lines) + "\n")


def run_cell(b, d, model=None, cap=0):
    model = model or MODEL
    write_ub(STATE)
    t0 = time.time()
    r = subprocess.run([str(EXE_P), str(b), str(d), model, str(cap), str(UB)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"cell b={b} d={d} failed: {r.stderr[:400]}")
    c = json.loads(r.stdout)
    c["wall"] = round(time.time() - t0, 1)
    return c


STATE = load()

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--model":
        MODEL = args[1]
        args = args[2:]
        if MODEL != "AB":
            OUT = ROOT / "outputs" / f"rr_l6_marked_capacity_table_{MODEL}_144.json"
            UB = ROOT / "outputs" / f"rr_l6_capacity_ub_{MODEL}_144.txt"
            STATE = load()
    for spec in args:
        b, dmax = (int(x) for x in spec.split(":"))
        tab = STATE["tables"].setdefault(str(b), {})
        for d in range(0, dmax + 1):
            if f"{d}|00" in tab and STATE["cells"].get(f"{b}|{d}", {}).get("capped") is False:
                continue
            c = run_cell(b, d)
            for m in ("00", "10", "01", "11"):
                tab[f"{d}|{m}"] = c["table"][f"{d}|{m}"]
            STATE["cells"][f"{b}|{d}"] = dict(
                nodes=c["nodes"], capped=c["capped"], seconds=c["seconds"],
                wall=c["wall"], pruned=c["pruned"], model=c["model"])
            STATE["bmax"][str(b)] = max(STATE["bmax"].get(str(b), 0), d)
            STATE["dmax"] = max(STATE["dmax"], d)
            OUT.write_text(json.dumps(STATE, ensure_ascii=False, indent=1))
            print(f"b={b} d={d:2d}  " + " ".join(
                "%s=%-4d" % (m, tab[f'{d}|{m}']) for m in ("00", "10", "01", "11")) +
                f"  nodes={c['nodes']:,} wall={c['wall']}s capped={c['capped']}",
                flush=True)
    write_ub(STATE)
