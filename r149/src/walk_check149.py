#!/usr/bin/env python3
"""Round 149 A/H -- is a REAL extracted chain literally a walk in the searcher's
move graph, with the searcher's own bookkeeping reproducing the extraction's
budgets?

This is the join between the hand theorem (the extraction) and the machine
(the capacity searcher).  The searcher's maximum bounds reality only if

  (W1) every step of a real chain is one of the searcher's moves, and
  (W2) the resources the searcher charges for those steps are no more than the
       budgets the extraction proves the row provides.

(W1) is about the MOVE CATALOGUE; (W2) is about the BOOKKEEPING.  Both are
checked here literally, step by step, on real covers -- not by comparing
aggregate numbers, but by replaying each chain through the searcher's own
transition rules and watching the counters.

Nothing here is evidence that the bound holds for hypothetical short covers;
that is the hand proof's job (r149/PROOF.md).  What this establishes is that
the machine's transition system is the real one, so the hand proof about the
transition system is a hand proof about covers.
"""
from __future__ import annotations
import gzip, itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r147" / "src"))
sys.path.insert(0, str(ROOT / "src"))
import catalogue147 as C                                            # noqa: E402
import l6_extraction_145 as EX                                      # noqa: E402
import l6_splicing_145 as SP                                        # noqa: E402

PERMS, IDX, HEX, ORB, PH = C.PERMS, C.IDX, C.HEX, C.ORB, C.PHASE
FREE, DA, DB, PAID, KIND, HEAVY = C.catalogue()
MOVES = {}
for i in range(720):
    MOVES[(i, FREE[i])] = ("freeE", 0)
    MOVES.setdefault((i, DA[i]), ("dirtyA", 0))
    MOVES.setdefault((i, DB[i]), ("dirtyB", 0))
    for j in range(5):
        MOVES.setdefault((i, PAID[i][j]), (f"paid{KIND[i][j]}", 0))
    for t, c in HEAVY[i]:
        MOVES.setdefault((i, t), ("heavy", c))


def chains_of(W, n=6, keep_heavy=False):
    """The chains the extraction produces, as lists of pass-entry indices."""
    b = EX.build(W, n)
    passes, P, beta, dummy = b["passes"], b["P"], b["beta"], b["dummy"]
    etype = b["etype"]
    seen, comps = [False] * (P + 1), []
    for i in range(P + 1):
        if seen[i]:
            continue
        cy, x = [], i
        while not seen[x]:
            seen[x] = True
            cy.append(x)
            x = beta[x]
        comps.append(cy)
    pure = [cy for cy in comps if dummy not in cy
            and all(etype.get(x) == "E" for x in cy)]
    nonpure = [cy for cy in comps if cy not in pure]
    out = []
    for cy in nonpure:
        if dummy in cy:
            # the component carrying the DUMMY is already a path once the dummy
            # is removed: the dummy marks where the writing order starts and
            # ends, so the element after it is the first port and the element
            # before it is the last.  Rotating this one as if it were a cycle
            # invents an edge that does not exist -- an earlier version of this
            # script did exactly that and manufactured a phantom weight-6
            # "heavy" step (342156 -> 123456) that blew the heavy budget.
            j = cy.index(dummy)
            seq = cy[j + 1:] + cy[:j]
        else:
            seq = list(cy)
            # a nonpure cycle is opened at one non-E edge
            k = next((j for j in range(len(seq))
                      if etype.get(seq[j]) not in (None, "E")), 0)
            seq = seq[k + 1:] + seq[:k + 1]
        cut = []
        cur = []
        for j, x in enumerate(seq):
            cur.append(x)
            if not keep_heavy and etype.get(x) not in (None, "E") \
               and b["eweight"].get(x, 0) >= 4 and j < len(seq) - 1:
                cut.append(cur)
                cur = []
        if cur:
            cut.append(cur)
        for piece in cut:
            out.append([passes[x][0] for x in piece])
    return out, len(pure)


