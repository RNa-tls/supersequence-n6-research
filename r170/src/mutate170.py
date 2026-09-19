#!/usr/bin/env python3
"""Round 170 -- mutation regression for the two-factor architecture.

Round 168's suite attacked the EXTREE layer.  Round 170 added three things
that layer cannot defend on its own, so each gets its own attacks:

  a LADDER, whose rungs close no census row and so cannot be validated by
  "does the census still close" -- only by the certificate chain;
  a CENSUS-SAFE BOUND, which is weaker than the exact capacity and therefore
  has to be shown to be the LARGEST value that still closes every row;
  a LOWER-BOUND CERTIFICATE, the claim that no 34-cell basis exists, which is
  an assertion about an exhaustive scan and is worthless if the scan can be
  quietly narrowed.

The EXTREE attacks run against the genuine A2 target certificate rather than a
synthetic DAG.  It carries only 218 proof nodes while citing 109 dependencies
across five referenced batches, so it exercises the full reference and
dependency machinery at negligible replay cost -- the ladder it depends on is
accepted on its pinned hash, exactly as production does.

Every case states the outcome it expects BEFORE running, and a case that is
expected to be rejected but is accepted is reported as MISSED, not explained.
"""
from __future__ import annotations
import gzip, json, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
sys.path.insert(0, str(ROOT / "r169" / "src"))
import verify168 as V                                             # noqa: E402
from gzrule167 import write_gz                                    # noqa: E402
from closure169 import ClosedSystem                               # noqa: E402

SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")
WORK = SCRATCH / "r170mut"
TARGET_REL = "r170/certs/extree_target_a2_170.txt.gz"
LADDER_REL = "r170/certs/extree_ladder_a2_170.txt.gz"
COPY = ("r164/certs/extree_prefix_164.txt.gz",
        "r166/certs/extree_batch2_166.txt.gz",
        "r166/certs/extree_batch3_166.txt.gz",
        "r168/certs/extree_batch1_168.txt.gz",
        LADDER_REL)


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


def verify_text(text, swap=()):
    """Verify a mutated target certificate in an isolated tree."""
    if WORK.exists():
        shutil.rmtree(WORK)
    for rel in COPY:
        (WORK / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, WORK / rel)
    for rel, t in swap:
        (WORK / rel).parent.mkdir(parents=True, exist_ok=True)
        write_gz(WORK / rel, t)
    (WORK / TARGET_REL).parent.mkdir(parents=True, exist_ok=True)
    write_gz(WORK / TARGET_REL, text)
    old = V.ROOT
    V.ROOT = WORK
    try:
        res = V.verify_any(TARGET_REL)
        return bool(res["ok"]), res.get("error")
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        V.ROOT = old


