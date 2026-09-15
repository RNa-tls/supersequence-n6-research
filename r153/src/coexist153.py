#!/usr/bin/env python3
"""Round 153 Phases 5-7 -- the coexistence obligation, stated and decided.

THE OBLIGATION.  Let W be an equality witness: a walk of P ports realising the
row's required port count at its certified capacity.  For both equality rows the
row coordinates give c = G, K = c + 1 and R_int = 0, so the incidence bound
K + R_int <= G + 1 is TIGHT.  The round-145 write-up (research/
RR_L6_PROOF_145_CLAUDE.md section 9, resting on the incidence forest lemma) then
forces, for any cover realising the row:

  (T1) the bipartite hexagon/component graph is a tree, so all 120 hexagons are
       used;
  (T2) R_int = 0, so the chain is hexagon-simple and uses exactly P hexagons;
  (T3) the remaining F = 120 - P hexagons, |F| = 4c, must be covered by the c
       deleted pure circuits, each a complete tau-orbit meeting five hexagons.

(T1)-(T3) are HAND steps carried over from rounds 144-146.  What this file does
is (a) verify their machine-checkable consequences on each witness -- hexagon
simplicity, |F| = 4c, every tau-orbit meeting exactly five hexagons -- and
(b) decide the finite question they leave:

       do c tau-orbits exist whose hexagon sets cover F?

If not, the witness cannot extend to a cover, and the row dies.

TWO STRENGTHENINGS over round 148.
  * Round 148 restricted the candidate orbits to those the chain does not use
    (its "Lemma E").  This file decides the question BOTH ways and reports both.
    The unrestricted question is strictly harder to answer NO, so an
    unrestricted NO makes Lemma E unnecessary for the conclusion.
  * Three decision procedures with materially different branching, plus an
    explicit exhaustion tree that a search-free validator checks
    (r153/src/covertree153.py).

POSITIVE CONTROLS.  Each procedure is also asked a question it must answer YES:
the same F with a budget raised to the true minimum cover size, and constructed
instances built by picking c orbits first and taking F to be their union.  A
procedure that cannot say YES cannot be believed when it says NO.
"""
from __future__ import annotations
import hashlib, itertools, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
from checker152 import HEX, ORB, N                                  # noqa: E402

NH, NQ = 120, 144
ORBHEX = [set() for _ in range(NQ)]
for _v in range(N):
    ORBHEX[ORB[_v]].add(HEX[_v])


def geometry_facts():
    sizes = {}
    for q in range(NQ):
        sizes.setdefault(len(ORBHEX[q]), 0)
        sizes[len(ORBHEX[q])] += 1
    return dict(hexagons=len({HEX[v] for v in range(N)}),
                orbits=len({ORB[v] for v in range(N)}),
                orbit_hexagon_counts=sizes,
                every_orbit_meets_five_hexagons=set(sizes) == {5})


def instance(ports, c, restrict):
    """The set-cover instance a witness induces."""
    Hc = {HEX[v] for v in ports}
    Oc = {ORB[v] for v in ports}
    F = sorted(set(range(NH)) - Hc)
    bit = {h: 1 << i for i, h in enumerate(F)}
    cands = []
    for q in range(NQ):
        if restrict and q in Oc:
            continue
        m = 0
        for h in ORBHEX[q]:
            if h in bit:
                m |= bit[h]
        if m:
            cands.append((q, m))
    return dict(F=F, n=len(F), full=(1 << len(F)) - 1, cands=cands, c=c,
                hex_simple=len(Hc) == len(ports), F_equals_4c=len(F) == 4 * c,
                chain_orbits=len(Oc))


# ------------------------------------------------------- three procedures
def solve_bfs(inst, budget):
    """Layered BFS over covered-masks, lowest-uncovered branching rule."""
    n, FULL, cands = inst["n"], inst["full"], inst["cands"]
    by = [[qm for qm in cands if qm[1] >> i & 1] for i in range(n)]
    layer, nodes = {0}, 0
    for depth in range(budget):
        nxt = set()
        for mask in layer:
            low = min(i for i in range(n) if not mask >> i & 1)
            for q, m in by[low]:
                nodes += 1
                nm = mask | m
                if bin(FULL ^ nm).count("1") > 5 * (budget - depth - 1):
                    continue
                nxt.add(nm)
        layer = nxt
        if FULL in layer:
            return dict(coverable=True, at=depth + 1, nodes=nodes)
        if not layer:
            break
    return dict(coverable=False, at=None, nodes=nodes)