def replay(chain):
    """Replay a chain through the searcher's transition rules."""
    ports = [IDX[v] for v in chain]
    if len(set(ports)) != len(ports):
        return dict(ok=False, why="ports not distinct")
    hexu, phm, opened = {}, {}, []
    deficit, tok, a, bb, e, h = 4, 0, 0, 0, 0, 0
    steps = []
    v0 = ports[0]
    phm[ORB[v0]] = {PH[v0]}
    opened.append(ORB[v0])
    hexu[HEX[v0]] = 1
    for i in range(len(ports) - 1):
        u, t = ports[i], ports[i + 1]
        mv = MOVES.get((u, t))
        if mv is None:
            return dict(ok=False, why="step is NOT a catalogue move",
                        at=i, src=PERMS[u], dst=PERMS[t],
                        gap=C.gap(C.end(PERMS[u]), PERMS[t]))
        name, cost_h = mv
        q = ORB[t]
        fresh = q not in phm
        if PH[t] in phm.get(q, ()):
            return dict(ok=False, why="phase reused", at=i)
        newhex = HEX[t] not in hexu
        if not newhex and name not in ("dirtyA", "dirtyB"):
            e += 1
        if name == "dirtyA":
            a += 1
        if name == "dirtyB":
            bb += 1
        if name == "heavy":
            h += cost_h
        if name == "freeE":
            if q != ORB[u]:
                return dict(ok=False, why="free E left the orbit", at=i)
            cost = 0
        else:
            cost = 0 if fresh else 1
        tok += cost
        phm.setdefault(q, set()).add(PH[t])
        if fresh:
            opened.append(q)
            deficit += 4
        else:
            deficit -= 1
        hexu[HEX[t]] = hexu.get(HEX[t], 0) + 1
        steps.append(name)
    return dict(ok=True, ports=len(ports), deficit=deficit, tok=tok,
                a=a, bb=bb, e=e, h=h, orbits=len(phm),
                distinct_hexes=len(hexu), steps=steps)


def words(paths, limit):
    n = 0
    for p in paths:
        p = Path(p)
        op = gzip.open if p.suffix == ".gz" else open
        with op(p, "rt") as fh:
            for ln in fh:
                w = ln.strip()
                if len(w) >= 800 and len(set(w)) == 6:
                    yield w
                    n += 1
                    if n >= limit:
                        return


def main(argv):
    limit = int(argv[0]) if argv and argv[0].isdigit() else 60
    paths = [a for a in argv if not a.isdigit()]
    rows, bad = [], []
    for W in words(paths, limit):
        r = EX.extract(W, 6, keep_heavy=False)
        ch, npure = chains_of(W)
        reps = [replay(c) for c in ch]
        okall = all(x["ok"] for x in reps)
        tot = dict(ports=sum(x.get("ports", 0) for x in reps),
                   deficit=sum(x.get("deficit", 0) for x in reps),
                   tok=sum(x.get("tok", 0) for x in reps),
                   a=sum(x.get("a", 0) for x in reps),
                   bb=sum(x.get("bb", 0) for x in reps),
                   e=sum(x.get("e", 0) for x in reps),
                   h=sum(x.get("h", 0) for x in reps))
        agree = dict(
            ports=(tot["ports"] == r["sum_P"]),
            deficit=(tot["deficit"] == r["sum_D"]),
            tokens=(tot["tok"] == r["sum_tok"]),
            chains=(len(ch) == r["chains"]),
            circuits=(npure == r["c"]))
        # the budgets the ROW provides, from the extraction's own numbers
        Z = (r["G"] - r["c"]) - r["D2"]          # z = G - c = 2g + d, Z = z - D2
        budget = dict(a_max=r["D2"], bb_max=r["Qs"],
                      e_max=max(0, Z - r["Qs"]),
                      sum_max=2 * r["g"], h_max=r["H"], Z=Z)
        within = dict(a=(tot["a"] <= budget["a_max"]),
                      bb=(tot["bb"] <= budget["bb_max"]),
                      e=(tot["e"] <= budget["e_max"]),
                      sum=(tot["a"] + tot["bb"] + tot["e"] <= budget["sum_max"]),
                      h=(tot["h"] <= budget["h_max"]))
        rec = dict(length=r["length"], profile=dict(k=r["k"], G=r["G"], c=r["c"],
                   d=r["d"], H=r["H"], Z=Z, D2=r["D2"], Qs=r["Qs"],
                   g=r["g"], Bstar=r["Bstar"]),
                   chains=len(ch), replay_ok=okall, totals=tot,
                   budget=budget, agree=agree, within_budget=within,
                   failures=[x for x in reps if not x["ok"]][:2])
        rows.append(rec)
        if not (okall and all(agree.values()) and all(within.values())):
            bad.append(rec)
    out = dict(covers=len(rows), violations=len(bad),
               all_steps_are_catalogue_moves=all(r["replay_ok"] for r in rows),
               bookkeeping_matches_extraction=all(all(r["agree"].values())
                                                  for r in rows),
               within_row_budgets=all(all(r["within_budget"].values())
                                      for r in rows),
               examples=rows[:4], bad=bad[:3],
               ok=(len(rows) > 0 and not bad))
    (ROOT / "r149" / "certs" / "walk_check_149.json").write_text(
        json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("examples", "bad")}))
    for r in rows[:3]:
        print("  ", json.dumps({k: r[k] for k in
                                ("length", "chains", "totals", "budget",
                                 "agree", "within_budget")}))
    for r in bad[:2]:
        print("  BAD", json.dumps(r)[:500])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
