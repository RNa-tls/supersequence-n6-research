"""Round 172 (EXPERIMENTAL) -- small complete test trees for the verifiers and the
mutation suite.  Each fixture cell is searched at its known witness value J
in the e5 environment with every certified dominator of the cell removed
(otherwise the root would close by (p) and nothing would be exercised).
These are test objects, not production certificates."""
from __future__ import annotations
import hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
import env172 as E                                                # noqa: E402
import gen172 as X                                                # noqa: E402

ENV_JOB = "1_6_3_0_1_0_c50000000_e5"
CELLS = [((1, 1, 0, 0, 0, 0), 35), ((1, 2, 0, 0, 0, 0), 48),
         ((1, 4, 0, 0, 0, 0), 61), ((1, 2, 1, 0, 0, 0), 48)]
DIR = "r172/certs/test/"


def reduced(cell):
    job, refs, dep, cert = E.load_job_env(ENV_JOB)
    keep = {k: v for k, v in dep.items()
            if not all(a >= b for a, b in zip(k, cell))}
    return refs, keep


def name(cell, J, mode):
    return DIR + "_".join(map(str, cell)) + f"_J{J}_{mode}"


def build(cell, J, mode, cap=5_000_000):
    refs, dep = reduced(cell)
    g = X.Engine172({k: v[0] for k, v in dep.items()}, cap, mode)
    toks, err = g.build(cell, J)
    assert toks is not None, err
    return refs, E.deps_list(dep), toks, g


def write(cell, J, mode, rel=None):
    refs, deps, toks, g = build(cell, J, mode)
    if mode == "old":
        rel = rel or name(cell, J, mode) + ".extree3.txt.gz"
        (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
        text = X.G.write_batch(ROOT / rel, refs, deps, [(cell, J, " ".join(toks))])
    else:
        rel = rel or name(cell, J, mode) + ".extree4.txt.gz"
        text = X.write_batch4(ROOT / rel, refs, deps, [(cell, J, " ".join(toks))])
    return rel, hashlib.sha256(text.encode()).hexdigest(), g


if __name__ == "__main__":
    import json
    rows = []
    for c, J in CELLS:
        for mode in ("old", "r1"):
            rel, psha, g = write(c, J, mode)
            rows.append(dict(cell="|".join(map(str, c)), J=J, mode=mode, path=rel,
                             plain_sha256=psha, nodes=g.nodes, counters=dict(g.t)))
            print(rel, g.nodes, flush=True)
    (ROOT / DIR / "fixtures.json").write_text(json.dumps(dict(
        title="fixture trees (test objects, dominators removed; EXPERIMENTAL)",
        environment_job=ENV_JOB, rows=rows), indent=1) + "\n")
