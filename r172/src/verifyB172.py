#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- verifier B for L6-EXTREE-4.

Derived from `routeb164.TreeVerifier` (geometry rebuilt from string algebra,
exact legal-children count at every node, incremental feasibility histogram
asserted equal to a from-scratch recomputation at every node) and the Round
168 driver `verify168.verify_any`.  One leaf kind is added, the R1 leaf of
r172/THEOREM_R1.md.

Independent of verifier A: B computes the live range in closed form,

    r_lo = 0                    if d0 >= 0
         = ceil(-d0 / 5)        if d0 <  0          (smallest r with d0+5r >= 0)
    Live(s) = [r_lo, tok]  (empty when r_lo > tok),

evaluates U with its own `ub`, parses the stored annotation with its own
grammar, and uses the annotation only for an equality check.

Old formats (L6-EXTREE-1/2/3) are delegated, unchanged, to
`verify168.verify_any`.  An `L` leaf never receives R1.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import routeb164 as RB                                            # noqa: E402
import verify168 as V3                                            # noqa: E402
from gzrule167 import plain_sha256                                # noqa: E402

FORMAT4 = "L6-EXTREE-4"
RULE4 = "rule R1 token_split_v1 leaves=L:b,f,p S:r1"
_SEEN = {}          # verify168 closure cache for REFERENCED files (per process)
_HASHMEMO = {}      # (path, size, mtime) -> (container sha, plain sha)
S_GRAMMAR = re.compile(r"^S:(-?[0-9]+):(-|[0-9]+=[0-9]+(?:,[0-9]+=[0-9]+)*)$")


def live_range(d0, tok):
    r_lo = 0 if d0 >= 0 else (-d0 + 4) // 5
    return range(r_lo, tok + 1)


