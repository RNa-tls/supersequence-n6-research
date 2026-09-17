#!/usr/bin/env python3
"""Round 166 -- independent verifier for the L6-EXTREE-2 certificate DAG.

It searches nothing.  For a batch it

  1. resolves every `ref` line, checks the referenced file's sha256 EXACTLY,
     and verifies that batch first (depth first, with cycle detection), so a
     certified value may only enter from a proof this run has checked;
  2. replays every tree with round 164's independent verifier (verifier B),
     which rebuilt the permutation geometry from string algebra and which
     asserts at EVERY node that the incrementally maintained feasibility
     histogram equals a from-scratch recomputation;
  3. optionally hands the flattened L6-EXTREE-1 form -- the referenced trees
     followed by this batch's -- to round 152's validator (verifier A), a
     separately written program, so two independent validators see the same
     proof object.

A cell counts as second-route certified only when a proof object for it is
accepted here.  The generator's word is never taken.
"""
from __future__ import annotations
import gzip, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
import routeb164 as R                                             # noqa: E402

SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")


def read_text(rel):
    p = ROOT / rel
    raw = p.read_bytes()
    text = gzip.decompress(raw).decode() if str(p).endswith(".gz") \
        else raw.decode()
    return text, hashlib.sha256(raw).hexdigest()


def parse_batch(text):
    """L6-EXTREE-2 (or a plain L6-EXTREE-1, which simply has no refs)."""
    lines = text.splitlines()
    assert lines[0] in ("L6-EXTREE-2", "L6-EXTREE-1"), lines[0]
    refs, trees, i = [], [], 1
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        if f[0] == "ref":
            refs.append((f[1], f[2]))
            i += 1
            continue
        assert f[0] == "tree", f[:2]
        cell = tuple(int(x) for x in f[1:7])
        capv = int(f[7])
        trees.append((cell, capv, lines[i + 1].split()))
        i += 2
    return refs, trees


def verify_chain(rel, verifier_a=True, _seen=None, _stack=None):
    """Verify a batch and everything it references.  Returns certified cells."""
    _seen = {} if _seen is None else _seen
    _stack = set() if _stack is None else _stack
    if rel in _seen:
        return _seen[rel]
    if rel in _stack:
        return dict(ok=False, path=rel, error="certificate dependency cycle",
                    certified={}, sha256=None)
    _stack.add(rel)
    text, digest = read_text(rel)
    refs, trees = parse_batch(text)

    certified, ref_rows, flat = {}, [], []
    for want_sha, ref_rel in refs:
        p = ROOT / ref_rel
        if not p.exists():
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={}, sha256=digest,
                        error=f"missing referenced certificate {ref_rel}")
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want_sha:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={}, sha256=digest,
                        error=f"reference hash mismatch for {ref_rel}: "
                              f"declared {want_sha[:16]}, actual {got[:16]}")
        sub = verify_chain(ref_rel, verifier_a=False, _seen=_seen,
                           _stack=_stack)
        if not sub["ok"]:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={}, sha256=digest,
                        error=f"referenced certificate failed: {ref_rel}",
                        inner=sub)
        certified.update(sub["certified"])
        flat.extend(sub["flat"])
        ref_rows.append(dict(path=ref_rel, sha256=got,
                             cells=len(sub["certified"])))

    nodes = hist = 0
    rows = []
    for cell, capv, toks in trees:
        v = R.TreeVerifier(dict(certified), check_feas_forms=False)
        ok, info = v.validate(cell, capv, toks)
        nodes += v.nodes
        hist += v.hist_checks
        rows.append(dict(cell="|".join(map(str, cell)), cap=capv,
                         nodes=v.nodes, verified=bool(ok),
                         detail=None if ok else info))
        if not ok:
            _stack.discard(rel)
            return dict(ok=False, path=rel, certified={}, sha256=digest,
                        error=f"tree invalid for {rows[-1]['cell']}: {info}",
                        rows=rows)
        certified[cell] = capv
        flat.append((cell, capv, toks))

    a_res = None
    if verifier_a:
        with tempfile.NamedTemporaryFile("w", suffix=".extree",
                                         delete=False,
                                         dir=str(SCRATCH)) as fh:
            fh.write("L6-EXTREE-1\n")
            for cell, capv, toks in flat:
                fh.write("\ntree " + " ".join(map(str, cell)) + f" {capv}\n")
                fh.write(" ".join(toks) + "\n")
            tmp = fh.name
        rep = SCRATCH / "verifier_a_report.json"
        r = subprocess.run(
            [sys.executable, str(ROOT / "r152" / "src" / "extree152.py"),
             "--tree", tmp, "--report", str(rep)],
            capture_output=True, text=True, cwd=str(ROOT))
        if rep.exists():
            d = json.loads(rep.read_text())
            a_res = dict(cells=d["cells"], certified=d["certified"],
                         all_valid=d["all_valid"], exit_code=r.returncode)
        Path(tmp).unlink(missing_ok=True)

    _stack.discard(rel)
    out = dict(ok=True, path=rel, sha256=digest, trees=len(trees),
               refs=ref_rows, proof_nodes=nodes, histogram_assertions=hist,
               histogram_mismatches=0, certified=certified, flat=flat,
               verifier_b_rows=rows, verifier_a=a_res)
    _seen[rel] = out
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_a = "--no-verifier-a" not in sys.argv
    report = None
    for a in sys.argv[1:]:
        if a.startswith("--report="):
            report = a.split("=", 1)[1]
    if not args:
        print("usage: extree_basis_verify.py <batch.gz> [...]",
              file=sys.stderr)
        return 2
    results = []
    for rel in args:
        res = verify_chain(rel, verifier_a=want_a)
        results.append(dict(
            path=rel, ok=res["ok"], sha256=res.get("sha256"),
            trees=res.get("trees"), proof_nodes=res.get("proof_nodes"),
            histogram_assertions=res.get("histogram_assertions"),
            histogram_mismatches=res.get("histogram_mismatches"),
            refs=res.get("refs"), verifier_a=res.get("verifier_a"),
            cells_certified=len(res.get("certified", {})),
            error=res.get("error")))
        if res["ok"]:
            results[-1]["certified_cells"] = sorted(
                "|".join(map(str, k)) for k in res["certified"])
        print(json.dumps({k: v for k, v in results[-1].items()
                          if k != "certified_cells"},
                         ensure_ascii=False, indent=1))
    if report:
        out = dict(batches=results,
                   all_ok=all(r["ok"] for r in results),
                   verifier_b="r164/src/routeb164.py TreeVerifier "
                              "(geometry rebuilt from string algebra; at every "
                              "node the incremental feasibility histogram is "
                              "compared with a from-scratch recomputation)",
                   verifier_a=("r152/src/extree152.py" if want_a
                               else "not run for these batches"))
        (ROOT / report).write_text(json.dumps(out, ensure_ascii=False,
                                              indent=1) + "\n")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
