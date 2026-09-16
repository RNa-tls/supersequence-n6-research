#!/usr/bin/env python3
"""Round 159 Phase 11/13 -- the SAME-HEX counting lemma, decided abstractly.

THE LEMMA, stripped of everything but what the proof uses.

  Vertices {0, ..., m-1}, the passes, ORDERED BY PASS INDEX.
  A GROUP labelling: each vertex gets a class (hexagon, beta-component).
  A set S of directed edges (the type A and type B beta-edges) such that

     (h1) both endpoints of an edge lie in the SAME group,
     (h2) every edge goes from a strictly SMALLER index to a larger one,
     (h3) every vertex is the target of at most ONE edge.

  Claim:   |S|  <=  sum over groups of (size - 1)   ( = R_int ).

  Proof in one line: by (h1)+(h2) the minimum-index vertex of each group is
  never a target, and by (h3) the map (edge -> its target) is injective, so
  each group carries at most (size - 1) edges.

FINITE UNIVERSE.  For a fixed group partition the admissible S are in
bijection with the choices, for each vertex q, of either "no in-edge" or one
smaller-index vertex of its own group -- so exactly  prod_i (m_i!)  of them.
Enumerating every set partition of {0..m-1} and every such S is therefore
EXHAUSTIVE, with no sampling and no pruning.

ABLATIONS drop (h1), (h2) and (h3) in turn; each must produce a counterexample
or the hypothesis is decorative.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "r156" / "src"))
import abstract156 as A6                                          # noqa: E402


def choices(m, grp, h1=True, h2=True):
    """For each vertex q, the admissible sources of its single in-edge."""
    out = []
    for q in range(m):
        cand = [None]
        for p in range(m):
            if p == q:
                continue
            if h1 and grp[p] != grp[q]:
                continue
            if h2 and not p < q:
                continue
            cand.append(p)
        out.append(cand)
    return out


def sweep(m, h1=True, h2=True, h3=True, cap=None):
    st, ex = Counter(), []
    for grp in A6.part_labels(m):
        R = sum(v - 1 for v in Counter(grp).values())
        ch = choices(m, grp, h1, h2)
        if h3:
            it = itertools.product(*ch)
        else:
            # in-degree may be 2: allow an optional SECOND in-edge per vertex
            it = itertools.product(*[list(itertools.combinations(
                [c for c in cs if c is not None], k))
                for cs in ch for k in ()] or ch)
        n_done = 0
        for pick in it:
            S = [(p, q) for q, p in enumerate(pick) if p is not None]
            st["cases"] += 1
            n_done += 1
            if len(S) > R:
                st["violations"] += 1
                if len(ex) < 4:
                    ex.append(dict(m=m, grp=list(grp), S=S, R=R))
            if cap and n_done >= cap:
                break
    return st, ex


def sweep_indeg2(m):
    """Ablation of (h3): every vertex may take up to TWO in-edges."""
    st, ex = Counter(), []
    for grp in A6.part_labels(m):
        R = sum(v - 1 for v in Counter(grp).values())
        ch = []
        for q in range(m):
            cand = [p for p in range(m) if p != q and grp[p] == grp[q] and p < q]
            opts = [()]
            opts += [(p,) for p in cand]
            opts += list(itertools.combinations(cand, 2))
            ch.append(opts)
        for pick in itertools.product(*ch):
            S = [(p, q) for q, ps in enumerate(pick) for p in ps]
            st["cases"] += 1
            if len(S) > R:
                st["violations"] += 1
                if len(ex) < 4:
                    ex.append(dict(m=m, grp=list(grp), S=S, R=R))
    return st, ex


def main():
    t0 = time.time()
    out = {"exhaustive": [], "ablations": []}
    for m in range(1, 8):
        st, ex = sweep(m)
        out["exhaustive"].append(dict(m=m, cases=st["cases"],
                                      violations=st["violations"],
                                      examples=ex))
        print(f"  m={m}: {st['cases']:,} cases, {st['violations']} violations",
              flush=True)
    for name, kw, fn in (("drop (h1) same group", dict(h1=False), sweep),
                         ("drop (h2) index increases", dict(h2=False), sweep),
                         ("drop (h3) in-degree <= 1", {}, sweep_indeg2)):
        tot, exs = Counter(), []
        for m in range(2, 6):
            st, ex = (fn(m, **kw) if fn is sweep else fn(m))
            tot.update(st)
            exs += ex
        out["ablations"].append(dict(name=name, cases=tot["cases"],
                                     counterexamples=tot["violations"],
                                     example=exs[0] if exs else None,
                                     as_expected=tot["violations"] > 0))
        print(f"  ablation {name}: {tot['cases']:,} cases, "
              f"{tot['violations']} counterexamples", flush=True)
    out["seconds"] = round(time.time() - t0, 1)
    out["exhaustive_cases"] = sum(e["cases"] for e in out["exhaustive"])
    out["ok"] = (all(e["violations"] == 0 for e in out["exhaustive"])
                 and all(a["as_expected"] for a in out["ablations"]))
    (ROOT / "r159" / "certs" / "abstract_159.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("exhaustive", out["exhaustive_cases"], "ok", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
