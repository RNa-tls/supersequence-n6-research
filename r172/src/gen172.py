#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL, NOT PRODUCTION) -- OLD vs R1 exhaustion-tree generator.

Two modes over the SAME move machinery (`gen168.Engine._legal`, same child
order, same node-cap semantics):

  old  -- the Round 168 leaf rules (b), (f), (p); output is byte-identical to
          gen168 and written as L6-EXTREE-3.
  r1   -- the same three rules first, then the R1 token-split rule
          (r172/THEOREM_R1.md).  A leaf closed ONLY by R1 is written as

              S:<d0>:<r>=<U>,<r>=<U>,...      (live branches)
              S:<d0>:-                         (Live(s) empty: dead node)

          and the file is L6-EXTREE-4 with the hashed header line RULE_LINE.
          The annotation is a claim for the verifiers to recompute, never an
          input they trust.

R2 (rho / dead-branch refinement) is deliberately NOT implemented.

The generator is untrusted: only verifiers A4 and B4 decide.
"""
from __future__ import annotations
import collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
import gen168 as G                                                # noqa: E402
from gzrule167 import write_gz                                    # noqa: E402
from gen168 import R                                              # noqa: E402

MAGIC4 = "L6-EXTREE-4"
RULE_LINE = "rule R1 token_split_v1 leaves=L:b,f,p S:r1"


def s_token(d0, branches):
    if not branches:
        return f"S:{d0}:-"
    return f"S:{d0}:" + ",".join(f"{r}={u}" for r, u in branches)


class Engine172(G.Engine):
    """gen168.Engine plus the R1 leaf and experiment telemetry."""

    def __init__(self, deps, node_cap, mode, keep_tokens=True, audit=True):
        super().__init__(deps, node_cap)
        assert mode in ("old", "r1")
        self.mode = mode
        self.keep_tokens = keep_tokens
        # conservativity audit: at every node closed by the OLD scalar (p)
        # rule, also evaluate R1 and count any node R1 would NOT close.
        # THEOREM_R1 section 7 says this count is always 0.
        self.audit = audit
        self.t = collections.Counter()
        self.depth_nodes = collections.Counter()
        self.depth_leaf = collections.defaultdict(collections.Counter)
        self.branch_hist_eval = collections.Counter()
        self.branch_hist_prune = collections.Counter()
        self.ntok = 0

    def fb(self, a, bb, e):
        return R.UBFALL + a + bb + e

    def r1_branches(self, tok, d0, a, bb, e, h):
        """Live(s) and U for each live branch -- exactly THEOREM_R1 section 3."""
        out = []
        for r in range(tok + 1):
            if d0 + 5 * r >= 0:
                out.append((r, self.ub(tok - r, d0 + 5 * r, a, bb, e, h)))
        return out

    def r1_decide(self, tok, d0, a, bb, e, h, ports, target):
        """(closes, annotation branches, evaluated branches).  The mutation
        suite overrides this with deliberately wrong rules; nothing else does."""
        br = self.r1_branches(tok, d0, a, bb, e, h)
        closes = not br or ports + max(x for _r, x in br) - 1 < target
        return closes, br, br

    def build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        toks = []
        target = cap + 1
        T = self.t
        keep = self.keep_tokens
        mode_r1 = self.mode == "r1"
        audit = self.audit

        def emit(tk):
            self.ntok += 1
            if keep:
                toks.append(tk)

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            depth = ports - 1
            self.depth_nodes[depth] += 1
            if ports >= target and deficit <= dmax:
                raise StopIteration
            r1 = ports + (R.NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                + (emax - eu)
            if r1 < target:
                T["leaf_b"] += 1
                self.depth_leaf["b"][depth] += 1
                emit("L")
                return
            if not R.feas_greedy(phm, corb, tok, dmax):
                T["leaf_f"] += 1
                self.depth_leaf["f"][depth] += 1
                emit("L")
                return
            ra, rbb, re_, rh = amax - au, bmax - bu, emax - eu, hmax - hu
            d0 = dmax - deficit + 4
            T["p_calls"] += 1
            u = self.ub(tok, d0 + 5 * tok, ra, rbb, re_, rh)
            if u == self.fb(ra, rbb, re_):
                T["p_fallback"] += 1
            if ports + u - 1 < target:
                T["leaf_p_old"] += 1
                self.depth_leaf["p_old"][depth] += 1
                if audit:
                    T["audit_old_p_leaves"] += 1
                    ok, _an, _br = Engine172.r1_decide(
                        self, tok, d0, ra, rbb, re_, rh, ports, target)
                    if not ok:
                        T["audit_conservativity_failures"] += 1
                emit("L")
                return
            if mode_r1:
                T["r1_evals"] += 1
                closes, annot, br = self.r1_decide(tok, d0, ra, rbb, re_, rh,
                                                   ports, target)
                self.branch_hist_eval[len(br)] += 1
                fbv = self.fb(ra, rbb, re_)
                T["r1_branch_lookups"] += len(br)
                T["r1_branch_fallback"] += sum(1 for _r, x in br if x == fbv)
                if closes:
                    T["leaf_r1_only"] += 1
                    if not br:
                        T["leaf_r1_dead"] += 1
                    self.depth_leaf["r1_only"][depth] += 1
                    self.branch_hist_prune[len(br)] += 1
                    emit(s_token(d0, annot))
                    return
            ms = self._legal(phm, hexc, cell, v, corb, tok, au, bu, eu, hu)
            T["internal"] += 1
            emit(f"N{len(ms)}")
            for t, kind, cost, fresh, se, c in ms:
                q = R.ORB[t]
                if fresh:
                    phm[q] = {R.PHASE[t]}
                else:
                    phm[q].add(R.PHASE[t])
                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1
                rec(t, q, ports + 1, tok - c, au + (kind == "A"),
                    bu + (kind == "B"), eu + se,
                    hu + (cost if kind == "H" else 0),
                    deficit + (4 if fresh else -1))
                hexc[R.HEX[t]] -= 1
                if hexc[R.HEX[t]] == 0:
                    del hexc[R.HEX[t]]
                if fresh:
                    del phm[q]
                else:
                    phm[q].discard(R.PHASE[t])

        sys.setrecursionlimit(10000)
        try:
            rec(0, R.ORB[0], 1, b, 0, 0, 0, 0, 4)
        except StopIteration:
            return None, f"a walk with {target} ports exists: cap > {cap}"
        except TimeoutError:
            return None, f"node cap {self.node_cap} reached"
        return (toks if keep else []), None

    def telemetry(self):
        return dict(mode=self.mode, visited_nodes=self.nodes,
                    proof_tokens=self.ntok, counters=dict(self.t),
                    depth_histogram_nodes=dict(sorted(self.depth_nodes.items())),
                    depth_histogram_leaves={k: dict(sorted(v.items()))
                                            for k, v in self.depth_leaf.items()},
                    branch_count_histogram_r1_evals=dict(sorted(self.branch_hist_eval.items())),
                    branch_count_histogram_r1_prunes=dict(sorted(self.branch_hist_prune.items())))


def write_batch4(path, refs, deps, trees, rule_line=RULE_LINE, magic=MAGIC4):
    """L6-EXTREE-4: magic, the hashed rule declaration, then the format-3 body."""
    lines = [magic, rule_line, "# generated by r172/src/gen172.py (EXPERIMENTAL)"]
    for csha, psha, rel in refs:
        lines.append(f"ref {csha} {psha} {rel}")
    for cell, cap, psha, rel in deps:
        lines.append(f"dep {' '.join(map(str, cell))} {cap} {psha} {rel}")
    for cell, cap, toks in trees:
        lines.append("")
        lines.append("tree " + " ".join(map(str, cell)) + f" {cap}")
        lines.append(toks if isinstance(toks, str) else " ".join(toks))
    text = "\n".join(lines) + "\n"
    write_gz(Path(path), text)
    return text
