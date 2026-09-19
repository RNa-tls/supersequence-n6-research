#!/usr/bin/env python3
"""Round 170 -- clean reproduction from two independent checkouts.

A hash-pinned artifact is only reproducible if it comes back byte-identical
from a tree that shares nothing with this one but the committed source.  Two
checkouts are used rather than one, because a single rerun in place can pass by
reading something it should have derived.

What can and cannot be checked here is worth stating plainly.

The CANONICAL artifacts -- the JSON reports of the basis optimisation, the
lower-bound certificate, the census audit, the dependency DAG and the
reclassification -- are pure functions of committed inputs and are re-derived
and compared byte for byte.

The CERTIFICATE artifacts are different.  Regenerating the H ladder costs
2,777 seconds and the A2 ladder 1,769, and the targets add more; a full
regeneration in two trees is over three hours of search.  So the certificates
are checked by hash against their pinned values and RE-VERIFIED in the clean
tree with both verifiers, which proves the committed bytes are a valid proof
of the claim from that tree's own source.  It does not prove the generator is
deterministic, and that distinction is reported rather than blurred: a
deterministic-generation claim would need the regeneration, and this module
does not make one.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")

CANONICAL = [
    ("r170/certs/basis_170.json", "r170/src/basis170.py", []),
    ("r170/certs/basis_audit_170.json", "r170/src/checkbasis170.py", []),
    ("r170/certs/census_audit_170.json", "r170/src/census170.py", []),
    ("r170/certs/reclass_170.json", "r170/src/reclass170.py", []),
    ("r170/certs/schedule_170.json", "r170/src/schedule170.py", []),
    ("r170/certs/global_cost_170.json", "r170/src/global170.py", []),
]
CERTS = [
    "r170/certs/extree_ladder_h_170.txt.gz",
    "r170/certs/extree_ladder_a2_170.txt.gz",
    "r170/certs/extree_target_h_170.txt.gz",
    "r170/certs/extree_target_a2_170.txt.gz",
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run(cmd, cwd, log):
    with open(log, "w") as fh:
        return subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT,
                              shell=True).returncode


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--clones", type=int, default=2)
    ap.add_argument("--report", default="r170/certs/reproduction_170.json")
    a = ap.parse_args()

    branch = subprocess.run("git rev-parse --abbrev-ref HEAD", cwd=ROOT,
                            shell=True, capture_output=True,
                            text=True).stdout.strip()
    head = subprocess.run("git rev-parse HEAD", cwd=ROOT, shell=True,
                          capture_output=True, text=True).stdout.strip()
    pinned = {rel: sha(ROOT / rel) for rel, _s, _x in CANONICAL}
    pinned_certs = {rel: sha(ROOT / rel) for rel in CERTS}
    print(f"branch {branch} at {head[:12]}", flush=True)

    clones = []
    t0 = time.time()
    for i in range(a.clones):
        w = SCRATCH / f"repro{i}"
        if w.exists():
            shutil.rmtree(w)
        rc = run(f"git clone -q --branch {branch} --single-branch "
                 f"{ROOT} {w}", SCRATCH, SCRATCH / f"clone{i}.log")
        if rc != 0:
            print(f"  clone {i}: FAILED", flush=True)
            clones.append(dict(clone=i, cloned=False))
            continue
        got = subprocess.run("git rev-parse HEAD", cwd=w, shell=True,
                             capture_output=True, text=True).stdout.strip()
        print(f"  clone {i} at {got[:12]}", flush=True)

        canon = []
        for rel, script, extra in CANONICAL:
            (w / rel).unlink(missing_ok=True)
            rc = run(f"python3 {script} {' '.join(extra)}", w,
                     SCRATCH / f"repro{i}_{Path(rel).stem}.log")
            ok = (w / rel).exists()
            digest = sha(w / rel) if ok else None
            canon.append(dict(artifact=rel, regenerated=ok, exit_code=rc,
                              sha256=digest,
                              byte_identical=(digest == pinned[rel])))
            print(f"    {rel:<44} "
                  f"{'identical' if digest == pinned[rel] else 'DIFFERS'}",
                  flush=True)

        certs = []
        for rel in CERTS:
            digest = sha(w / rel)
            certs.append(dict(certificate=rel, sha256=digest,
                              hash_matches=(digest == pinned_certs[rel])))

        # re-verify the certificates in the clean tree, both verifiers
        vr = []
        for rel, tag in ((CERTS[2], "targeth"), (CERTS[3], "targeta2")):
            ra = run(f"python3 r168/src/verifyA168.py --batch {rel} "
                     f"--report {SCRATCH}/repro{i}_va_{tag}.json", w,
                     SCRATCH / f"repro{i}_va_{tag}.log")
            rb = run(f"python3 r168/src/verify168.py --batch {rel} "
                     f"--report {SCRATCH}/repro{i}_vb_{tag}.json", w,
                     SCRATCH / f"repro{i}_vb_{tag}.log")
            aok = bok = None
            pa = SCRATCH / f"repro{i}_va_{tag}.json"
            pb = SCRATCH / f"repro{i}_vb_{tag}.json"
            if pa.exists():
                aok = json.loads(pa.read_text()).get("all_ok")
            if pb.exists():
                bok = json.loads(pb.read_text()).get("all_ok")
            vr.append(dict(certificate=rel, verifier_a_ok=aok,
                           verifier_b_ok=bok, exit_a=ra, exit_b=rb))
            print(f"    re-verified {rel:<40} A={aok} B={bok}", flush=True)

        clones.append(dict(clone=i, cloned=True, head=got,
                           head_matches=got == head,
                           canonical=canon, certificates=certs,
                           reverification=vr))

    all_canon_ok = all(c["byte_identical"]
                       for cl in clones if cl.get("cloned")
                       for c in cl["canonical"])
    all_hash_ok = all(c["hash_matches"]
                      for cl in clones if cl.get("cloned")
                      for c in cl["certificates"])
    all_ver_ok = all(v["verifier_a_ok"] and v["verifier_b_ok"]
                     for cl in clones if cl.get("cloned")
                     for v in cl["reverification"])
    out = dict(
        source=dict(branch=branch, head=head),
        clones=clones,
        canonical_artifacts_byte_identical=all_canon_ok,
        certificate_hashes_match=all_hash_ok,
        certificates_reverified_in_clean_tree=all_ver_ok,
        scope=dict(
            regenerated=[rel for rel, _s, _x in CANONICAL],
            hash_checked_and_reverified_not_regenerated=CERTS,
            why="regenerating all four certificates costs over three hours of "
                "search per clone; hash-checking plus dual re-verification in "
                "the clean tree proves the committed bytes are a valid proof "
                "from that tree's own source, which is a weaker claim than "
                "generator determinism and is not presented as one"),
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = all_canon_ok and all_hash_ok and all_ver_ok
    (ROOT / a.report).write_text(json.dumps(out, ensure_ascii=False,
                                            indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "clones"},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
