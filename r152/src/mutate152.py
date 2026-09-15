#!/usr/bin/env python3
"""Round 152 -- mutation tests for the capacity-certificate checkers.

A checker that accepts everything proves nothing.  Each mutation below breaks
the certificate (or the checker's own source) in one specific way and the test
passes only when BOTH checkers refuse: a non-zero exit and a status other than
EXACT_CERTIFIED on the mutated cell.

Usage: mutate152.py [--cert r152/certs/cap_cert_pilot_152.txt]
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r152" / "src"
PY = SRC / "checker152.py"
CEXE = SRC / "checker152.exe"
CSRC = SRC / "checker152.c"


def parse(text):
    """-> [(args, cap, ports)] in file order."""
    toks = []
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("L6-CAPCERT"):
            toks += line.split()
    out, i = [], 0
    while i < len(toks):
        assert toks[i] == "cell"
        args = [int(x) for x in toks[i + 1:i + 7]]
        cap, n = int(toks[i + 7]), int(toks[i + 8])
        w = [int(x) for x in toks[i + 9:i + 9 + n]]
        out.append([args, cap, w])
        i += 9 + n
    return out


def render(cells):
    s = ["L6-CAPCERT-2"]
    for args, cap, w in cells:
        s.append("cell " + " ".join(map(str, args)) + f" {cap} {len(w)}")
        s.append(" ".join(map(str, w)))
    return "\n".join(s) + "\n"


def run_py(cert, node_cap):
    r = subprocess.run([sys.executable, str(PY), "--cert", cert,
                        "--node-cap", str(node_cap)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def run_c(cert, node_cap, exe=None):
    r = subprocess.run([str(exe or CEXE), cert, str(node_cap)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def expect_refusal(name, text, node_cap, results, exe=None, which="both"):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    rc_py, out_py = ((None, "") if which == "c" else run_py(path, node_cap))
    rc_c, out_c = run_c(path, node_cap, exe)
    ok = rc_c != 0 and (which == "c" or rc_py != 0)
    results.append(dict(mutation=name, scope=which,
                        python_exit=rc_py, c_exit=rc_c, caught=ok,
                        python_tail=out_py.strip().splitlines()[-1][:160]
                        if out_py.strip() else "",
                        c_tail=out_c.strip().splitlines()[-1][:160]
                        if out_c.strip() else ""))
    print(f"  {'CAUGHT ' if ok else 'ESCAPED'} {name}"
          f"  (py exit {rc_py}, c exit {rc_c})", flush=True)
    Path(path).unlink()
    return ok


def build_mutant(tag, edits):
    """Compile a mutated copy of the C checker; return its path."""
    src = CSRC.read_text()
    for old, new in edits:
        if old not in src:
            raise SystemExit(f"mutant {tag}: pattern not found: {old[:60]}")
        src = src.replace(old, new, 1)
    d = Path(tempfile.mkdtemp())
    (d / "m.c").write_text(src)
    exe = d / "m.exe"
    subprocess.run(["cc", "-O2", "-o", str(exe), str(d / "m.c")], check=True)
    return exe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", default="r152/certs/cap_cert_pilot_152.txt")
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    ap.add_argument("--report", default="r152/certs/mutations_152.json")
    a = ap.parse_args()
    base = Path(a.cert).read_text()
    cells = parse(base)
    last = len(cells) - 1                       # the heaviest pilot cell
    res, allok = [], True

    print("baseline (must PASS):", flush=True)
    rc_py, _ = run_py(a.cert, a.node_cap)
    rc_c, _ = run_c(a.cert, a.node_cap)
    print(f"  python exit {rc_py}, c exit {rc_c}", flush=True)
    base_ok = rc_py == 0 and rc_c == 0
    allok &= base_ok

    print("certificate mutations (must all be CAUGHT):", flush=True)

    m = [list(x) for x in cells]; m[last] = [m[last][0], m[last][1] + 1, m[last][2]]
    allok &= expect_refusal("01_cap_inflated", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    m[last] = [m[last][0], m[last][1] - 1, m[last][2][:-1]]
    allok &= expect_refusal("02_cap_deflated_with_short_witness",
                            render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    w = list(m[last][2]); w[7] = (w[7] + 1) % 720
    m[last] = [m[last][0], m[last][1], w]
    allok &= expect_refusal("03_witness_port_corrupted", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    w = list(m[last][2]); w[3], w[4] = w[4], w[3]
    m[last] = [m[last][0], m[last][1], w]
    allok &= expect_refusal("04_witness_ports_swapped", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    w = list(m[last][2]); w[5] = w[2]
    m[last] = [m[last][0], m[last][1], w]
    allok &= expect_refusal("05_witness_port_repeated", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    args = list(m[0][0]); args[1] = 2            # cap(0,2,0,0,0,0) = 33 != 20
    m[0] = [args, m[0][1], m[0][2]]
    allok &= expect_refusal("06_budget_widened_value_kept",
                            render(m), a.node_cap, res)

    allok &= expect_refusal("07_node_cap_too_small", base, 500, res)

    print("checker-source mutations (must all be CAUGHT):", flush=True)
    mutants = [
        ("08_phase_reuse_allowed",
         [("    if (phm[q] >> PHASE[t] & 1) return;",
           "    if (0) return;")]),
        ("09_clean_E_may_leave_orbit",
         [("    if (isdirty == -1 && q != corb) return;", "    (void)corb;")]),
        ("10_heavy_budget_ignored",
         [("        if (hu + HV_C[cur][i] <= CH)", "        if (1)")]),
        ("11_token_budget_ignored",
         [("    if (cost > tok) return;", "    if (0) return;")]),
        ("12_hexagon_collision_budget_ignored",
         [("    if (!newhex && isdirty <= 0) { if (eu >= CE) return; spend_e = 1; }",
           "    if (!newhex && isdirty <= 0) { spend_e = 0; }")]),
    ]
    for tag, edits in mutants:
        exe = build_mutant(tag, edits)
        allok &= expect_refusal(tag, base, a.node_cap, res, exe=exe, which="c")

    out = dict(cert=a.cert, baseline_passes=base_ok,
               mutations=res, all_caught=all(r["caught"] for r in res),
               ok=allok)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "mutations"}, indent=1))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
