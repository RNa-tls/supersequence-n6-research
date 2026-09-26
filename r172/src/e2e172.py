#!/usr/bin/env python3
"""Round 172 V2 (EXPERIMENTAL) -- end-to-end tests against EXACT capacities.

Exact capacities come from r172/src/exhaust172.py (model definitions + the
proven (f) prune only; no certificate, no historical table).  For every cell
K with an exact capacity c and b >= 1:

  E1  genuine environment (Round-171 e5 predecessors, dominators of K removed)
        old and R1 at J = c      must COMPLETE
        old and R1 at J = c - 1  must NOT complete: the search must find a walk
      R1 trees at J = c are written as L6-EXTREE-4 and dual-verified (A4, B4:
      acceptance, node counts, leaf classes, generator counts).
  E2  adversarial tight environment: EVERY exact capacity as the certificate
      table (dominators of K removed) -- the smallest possible U, so R1 prunes
      as hard as it ever can.  R1 at J = c - 1 must still find a walk, and at
      J = c must complete.
  D   dead-first prover: a test generator that closes a node as S:<d0>:-
      whenever Live(s) is empty, BEFORE trying (f); both verifiers must accept
      those trees (the dead-leaf path of A4/B4 is otherwise never exercised,
      because Lemma 4 of THEOREM_R1 shows (f) always closes such nodes first).
      It also counts nodes with Live(s) empty where (f) would NOT close: Lemma
      4 says this count is 0.
"""
from __future__ import annotations
import glob, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
import env172 as E                                                # noqa: E402
import gen172 as X                                                # noqa: E402
import trust172                                                   # noqa: E402
import verifyA172 as VA                                           # noqa: E402
import verifyB172 as VB                                           # noqa: E402

R = X.R
OUT = ROOT / "r172/certs/v2/e2e_exact.json"
DIR = "r172/certs/v2/trees/"
ENV_JOB = "1_6_3_0_1_0_c50000000_e5"
MAP = {"L_b": "b_hexagon_and_repeat_budget", "L_f": "f_feasibility",
       "L_p": "p_monotone_from_earlier_cells", "S_live": "r1_token_split",
       "S_dead": "r1_dead_no_live_branch"}


def exact_caps():
    caps = {}
    for p in glob.glob(str(ROOT / "r172/certs/v2/exact_caps*.json")):
        for k, v in json.loads(Path(p).read_text()).items():
            if v["status"] == "EXACT":
                caps[tuple(int(x) for x in k.split("|"))] = v["cap"]
    for p in glob.glob(str(ROOT / "r172/certs/v2/exhaustive_*.json")):
        for r in json.loads(Path(p).read_text())["rows"]:
            if r.get("enumeration") == "EXACT":
                caps[tuple(int(x) for x in r["cell"].split("|"))] = r["exact_cap"]
    return caps


def dominated_out(table, cell):
    return {k: v for k, v in table.items()
            if not all(a >= b for a, b in zip(k, cell))}


