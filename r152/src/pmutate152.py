#!/usr/bin/env python3
"""Round 152 -- mutation tests for the marked-piece capacity checkers.

Same discipline as r152/src/mutate152.py: every mutation of the certificate
must be refused by BOTH checkers, and every mutation of the C checker's source
must make it refuse a certificate it otherwise accepts.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
PY_CHK = SRC / "piece152.py"
C_SRC = SRC / "piece152.c"
C_EXE = SRC / "piece152.exe"


def parse(text):
    toks = [t for line in text.splitlines()
            for t in line.split("#")[0].split()
            if not t.startswith("L6-PIECECERT")]
    out, i = [], 0
    while i < len(toks):
        assert toks[i] == "pcell", toks[i]
        b, d, fp, lp, cap, n = (int(x) for x in toks[i + 1:i + 7])
        w = [int(x) for x in toks[i + 7:i + 7 + n]]
        out.append([b, d, fp, lp, cap, w])
        i += 7 + n
    return out


def render(cells):
    s = ["L6-PIECECERT-1"]
    for b, d, fp, lp, cap, w in cells:
        s.append(f"pcell {b} {d} {fp} {lp} {cap} {len(w)}")
        s.append(" ".join(map(str, w)))
    return "\n".join(s) + "\n"


def run_py(cert, cap):
    r = subprocess.run([sys.executable, str(PY_CHK), "--cert", cert,
                        "--node-cap", str(cap)], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-300:]


def run_c(cert, cap, exe=None):
    r = subprocess.run([str(exe or C_EXE), "check", cert, str(cap)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-300:]


def build_mutant(tag, edits):
    src = C_SRC.read_text()
    for old, new in edits:
        if old not in src:
            raise SystemExit(f"{tag}: pattern not found: {old[:60]}")
        src = src.replace(old, new, 1)
    d = Path(tempfile.mkdtemp())
    (d / "piece152.c").write_text(src)
    (d / "checker152.c").write_text((SRC / "checker152.c").read_text())
    exe = d / "m.exe"
    subprocess.run(["cc", "-O2", "-I", str(d), "-o", str(exe),
                    str(d / "piece152.c")], check=True)
    return exe


def expect(name, text, cap, res, exe=None, which="both"):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text)
        p = f.name
    rc_py, out_py = ((None, "") if which == "c" else run_py(p, cap))
    rc_c, out_c = run_c(p, cap, exe)
    ok = rc_c != 0 and (which == "c" or rc_py != 0)
    res.append(dict(mutation=name, scope=which, python_exit=rc_py,
                    c_exit=rc_c, caught=ok))
    print(f"  {'CAUGHT ' if ok else 'ESCAPED'} {name} (py {rc_py}, c {rc_c})",
          flush=True)
    Path(p).unlink()
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cert", default="r152/certs/pcert_mut_152.txt")
    ap.add_argument("--node-cap", type=int, default=200_000_000)
    ap.add_argument("--report", default="r152/certs/mutations_piece_152.json")
    a = ap.parse_args()
    base = Path(a.cert).read_text()
    cells = parse(base)
    wit = [i for i, c in enumerate(cells) if c[5]]
    last = wit[-1]
    neg = [i for i, c in enumerate(cells) if c[4] < 0]
    res, allok = [], True

    rc_py, _ = run_py(a.cert, a.node_cap)
    rc_c, _ = run_c(a.cert, a.node_cap)
    print(f"baseline: py {rc_py}, c {rc_c}")
    allok &= rc_py == 0 and rc_c == 0

    m = [list(x) for x in cells]; m[last] = list(m[last]); m[last][4] += 1
    allok &= expect("P1_cap_inflated", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    m[last] = [*m[last][:4], m[last][4] - 1, m[last][5][:-1]]
    allok &= expect("P2_cap_deflated_with_short_witness", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    w = list(m[last][5]); w[3] = (w[3] + 1) % 720
    m[last] = [*m[last][:5], w]
    allok &= expect("P3_witness_port_corrupted", render(m), a.node_cap, res)

    m = [list(x) for x in cells]
    w = list(m[last][5]); w[2], w[3] = w[3], w[2]
    m[last] = [*m[last][:5], w]
    allok &= expect("P4_witness_ports_swapped", render(m), a.node_cap, res)

    if neg:
        i = neg[0]
        # An unreachable mask given a POSITIVE cap and no witness is not an
        # error: -1 means no piece exists, so any number is a valid UPPER
        # bound, and the checker is right to accept it.  What must be refused
        # is a WITNESS for a mask that has none, so that is the mutation.
        m = [list(x) for x in cells]
        m[i] = [*m[i][:4], len(cells[last][5]), list(cells[last][5])]
        allok &= expect("P5_unreachable_mask_given_a_borrowed_witness",
                        render(m), a.node_cap, res)
        m = [list(x) for x in cells]
        j = next(k for k, c in enumerate(cells)
                 if c[4] >= 0 and (c[2] or c[3]) and c[5])
        m[j] = [*m[j][:4], -1, []]     # claim a reachable mask is unreachable
        allok &= expect("P6_reachable_mask_claimed_unreachable",
                        render(m), a.node_cap, res)

    # Dropping the mask only proves anything on a cell where the mask BINDS,
    # i.e. where the unconstrained capacity is strictly larger.
    binding = [k for k, c in enumerate(cells)
               if (c[2] or c[3]) and c[5]
               and any(o[0] == c[0] and o[1] == c[1] and o[2] == 0 and o[3] == 0
                       and o[4] > c[4] for o in cells)]
    if binding:
        j = binding[-1]
        m = [list(x) for x in cells]
        mm = list(m[j]); mm[2] = 0; mm[3] = 0
        m[j] = mm
        allok &= expect("P7_binding_mask_dropped_value_kept",
                        render(m), a.node_cap, res)

    allok &= expect("P8_node_cap_too_small", base, 300, res)

    print("checker-source mutations:")
    for tag, edits in [
        ("P9_hex_simplicity_dropped_for_paid",
         [("        if (hexu[HEXID[t]]) continue;", "        if (0) continue;")]),
        ("P10_token_budget_ignored",
         [("if (!fresh) { if (phm[q] >> PHASE[t] & 1) continue; if (tok < 1) continue; }",
           "if (!fresh) { if (phm[q] >> PHASE[t] & 1) continue; }")]),
        ("P11_first_block_mask_ignored",
         [("        if ((!PFP || fl < 5) && (!PLP || curlen < 5)) {",
           "        if ((1) && (!PLP || curlen < 5)) {")]),
    ]:
        exe = build_mutant(tag, edits)
        allok &= expect(tag, base, a.node_cap, res, exe=exe, which="c")

    out = dict(cert=a.cert, results=res,
               all_caught=all(r["caught"] for r in res), ok=allok)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