def solve_dfs_lowest(inst, budget):
    """Recursive DFS, lowest-uncovered branching rule."""
    n, FULL, cands = inst["n"], inst["full"], inst["cands"]
    by = [[qm for qm in cands if qm[1] >> i & 1] for i in range(n)]
    st = dict(nodes=0, sol=None)

    def rec(mask, k, chosen):
        st["nodes"] += 1
        if mask == FULL:
            st["sol"] = list(chosen)
            return True
        if k == budget:
            return False
        if bin(FULL ^ mask).count("1") > 5 * (budget - k):
            return False
        low = min(i for i in range(n) if not mask >> i & 1)
        for q, m in by[low]:
            chosen.append(q)
            if rec(mask | m, k + 1, chosen):
                return True
            chosen.pop()
        return False

    r = rec(0, 0, [])
    return dict(coverable=r, nodes=st["nodes"], solution=st["sol"])


def solve_dfs_fewest(inst, budget):
    """Recursive DFS branching on the uncovered element with the FEWEST
    candidate orbits -- Knuth's S heuristic, a materially different tree."""
    n, FULL, cands = inst["n"], inst["full"], inst["cands"]
    by = [[qm for qm in cands if qm[1] >> i & 1] for i in range(n)]
    st = dict(nodes=0, sol=None)

    def rec(mask, k, chosen):
        st["nodes"] += 1
        if mask == FULL:
            st["sol"] = list(chosen)
            return True
        if k == budget:
            return False
        if bin(FULL ^ mask).count("1") > 5 * (budget - k):
            return False
        best, bl = None, None
        for i in range(n):
            if mask >> i & 1:
                continue
            opts = [qm for qm in by[i] if (qm[1] & ~mask)]
            if bl is None or len(opts) < bl:
                best, bl = opts, len(opts)
                if bl == 0:
                    break
        for q, m in best:
            chosen.append(q)
            if rec(mask | m, k + 1, chosen):
                return True
            chosen.pop()
        return False

    r = rec(0, 0, [])
    return dict(coverable=r, nodes=st["nodes"], solution=st["sol"])


def counting_bound(inst):
    """c orbits cover at most the c largest |hex(orbit) cap F|."""
    tops = sorted((bin(m).count("1") for _, m in inst["cands"]), reverse=True)
    s = sum(tops[:inst["c"]])
    return dict(top_c=tops[:inst["c"]], sum_top_c=s, F_size=inst["n"],
                settles=s < inst["n"])


# ------------------------------------------------------- positive controls
def min_cover(inst, cap=14):
    for b in range(1, cap + 1):
        r = solve_dfs_lowest(inst, b)
        if r["coverable"]:
            return dict(min_orbits=b, nodes=r["nodes"], solution=r["solution"])
    return dict(min_orbits=None)


def constructed_controls(k, trials, seed=20261115):
    """Instances that DO have a cover, built the only honest way: choose k
    orbits first and let F be exactly the union of their hexagons.  The budget
    given to the solver is k, so a correct procedure must answer YES."""
    rnd = random.Random(seed)
    out = []
    for _ in range(trials):
        qs = rnd.sample(range(NQ), k)
        F = sorted(set().union(*(ORBHEX[q] for q in qs)))
        bit = {h: 1 << i for i, h in enumerate(F)}
        cands = []
        for q in range(NQ):
            m = 0
            for h in ORBHEX[q]:
                if h in bit:
                    m |= bit[h]
            if m:
                cands.append((q, m))
        inst = dict(F=F, n=len(F), full=(1 << len(F)) - 1, cands=cands, c=k)
        out.append(dict(k=k, F=len(F),
                        bfs=solve_bfs(inst, k)["coverable"],
                        dfs_lowest=solve_dfs_lowest(inst, k)["coverable"],
                        dfs_fewest=solve_dfs_fewest(inst, k)["coverable"]))
    return out