class DeadFirst(X.Engine172):
    """Test prover: (b), then DEAD S leaf if Live(s) empty, then (f), (p), R1."""

    def build(self, cell, cap):
        b, dmax, amax, bmax, emax, hmax = cell
        f = self._frame(cell)
        phm, hexc = f["phm"], f["hexc"]
        toks, target = [], cap + 1
        T = self.t

        def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            if self.node_cap and self.nodes > self.node_cap:
                raise TimeoutError
            if ports >= target and deficit <= dmax:
                raise StopIteration
            r1 = ports + (R.NHEX - len(hexc)) + (amax - au) + (bmax - bu) + (emax - eu)
            if r1 < target:
                toks.append("L")
                return
            d0 = dmax - deficit + 4
            if d0 + 5 * tok < 0:                         # Live(s) empty
                if R.feas_greedy(phm, corb, tok, dmax):
                    T["lemma4_violations"] += 1        # (f) would not close it
                T["dead_leaves"] += 1
                toks.append(X.s_token(d0, []))
                return
            if not R.feas_greedy(phm, corb, tok, dmax):
                toks.append("L")
                return
            ra, rbb, re_, rh = amax - au, bmax - bu, emax - eu, hmax - hu
            if ports + self.ub(tok, d0 + 5 * tok, ra, rbb, re_, rh) - 1 < target:
                toks.append("L")
                return
            closes, annot, br = self.r1_decide(tok, d0, ra, rbb, re_, rh, ports, target)
            if closes:
                toks.append(X.s_token(d0, annot))
                return
            ms = self._legal(phm, hexc, cell, v, corb, tok, au, bu, eu, hu)
            toks.append(f"N{len(ms)}")
            for t, kind, cost, fresh, se, c in ms:
                q = R.ORB[t]
                if fresh:
                    phm[q] = {R.PHASE[t]}
                else:
                    phm[q].add(R.PHASE[t])
                hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1
                rec(t, q, ports + 1, tok - c, au + (kind == "A"), bu + (kind == "B"),
                    eu + se, hu + (cost if kind == "H" else 0),
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
        return toks, None


def status(toks, err):
    if toks is not None:
        return "COMPLETED"
    return "WALK_FOUND" if "walk with" in (err or "") else "NODE_CAP"


def dual(rel, gen_nodes):
    a = VA.verify(rel, log=lambda *_x, **_k: None)
    b = VB.verify_any4(rel)
    al = {MAP[k]: v for k, v in (a.get("leaves") or {}).items()}
    return dict(A4_ok=a["ok"], B4_ok=b["ok"], A4_nodes=a.get("nodes"),
                B4_nodes=b.get("nodes"), leaves_A=al, leaves_B=b.get("leaves"),
                agree=bool(a["ok"] and b["ok"] and a["nodes"] == b["nodes"] == gen_nodes
                           and al == b.get("leaves")),
                error=a.get("error") or b.get("error"))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5_000_000
    trust172.setup()
    caps = exact_caps()
    job, refs, dep, cert = E.load_job_env(ENV_JOB)
    targets = sorted(k for k in caps if k[0] >= 1)
    rows = json.loads(OUT.read_text())["rows"] if OUT.exists() else []
    done = {r["cell"] for r in rows}
    targets = [k for k in targets if "|".join(map(str, k)) not in done]
    print("new target cells:", len(targets), flush=True)
    for cell in targets:
        c = caps[cell]
        t0 = time.time()
        row = dict(cell="|".join(map(str, cell)), exact_cap=c)
        dep1 = {k: v for k, v in dep.items() if not all(a >= b for a, b in zip(k, cell))}
        cert1 = {k: v[0] for k, v in dep1.items()}
        cert2 = dominated_out(caps, cell)
        for env, cc in (("E1", cert1), ("E2", cert2)):
            for mode in ("old", "r1"):
                for J in (c, c - 1):
                    g = X.Engine172(cc, limit, mode)
                    toks, err = g.build(cell, J)
                    s = status(toks, err)
                    row[f"{env}_{mode}_J{'c' if J == c else 'c-1'}"] = dict(
                        status=s, nodes=g.nodes, r1_only=g.t.get("leaf_r1_only", 0),
                        audit_failures=g.t.get("audit_conservativity_failures", 0))
                    if env == "E1" and mode == "r1" and J == c and s == "COMPLETED":
                        rel = DIR + row["cell"].replace("|", "_") + "_r1.extree4.txt.gz"
                        X.write_batch4(ROOT / rel, refs, E.deps_list(dep1),
                                       [(cell, J, " ".join(toks))])
                        row["E1_r1_dual"] = dual(rel, g.nodes)
                    del toks
        g = DeadFirst(cert1, limit, "r1")
        toks, err = g.build(cell, c)
        row["dead_first"] = dict(status=status(toks, err), nodes=g.nodes,
                                 dead_leaves=g.t.get("dead_leaves", 0),
                                 lemma4_violations=g.t.get("lemma4_violations", 0))
        if toks is not None and g.t.get("dead_leaves"):
            rel = DIR + row["cell"].replace("|", "_") + "_deadfirst.extree4.txt.gz"
            X.write_batch4(ROOT / rel, refs, E.deps_list(dep1), [(cell, c, " ".join(toks))])
            row["dead_first"]["dual"] = dual(rel, g.nodes)
        # verdict for this cell
        bad = []
        for env in ("E1", "E2"):
            for mode in ("old", "r1"):
                if row[f"{env}_{mode}_Jc-1"]["status"] == "COMPLETED":
                    bad.append(f"{env} {mode} PROVED cap <= c-1 (UNSOUND)")
                if row[f"{env}_{mode}_Jc"]["status"] == "WALK_FOUND":
                    bad.append(f"{env} {mode} found a walk longer than the exact cap")
                if row[f"{env}_{mode}_Jc"]["audit_failures"]:
                    bad.append(f"{env} {mode} conservativity audit failure")
        if "E1_r1_dual" in row and not row["E1_r1_dual"]["agree"]:
            bad.append("E1 R1 tree dual verification disagreement")
        if row["dead_first"]["lemma4_violations"]:
            bad.append("Lemma 4 violated")
        if "dual" in row["dead_first"] and not row["dead_first"]["dual"]["agree"]:
            bad.append("dead-first tree not dual-accepted")
        row["problems"] = bad
        row["seconds_noncanonical"] = round(time.time() - t0, 1)
        rows.append(row)
        OUT.write_text(json.dumps(dict(node_limit=limit, rows=rows), indent=1) + "\n")
        print(row["cell"], c, {k: v["status"] for k, v in row.items()
                               if isinstance(v, dict) and "status" in v},
              "dual", row.get("E1_r1_dual", {}).get("agree"),
              "dead", row["dead_first"]["dead_leaves"],
              "problems", bad, flush=True)


if __name__ == "__main__":
    main()
