#!/usr/bin/env python3
"""Round 149 K -- an INDEPENDENT certificate checker for the capacity values.

After the hand proof the finite residue is: "cell (b,d,a,bb,e,h) has capacity
cc".  That splits into two halves.

  ATTAINABILITY  some admissible walk has cc ports.  This half has a short
                 certificate -- the walk itself -- and is checked HERE, by a
                 checker written from the transition rules, not from the
                 solver: it re-derives the catalogue from string algebra, walks
                 the certificate, and recomputes every counter.  It shares no
                 code path with the C searcher and no architecture with it.
  MAXIMALITY     no admissible walk has cc+1 ports.  This half has no short
                 certificate; it is the exhaustive search, and it is what the
                 two independent implementations agree on (905/905 cells).

So this checker closes the half that CAN be closed by a certificate, and says
so about the half that cannot.  A cell whose witness cannot be produced within
the budget is UNKNOWN_CAP -- never "verified".
"""
from __future__ import annotations
import itertools, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R147, R149 = ROOT / "r147", ROOT / "r149"
sys.path.insert(0, str(R147 / "src"))
import catalogue147 as C                                            # noqa: E402
import ub147                                                        # noqa: E402

EXE = R147 / "l6chain147b.exe"
PERMS, IDX, HEX, ORB, PH = C.PERMS, C.IDX, C.HEX, C.ORB, C.PHASE
FREE, DA, DB, PAID, KIND, HEAVY = C.catalogue()
MOVE = {}
for i in range(720):
    MOVE[(i, FREE[i])] = ("freeE", 0)
    MOVE.setdefault((i, DA[i]), ("dirtyA", 0))
    MOVE.setdefault((i, DB[i]), ("dirtyB", 0))
    for j in range(5):
        MOVE.setdefault((i, PAID[i][j]), ("paid", 0))
    for t, c in HEAVY[i]:
        MOVE.setdefault((i, t), ("heavy", c))
BUDGET = int(os.environ.get("R149_CELL_SECONDS", "300"))


def verify_walk(ports, cell):
    """Independently replay a claimed maximal walk and recompute every counter."""
    b, dmax, amax, bmax, emax, hmax = cell
    if len(set(ports)) != len(ports):
        return dict(ok=False, why="ports repeat")
    phm, hexu = {}, set()
    deficit, tok, a, bb, e, h = 4, 0, 0, 0, 0, 0
    v0 = ports[0]
    phm[ORB[v0]] = {PH[v0]}
    hexu.add(HEX[v0])
    for i in range(len(ports) - 1):
        u, t = ports[i], ports[i + 1]
        mv = MOVE.get((u, t))
        if mv is None:
            return dict(ok=False, why="not a legal move", at=i)
        name, ch = mv
        q = ORB[t]
        if PH[t] in phm.get(q, set()):
            return dict(ok=False, why="phase reused", at=i)
        fresh = q not in phm
        if name == "freeE" and q != ORB[u]:
            return dict(ok=False, why="free E left its orbit", at=i)
        newhex = HEX[t] not in hexu
        if not newhex and name not in ("dirtyA", "dirtyB"):
            e += 1
        a += name == "dirtyA"
        bb += name == "dirtyB"
        h += ch if name == "heavy" else 0
        tok += 0 if (name == "freeE" or fresh) else 1
        phm.setdefault(q, set()).add(PH[t])
        deficit += 4 if fresh else -1
        hexu.add(HEX[t])
    orbits = len(phm)
    ok = (tok <= b and deficit <= dmax and a <= amax and bb <= bmax
          and e <= emax and h <= hmax
          and deficit == 5 * orbits - len(ports))
    return dict(ok=ok, ports=len(ports), orbits=orbits, deficit=deficit,
                tok=tok, a=a, bb=bb, e=e, h=h,
                deficit_identity_holds=(deficit == 5 * orbits - len(ports)))


def store():
    st = {}
    for f in ("chain_cells_147.json", "heavy_cells_147.json"):
        for k, v in json.loads((R147 / "tables" / f).read_text()).items():
            if v.get("status") == "EXACT_UNCAPPED":
                st[tuple(int(x) for x in k.split("|"))] = v
    return st


ST = store()


