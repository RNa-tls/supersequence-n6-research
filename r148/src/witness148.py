#!/usr/bin/env python3
"""Round 148 Phase 10/11 -- re-enumerate the equality witnesses, one route with
NO precomputed pruning table at all, and certify every witness independently.

Two enumeration routes per equality row:
  R1  the round-147 searcher with the freshly regenerated sound table;
  R2  the SAME searcher with no table whatsoever (argv[8] = "-"), so the only
      prunes left are the analytic hexagon bound and the target bound, both
      proved.  No capped run is used.
The canonical witness sets (each witness reduced to the least relabelling of the
six letters) must be equal, and their SHA-256 must match.

Then, per witness, the structural certification:
  the used-hexagon set and its complement F,
  |F| = 4c and the chain is hexagon-simple (the incidence equality / tree
  condition in the form it is used),
  the clean-E orbit structure available,
  and two independent coexistence solvers, each with a positive control.
For the 96-port witness whose six largest |hex(orbit) cap F| are 5,5,3,3,3,3 the
hand obstruction 22 < 24 is reproduced; for the other two it is reported that
the same hand bound does NOT apply (26 and 35 are both >= |F|).
"""
from __future__ import annotations
import hashlib, itertools, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R148 = ROOT / "r147", ROOT / "r148"
sys.path.insert(0, str(R147 / "src"))
sys.path.insert(0, str(ROOT / "src"))
import ub147                                                        # noqa: E402
import l6_cover_bfs_146 as CB                                       # noqa: E402
import l6_circuit_coexist_144 as CO                                 # noqa: E402
import l6_coexist_check3_144 as CO3                                 # noqa: E402

EXE = R147 / "l6chain147b.exe"
PERMS = ["".join(p) for p in itertools.permutations("123456")]
IDX = {p: i for i, p in enumerate(PERMS)}
NODECAP = 600_000_000_000
ROWS = [("row96", (0, 14, 0, 0, 0, 0), 96, 6),
        ("row92", (0, 8, 0, 0, 0, 1), 92, 7)]


def store():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                st[tuple(int(x) for x in k.split("|"))] = dict(cc=v["cc"])
    return st


def canon(ports):
    words = [PERMS[v] for v in ports]
    best = None
    for g in itertools.permutations("123456"):
        m = dict(zip("123456", g))
        seq = tuple(IDX["".join(m[ch] for ch in w)] for w in words)
        if best is None or seq < best:
            best = seq
    return best


