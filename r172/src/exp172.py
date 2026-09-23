#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- bounded OLD vs R1 side-by-side runs.

usage: exp172.py --job <recorded bulk job id> --mode old|r1 --cap N [--tag T]

The job id fixes the certified predecessor environment (re-hashed, recorded
predecessor_set_sha256 reproduced) and the target bound J.  Both modes use the
same move order and the same node-cap semantics.  Output:
r172/certs/exp/<cell>_<mode>_c<cap>_<env>.json, and on completion the tree
(old: L6-EXTREE-3 byte-identical to gen168; r1: L6-EXTREE-4).
Nothing here is a production certificate.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time, resource
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
import env172 as E                                                # noqa: E402
import gen172 as X                                                # noqa: E402

OUT = "r172/certs/exp/"


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--mode", choices=["old", "r1"], required=True)
    ap.add_argument("--cap", type=int, required=True)
    ap.add_argument("--no-tree", action="store_true")
    ap.add_argument("--cell", default=None,
                    help="target other than the job's own (same environment)")
    ap.add_argument("--bound", type=int, default=None)
    a = ap.parse_args()
    job, refs, dep, cert = E.load_job_env(a.job)
    if a.cell:
        job = dict(job, cell=a.cell, bound=a.bound)
        assert a.bound is not None
    cell = E.BK.key(job["cell"])
    assert cell not in cert, "target certified in this environment"
    bound = job["bound"]
    envtag = a.job.rsplit("_", 1)[-1]
    name = f"{job['cell'].replace('|', '_')}_{a.mode}_c{a.cap}_{envtag}"
    g = X.Engine172(cert, a.cap, a.mode)
    t0 = time.monotonic()
    toks, err = g.build(cell, bound)
    secs = time.monotonic() - t0
    status = "COMPLETED" if toks is not None else (
        "DEFERRED" if "node cap" in (err or "") else "REFUTED_WALK_FOUND")
    row = dict(status=status, detail=err, cell=job["cell"], bound=bound,
               target=bound + 1, node_cap=a.cap,
               environment_job=a.job,
               predecessor_set_sha256=job["predecessor_set_sha256"],
               predecessor_count=len(dep),
               generator_sha256=dict(gen172=sha("r172/src/gen172.py"),
                                     gen168=sha("r168/src/gen168.py"),
                                     exp172=sha("r172/src/exp172.py")),
               **g.telemetry(),
               seconds_noncanonical=round(secs, 1),
               peak_rss_kb_noncanonical=resource.getrusage(
                   resource.RUSAGE_SELF).ru_maxrss,
               semantics="EXPERIMENTAL bounded diagnostic; DEFERRED is not "
                         "refutation; not a production certificate")
    if toks is not None and not a.no_tree:
        deps = E.deps_list(dep)
        if a.mode == "old":
            rel = OUT + "trees/" + name + ".extree3.txt.gz"
            (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
            text = X.G.write_batch(ROOT / rel, refs, deps,
                                   [(cell, bound, " ".join(toks))])
        else:
            rel = OUT + "trees/" + name + ".extree4.txt.gz"
            text = X.write_batch4(ROOT / rel, refs, deps,
                                  [(cell, bound, " ".join(toks))])
        row["tree"] = dict(path=rel, sha256=sha(rel),
                           plain_sha256=hashlib.sha256(text.encode()).hexdigest(),
                           tokens=len(toks))
    del toks
    p = ROOT / OUT / (name + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(row, indent=1) + "\n")
    c = row["counters"]
    print(name, status, "nodes", g.nodes, "tokens", g.ntok,
          "old_p", c.get("leaf_p_old", 0), "r1_only", c.get("leaf_r1_only", 0),
          f"{secs:.1f}s", flush=True)


if __name__ == "__main__":
    main()