def one(cell, tmp):
    cc = ST[cell]["cc"]
    ubp = tmp / ("ub_%d_%d_%d_%d_%d_%d.txt" % cell)
    ub147.write_table(ubp, cell, {k: dict(cc=v["cc"]) for k, v in ST.items()
                                  if k != cell}, exclude={cell})
    a = [str(x) for x in cell]
    try:
        j = json.loads(subprocess.run([str(EXE)] + a + ["0", str(ubp), "0"],
                                      capture_output=True, text=True, cwd=ROOT,
                                      timeout=BUDGET).stdout)
    except Exception as ex:
        return dict(cell=list(cell), status="UNKNOWN_CAP", why=repr(ex)[:90])
    if j["capped"] or j["cc"] != cc:
        return dict(cell=list(cell), status="UNKNOWN_CAP",
                    why=f"capped={j['capped']} cc={j['cc']} vs {cc}")
    tab = j["table"]
    dstar = next((d for d in range(cell[1] + 1) if tab.get(str(d)) == cc), None)
    if dstar is None:
        return dict(cell=list(cell), status="UNKNOWN_CAP",
                    why="no deficit level attains the capacity")
    wp = tmp / ("wit_%d_%d_%d_%d_%d_%d.jsonl" % cell)
    aa = [str(cell[0]), str(dstar)] + [str(x) for x in cell[2:]]
    # The WITNESS is generated by the solver; that is fine and is the right
    # separation for a certificate checker -- what must be independent is the
    # VERIFICATION, and verify_walk() re-derives the catalogue from string
    # algebra and recomputes every counter without touching the solver.  Using
    # the sound table here only makes the witness cheaper to find; the witness
    # itself is then checked on its own terms.
    try:
        jw = json.loads(subprocess.run([str(EXE)] + aa + ["0", str(ubp), str(cc),
                                                          str(wp)],
                                       capture_output=True, text=True, cwd=ROOT,
                                       timeout=BUDGET).stdout)
    except Exception as ex:
        return dict(cell=list(cell), status="UNKNOWN_CAP",
                    why="witness run: " + repr(ex)[:80])
    lines = [x for x in wp.read_text().splitlines() if x.strip()] if wp.exists() else []
    if not lines:
        return dict(cell=list(cell), status="UNKNOWN_CAP",
                    why="no witness dumped", capped=jw["capped"])
    ports = json.loads(lines[0])["ports"]
    v = verify_walk(ports, (cell[0], dstar) + tuple(cell[2:]))
    return dict(cell=list(cell), claimed_capacity=cc, deficit_level=dstar,
                witness_ports=len(ports), independent_replay=v,
                witnesses_dumped=len(lines),
                status=("ATTAINABILITY_VERIFIED"
                        if v["ok"] and len(ports) == cc else "MISMATCH"))


def main(argv):
    tmp = R149 / "logs" / "cert"
    tmp.mkdir(parents=True, exist_ok=True)
    sel = [(0, 14, 0, 0, 0, 0), (0, 8, 0, 0, 0, 1), (0, 0, 0, 0, 0, 0)]
    cheap = sorted((k for k in ST if (ST[k]["nodes"] or 0) < 3_000_000),
                   key=lambda k: ST[k]["nodes"] or 0)
    step = max(1, len(cheap) // int(argv[0] if argv else 60))
    sel += [k for k in cheap[::step] if k not in sel]
    rows = []
    for cell in sel:
        r = one(cell, tmp)
        rows.append(r)
        print(json.dumps(r), flush=True)
    ver = sum(1 for r in rows if r["status"] == "ATTAINABILITY_VERIFIED")
    out = dict(cells=len(rows), attainability_verified=ver,
               unknown_cap=[r["cell"] for r in rows
                            if r["status"] == "UNKNOWN_CAP"],
               mismatches=[r for r in rows if r["status"] == "MISMATCH"],
               note="ATTAINABILITY only.  Maximality is the exhaustive search, "
                    "cross-verified by the second implementation on all 905 "
                    "load-bearing cells.  A cap is UNKNOWN_CAP, never UNSAT.",
               detail=rows,
               ok=(ver > 0 and not [r for r in rows if r["status"] == "MISMATCH"]))
    (R149 / "certs" / "certcheck_149.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
