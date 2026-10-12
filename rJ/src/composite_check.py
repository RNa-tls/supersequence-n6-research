#!/usr/bin/env python3
"""Composite certificate check: a top certificate whose delegated leaves are each closed by a subtree
certificate.  Runs chainset_check.py on the top (collecting its delegated fixing sets) and on every
subtree (with the top's validated global fixings), then checks that every delegated leaf is matched by
exactly one complete subtree certificate with the same initial fixings and the same T and arc list."""
import sys, os, json, subprocess, tempfile, gzip
def jload(path):
    return json.load(gzip.open(path, 'rt') if path.endswith('.gz') else open(path))
word, top, subs = sys.argv[1], sys.argv[2], sys.argv[3:]
PY = sys.executable; CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chainset_check.py")
dl = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
r = subprocess.run([PY, "-I", CK, word, top], capture_output=True, text=True, env=dict(os.environ, DELEG_OUT=dl))
assert r.returncode == 0, r.stderr[-2000:]
topres = json.loads(r.stdout.strip().splitlines()[-1]); delegated = [sorted(map(tuple, d)) for d in json.load(open(dl))]
T = jload(top); need = {tuple(d): False for d in delegated}
for sf in subs:
    S = jload(sf)
    assert S["T"] == T["T"] and S["arcs"] == T["arcs"] and S["complete"], f"{sf}: mismatch/incomplete"
    key = tuple(sorted(map(tuple, S["init_fix"])))
    assert key in need and not need[key], f"{sf}: not a delegated leaf (or duplicate)"
    r = subprocess.run([PY, "-I", CK, word, sf, top], capture_output=True, text=True)
    assert r.returncode == 0, f"{sf}: " + r.stderr[-2000:]
    sub = json.loads(r.stdout.strip().splitlines()[-1]); assert sub["delegated"] == 0
    need[key] = True
missing = [k for k, v in need.items() if not v]
assert not missing, f"{len(missing)} delegated leaves without a subtree certificate"
print(json.dumps(dict(ok=True, top_leaves=topres["leaves"], delegated=len(delegated), subtrees=len(subs), T=T["T"],
                      theorem=f"every route on this chain set has weight >= {T['T']}, length >= {T['BASE'] + T['T']}")))
