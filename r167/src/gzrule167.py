#!/usr/bin/env python3
"""Round 167 phase 18 -- what exactly is hash pinned in a compressed artifact.

Round 166 found that regenerating a batch to a DIFFERENT path produced
different `.gz` bytes and recorded it as a property.  The cause is specific:

    gzip.GzipFile(fileobj=raw, mtime=0)

leaves `filename` unset, and `GzipFile.__init__` then falls back to
`getattr(fileobj, "name", "")`, so the output path is written into the gzip
FNAME header field.  `mtime=0` removes the other source of nondeterminism but
not this one.

Two rules follow, and this module implements both.

  (G1)  THE PINNED PROOF OBJECT IS THE CANONICAL UNCOMPRESSED TEXT.
        Every manifest records `plain_sha256` alongside `sha256`.  The
        verifier reads the plain text, so `plain_sha256` is the hash that
        carries proof weight; the container hash is provenance only.

  (G2)  A COMPRESSED ARTIFACT IS WRITTEN WITH AN EMPTY FNAME.
        `write_gz` below passes `filename=""` explicitly, so the container is
        a pure function of the text and is reproducible from any path.

The round-164 and round-166 artifacts are NOT rewritten: their container
hashes are already pinned in audited manifests and rewriting them would
invalidate a reproduction claim that was made and checked.  They are instead
re-pinned by `plain_sha256` here, which is the hash that matters, and the new
rule applies to everything generated from round 168 on.
"""
from __future__ import annotations
import gzip, hashlib, io, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BATCHES = ("r164/certs/extree_prefix_164.txt.gz",
           "r166/certs/extree_batch2_166.txt.gz",
           "r166/certs/extree_batch3_166.txt.gz")


def write_gz(path: Path, text: str) -> bytes:
    """(G2) deterministic, path-independent gzip container."""
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", compresslevel=9, mtime=0,
                       fileobj=buf) as fh:
        fh.write(text.encode())
    data = buf.getvalue()
    path.write_bytes(data)
    return data


def plain_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 22)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fname_field(path: Path) -> str:
    """The FNAME the container carries, '' when the rule is honoured."""
    with open(path, "rb") as fh:
        head = fh.read(10)
        if len(head) < 10 or head[:2] != b"\x1f\x8b":
            return "(not gzip)"
        if not head[3] & 0x08:
            return ""
        out = b""
        while True:
            c = fh.read(1)
            if not c or c == b"\x00":
                break
            out += c
        return out.decode("latin-1")


def main():
    # the rule demonstrated: same text, two paths, identical bytes
    text = "L6-EXTREE-2\n# demonstration\ntree 0 0 0 0 0 0 20\nL\n"
    a = write_gz(ROOT / "r167" / "certs" / "gzrule_a.gz", text)
    b = write_gz(ROOT / "r167" / "certs" / "gzrule_b_other_name.gz", text)
    old = io.BytesIO()
    with open(ROOT / "r167" / "certs" / "gzrule_old.gz", "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9,
                           mtime=0) as fh:
            fh.write(text.encode())
    old_fname = fname_field(ROOT / "r167" / "certs" / "gzrule_old.gz")

    pinned = {}
    for rel in BATCHES:
        p = ROOT / rel
        pinned[rel] = dict(
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            plain_sha256=plain_sha256(p),
            container_fname=fname_field(p),
            bytes=p.stat().st_size)

    out = dict(
        rule_G1="the pinned proof object is the canonical uncompressed text; "
                "manifests carry plain_sha256 and the verifier reads the "
                "plain text, so the container hash is provenance only",
        rule_G2="compressed artifacts are written with filename='' so the "
                "container is a pure function of the text; applies from "
                "round 168 on, existing artifacts are re-pinned not rewritten",
        demonstration=dict(
            two_paths_same_bytes=(a == b),
            new_container_fname=fname_field(
                ROOT / "r167" / "certs" / "gzrule_a.gz"),
            old_container_fname=old_fname,
            old_rule_leaks_the_path=old_fname != "",
            cause="GzipFile falls back to fileobj.name when filename is None"),
        existing_artifacts=pinned,
    )
    out["ok"] = (out["demonstration"]["two_paths_same_bytes"]
                 and out["demonstration"]["new_container_fname"] == ""
                 and out["demonstration"]["old_rule_leaks_the_path"])
    for n in ("gzrule_a.gz", "gzrule_b_other_name.gz", "gzrule_old.gz"):
        (ROOT / "r167" / "certs" / n).unlink()
    (ROOT / "r167" / "certs" / "gzip_rule_167.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
