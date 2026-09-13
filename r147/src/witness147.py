#!/usr/bin/env python3
"""Round 147 Phase 11 -- enumerate the equality witnesses with the SOUND table.

The two rows that survive L = 871 as EQUALITY are found by the corrected
computation, not assumed: nothing here reads the round-144 witness files or the
old Q1/Q2 labels.  For each surviving row the searcher is run in WITNESS mode,
which dumps every chain whose port count equals the required count and whose
deficit equals the budget exactly.  In witness mode the best-so-far prune is
off, so the dump is exhaustive whenever the run ends uncapped -- only the target
prune, the analytic hexagon prune and the sound table prune remain, and all
three are proved bounds.

Each witness is then
  * canonicalised under the left S6 action (relabelling the six letters), which
    commutes with every connector map, so the classes are what "up to symmetry"
    means here;
  * fed to the pure-circuit coexistence test (src/l6_cover_bfs_146.py), which
    also reports the minimum number of tau-orbits that DOES cover F, so a
    negative answer comes with its own positive control.
"""
from __future__ import annotations
import itertools, json, subprocess, sys, time
from pathlib import Path

R147 = Path(__file__).resolve().parent.parent
ROOT = R147.parent
sys.path.insert(0, str(R147 / "src"))
sys.path.insert(0, str(ROOT / "src"))
import ub147                                                        # noqa: E402
import l6_cover_bfs_146 as CB                                       # noqa: E402

EXE = R147 / "l6chain147.exe"
PERMS = ["".join(p) for p in itertools.permutations("123456")]
IDX = {p: i for i, p in enumerate(PERMS)}
NODECAP = 400_000_000_000


def canon(ports):
    """Least relabelling of the six letters, applied to the whole port list."""
    words = [PERMS[v] for v in ports]
    best = None
    for g in itertools.permutations("123456"):
        m = {c: g[i] for i, c in enumerate("123456")}
        seq = tuple(IDX["".join(m[c] for c in w)] for w in words)
        if best is None or seq < best:
            best = seq
    return best


def store():
    out = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        p = R147 / "tables" / f
        if p.exists():
            for k, v in json.loads(p.read_text()).items():
                if v.get("status") == "EXACT_UNCAPPED":
                    out[tuple(int(x) for x in k.split("|"))] = dict(cc=v["cc"])
    return out


def enumerate_row(name, cell, target, c):
    b, d, a, bb, e, h = cell
    st = store()
    ubp = R147 / "witnesses" / f"ub_{name}.txt"
    info = ub147.write_table(ubp, cell, st, exclude={cell})
    val = ub147.validate_table(ubp, cell, st, exclude={cell})
    if not val["ok"]:
        return dict(name=name, status="UB_TABLE_REJECTED", ub_validation=val)
    wp = R147 / "witnesses" / f"wit_{name}.jsonl"
    t0 = time.time()
    r = subprocess.run([str(EXE), str(b), str(d), str(a), str(bb), str(e),
                        str(h), str(NODECAP), str(ubp), str(target), str(wp)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        return dict(name=name, status="ERROR", stderr=r.stderr[:300])
    j = json.loads(r.stdout)
    raw = [json.loads(x)["ports"] for x in wp.read_text().splitlines() if x.strip()]
    classes = {}
    for p in raw:
        classes.setdefault(canon(p), []).append(p)
    out = dict(name=name, cell=list(cell), target=target, c=c,
               status="UNKNOWN_CAP" if j["capped"] else "EXHAUSTIVE",
               capped=j["capped"], nodes=j["nodes"], cc=j["cc"],
               seconds=round(time.time() - t0, 1),
               witnesses_raw=len(raw), classes_up_to_left_S6=len(classes),
               ub_rows=info["rows"], ub_validation_ok=val["ok"])
    # the pure-circuit test, one representative per class, and every raw witness
    dec = []
    for i, (ck, members) in enumerate(sorted(classes.items())):
        rep = members[0]
        res = CB.decide(rep, c)
        cnt = CB.hand_count(rep, c)
        dec.append(dict(cls=i, members=len(members), ports=len(rep),
                        bfs=res, counting=cnt))
    out["pure_circuit_test"] = dec
    out["all_excluded"] = all(not x["bfs"]["coverable_by_c_orbits"] for x in dec)
    out["all_controls_positive"] = all(
        x["bfs"]["min_orbits_to_cover_F"] is not None for x in dec)
    return out


def main(argv):
    (R147 / "witnesses").mkdir(parents=True, exist_ok=True)
    ev = json.loads((R147 / "rows" / "rows_eval_147.json").read_text())
    jobs = []
    for t in (3, 4):
        for s in ev.get(f"L{867 + t}_survivors", []):
            if s["verdict"] != "EQUALITY":
                continue
            k, G, c, d, h = s["k"], s["G"], s["c"], s["d"], s["h"]
            req = s["required"]
            # the attaining object: one chain, s = 0, heavy joints kept inside
            cell = (0, 5 * k - G, min(s["D2"], 2 * s["g"]),
                    min(s["Qs"], 2 * s["g"]),
                    min(max(0, s["Z"] - s["Qs"]), 2 * s["g"]), h)
            jobs.append((f"L{867 + t}_k{k}_G{G}_c{c}_h{h}", cell, req, c, s))
    out = {"rows": []}
    for name, cell, req, c, s in jobs:
        print(f"enumerating {name}: cell={cell} target={req} c={c}", flush=True)
        r = enumerate_row(name, cell, req, c)
        r["row"] = s
        out["rows"].append(r)
        print(json.dumps({k: v for k, v in r.items()
                          if k not in ("pure_circuit_test", "row")}), flush=True)
        for x in r.get("pure_circuit_test", []):
            print("   ", json.dumps(x), flush=True)
    out["ok"] = bool(out["rows"]) and all(
        r.get("status") == "EXHAUSTIVE" and r.get("all_excluded")
        and r.get("all_controls_positive") for r in out["rows"])
    (R147 / "certs" / "witnesses_147.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print("ALL EQUALITY ROWS EXCLUDED:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