class TreeVerifierR1(RB.TreeVerifier):

    def validate(self, cell, cap, toks):
        b, dmax, amax, bmax, emax, hmax = cell
        ORB, PHASE, HEX, MOVES = RB.ORB, RB.PHASE, RB.HEX, RB.MOVES
        phm = {ORB[0]: {PHASE[0]}}
        hexc = {HEX[0]: 1}
        inc = {ORB[0]: 1}
        st = dict(err=None, pos=0)

        def fresh_hist():
            return {q: len(ph) for q, ph in phm.items()}

        def legal(v, corb, tok, au, bu, eu, hu):
            out = []
            for t, kind, cost in MOVES[v]:
                q = ORB[t]
                ph = phm.get(q)
                if ph is not None and PHASE[t] in ph:
                    continue
                if kind == "E" and q != corb:
                    continue
                if kind == "A" and au >= amax:
                    continue
                if kind == "B" and bu >= bmax:
                    continue
                if kind == "H" and hu + cost > hmax:
                    continue
                newhex = HEX[t] not in hexc
                se = 0
                if not newhex and kind not in ("A", "B"):
                    if eu >= emax:
                        continue
                    se = 1
                fresh = ph is None
                c = 0 if (kind == "E" or fresh) else 1
                if c > tok:
                    continue
                out.append((t, kind, cost, fresh, se, c))
            return out

        def s_leaf(tk, i, ports, tok, deficit, res):
            m = S_GRAMMAR.match(tk)
            if not m:
                return f"S leaf {tk!r} at {i} does not parse"
            stored_d0 = int(m.group(1))
            stored = [] if m.group(2) == "-" else \
                [tuple(map(int, x.split("="))) for x in m.group(2).split(",")]
            d0 = dmax - deficit + 4
            branch_u = {r: self.ub(tok - r, d0 + 5 * r, *res)
                        for r in live_range(d0, tok)}
            if stored_d0 != d0 or stored != sorted(branch_u.items()):
                return (f"S leaf at {i}: stored ({stored_d0}, {stored}) != "
                        f"recomputed ({d0}, {sorted(branch_u.items())})")
            if not branch_u:
                self.leaf_reasons["r1_dead_no_live_branch"] += 1
                return None
            if ports + max(branch_u.values()) - 1 >= cap + 1:
                return (f"S leaf at {i} not justified: ports={ports} "
                        f"U_R1={max(branch_u.values())} target={cap + 1}")
            self.leaf_reasons["r1_token_split"] += 1
            return None

        def walk(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            self.max_open_orbits = max(self.max_open_orbits, len(phm))
            self.hist_checks += 1
            if inc != fresh_hist():
                st["err"] = "incremental histogram != fresh recomputation"
                return
            i = st["pos"]
            if i >= len(toks):
                st["err"] = "token stream ended early"
                return
            tk = toks[i]
            st["pos"] = i + 1
            if ports >= cap + 1 and deficit <= dmax:
                st["err"] = (f"the tree itself reaches {ports} ports at "
                             f"deficit {deficit} <= {dmax}")
                return
            if tk == "L":
                r1 = ports + (RB.NHEX - len(hexc)) + (amax - au) \
                    + (bmax - bu) + (emax - eu)
                if r1 < cap + 1:
                    self.leaf_reasons["b_hexagon_and_repeat_budget"] += 1
                    return
                if not RB.feas_greedy(phm, corb, tok, dmax):
                    self.leaf_reasons["f_feasibility"] += 1
                    return
                r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                     amax - au, bmax - bu, emax - eu,
                                     hmax - hu) - 1
                if r2 < cap + 1:
                    self.leaf_reasons["p_monotone_from_earlier_cells"] += 1
                    return
                st["err"] = (f"unjustified L leaf at token {i}: ports={ports}"
                             f" deficit={deficit} r1={r1} r2={r2}")
                return
            if tk[:1] == "S":
                st["err"] = s_leaf(tk, i, ports, tok, deficit,
                                   (amax - au, bmax - bu, emax - eu, hmax - hu))
                return
            if not tk.startswith("N"):
                st["err"] = f"bad token {tk!r} at {i}"
                return
            k = int(tk[1:])
            ms = legal(v, corb, tok, au, bu, eu, hu)
            if k != len(ms):
                st["err"] = (f"token {i} declares {k} children but the state "
                             f"has {len(ms)} legal moves")
                return
            for t, kind, cost, fresh, se, c in ms:
                q = ORB[t]
                if fresh:
                    phm[q] = {PHASE[t]}
                    inc[q] = 1
                else:
                    phm[q].add(PHASE[t])
                    inc[q] += 1
                hexc[HEX[t]] = hexc.get(HEX[t], 0) + 1
                walk(t, q, ports + 1, tok - c, au + (kind == "A"),
                     bu + (kind == "B"), eu + se,
                     hu + (cost if kind == "H" else 0),
                     deficit + (4 if fresh else -1))
                hexc[HEX[t]] -= 1
                if hexc[HEX[t]] == 0:
                    del hexc[HEX[t]]
                if fresh:
                    del phm[q]
                    del inc[q]
                else:
                    phm[q].discard(PHASE[t])
                    inc[q] -= 1
                if st["err"]:
                    return

        sys.setrecursionlimit(10000)
        walk(0, ORB[0], 1, b, 0, 0, 0, 0, 4)
        if st["err"]:
            return False, st["err"]
        if st["pos"] != len(toks):
            return False, f"{len(toks) - st['pos']} tokens left over"
        return True, dict(nodes=self.nodes)


def parse4(text):
    lines = text.splitlines()
    if len(lines) < 2 or lines[0] != FORMAT4:
        raise ValueError("not L6-EXTREE-4")
    if lines[1] != RULE4:
        raise ValueError("line 2 is not the exact R1 rule declaration")
    refs, deps, trees, i = [], [], [], 2
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        if f[0] == "ref" and len(f) == 4:
            refs.append((f[1], f[2], f[3]))
        elif f[0] == "dep" and len(f) == 10:
            deps.append((tuple(int(x) for x in f[1:7]), int(f[7]), f[8], f[9]))
        elif f[0] == "tree" and len(f) == 8:
            trees.append((tuple(int(x) for x in f[1:7]), int(f[7]),
                          lines[i + 1].split()))
            i += 2
            continue
        else:
            raise ValueError(f"unexpected header line {s[:60]!r}")
        i += 1
    return refs, deps, trees


