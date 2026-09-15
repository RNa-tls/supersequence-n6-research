#!/usr/bin/env python3
"""Round 153 Phases 3-4 -- compare every equality-witness enumeration and state
why the enumeration is COMPLETE.

Routes compared:
  A  round 148, production searcher + its bootstrap UB table   (on disk)
  A' round 148, production searcher with NO table              (on disk)
  B  round 153, r153/src/eqwit153.c with a prune list of ROUND-152 CERTIFIED
     values only
  B' round 153, r153/src/eqwit153.c with NO table
  C  round 153, r153/src/eqwit153.py -- separate language, separately built
     catalogue, moves visited in the reverse order

Every witness in every file is REPLAYED before it is counted, so a file that
merely contains the right number of lines proves nothing.

COMPLETENESS.  The enumeration is exhaustive because:
  (1) round 152 certified cap(K) = T for the two cells, so no walk of the
      transition system has more than T ports within the cell's budgets;
  (2) the enumerator visits every walk of the transition system from the fixed
      start word, cutting a branch only by the analytic reach bound (P2), the
      round-150 feasibility lemma, or -- on the table routes -- the (P1)
      monotone bound taken from round-152 CERTIFIED values, all three of which
      are proved never to remove a walk that could still reach T ports;
  (3) fixing the start word at 123456 is without loss of generality because
      left S6 acts transitively on the 720 words and commutes with the whole
      catalogue, which is rechecked here over all 518,400 pairs;
  (4) a realisation of an equality row induces exactly such a walk with exactly
      T ports and total deficit equal to the row's D_sum, and this enumeration
      records every walk with T ports and deficit <= D_sum, which is a superset.
Therefore every capacity-achieving configuration appears in the enumerated set.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r153" / "src"))
import eqwit153 as EW                                               # noqa: E402

ROWS = [
    ("E1", (0, 14, 0, 0, 0, 0), 96, 6, {
        "A_round148_table": "r148/witnesses/row96_table.jsonl",
        "A_round148_notable": "r148/witnesses/row96_notable.jsonl",
        "B_r153_c_table": "r153/certs/E1_table.jsonl",
        "B_r153_c_notable": "r153/certs/E1_notable.jsonl",
        "C_r153_python": "r153/certs/E1_py.jsonl"}),
    ("E2", (0, 8, 0, 0, 0, 1), 92, 7, {
        "A_round148_table": "r148/witnesses/row92_table.jsonl",
        "A_round148_notable": "r148/witnesses/row92_notable.jsonl",
        "B_r153_c_table": "r153/certs/E2_table.jsonl",
        "B_r153_c_notable": "r153/certs/E2_notable.jsonl",
        "C_r153_python": "r153/certs/E2_py.jsonl"}),
]


def read(p):
    out = []
    for line in Path(p).read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        out.append(d["ports"])
    return out


def main():
    t0 = time.time()
    out = dict(equivariance=EW.equivariance_check(), rows=[])
    for name, cell, target, c, files in ROWS:
        entry = dict(name=name, cell="|".join(map(str, cell)), target=target,
                     circuits=c, routes={})
        for tag, rel in files.items():
            p = ROOT / rel
            if not p.exists():
                entry["routes"][tag] = dict(present=False)
                continue
            ports = read(p)
            bad = []
            for w in ports:
                ok, info = EW.check_witness(cell, target, w)
                if not ok:
                    bad.append(info)
            raw = sorted(tuple(w) for w in ports)
            classes = sorted({EW.canonical(w) for w in ports})
            entry["routes"][tag] = dict(
                present=True, file=rel, witnesses=len(ports),
                replay_failures=len(bad), replay_detail=bad[:3],
                raw_sha256=hashlib.sha256(
                    json.dumps([list(x) for x in raw]).encode()).hexdigest(),
                classes=len(classes),
                canonical_sha256=hashlib.sha256(
                    json.dumps([list(x) for x in classes]).encode()).hexdigest(),
                deficits=sorted({5 * len({EW.ORB[v] for v in w}) - len(w)
                                 for w in ports}))
        present = {k: v for k, v in entry["routes"].items() if v["present"]}
        raws = {v["raw_sha256"] for v in present.values()}
        cans = {v["canonical_sha256"] for v in present.values()}
        cnts = {v["witnesses"] for v in present.values()}
        cls = {v["classes"] for v in present.values()}
        entry.update(routes_present=len(present),
                     all_raw_sets_identical=len(raws) == 1,
                     all_canonical_sets_identical=len(cans) == 1,
                     witness_count=sorted(cnts)[0] if len(cnts) == 1 else None,
                     class_count=sorted(cls)[0] if len(cls) == 1 else None,
                     any_replay_failure=any(v["replay_failures"]
                                            for v in present.values()))
        entry["agree"] = (entry["all_raw_sets_identical"]
                          and entry["all_canonical_sets_identical"]
                          and not entry["any_replay_failure"]
                          and len(present) >= 4)
        out["rows"].append(entry)
    out["ok"] = out["equivariance"]["ok"] and all(r["agree"] for r in out["rows"])
    out["seconds"] = round(time.time() - t0, 1)
    (ROOT / "r153" / "certs" / "eqcompare_153.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["equivariance"], indent=1))
    for r in out["rows"]:
        print(f"  {r['name']} cell={r['cell']} target={r['target']}: "
              f"routes={r['routes_present']} witnesses={r['witness_count']} "
              f"classes={r['class_count']} raw_identical="
              f"{r['all_raw_sets_identical']} canonical_identical="
              f"{r['all_canonical_sets_identical']} replay_failures="
              f"{r['any_replay_failure']}")
        for tag, v in r["routes"].items():
            if v["present"]:
                print(f"      {tag:22s} n={v['witnesses']} classes={v['classes']}"
                      f" raw={v['raw_sha256'][:16]} canon="
                      f"{v['canonical_sha256'][:16]} deficits={v['deficits']}")
    print("ok:", out["ok"], f"({out['seconds']}s)")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
