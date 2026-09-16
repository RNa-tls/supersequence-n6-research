#!/usr/bin/env python3
"""Round 156 Phase 2/6/11 -- the extraction claims on ABSTRACT structures.

No words, no catalogue, no n = 6.  The data is exactly what the hypotheses of
the extraction theorem leave you with once the dummy vertex has been deleted:

  (S)  m vertices and a partial injection whose functional graph is
       (some cycles) + EXACTLY ONE path.  The cycles are the beta components
       that do not contain the dummy; the path is the dummy component with the
       dummy removed.  It therefore has m - 1 edges, as beta does.
  (E)  a set E of edges, the "clean E" edges.
  (O)  an orbit labelling, CONSTANT ALONG E EDGES, every class of size <= r.
  (X)  a hexagon labelling, completely arbitrary.
  (L)  LEMMA E: every all-E cycle has exactly r vertices and its vertex set IS
       its entire orbit class.

Claims 1-5, the block identity and the chain count are statements about this
data alone -- the words, the catalogue and n play no further role.  Each sweep
below is EXHAUSTIVE in its own dimensions for the stated m, so those claims are
decided, not sampled; the larger m are sampled and labelled as such.

ABLATIONS drop one hypothesis at a time and look for the first counterexample.
A hypothesis that can be dropped without breaking anything is decorative.
"""
from __future__ import annotations
import itertools, json, random, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------ enumeration
def shapes(m):
    """(succ, cycles, path) for every  cycles + exactly one path  shape.
    There are m * m! of them."""
    verts = list(range(m))
    for s in range(1, m + 1):
        for path in itertools.permutations(verts, s):
            ps = set(path)
            rest = [v for v in verts if v not in ps]
            for perm in itertools.permutations(rest):
                succ = {}
                for i in range(s - 1):
                    succ[path[i]] = path[i + 1]
                pm = dict(zip(rest, perm))
                succ.update(pm)
                cycles, seen = [], set()
                for v in rest:
                    if v in seen:
                        continue
                    cyc, x = [], v
                    while x not in seen:
                        seen.add(x)
                        cyc.append(x)
                        x = pm[x]
                    cycles.append(cyc)
                yield succ, cycles, list(path)


def random_shape(m, rng):
    verts = list(range(m))
    rng.shuffle(verts)
    s = rng.randint(1, m)
    path, rest = verts[:s], verts[s:]
    perm = rest[:]
    rng.shuffle(perm)
    succ = {path[i]: path[i + 1] for i in range(s - 1)}
    pm = dict(zip(rest, perm))
    succ.update(pm)
    cycles, seen = [], set()
    for v in rest:
        if v in seen:
            continue
        cyc, x = [], v
        while x not in seen:
            seen.add(x)
            cyc.append(x)
            x = pm[x]
        cycles.append(cyc)
    return succ, cycles, path