def verify_any4(rel):
    text, csha, psha = V3.read_text(rel)
    if not text.startswith(FORMAT4 + "\n"):
        res = V3.verify_any(rel)                 # old formats: old semantics
        return {k: v for k, v in res.items() if k != "certified"} | dict(
            certified=res.get("certified", {}))
    try:
        refs, deps, trees = parse4(text)
    except ValueError as e:
        return dict(ok=False, path=rel, error=str(e), certified={})
    ref_index, certified = {}, {}
    for want_c, want_p, ref_rel in refs:
        sub = V3.verify_any(ref_rel, _SEEN)
        if not sub["ok"]:
            return dict(ok=False, path=rel, certified={},
                        error=f"referenced certificate failed: {ref_rel}")
        st = (ROOT / ref_rel).stat()
        hk = (ref_rel, st.st_size, st.st_mtime_ns)
        if hk not in _HASHMEMO:
            c_ = hashlib.sha256((ROOT / ref_rel).read_bytes()).hexdigest()
            _HASHMEMO[hk] = (c_, plain_sha256(ROOT / ref_rel)
                             if ref_rel.endswith(".gz") else c_)
        got_c, got_p = _HASHMEMO[hk]
        if got_c != want_c or got_p != want_p:
            return dict(ok=False, path=rel, certified={},
                        error=f"reference hash mismatch for {ref_rel}")
        ref_index[ref_rel] = (want_p, sub["certified"])
    for cell, cap, dsha, dref in deps:
        if dref not in ref_index:
            return dict(ok=False, path=rel, certified={},
                        error=f"dep cites undeclared reference {dref}")
        psha_ref, cells = ref_index[dref]
        if dsha != psha_ref or cells.get(cell) != cap:
            return dict(ok=False, path=rel, certified={},
                        error=f"dep {cell} does not match {dref}")
        certified[cell] = cap
    rows, nodes, hist = [], 0, 0
    leaves = Counter()
    for cell, cap, toks in trees:
        v = TreeVerifierR1(dict(certified), check_feas_forms=False)
        ok, info = v.validate(cell, cap, toks)
        nodes += v.nodes
        hist += v.hist_checks
        leaves.update(v.leaf_reasons)
        rows.append(dict(cell="|".join(map(str, cell)), cap=cap,
                         nodes=v.nodes, hist_checks=v.hist_checks,
                         leaves=dict(v.leaf_reasons), verified=bool(ok),
                         detail=None if ok else info))
        if not ok:
            return dict(ok=False, path=rel, certified={}, rows=rows,
                        error=f"tree invalid for {rows[-1]['cell']}: {info}")
        certified[cell] = cap
    return dict(ok=True, path=rel, format=FORMAT4, rule=RULE4, sha256=csha,
                plain_sha256=psha, certified=certified, rows=rows,
                nodes=nodes, hist_checks=hist, leaves=dict(leaves),
                declared_dependencies=len(deps), error=None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT / "r172" / "src"))
    import trust172
    trust172.setup()
    out = {rel: verify_any4(rel) for rel in a.batch}
    res = dict(verifier="r172/src/verifyB172.py (routeb164.TreeVerifier-derived, R1)",
               verifier_sha256=hashlib.sha256(
                   Path(__file__).read_bytes()).hexdigest(),
               batches={k: {kk: vv for kk, vv in v.items()
                            if kk != "certified"} for k, v in out.items()},
               all_ok=all(v["ok"] for v in out.values()))
    (ROOT / a.report).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / a.report).write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: {kk: vv.get(kk) for kk in ("ok", "nodes", "leaves",
                                                     "error")}
                      for k, vv in res["batches"].items()}, indent=1))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
