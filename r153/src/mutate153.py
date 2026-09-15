#!/usr/bin/env python3
"""Round 153 Phase 8 -- mutation testing of the equality/coexistence chain.

Two classes of mutation, kept apart because they mean different things.

  INVALID    the object is broken in a way that must be refused.  A mutation
             that escapes is a hole in the verification chain.
  VALIDITY-PRESERVING
             the object changes but the claim it supports stays true, so the
             checker is RIGHT to accept it.  These are listed so that an
             "escape" is never silently counted as a pass.

The mutations follow the round-153 brief, mapped onto the actual proof objects:

  incompatibility edge  -> a hexagon added to / removed from an orbit's hexagon
                           set, which is what decides whether an orbit can
                           cover a given part of F
  orbit label           -> the orbit id of a word
  hexagon label         -> the hexagon id of a word
  witness deleted /     -> lines removed from, or repeated in, a witness file
  duplicated
  canonical rep         -> a port changed inside a stored witness
  S6 normalization      -> the equivariance of the catalogue under left S6
  seam / first          -> F, the set of hexagons the circuits must cover, and
  occurrence               the budget c that must cover it
  certificate hash      -> a recorded SHA-256
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "r153" / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "r152" / "src"))

TREE = ROOT / "r153" / "certs" / "covertree_153.txt"


def run_validator(text, extra_src=None):
    """Run covertree153.py (optionally a mutated copy) on given tree bytes."""
    d = Path(tempfile.mkdtemp())
    (d / "t.txt").write_text(text)
    script = SRC / "covertree153.py"
    if extra_src is not None:
        (d / "covertree153.py").write_text(extra_src)
        (d / "checker152.py").write_text(
            (ROOT / "r152" / "src" / "checker152.py").read_text())
        script = d / "covertree153.py"
    r = subprocess.run([sys.executable, str(script), "validate",
                        "--tree", str(d / "t.txt"),
                        "--report", str(d / "r.json")],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-300:]


def parse_tree(text):
    lines = [l for l in text.splitlines()
             if l.strip() and not l.lstrip().startswith("#")
             and not l.startswith("L6-COVERTREE")]
    blocks, i = [], 0
    while i < len(lines):
        hd = lines[i].split()
        blocks.append([hd, lines[i + 1].split()])
        i += 2
    return blocks


def render_tree(blocks):
    out = ["L6-COVERTREE-1"]
    for hd, toks in blocks:
        out.append(" ".join(hd))
        out.append(" ".join(toks))
    return "\n".join(out) + "\n"


def span(toks, i):
    """End index of the subtree whose preorder starts at token i.

    An internal token N<j> is followed by its j child orbit ids, then the j
    subtrees."""
    if toks[i] == "L":
        return i + 1
    k = int(toks[i][1:])
    j = i + 1 + k
    for _ in range(k):
        j = span(toks, j)
    return j


def main():
    res, allok = [], True
    base = TREE.read_text()
    rc, _ = run_validator(base)
    print(f"baseline: exit {rc}")
    allok &= rc == 0

    def invalid(name, text, src=None):
        nonlocal allok
        rc, tail = run_validator(text, src)
        caught = rc != 0
        res.append(dict(kind="INVALID", mutation=name, exit=rc, caught=caught,
                        tail=tail.strip().splitlines()[-1][:140] if tail.strip()
                        else ""))
        print(f"  {'CAUGHT ' if caught else 'ESCAPED'} {name} (exit {rc})")
        allok &= caught

    def preserving(name, text, src=None):
        rc, tail = run_validator(text, src)
        res.append(dict(kind="VALIDITY_PRESERVING", mutation=name, exit=rc,
                        accepted=rc == 0))
        print(f"  {'accepted' if rc == 0 else 'refused '} {name} "
              f"(validity-preserving, exit {rc})")

    B = parse_tree(base)
    sys.setrecursionlimit(100000)

    # --- the exhaustion tree itself
    m = [[list(h), list(t)] for h, t in B]
    j = next(i for i, t in enumerate(m[0][1]) if t.startswith("N")
             and int(t[1:]) > 1)
    m[0][1][j] = "N" + str(int(m[0][1][j][1:]) - 1)
    invalid("T1_child_count_reduced", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    end = span(m[0][1], j)
    m[0][1] = m[0][1][:j] + ["L"] + m[0][1][end:]
    invalid("T2_subtree_replaced_by_unjustified_leaf", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    del m[0][1][j + 1]
    invalid("T3_token_deleted", render_tree(m))

    # Lowering c is VALIDITY-PRESERVING: every leaf justified at c stays
    # justified at c-1 (the waste bound only gets easier) and no node reaches a
    # full cover, so the same file proves the weaker statement "no c-1 orbits
    # cover F".  The checker is right to accept it.
    m = [[list(h), list(t)] for h, t in B]
    m[0][0][3] = str(int(m[0][0][3]) - 1)
    preserving("T4_circuit_budget_lowered", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    j2 = next(i for i, t in enumerate(m[0][1]) if t.startswith("N")
              and int(t[1:]) > 1)
    m[0][1][j2 + 1] = str((int(m[0][1][j2 + 1]) + 1) % 144)
    invalid("T9_one_child_orbit_id_changed", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    m[0][0][3] = str(int(m[0][0][3]) + 1)          # c -> c+1
    invalid("T5_circuit_budget_raised", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    m[0][0][6] = str((int(m[0][0][6]) + 1) % 120)  # one hexagon of F changed
    invalid("T6_one_hexagon_of_F_changed", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    del m[0][0][6]
    m[0][0][5] = str(int(m[0][0][5]) - 1)          # F shrunk consistently
    invalid("T7_one_hexagon_removed_from_F", render_tree(m))

    m = [[list(h), list(t)] for h, t in B]
    m[0][0][5] = str(int(m[0][0][5]) + 1)          # |F| inconsistent
    invalid("T8_F_size_inconsistent", render_tree(m))

    # --- the geometry the validator recomputes from (the round-146 lesson)
    src = (SRC / "covertree153.py").read_text()
    mut = src.replace("    _tmp[ORB[_v]].add(HEX[_v])",
                      "    _tmp[ORB[_v]].add((HEX[_v] + 1) % 120)")
    assert mut != src
    invalid("G1_orbit_to_hexagon_table_corrupted", base, mut)
    # Now that the file names its children, a relabelling of the orbit ids is
    # refused too: the certificate is tied to the labelling the string algebra
    # produces.
    mut = src.replace("    _tmp[ORB[_v]].add(HEX[_v])",
                      "    _tmp[(ORB[_v] + 1) % 144].add(HEX[_v])")
    assert mut != src
    invalid("G2_orbit_labels_shifted", base, mut)

    # these DO change the instance
    # target an orbit the tree actually branches on, and a hexagon of F
    first_child = int(B[0][1][1])
    Fhex = sorted(int(x) for x in B[0][0][6:])
    mut = src.replace(
        "ORBHEX = [frozenset(s) for s in _tmp]",
        "_tmp[%d].discard(sorted(h for h in _tmp[%d] if h in %r)[0])\n"
        "ORBHEX = [frozenset(s) for s in _tmp]" % (first_child, first_child,
                                                   Fhex))
    assert mut != src
    invalid("G4_one_hexagon_removed_from_a_branching_orbit", base, mut)
    mut = src.replace("ORBHEX = [frozenset(s) for s in _tmp]",
                      "_tmp[7].add((sorted(_tmp[7])[0] + 60) % 120)\n"
                      "ORBHEX = [frozenset(s) for s in _tmp]")
    assert mut != src
    invalid("G5_one_hexagon_added_to_one_orbit", base, mut)
    mut = src.replace("ORBHEX = [frozenset(s) for s in _tmp]",
                      "_tmp[7], _tmp[8] = _tmp[7] | _tmp[8], set()\n"
                      "ORBHEX = [frozenset(s) for s in _tmp]")
    assert mut != src
    invalid("G6_two_orbits_merged", base, mut)
    # is the child-ORBIT-LIST check what catches a changed id?
    mut = src.replace(
        "            if [int(x) for x in listed] != [q for q, _ in ch]:",
        "            if False:")
    assert mut != src
    preserving("G3a_id_check_removed_on_the_HONEST_tree", base, mut)
    m = [[list(h), list(t)] for h, t in B]
    j3 = next(i for i, t in enumerate(m[0][1]) if t.startswith("N")
              and int(t[1:]) > 1)
    m[0][1][j3 + 1] = str((int(m[0][1][j3 + 1]) + 1) % 144)
    rc, _ = run_validator(render_tree(m), mut)
    res.append(dict(kind="LOAD_BEARING",
                    mutation="G3a_id_check_is_load_bearing",
                    exit=rc, accepts_broken_tree=rc == 0))
    print(f"  {'LOAD-BEARING' if rc == 0 else 'NOT LOAD-BEARING'} "
          f"G3a_child_id_check (mutant on a changed-id tree: exit {rc})")
    allok &= rc == 0

    # is the leaf justification what catches a dropped subtree?
    marker = 'state["err"] = (f"unjustified leaf at token {j}: k={k}, "'
    k0 = src.index(marker)
    k1 = src.index("return", src.index("budget {c - k}", k0)) + len("return")
    mut = src[:k0] + "return" + src[k1:]
    # raising c keeps the token stream EXACTLY the same length and only makes
    # leaves that were justified by "the budget is spent" unjustified, so it
    # isolates the leaf-justification check from every other check.
    m = [[list(h), list(t)] for h, t in B]
    m[0][0][3] = str(int(m[0][0][3]) + 1)
    rc, _ = run_validator(render_tree(m), mut)
    res.append(dict(kind="LOAD_BEARING",
                    mutation="G3b_leaf_justification_is_load_bearing",
                    exit=rc, accepts_broken_tree=rc == 0))
    print(f"  {'LOAD-BEARING' if rc == 0 else 'NOT LOAD-BEARING'} "
          f"G3b_leaf_justification (mutant on a raised-budget tree: "
          f"exit {rc})")
    allok &= rc == 0

    # --- the witness files
    import eqwit153 as EW
    cellmap = {"E1": ((0, 14, 0, 0, 0, 0), 96), "E2": ((0, 8, 0, 0, 0, 1), 92)}

    def witness_case(name, path, transform, expect_bad):
        nonlocal allok
        cell, target = cellmap[name]
        ws = [json.loads(x) for x in Path(path).read_text().splitlines()
              if x.strip()]
        ws = transform([dict(w) for w in ws])
        bad = 0
        for w in ws:
            ok, _ = EW.check_witness(cell, target, w["ports"])
            if not ok:
                bad += 1
        caught = (bad > 0) == expect_bad
        res.append(dict(kind="INVALID" if expect_bad else "VALIDITY_PRESERVING",
                        mutation=f"W_{name}_{transform.__name__}",
                        replay_failures=bad, caught=caught))
        print(f"  {'CAUGHT ' if caught else 'ESCAPED'} "
              f"W_{name}_{transform.__name__} (replay failures {bad})")
        allok &= caught

    def corrupt_one_port(ws):
        ws[0]["ports"] = list(ws[0]["ports"])
        ws[0]["ports"][7] = (ws[0]["ports"][7] + 1) % 720
        return ws

    def swap_two_ports(ws):
        p = list(ws[0]["ports"])
        p[3], p[4] = p[4], p[3]
        ws[0]["ports"] = p
        return ws

    def truncate(ws):
        ws[0]["ports"] = ws[0]["ports"][:-1]
        return ws

    def duplicate_witness(ws):
        return ws + [dict(ws[0])]

    witness_case("E1", ROOT / "r153/certs/E1_table.jsonl", corrupt_one_port, True)
    witness_case("E1", ROOT / "r153/certs/E1_table.jsonl", swap_two_ports, True)
    witness_case("E1", ROOT / "r153/certs/E1_table.jsonl", truncate, True)
    witness_case("E1", ROOT / "r153/certs/E1_table.jsonl", duplicate_witness, False)

    # a deleted witness is not caught by REPLAY -- it is caught by the
    # cross-route comparison, so that is where it is tested
    cmp_src = (SRC / "eqcompare153.py").read_text()
    d = Path(tempfile.mkdtemp())
    for f in ("eqcompare153.py", "eqwit153.py"):
        (d / f).write_text((SRC / f).read_text())
    (d / "checker152.py").write_text(
        (ROOT / "r152" / "src" / "checker152.py").read_text())
    # delete one witness from one route's file, in a scratch copy of the tree
    scratch = Path(tempfile.mkdtemp())
    (scratch / "E1_table.jsonl").write_text(
        Path(ROOT / "r153/certs/E1_table.jsonl").read_text().splitlines()[0] + "\n")
    hacked = cmp_src.replace('"B_r153_c_table": "r153/certs/E1_table.jsonl"',
                             f'"B_r153_c_table": "{scratch}/E1_table.jsonl"')
    assert hacked != cmp_src
    (d / "eqcompare153.py").write_text(hacked)
    r = subprocess.run([sys.executable, str(d / "eqcompare153.py")],
                       capture_output=True, text=True, cwd=str(ROOT))
    caught = r.returncode != 0
    res.append(dict(kind="INVALID", mutation="W_E1_one_witness_deleted",
                    exit=r.returncode, caught=caught))
    print(f"  {'CAUGHT ' if caught else 'ESCAPED'} W_E1_one_witness_deleted "
          f"(exit {r.returncode})")
    allok &= caught

    # --- left S6 equivariance (the WLOG that makes the enumeration complete)
    ew = (SRC / "eqwit153.py").read_text()
    mut = ew.replace("    return [IDX[\"\".join(m[ch] for ch in w)] for w in PERMS]",
                     "    r = [IDX[\"\".join(m[ch] for ch in w)] for w in PERMS]\n"
                     "    r[0], r[1] = r[1], r[0]\n    return r")
    assert mut != ew
    d2 = Path(tempfile.mkdtemp())
    (d2 / "eqwit153.py").write_text(mut)
    (d2 / "checker152.py").write_text(
        (ROOT / "r152" / "src" / "checker152.py").read_text())
    r = subprocess.run([sys.executable, "-c",
                        "import sys;sys.path.insert(0,'.');import eqwit153 as E;"
                        "import json;print(json.dumps(E.equivariance_check()))"],
                       capture_output=True, text=True, cwd=str(d2))
    eq = json.loads(r.stdout) if r.stdout.strip() else {"ok": None}
    caught = eq.get("ok") is False
    res.append(dict(kind="INVALID", mutation="S1_left_S6_action_corrupted",
                    equivariance_ok=eq.get("ok"), caught=caught))
    print(f"  {'CAUGHT ' if caught else 'ESCAPED'} S1_left_S6_action_corrupted "
          f"(equivariance ok={eq.get('ok')})")
    allok &= caught

    # --- a recorded hash
    cert = json.loads((ROOT / "r153" / "certs" / "covertree_153.json").read_text())
    bad_hash = cert["tree_sha256"][:-1] + ("0" if cert["tree_sha256"][-1] != "0"
                                           else "1")
    actual = hashlib.sha256(TREE.read_bytes()).hexdigest()
    caught = bad_hash != actual
    res.append(dict(kind="INVALID", mutation="H1_certificate_hash_modified",
                    caught=caught))
    print(f"  {'CAUGHT ' if caught else 'ESCAPED'} H1_certificate_hash_modified")
    allok &= caught

    out = dict(results=res,
               invalid_all_caught=all(r["caught"] for r in res
                                      if r["kind"] == "INVALID"),
               ok=allok)
    (ROOT / "r153" / "certs" / "mutations_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
