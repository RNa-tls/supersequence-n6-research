"""Round 172 (EXPERIMENTAL) -- certified predecessor environments for the R1 experiment.

An environment is taken verbatim from an already-recorded Round 171 bulk job:
its `predecessor_refs` are re-hashed and closure-checked by the Round 171
`validate_dag` (container sha, plain sha, dep/closure consistency), and the
resulting predecessor set must reproduce the job's recorded
`predecessor_set_sha256`.  Nothing historical (Round 152 tables) is read.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r171" / "src"))
import bulk_j171 as BK                                            # noqa: E402

JOBS = "r171/certs/bulk_j171/jobs/"


def load_job_env(job_id):
    """(job, refs, dep, cert) for a recorded bulk job; asserts the recorded hash."""
    job = BK.load(JOBS + job_id + ".json")
    refs = [tuple(r) for r in job["predecessor_refs"]]
    dep = BK.validate_dag(refs)
    got = BK.canonical([(BK.text(k), v) for k, v in sorted(dep.items())])
    assert got == job["predecessor_set_sha256"], (job_id, got)
    assert BK.key(job["cell"]) not in dep, "target must not certify itself"
    cert = {k: v[0] for k, v in dep.items()}
    return job, refs, dep, cert


def deps_list(dep):
    return [(k, *v) for k, v in sorted(dep.items())]