def load(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def main(argv):
    rows = [("E1", "r153/certs/E1_table.jsonl", (0, 14, 0, 0, 0, 0), 96, 6),
            ("E2", "r153/certs/E2_table.jsonl", (0, 8, 0, 0, 0, 1), 92, 7)]
    if argv:
        rows = [r for r in rows if r[0] in argv]
    out = dict(geometry=geometry_facts(), rows=[])
    for name, path, cell, target, c in rows:
        p = ROOT / path
        if not p.exists():
            out["rows"].append(dict(name=name, status="WITNESS_FILE_MISSING",
                                    file=path))
            continue
        wits = load(p)
        entry = dict(name=name, cell="|".join(map(str, cell)), target=target,
                     circuits=c, witnesses=len(wits), certificates=[])
        for i, w in enumerate(wits):
            ports = w["ports"]
            cert = dict(index=i, deficit=w["deficit"],
                        ports=len(ports),
                        sha256=hashlib.sha256(
                            json.dumps(ports).encode()).hexdigest())
            for restrict in (True, False):
                inst = instance(ports, c, restrict)
                tag = "lemmaE" if restrict else "unrestricted"
                bfs = solve_bfs(inst, c)
                d1 = solve_dfs_lowest(inst, c)
                d2 = solve_dfs_fewest(inst, c)
                mc = min_cover(inst)
                cert[tag] = dict(
                    F_size=inst["n"], candidates=len(inst["cands"]),
                    hex_simple=inst["hex_simple"],
                    F_equals_4c=inst["F_equals_4c"],
                    chain_orbits=inst["chain_orbits"],
                    bfs=bfs, dfs_lowest=d1, dfs_fewest=d2,
                    counting=counting_bound(inst),
                    agree=(bfs["coverable"] == d1["coverable"] ==
                           d2["coverable"]),
                    excluded=not (bfs["coverable"] or d1["coverable"]
                                  or d2["coverable"]),
                    positive_control_same_instance=mc)
            cert["excluded"] = cert["unrestricted"]["excluded"]
            cert["excluded_without_lemmaE"] = cert["unrestricted"]["excluded"]
            entry["certificates"].append(cert)
        entry["all_excluded"] = all(c2["excluded"] for c2 in
                                    entry["certificates"])
        out["rows"].append(entry)

    out["constructed_controls"] = {}
    for k in (6, 7):
        ctrl = constructed_controls(k, 40)
        out["constructed_controls"][str(k)] = dict(
            instances=len(ctrl),
            bfs_yes=sum(x["bfs"] for x in ctrl),
            dfs_lowest_yes=sum(x["dfs_lowest"] for x in ctrl),
            dfs_fewest_yes=sum(x["dfs_fewest"] for x in ctrl),
            all_yes=all(x["bfs"] and x["dfs_lowest"] and x["dfs_fewest"]
                        for x in ctrl))
    out["controls_ok"] = all(v["all_yes"] for v in
                             out["constructed_controls"].values())
    out["ok"] = (out["geometry"]["every_orbit_meets_five_hexagons"]
                 and out["controls_ok"]
                 and all(r.get("all_excluded") for r in out["rows"]))
    (ROOT / "r153" / "certs" / "coexist_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in out["rows"]:
        print(f"  {r['name']}: witnesses={r.get('witnesses')} "
              f"all_excluded={r.get('all_excluded')}")
        for c2 in r.get("certificates", []):
            u, l = c2["unrestricted"], c2["lemmaE"]
            print(f"    #{c2['index']} |F|={u['F_size']} "
                  f"lemmaE: excluded={l['excluded']} nodes={l['bfs']['nodes']}"
                  f"/{l['dfs_lowest']['nodes']}/{l['dfs_fewest']['nodes']} | "
                  f"unrestricted: excluded={u['excluded']} "
                  f"nodes={u['bfs']['nodes']}/{u['dfs_lowest']['nodes']}"
                  f"/{u['dfs_fewest']['nodes']} | counting settles="
                  f"{u['counting']['settles']} | min cover="
                  f"{u['positive_control_same_instance']['min_orbits']}")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
