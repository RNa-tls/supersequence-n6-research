#!/usr/bin/env python3
"""Round 173 -- the general-n MASTER decomposition applied, for the first time,
to verified literature superpermutations for n = 5..9 (archive
github.com/superpermutators/superperm).  Uses the round-156/160 general-n
code unchanged (r156/src/extract156.structure, r160/src/master160.master)."""
import glob, gzip, json, os, re, sys, time
from collections import Counter
from math import factorial
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r160" / "src")); sys.path.insert(0, str(ROOT / "r156" / "src"))
sys.path.insert(0, str(ROOT))
import master160 as M
import extract156 as X
from src.verify import verify_superpermutation
SPL = Path(sys.argv[1])
def strings(p, n):
    raw = open(p, "rb").read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    txt = raw.decode("utf-8", "replace")
    return [t for t in re.findall(r"[1-9]+", txt) if len(t) >= factorial(n)]
rows = []
for n in (5, 6, 7, 8, 9):
    files = sorted(f for f in glob.glob(str(SPL / "superpermutations" / str(n) / "*")) if os.path.isfile(f))
    seen = set()
    for f in files:
        for s in strings(f, n):
            alph = "".join(sorted(set(s)))
            if len(alph) != n or s in seen:
                continue
            seen.add(s)
            if not verify_superpermutation(s, n, alphabet=alph)["valid"]:
                continue
            t0 = time.time()
            try:
                st = X.structure(s, n)
                r = M.master(st)
                row = dict(n=n, file=os.path.basename(f), L=len(s), ok=r["ok"],
                           fixedrep=st["fixed"], **{k: r[k] for k in
                           ("CONST", "t", "k", "Z", "H", "Bstar", "P", "G", "S", "O", "c", "D2", "Qs", "h")},
                           failures=[str(x)[:120] for x in r["failures"][:3]])
            except Exception as e:
                row = dict(n=n, file=os.path.basename(f), L=len(s), ok=None,
                           error=f"{type(e).__name__}: {e}"[:160])
            row["seconds"] = round(time.time() - t0, 1)
            rows.append(row)
    (ROOT / "r173/certs/master_bign_173.json").write_text(json.dumps(rows, indent=1) + "\n")
    c = Counter((r.get("ok"), r.get("error", "")[:40]) for r in rows if r["n"] == n)
    print(n, dict(c), flush=True)
