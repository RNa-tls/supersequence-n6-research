#!/usr/bin/env python3
"""Round 153 -- verify the explicit length-872 cover from first principles.

A superpermutation on n = 6 is a word over {1..6} every one of whose 720
permutations appears as a contiguous window.  This reads the stored word,
checks the alphabet, slides a window of six over it, and requires all 720
permutations to be present.  Nothing else is consulted.
"""
from __future__ import annotations
import hashlib, itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
P = ROOT / "data" / "verified_872_witness.txt"


def main():
    raw = P.read_bytes()
    w = raw.decode().strip()
    perms = {"".join(p) for p in itertools.permutations("123456")}
    windows = {w[i:i + 6] for i in range(len(w) - 5)}
    covered = perms & windows
    out = dict(file=str(P.relative_to(ROOT)),
               sha256=hashlib.sha256(raw).hexdigest(),
               bytes=len(raw), length=len(w),
               alphabet=sorted(set(w)),
               alphabet_ok=set(w) == set("123456"),
               permutations_needed=len(perms),
               permutations_covered=len(covered),
               missing=sorted(perms - covered)[:5],
               is_superpermutation=len(covered) == 720,
               length_is_872=len(w) == 872)
    out["ok"] = out["alphabet_ok"] and out["is_superpermutation"] \
        and out["length_is_872"]
    (ROOT / "r153" / "certs" / "witness872_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
