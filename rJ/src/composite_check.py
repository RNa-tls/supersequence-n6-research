#!/usr/bin/env python3
"""Composite certificate check: a top certificate whose delegated leaves are each closed by a subtree
certificate; subtree certificates may themselves delegate leaves (nested delegation, e.g. after a time
limit), which must again be closed by their own certificates.

Runs chainset_check.py on the top (collecting its delegated fixing sets) and on every subtree (with the
top's validated global fixings; these runs are independent and may run in parallel, -j N), and checks:
  * every delegated leaf (at any level) is matched by exactly one certificate with the same T, arc list
    and initial fixings equal to the leaf's fixings;
  * every delegated leaf of a subtree is strictly deeper than the subtree's root (its fixing set strictly
    contains the subtree's initial fixings), so the recursion is well founded;
  * every given certificate is used.
If all pass: every route on the chain set has weight >= T (length >= BASE + T).

Usage: composite_check.py [-j N] WORD TOP SUB...  (SUB files may be in any order)"""
import sys, os, json, subprocess, tempfile, gzip
from concurrent.futures import ThreadPoolExecutor
def jload(path):
    return json.load(gzip.open(path, 'rt') if path.endswith('.gz') else open(path))
PY = sys.executable; CK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chainset_check.py")

def run_check(word, cert, top=None):
    fd, dl = tempfile.mkstemp(suffix=".json"); os.close(fd)
    args = [PY, "-I", CK, word, cert] + ([top] if top else [])
    r = subprocess.run(args, capture_output=True, text=True, env=dict(os.environ, DELEG_OUT=dl))
    assert r.returncode == 0, f"{cert}: " + r.stderr[-2000:]
    res = json.loads(r.stdout.strip().splitlines()[-1])
    deleg = [tuple(sorted(map(tuple, d))) for d in json.load(open(dl))]
    os.unlink(dl)
    assert res["delegated"] == len(deleg)
    return res, deleg

def main():
    args = sys.argv[1:]; J = 1
    if args[0] == "-j": J = int(args[1]); args = args[2:]
    word, top, subs = args[0], args[1], args[2:]
    T = jload(top)
    assert not T.get("init_fix"), "the top certificate must cover the whole space"
    topres, d0 = run_check(word, top)
    by_key = {}
    for sf in subs:
        S = jload(sf)
        assert S["T"] == T["T"] and S["BASE"] == T["BASE"] and S["arcs"] == T["arcs"], f"{sf}: T/BASE/arc mismatch"
        assert S.get("init_fix"), f"{sf}: not a subtree certificate"
        key = tuple(sorted(map(tuple, S["init_fix"])))
        assert key not in by_key, f"{sf}: second certificate for the same delegated leaf ({by_key.get(key)})"
        by_key[key] = sf
        del S
    # check every subtree certificate (independent runs)
    def one(sf):
        res, dk = run_check(word, sf, top)
        print(json.dumps(dict(checked=os.path.basename(sf), leaves=res["leaves"], min_leaf_bound=res["min_leaf_bound"],
                              delegated=len(dk))), file=sys.stderr, flush=True)
        return sf, res, dk
    with ThreadPoolExecutor(max_workers=J) as ex:
        results = {sf: (res, dk) for sf, res, dk in ex.map(one, subs)}
    # delegation structure: every delegated leaf closed exactly once, strictly deeper, all certificates used
    queue = list(d0); used = set(); leaves = topres["leaves"]; worst = topres["min_leaf_bound"]; maxlevel = 0
    level = {k: 1 for k in d0}
    while queue:
        k = queue.pop()
        assert k in by_key, f"delegated leaf with fixings {list(k)[:8]}... has no subtree certificate"
        sf = by_key[k]; assert sf not in used, f"{sf}: used twice"; used.add(sf)
        res, dk = results[sf]
        leaves += res["leaves"]
        if res["min_leaf_bound"] is not None: worst = res["min_leaf_bound"] if worst is None else min(worst, res["min_leaf_bound"])
        maxlevel = max(maxlevel, level[k])
        for k2 in dk:
            assert set(k) < set(k2), f"{sf}: delegated leaf not strictly below the subtree root"
            assert k2 not in level, "delegated leaf reached twice"
            level[k2] = level[k] + 1; queue.append(k2)
    unused = sorted(set(subs) - used)
    assert not unused, f"certificates not attached to any delegated leaf: {unused}"
    print(json.dumps(dict(ok=True, top_leaves=topres["leaves"], delegated_total=len(level), subtrees=len(subs),
                          nesting_depth=maxlevel, pruned_leaves_total=leaves, min_leaf_bound=worst, T=T["T"],
                          theorem=f"every route on this chain set has weight >= {T['T']}, length >= {T['BASE'] + T['T']}")))

if __name__ == "__main__":
    main()