def enumerate_route(name, cell, target, ub):
    wp = R148 / "witnesses" / f"{name}_{'table' if ub != '-' else 'notable'}.jsonl"
    t0 = time.time()
    r = subprocess.run([str(EXE)] + [str(x) for x in cell] +
                       [str(NODECAP), str(ub), str(target), str(wp)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return dict(status="ERROR", stderr=r.stderr[:200])
    j = json.loads(r.stdout)
    raw = [json.loads(x)["ports"] for x in wp.read_text().splitlines() if x.strip()]
    classes = {}
    for p in raw:
        classes.setdefault(canon(p), []).append(p)
    cs = sorted(classes)
    return dict(status="UNKNOWN_CAP" if j["capped"] else "EXHAUSTIVE",
                capped=j["capped"], nodes=j["nodes"], cc=j["cc"],
                seconds=round(time.time() - t0, 1), witnesses=len(raw),
                classes=len(cs),
                canonical_sha256=hashlib.sha256(
                    json.dumps(cs).encode()).hexdigest(),
                canonical=cs, file=str(wp.relative_to(ROOT)))


def certify(ports, c):
    """Structure + two independent coexistence solvers, each with a control."""
    bfs = CB.decide(ports, c)
    hand = CB.hand_count(ports, c)
    # solver 1: the round-144 exact-cover DFS
    s1 = CO.coexist(list(ports), c)
    # solver 2: the round-144 subset enumeration
    s2 = CO3.solve(list(ports), c)
    # positive controls for both round-144 solvers: the same instance with the
    # circuit count raised to the value the third procedure says is needed
    need = bfs["min_orbits_to_cover_F"]
    c1 = CO.coexist(list(ports), need) if need else None
    c2 = CO3.solve(list(ports), need) if need else None
    Hc = {CB.HEX[v] for v in ports}
    F = sorted(set(range(120)) - Hc)
    cleanE = sorted(q for q in range(144)
                    if CB.ORBHEX[q] <= set(F) and q not in {CB.ORB[v] for v in ports})
    return dict(
        ports=len(ports), hex_simple=(len(Hc) == len(ports)),
        used_hexagons=sorted(Hc), unused_F=F, F_size=len(F),
        F_equals_4c=(len(F) == 4 * c), circuits_required=c,
        clean_E_orbits_inside_F=len(cleanE),
        distinct_chain_orbits=len({CB.ORB[v] for v in ports}),
        solver_bfs=dict(coverable=bfs["coverable_by_c_orbits"],
                        nodes=bfs["nodes_at_c"], capped=False,
                        min_orbits=need, margin=bfs["margin"],
                        control_nodes=bfs["nodes_control"]),
        solver_dfs=dict(ok=s1.get("ok"), nodes=s1.get("nodes"),
                        capped=s1.get("capped"), reason=s1.get("reason"),
                        control_at_min_orbits=(c1 or {}).get("ok"),
                        control_nodes=(c1 or {}).get("nodes")),
        solver_subset=dict(ok=s2.get("ok"), nodes=s2.get("nodes"),
                           capped=s2.get("capped"), reason=s2.get("reason"),
                           control_at_min_orbits=(c2 or {}).get("ok"),
                           control_nodes=(c2 or {}).get("nodes")),
        hand_obstruction=dict(top_c=hand["top_c"], sum_top_c=hand["sum_top_c"],
                              F_size=hand["Fsize"],
                              applies=hand["settles_row"],
                              statement=(f"{' + '.join(map(str, hand['top_c']))}"
                                         f" = {hand['sum_top_c']} < {hand['Fsize']}"
                                         if hand["settles_row"] else
                                         f"{' + '.join(map(str, hand['top_c']))}"
                                         f" = {hand['sum_top_c']} >= "
                                         f"{hand['Fsize']}: the hand bound does "
                                         f"NOT settle this witness")))


def main():
    (R148 / "witnesses").mkdir(parents=True, exist_ok=True)
    st = store()
    out = {"rows": []}
    for name, cell, target, c in ROWS:
        ubp = R148 / "witnesses" / f"ub_{name}.txt"
        info = ub147.write_table(ubp, cell, st, exclude={cell})
        val = ub147.validate_table(ubp, cell, st, exclude={cell})
        print(f"== {name} cell={cell} target={target} c={c} "
              f"ub_rows={info['rows']} validator_ok={val['ok']}", flush=True)
        r1 = enumerate_route(name, cell, target, ubp)
        print("   R1 (sound table):", json.dumps(
            {k: v for k, v in r1.items() if k != "canonical"}), flush=True)
        r2 = enumerate_route(name, cell, target, "-")
        print("   R2 (NO table)   :", json.dumps(
            {k: v for k, v in r2.items() if k != "canonical"}), flush=True)
        same = (r1.get("canonical_sha256") == r2.get("canonical_sha256")
                and r1.get("classes") == r2.get("classes"))
        certs = [certify(list(cl), c) for cl in r1.get("canonical", [])]
        for i, cc in enumerate(certs):
            print(f"   class {i}: ", json.dumps(
                {k: v for k, v in cc.items()
                 if k not in ("used_hexagons", "unused_F")}), flush=True)
        out["rows"].append(dict(
            name=name, cell=list(cell), target=target, circuits=c,
            ub_validator_ok=val["ok"], route_table=r1, route_notable=r2,
            routes_agree=same, certificates=certs,
            all_excluded=all(not x["solver_bfs"]["coverable"]
                             and x["solver_dfs"]["ok"] is False
                             and x["solver_subset"]["ok"] is False
                             for x in certs),
            all_controls_positive=all(
                x["solver_bfs"]["min_orbits"] is not None
                and x["solver_dfs"]["control_at_min_orbits"] is True
                and x["solver_subset"]["control_at_min_orbits"] is True
                for x in certs)))
    out["ok"] = all(r["route_table"]["status"] == "EXHAUSTIVE"
                    and r["route_notable"]["status"] == "EXHAUSTIVE"
                    and r["routes_agree"] and r["all_excluded"]
                    and r["all_controls_positive"] for r in out["rows"])
    (R148 / "certs" / "witnesses_148.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print("PHASE 10/11 OK:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
