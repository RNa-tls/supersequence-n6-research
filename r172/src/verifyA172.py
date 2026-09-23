#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- verifier A for L6-EXTREE-4.

Derived from the Round 152 validator `r152/src/extree152.py` (geometry from
`checker152`, catalogue order `canon`, leaf rules (b), (f), (p) exactly as
there) and the Round 168 streaming driver `verifyA168.py`.  It adds ONE leaf
kind, the R1 token-split leaf of r172/THEOREM_R1.md:

    S:<d0>:<r>=<U>,...   or   S:<d0>:-

For an S leaf this verifier RECOMPUTES from the replayed state

    d0 = dmax - deficit + 4,
    Live(s) = { r in [0, tok] : d0 + 5r >= 0 },
    U(r) = ub(tok - r, d0 + 5r, residual a, bb, e, h),

requires the stored annotation to equal the recomputation exactly (a stored
value is never used), and accepts the leaf iff Live(s) is empty or
ports - 1 + max_r U(r) < cap + 1.

An `L` leaf keeps its Round 152 meaning -- (b), (f) or scalar (p) only; R1 is
never applied to it.  Files whose first line is L6-EXTREE-1/2/3 are NOT read
by this module: they go to the unchanged Round 168 verifier.

This file shares no R1 code with verifier B (r172/src/verifyB172.py).
"""
from __future__ import annotations
import argparse, collections, gzip, hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
from checker152 import HEX, ORB, PHASE, NHEX                      # noqa: E402
from extree152 import canon                                       # noqa: E402
from gzrule167 import plain_sha256                                # noqa: E402
import verifyA168 as A3                                           # noqa: E402
from verify168 import scan_headers                                # noqa: E402

MAGIC4 = "L6-EXTREE-4"
RULE_R1 = "rule R1 token_split_v1 leaves=L:b,f,p S:r1"
SKIP = ("ref", "dep", "rule")
# file-derived facts about referenced certificates (hashes, carried cells),
# memoized per process and keyed by (path, size, mtime) -- never by claim.
_REFMEMO = {}


def ref_facts(ref_rel):
    p = ROOT / ref_rel
    st = p.stat()
    k = (ref_rel, st.st_size, st.st_mtime_ns)
    if k not in _REFMEMO:
        got_c = hashlib.sha256(p.read_bytes()).hexdigest()
        got_p = plain_sha256(p) if ref_rel.endswith(".gz") else got_c
        _REFMEMO[k] = (got_c, got_p, A3.cells_of(ref_rel, {}))
    return _REFMEMO[k]


class ValidatorR1:
    """extree152.Validator, plus the S leaf.  Search-free replay."""

    def __init__(self, certified):
        self.cert = certified
        self._ubc = {}
        self.nodes = 0
        self.leaves = collections.Counter()

    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best = NHEX + a + bb + e                       # (P2), analytic fallback
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        self._ubc[key] = best
        return best

    @staticmethod
    def feas(phm, corb, tok, dmax):
        us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                    reverse=True)
        return sum(us[tok:]) <= dmax

    # ---------------------------------------------------------------- R1 (A)
    def r1_recompute(self, tok, deficit, dmax, ra, rbb, re_, rh):
        d0 = dmax - deficit + 4
        live = []
        r = 0
        while r <= tok:
            dd = d0 + 5 * r
            if dd >= 0:
                live.append((r, self.ub(tok - r, dd, ra, rbb, re_, rh)))
            r += 1
        return d0, live

    @staticmethod
    def r1_parse(tk):
        """'S:<d0>:<list>' -> (d0, [(r, U), ...]); None if malformed."""
        parts = tk.split(":")
        if len(parts) != 3 or parts[0] != "S":
            return None
        try:
            d0 = int(parts[1])
            if parts[2] == "-":
                return d0, []
            out = []
            for item in parts[2].split(","):
                r, u = item.split("=")
                out.append((int(r), int(u)))
            return d0, out
        except ValueError:
            return None

    def validate(self, cell, cap, toks, pos):
        b, dmax, amax, bmax, emax, hmax = cell
        phm = {ORB[0]: {PHASE[0]}}
        hexc = {HEX[0]: 1}
        state = dict(err=None, pos=pos)

        def legal(v, corb, tok, au, bu, eu, hu):
            out = []
            for t, kind, cost in canon(v):
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
                out.append((t, kind, cost, fresh, newhex, se, c))
            return out

        def walk(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            i = state["pos"]
            if i >= len(toks):
                state["err"] = "token stream ended early"
                return
            tk = toks[i]
            state["pos"] = i + 1
            if ports >= cap + 1 and deficit <= dmax:
                state["err"] = (f"the tree itself reaches {ports} ports at "
                                f"deficit {deficit} <= {dmax}")
                return
            if tk == "L":
                r1 = ports + (NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                     + (emax - eu)
                if r1 < cap + 1:
                    self.leaves["L_b"] += 1
                    return
                if not self.feas(phm, corb, tok, dmax):
                    self.leaves["L_f"] += 1
                    return
                r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                     amax - au, bmax - bu, emax - eu,
                                     hmax - hu) - 1
                if r2 < cap + 1:
                    self.leaves["L_p"] += 1
                    return
                state["err"] = (f"unjustified L leaf at token {i}: "
                                f"ports={ports} deficit={deficit} r1={r1} "
                                f"r2={r2}")
                return
            if tk.startswith("S"):
                claim = self.r1_parse(tk)
                if claim is None:
                    state["err"] = f"malformed S leaf {tk!r} at {i}"
                    return
                d0, live = self.r1_recompute(tok, deficit, dmax, amax - au,
                                             bmax - bu, emax - eu, hmax - hu)
                if claim != (d0, live):
                    state["err"] = (f"S leaf at token {i} claims {tk!r}; "
                                    f"recomputed d0={d0} live={live}")
                    return
                if not live:
                    self.leaves["S_dead"] += 1
                    return
                top = max(u for _r, u in live)
                if ports - 1 + top < cap + 1:
                    self.leaves["S_live"] += 1
                    return
                state["err"] = (f"unjustified S leaf at token {i}: ports="
                                f"{ports} max U={top} cap={cap}")
                return
            if not tk.startswith("N"):
                state["err"] = f"bad token {tk!r} at {i}"
                return
            k = int(tk[1:])
            ms = legal(v, corb, tok, au, bu, eu, hu)
            if k != len(ms):
                state["err"] = (f"token {i} says {k} children, the state has "
                                f"{len(ms)} legal moves")
                return
            for t, kind, cost, fresh, newhex, se, c in ms:
                q = ORB[t]
                if fresh:
                    phm[q] = {PHASE[t]}
                else:
                    phm[q].add(PHASE[t])
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
                else:
                    phm[q].discard(PHASE[t])
                if state["err"]:
                    return

        sys.setrecursionlimit(10000)
        walk(0, ORB[0], 1, b, 0, 0, 0, 0, 4)
        return state["err"] is None, state["err"], state["pos"]


class Stream4(A3.Stream):
    def _tokens(self):
        op = gzip.open if str(self.path).endswith(".gz") else open
        with op(self.path, "rt") as fh:
            for line in fh:
                f = line.split("#")[0].split()
                if not f or f[0] in SKIP or f[0].startswith("L6-EXTREE"):
                    continue
                yield from f


def count4(path):
    n = 0
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as fh:
        for line in fh:
            f = line.split("#")[0].split()
            if not f or f[0] in SKIP or f[0].startswith("L6-EXTREE"):
                continue
            n += len(f)
    return n


def verify(rel, log=print):
    """Any EXTREE format: 1-3 go to the unchanged Round 168 driver."""
    text, csha, psha = A3.read_head(rel)
    lines = text.splitlines()
    if lines[0] != MAGIC4:
        return A3.verify(rel, log=log)
    if len(lines) < 2 or lines[1] != RULE_R1:
        return dict(ok=False, path=rel, error="EXTREE-4 without the exact R1 "
                                              "rule declaration on line 2")
    if sum(1 for ln in lines if ln.startswith("rule")) != 1:
        return dict(ok=False, path=rel, error="more than one rule line")
    refs, deps, _own = scan_headers(text)
    certified, index = {}, {}
    for f in refs:
        if len(f) != 3:
            return dict(ok=False, path=rel, error="malformed ref line")
        want_c, want_p, ref_rel = f
        p = ROOT / ref_rel
        if not p.exists():
            return dict(ok=False, path=rel, error=f"missing reference {ref_rel}")
        got_c, got_p, cells = ref_facts(ref_rel)
        if got_c != want_c or got_p != want_p:
            return dict(ok=False, path=rel,
                        error=f"reference hash mismatch for {ref_rel}")
        index[ref_rel] = (want_p, cells)
    for cell, cap, dsha, dref in deps:
        if dref not in index:
            return dict(ok=False, path=rel,
                        error=f"dep cites undeclared reference {dref}")
        pref, cells = index[dref]
        if dsha != pref or cells.get(cell) != cap:
            return dict(ok=False, path=rel,
                        error=f"dep {cell} does not match {dref}")
        certified[cell] = cap
    ntok = count4(ROOT / rel)
    toks = Stream4(ROOT / rel, ntok)
    rows, i, ok = [], 0, True
    while i < ntok:
        if toks[i] != "tree":
            return dict(ok=False, path=rel,
                        error=f"expected 'tree' at token {i}, saw {toks[i]!r}")
        cell = tuple(int(toks[i + j]) for j in range(1, 7))
        cap = int(toks[i + 7])
        v = ValidatorR1(dict(certified))
        t0 = time.time()
        good, err, i = v.validate(cell, cap, toks, i + 8)
        rows.append(dict(cell="|".join(map(str, cell)), cap=cap,
                         nodes=v.nodes, leaves=dict(v.leaves),
                         status="UPPER_CERTIFIED" if good else "TREE_INVALID",
                         detail=err))
        log(f"  A4 {rows[-1]['cell']:>16} cap={cap:<4} {rows[-1]['status']:<14}"
            f" nodes={v.nodes:<12,} {dict(v.leaves)} "
            f"{round(time.time() - t0, 1)}s" + (f"  {err}" if err else ""))
        if not good:
            ok = False
            break
        certified[cell] = cap
    return dict(ok=ok, path=rel, format=MAGIC4, rule=RULE_R1, sha256=csha,
                plain_sha256=psha, declared_dependencies=len(deps),
                tokens=ntok, cells=len(rows),
                nodes=sum(r["nodes"] for r in rows),
                leaves=dict(sum((collections.Counter(r["leaves"])
                                 for r in rows), collections.Counter())),
                certified={"|".join(map(str, k)): v
                           for k, v in certified.items()},
                rows=rows, error=None if ok else rows[-1]["detail"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    out = {rel: verify(rel) for rel in a.batch}
    res = dict(verifier="r172/src/verifyA172.py (extree152-derived, R1)",
               verifier_sha256=hashlib.sha256(
                   Path(__file__).read_bytes()).hexdigest(),
               batches={k: {kk: vv for kk, vv in v.items()
                            if kk not in ("certified",)}
                        for k, v in out.items()},
               all_ok=all(v["ok"] for v in out.values()))
    (ROOT / a.report).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / a.report).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: {kk: vv.get(kk) for kk in ("ok", "nodes", "leaves",
                                                     "error")}
                      for k, vv in res["batches"].items()}, indent=1))
    return 0 if res["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