def main():
    V.load_trust()
    text = gzip.decompress((ROOT / TARGET_REL).read_bytes()).decode()
    lines = text.splitlines()
    ladder_text = gzip.decompress((ROOT / LADDER_REL).read_bytes()).decode()
    ref_line = next(l for l in lines if l.startswith("ref ")
                    and l.strip().endswith(LADDER_REL))
    dep_lines = [l for l in lines if l.startswith("dep ")]
    tree_line = next(l for l in lines if l.startswith("tree "))
    rows = []
    t0 = time.time()

    def case(name, mutate, expect_valid, swap=()):
        try:
            t = mutate()
        except Exception as e:
            rows.append(dict(attack=name, expected_valid=expect_valid,
                             accepted=None, correct=False,
                             rejection=f"mutation could not be built: {e}"))
            print(f"  {name:<52} BUILD-ERROR   MISSED", flush=True)
            return
        ok, err = verify_text(t, swap)
        rows.append(dict(attack=name, expected_valid=expect_valid,
                         accepted=ok, correct=(ok == expect_valid),
                         rejection=None if ok else str(err)[:140]))
        print(f"  {name:<52} {'accepted' if ok else 'rejected':<9}"
              f"{'OK' if rows[-1]['correct'] else '  MISSED'}", flush=True)

    print("EXTREE layer, against the genuine A2 target certificate", flush=True)
    case("unchanged (control)", lambda: text, True)

    # 1. a fake ladder certificate substituted for the real one
    def fake_ladder():
        # rungs claimed at absurdly strong bounds, with no trees at all
        body = ["L6-EXTREE-3"]
        for d in range(2, 18):
            body.append(f"tree 0 {d} 2 0 0 0 1")
            body.append("L")
        return text
    case("fake ladder certificate substituted", fake_ladder, False,
         swap=((LADDER_REL, "\n".join(
             ["L6-EXTREE-3"]
             + [f"tree 0 {d} 2 0 0 0 1\nL" for d in range(2, 18)]) + "\n"),))

    # 2. altered rung hash in the declared reference
    case("altered rung/ladder reference hash",
         lambda: text.replace(ref_line.split()[1],
                              "0" * 8 + ref_line.split()[1][8:]), False)

    # 3. a predecessor the proof needs is removed from the reference list
    case("missing predecessor reference",
         lambda: "\n".join(l for l in lines
                           if not l.strip().endswith(LADDER_REL)) + "\n",
         False)

    # 4. a counterfactual predecessor smuggled in as genuine: a dep line for a
    #    cell at a capacity no referenced certificate actually proves
    def counterfactual_dep():
        d = dep_lines[0].split()
        d[7] = str(int(d[7]) - 12)          # a stronger bound than proved
        return text.replace(dep_lines[0], " ".join(d))
    case("counterfactual predecessor admitted as genuine",
         counterfactual_dep, False)

    # 5a. wrong safe bound declared on the tree
    def wrong_bound():
        t = tree_line.split()
        t[7] = str(int(t[7]) - 5)           # claim a bound the tree lacks
        return text.replace(tree_line, " ".join(t))
    case("declared bound stronger than the tree proves", wrong_bound, False)

    # ---- census layer: the safe bound and the basis
    print("census layer, against the exact 35-cell basis", flush=True)
    bas = json.loads((ROOT / "r170" / "certs" / "basis_170.json").read_text())
    src = json.loads((ROOT / "r169" / "certs"
                      / "p1_closure_169.json").read_text())
    E = [parse(c) for c in src["minimum"]["cells"]]
    X = [parse(c) for c in bas["minimum"]["witness_completion"]]
    BASIS = sorted(set(E + X))
    S = ClosedSystem()
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    EXS = set(EX)

    def closes(sel, values=None, rows_=None):
        S.apply(set(sel), values=values)
        v = S.verdicts(rows_ or EXS)
        return all(v[k] == "STRICTLY_CLOSED" for k in (rows_ or EXS))

    cens = []

    def ccase(name, ok_expected, got):
        cens.append(dict(attack=name, expected_closes=ok_expected,
                         closes=got, correct=(got == ok_expected)))
        print(f"  {name:<52} {'closes' if got else 'opens':<9}"
              f"{'OK' if cens[-1]['correct'] else '  MISSED'}", flush=True)

    ccase("basis at exact values (control)", True, closes(BASIS))

    # 5b. a safe bound one step too weak must OPEN a row
    for K, S_ok in ((parse("0|15|0|0|0|1"), 115),
                    (parse("0|18|2|0|0|0"), 117)):
        ccase(f"safe bound +1 on {cellstr(K)} (S={S_ok}->{S_ok + 1})",
              False, closes(BASIS, values={K: S_ok + 1}))

    # 7. missing residual-row coverage: drop a completion cell
    for K in X:
        ccase(f"residual completion cell {cellstr(K)} removed",
              False, closes([c for c in BASIS if c != K]))

    # 6. invalid (P1) domination direction, checked over certified pairs
    def dom_violations(reverse):
        bad = 0
        items = list(S.chain_tab.items())[:400]
        for K, c in items:
            for T, ct in items:
                if K == T:
                    continue
                fwd = all(t <= k for t, k in zip(T, K))
                if (fwd and not reverse and ct > c) or \
                   (fwd and reverse and ct < c):
                    bad += 1
                    if bad > 3:
                        return bad
        return bad
    fwd_bad = dom_violations(False)
    rev_bad = dom_violations(True)
    cens.append(dict(attack="(P1) direction: correct orientation",
                     expected_violations=0, violations=fwd_bad,
                     correct=fwd_bad == 0))
    print(f"  {'(P1) correct orientation':<52} "
          f"{fwd_bad} violations   {'OK' if not fwd_bad else '  MISSED'}",
          flush=True)
    cens.append(dict(attack="(P1) direction: reversed orientation must break",
                     expected_violations=">0", violations=rev_bad,
                     correct=rev_bad > 0))
    print(f"  {'(P1) reversed orientation':<52} "
          f"{rev_bad} violations   {'OK' if rev_bad else '  MISSED'}",
          flush=True)

    # 8. corrupted lower-bound certificate: claim 34 is reachable
    single = {K for K in S.chain_tab if K not in S.dual_chain}
    st = json.loads((ROOT / "r168" / "certs" / "state_168.json").read_text())
    univ = sorted({parse(c) for c in st["universe_cells"]} | single)
    S.apply(set(E))
    ve = S.verdicts(EXS)
    R = {k for k in EX if ve[k] != "STRICTLY_CLOSED"}
    forged = None
    for K in sorted(set(univ) - set(E), key=cellstr):
        S.apply(set(E) | {K})
        v = S.verdicts(R)
        if all(v[k] == "STRICTLY_CLOSED" for k in R):
            forged = cellstr(K)
            break
    cens.append(dict(
        attack="corrupted lower bound: some single cell completes the 33",
        expected_closes=False, closes=forged is not None,
        correct=forged is None,
        detail=f"forged witness {forged}" if forged else
               "no single cell completes: the 34-impossible claim survives an "
               "independent exhaustive rescan"))
    print(f"  {'forged 34-cell witness':<52} "
          f"{'FOUND' if forged else 'none':<9}"
          f"{'  MISSED' if forged else 'OK'}", flush=True)

    all_rows = rows + cens
    missed = [r for r in all_rows if not r["correct"]]
    out = dict(
        extree_layer=dict(subject=TARGET_REL, cases=rows,
                          note="the A2 target carries 218 proof nodes while "
                               "citing 109 dependencies over five batches, so "
                               "the reference and dependency machinery is "
                               "fully exercised at negligible replay cost"),
        census_layer=dict(basis_size=len(BASIS), exposed_rows=len(EX),
                          cases=cens),
        not_expressible=[
            "corrupt token state, used-hexagon state or feasibility "
            "histogram: the certificate stores only N<k> and L, with no "
            "solver state, and the verifier recomputes all of it",
            "alter prune reason: no prune label is stored",
        ],
        total_cases=len(all_rows),
        missed=missed,
        all_invalid_paths_rejected=not missed,
        seconds_noncanonical=round(time.time() - t0, 1),
    )
    out["ok"] = not missed
    (ROOT / "r170" / "certs" / "mutations_170.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"\n{len(all_rows)} cases, {len(missed)} missed", flush=True)
    return 0 if not missed else 1


if __name__ == "__main__":
    sys.exit(main())