def setparts(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for p in setparts(rest):
        for i in range(len(p)):
            yield p[:i] + [[first] + p[i]] + p[i + 1:]
        yield [[first]] + p


def part_labels(m):
    out = []
    for p in setparts(list(range(m))):
        lab = [0] * m
        for i, blk in enumerate(p):
            for v in blk:
                lab[v] = i
        out.append(lab)
    return out


def e_blocks(m, E, succ):
    par = list(range(m))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for x in E:
        a, b = find(x), find(succ[x])
        if a != b:
            par[a] = b
    groups = {}
    for v in range(m):
        groups.setdefault(find(v), []).append(v)
    return list(groups.values())


def orbit_labelings(m, E, succ, r, respect_E=True):
    blocks = e_blocks(m, E, succ) if respect_E else [[v] for v in range(m)]
    for part in setparts(list(range(len(blocks)))):
        lab, ok = [None] * m, True
        for ci, cl in enumerate(part):
            vs = [v for b in cl for v in blocks[b]]
            if len(vs) > r:
                ok = False
                break
            for v in vs:
                lab[v] = ci
        if ok:
            yield lab


# ---------------------------------------------------------------- the cut
def cut_chains(m, succ, cycles, purevs, cut):
    s2 = {x: y for x, y in succ.items()
          if x not in purevs and x not in cut and y not in purevs}
    indeg = Counter(s2.values())
    chains, used = [], set()
    for s0 in range(m):
        if s0 in purevs or indeg.get(s0):
            continue
        ch, x = [], s0
        while True:
            ch.append(x)
            used.add(x)
            if x not in s2:
                break
            x = s2[x]
        chains.append(ch)
    if len(used) != m - len(purevs):
        return None
    return chains


def orbit_claims(m, r, succ, cycles, E, orb, openings, heavy=(), keep=True):
    """C1, C2, C3 (per chain and summed), BL, C4."""
    pure = [cy for cy in cycles if all(x in E for x in cy)]
    purevs = {x for cy in pure for x in cy}
    c = len(pure)
    cut = set(openings) | (set() if keep else set(heavy))
    chains = cut_chains(m, succ, cycles, purevs, cut)
    if chains is None:
        return ["PARTITION"]
    bad = []
    O = len(set(orb))
    sumP = sum(len(ch) for ch in chains)
    sumO = sum(len({orb[x] for x in ch}) for ch in chains)
    sig = sumO - (O - c)
    blocks = m - len(E)
    Bstar = blocks - (O - c)
    if sumP != m - r * c:
        bad.append("C1")
    if (r * sumO - sumP) != r * O - m + r * sig:
        bad.append("C2")
    tok = blk = 0
    for ch in chains:
        Oi = len({orb[x] for x in ch})
        opened, ti, bi = {orb[ch[0]]}, 0, 1
        for x, y in zip(ch, ch[1:]):
            if x not in E:
                bi += 1
                if orb[y] in opened:
                    ti += 1
            elif orb[y] != orb[x]:
                bad.append("Ehyp")            # only reachable in ablations
            opened.add(orb[y])
        if bi != Oi + ti:
            bad.append("C3")
        tok += ti
        blk += bi
    if blk != blocks:
        bad.append("BL")
    if tok != Bstar - sig:
        bad.append("C3sum")
    if sig < 0:
        bad.append("C4neg")
    if len(chains) == 1 and sig != 0:
        bad.append("C4one")
    if sig > Bstar:
        bad.append("C4sigmaB")
    return bad


def chain_count_claim(m, succ, cycles, E, openings, heavy, keep):
    pure = [cy for cy in cycles if all(x in E for x in cy)]
    purevs = {x for cy in pure for x in cy}
    c, d = len(pure), len(cycles) - len(pure)
    cut = set(openings) | (set() if keep else set(heavy))
    chains = cut_chains(m, succ, cycles, purevs, cut)
    if chains is None:
        return ["PARTITION"]
    h = len(heavy)
    shared = 0 if keep else len(set(openings) & set(heavy))
    expect = d + 1 + (0 if keep else h)
    bad = []
    if len(chains) != expect - shared:
        bad.append("CC")
    if len(chains) > expect:
        bad.append("CCmax")
    return bad


def hexrepeat_claim(m, succ, cycles, path, hexa, cut):
    """C5 for an ARBITRARY cut set: within-chain repeats <= R_int."""
    s2 = {x: y for x, y in succ.items() if x not in cut}
    indeg = Counter(s2.values())
    used, rep = set(), 0
    for s0 in range(m):
        if indeg.get(s0):
            continue
        ch, x = [], s0
        while True:
            ch.append(x)
            used.add(x)
            if x not in s2:
                break
            x = s2[x]
        rep += len(ch) - len({hexa[y] for y in ch})
    if len(used) != m:
        return None                            # an uncut cycle survived
    R = 0
    for comp in cycles + [path]:
        cnt = Counter(hexa[x] for x in comp)
        R += sum(v - 1 for v in cnt.values())
    return ["C5"] if rep > R else []


# ------------------------------------------------------------- the sweeps
def sweep_orbit(m, r, lemmaE=(True, True), respect_E=True, cut_E=False,
                cap=None, sample=None, rng=None):
    st, ex = Counter(), []
    src = ((random_shape(m, rng) for _ in range(sample)) if sample
           else shapes(m))
    for succ, cycles, path in src:
        edges = list(succ)
        emasks = (range(1 << len(edges)) if not sample
                  else [rng.getrandbits(len(edges)) for _ in range(3)])
        for Emask in emasks:
            E = {edges[i] for i in range(len(edges)) if Emask >> i & 1}
            pure = [cy for cy in cycles if all(x in E for x in cy)]
            nonpure = [cy for cy in cycles if not all(x in E for x in cy)]
            opts = []
            for cy in nonpure:
                o = cy if cut_E else [x for x in cy if x not in E]
                if not o:
                    opts = None
                    break
                opts.append(o)
            if opts is None:
                continue
            cp = r if cap is None else cap
            labs = (orbit_labelings(m, E, succ, cp, respect_E) if not sample
                    else itertools.islice(
                        orbit_labelings(m, E, succ, cp, respect_E), 40))
            for orb in labs:
                ok = True
                for cy in pure:
                    if lemmaE[0] and len(cy) != r:
                        ok = False
                    if lemmaE[1] and {v for v in range(m)
                                      if orb[v] == orb[cy[0]]} != set(cy):
                        ok = False
                if not ok:
                    continue
                for openings in (itertools.product(*opts) if opts else [()]):
                    st["cases"] += 1
                    b = orbit_claims(m, r, succ, cycles, E, orb, openings)
                    if b:
                        st["violations"] += 1
                        for x in b:
                            st["v_" + x] += 1
                        if len(ex) < 4:
                            ex.append(dict(m=m, r=r, succ=succ, E=sorted(E),
                                           orb=orb, openings=list(openings),
                                           broke=b))
    return st, ex


def sweep_count(m, sample=None, rng=None):
    st, ex = Counter(), []
    src = ((random_shape(m, rng) for _ in range(sample)) if sample
           else shapes(m))
    for succ, cycles, path in src:
        edges = list(succ)
        for Emask in range(1 << len(edges)):
            E = {edges[i] for i in range(len(edges)) if Emask >> i & 1}
            nonpure = [cy for cy in cycles if not all(x in E for x in cy)]
            opts, skip = [], False
            for cy in nonpure:
                o = [x for x in cy if x not in E]
                if not o:
                    skip = True
                    break
                opts.append(o)
            if skip:
                continue
            nonE = [x for x in edges if x not in E]
            for hm in range(1 << len(nonE)):
                heavy = tuple(nonE[i] for i in range(len(nonE)) if hm >> i & 1)
                for openings in (itertools.product(*opts) if opts else [()]):
                    for keep in (False, True):
                        st["cases"] += 1
                        b = chain_count_claim(m, succ, cycles, E,
                                              list(openings), heavy, keep)
                        if b:
                            st["violations"] += 1
                            for x in b:
                                st["v_" + x] += 1
                            if len(ex) < 4:
                                ex.append(dict(m=m, succ=succ, E=sorted(E),
                                               heavy=list(heavy),
                                               openings=list(openings),
                                               keep=keep, broke=b))
    return st, ex


def sweep_hex(m):
    st, ex = Counter(), []
    labs = part_labels(m)
    for succ, cycles, path in shapes(m):
        edges = list(succ)
        for cm in range(1 << len(edges)):
            cut = {edges[i] for i in range(len(edges)) if cm >> i & 1}
            for hexa in labs:
                r = hexrepeat_claim(m, succ, cycles, path, hexa, cut)
                if r is None:
                    st["uncut_cycle"] += 1
                    continue
                st["cases"] += 1
                if r:
                    st["violations"] += 1
                    if len(ex) < 4:
                        ex.append(dict(m=m, succ=succ, cut=sorted(cut),
                                       hexa=hexa))
    return st, ex


def main():
    t0 = time.time()
    rng = random.Random(156156)
    out = {"orbit_exhaustive": [], "count_exhaustive": [], "hex_exhaustive": [],
           "sampled": [], "ablations": []}
    for m in range(1, 6):
        for r in (2, 3, 4):
            st, ex = sweep_orbit(m, r)
            out["orbit_exhaustive"].append(
                dict(m=m, r=r, cases=st["cases"], violations=st["violations"],
                     examples=ex))
            print(f"  orbit m={m} r={r}: {st['cases']:,} cases, "
                  f"{st['violations']} violations", flush=True)
    for m in range(1, 7):
        st, ex = sweep_count(m)
        out["count_exhaustive"].append(dict(m=m, cases=st["cases"],
                                            violations=st["violations"],
                                            examples=ex))
        print(f"  count m={m}: {st['cases']:,} cases, "
              f"{st['violations']} violations", flush=True)
    for m in range(1, 7):
        st, ex = sweep_hex(m)
        out["hex_exhaustive"].append(dict(m=m, cases=st["cases"],
                                          uncut_cycle=st["uncut_cycle"],
                                          violations=st["violations"],
                                          examples=ex))
        print(f"  hex m={m}: {st['cases']:,} cases, "
              f"{st['violations']} violations", flush=True)
    for m, r in ((6, 3), (7, 3), (8, 4), (9, 4), (10, 5), (12, 5)):
        st, ex = sweep_orbit(m, r, sample=3000, rng=rng)
        out["sampled"].append(dict(m=m, r=r, cases=st["cases"],
                                   violations=st["violations"], examples=ex))
        print(f"  sampled orbit m={m} r={r}: {st['cases']:,} cases, "
              f"{st['violations']} violations", flush=True)

    # ------------------------------------------------- hypothesis ablations
    abl = [
        ("drop_LemmaE_size", 4, 2, dict(lemmaE=(False, True)), True),
        ("drop_E_preserves_orbit", 4, 2, dict(respect_E=False), True),
        ("open_at_a_clean_E_edge", 4, 2, dict(cut_E=True), True),
        # Lemma E's second half -- "the orbit class IS the cycle" -- cannot be
        # ablated while the orbit classes are still capped at r: a pure cycle
        # has r vertices, they are E-connected hence in one class, and a class
        # holds at most r.  So it is DERIVED, not assumed.  Ablating it under
        # the cap must therefore find nothing; ablating it together with the
        # cap must find something.  Both are recorded.
        ("drop_LemmaE_orbit_cap_kept", 4, 2, dict(lemmaE=(True, False)), False),
        ("drop_LemmaE_orbit_and_cap", 5, 2,
         dict(lemmaE=(True, False), cap=4), True),
    ]
    for name, m, r, kw, expect_break in abl:
        st, ex = sweep_orbit(m, r, **kw)
        which = {k[2:]: v for k, v in st.items() if k.startswith("v_")}
        out["ablations"].append(dict(name=name, m=m, r=r, cases=st["cases"],
                                     violations=st["violations"],
                                     expect_break=expect_break, which=which,
                                     example=ex[0] if ex else None,
                                     as_expected=((st["violations"] > 0)
                                                  == expect_break)))
        print(f"  ablation {name}: {st['cases']:,} cases, "
              f"{st['violations']} violations {which}", flush=True)

    out["seconds"] = round(time.time() - t0, 1)
    out["ok"] = (all(e["violations"] == 0 for e in out["orbit_exhaustive"])
                 and all(e["violations"] == 0 for e in out["count_exhaustive"])
                 and all(e["violations"] == 0 for e in out["hex_exhaustive"])
                 and all(e["violations"] == 0 for e in out["sampled"])
                 and all(a["as_expected"] for a in out["ablations"]))
    (ROOT / "r156" / "certs" / "abstract_156.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n")
    print("total decided cases:",
          sum(e["cases"] for e in out["orbit_exhaustive"]
              + out["count_exhaustive"] + out["hex_exhaustive"]),
          "ok:", out["ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
