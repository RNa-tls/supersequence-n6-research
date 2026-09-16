#!/usr/bin/env python3
"""Round 163 phases 10-12 -- independent re-derivation of H.catalogue,
H.wlog and the H.feas dual lemma.

These three nodes were never given a dedicated audit round.  Their evidence is
r149/PROOF.md sections 2.2-2.4 / 9.5 and r150/PROOF.md, both of which report
exhaustive checks.  A reported check is not a verified check, so everything
load-bearing in them is recomputed here from the definitions, importing
nothing from src/ or r149/ or r150/.
"""
from __future__ import annotations
import itertools, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
N = 6
LET = "123456"
PERMS = ["".join(p) for p in itertools.permutations(LET)]
PSET = set(PERMS)


def sigma(w):            # w[1:] + w[0]
    return w[1:] + w[0]


def sigma_inv(w):        # end(v)
    return w[-1] + w[:-1]


def tau(w):              # rotate the first n-1 letters, fix the last
    return w[1:N - 1] + w[0] + w[N - 1]


def hexrep(w):           # canonical name of the sigma-class
    best, x = w, w
    for _ in range(N - 1):
        x = sigma(x)
        best = min(best, x)
    return best


def omega(a, b):
    for k in range(1, N + 1):
        if a[k:] == b[:N - k]:
            return k
    return N


def hidden(a, b, g):
    """permutation windows strictly inside the spelling a + b[N-g:]"""
    sp = a + b[N - g:]
    return [sp[i:i + N] for i in range(1, len(sp) - N)
            if sp[i:i + N] in PSET]


# --------------------------------------------------------- H.catalogue
def catalogue():
    t0 = time.time()
    gapdist, kinds, per_src = Counter(), Counter(), Counter()
    bad, unclassified = [], []
    c1 = c2a = c2b = c3a = c3b = 0
    paid_in_source_hex = 0
    heavy_in_source_hex = 0
    excluded = Counter()
    for v in PERMS:
        src = sigma_inv(v)
        hv = hexrep(v)
        n_free = n_a = n_b = n_paid = n_heavy = 0
        for t in PERMS:
            g = omega(src, t)
            gapdist[g] += 1
            if t == v:
                excluded["t == v"] += 1
                if g != 1:
                    bad.append(("t == v must have gap 1", v, t, g))
                continue
            if t == src:
                excluded["t == end(v)"] += 1
                continue
            hid = hidden(src, t, g)
            if g == 1:
                bad.append(("gap 1 with t != v", v, t))
            elif g == 2 and hid == []:
                kinds["cleanE"] += 1
                n_free += 1
                if t == tau(v):
                    c1 += 1
                else:
                    bad.append(("C1 clean E is not tau", v, t))
            elif g == 2 and hid == [v]:
                kinds["dirtyA"] += 1
                n_a += 1
                if t == sigma(v):
                    c2a += 1
                else:
                    bad.append(("C2 type A is not sigma", v, t))
                if hexrep(t) == hv:
                    c3a += 1
                else:
                    bad.append(("C3 type A leaves the hexagon", v, t))
            elif g == 2:
                bad.append(("gap 2 with an unexpected hidden set", v, t, hid))
            elif g == 3 and len(hid) == 2 and hid[0] == v and \
                    hexrep(hid[1]) == hv and hexrep(t) == hv:
                kinds["dirtyB"] += 1
                n_b += 1
                if t == sigma(sigma(v)):
                    c2b += 1
                else:
                    bad.append(("C2 type B is not sigma^2", v, t))
                c3b += 1
            elif g == 3:
                kinds["paid"] += 1
                n_paid += 1
                if hexrep(t) == hv:
                    paid_in_source_hex += 1
            elif g >= 4:
                kinds["heavy"] += 1
                n_heavy += 1
                if hexrep(t) == hv:
                    heavy_in_source_hex += 1
            else:
                unclassified.append((v, t, g, hid))
        for name, cnt, want in (("free", n_free, 1), ("dirtyA", n_a, 1),
                                ("dirtyB", n_b, 1), ("paid", n_paid, 5),
                                ("heavy", n_heavy, 710)):
            per_src[f"{name}={cnt}"] += 1
            if cnt != want:
                bad.append((f"per-source {name} count", v, cnt, want))
    # gap >= 7 is impossible because two N-windows overlap in 0..N-1 letters
    maxgap = max(gapdist)
    return dict(
        seconds=round(time.time() - t0, 1),
        ordered_pairs=len(PERMS) ** 2, exhaustive=True,
        gap_distribution={str(k): v for k, v in sorted(gapdist.items())},
        max_gap=maxgap, gap_cannot_exceed_n=maxgap <= N,
        kinds=dict(kinds), excluded_pairs=dict(excluded),
        per_source_profile=dict(per_src),
        C1_cleanE_is_tau=c1, C2_A_is_sigma=c2a, C2_B_is_sigma2=c2b,
        C3_A_same_hexagon=c3a, C3_B_same_hexagon=c3b,
        C4_paid_landing_in_source_hexagon=paid_in_source_hex,
        heavy_landing_in_source_hexagon=heavy_in_source_hex,
        unclassified=unclassified[:8], unclassified_count=len(unclassified),
        failures=[list(map(str, b)) for b in bad[:8]],
        failure_count=len(bad),
        ok=not bad and not unclassified)


# --------------------------------------------------------------- H.wlog
def wlog():
    """left S6 is transitive on the ports, and the catalogue is equivariant."""
    t0 = time.time()
    group = ["".join(p) for p in itertools.permutations(LET)]
    # transitivity: from 123456 every port is reached by exactly one element
    reach = Counter()
    for gmap in group:
        m = str.maketrans(LET, gmap)
        reach[LET.translate(m)] += 1
    transitive = set(reach) == PSET and set(reach.values()) == {1}

    def kind(v, t):
        src = sigma_inv(v)
        g = omega(src, t)
        if t == v or t == src:
            return "excluded"
        hid = hidden(src, t, g)
        if g == 2 and hid == []:
            return "cleanE"
        if g == 2:
            return "dirtyA"
        if g == 3 and len(hid) == 2 and hid[0] == v and \
                hexrep(hid[1]) == hexrep(v):
            return "dirtyB"
        if g == 3:
            return "paid"
        return f"heavy{g}"

    # equivariance on 720 group elements x 720 ports, target chosen per port
    # as the canonical representative of each kind
    probes = {}
    for v in PERMS[:1]:
        pass
    pairs, viol = 0, []
    for gmap in group:
        m = str.maketrans(LET, gmap)
        for v in PERMS:
            vv = v.translate(m)
            # one representative target of each kind out of v
            src = sigma_inv(v)
            tried = set()
            for t in (tau(v), sigma(v), sigma(sigma(v))):
                if t in tried:
                    continue
                tried.add(t)
                pairs += 1
                if kind(v, t) != kind(vv, t.translate(m)):
                    viol.append((gmap, v, t))
            if omega(src, LET) >= 3 and LET not in tried:
                pairs += 1
                if kind(v, LET) != kind(vv, LET.translate(m)):
                    viol.append((gmap, v, LET))
    # STRONGER: full (v, t) equivariance for a GENERATING SET.  Equivariance
    # is closed under composition, so generators settle all of S6 -- and each
    # generator is checked on every one of the 518,400 ordered pairs, not on
    # representatives.
    gens = []
    for i in range(N - 1):
        g = list(LET)
        g[i], g[i + 1] = g[i + 1], g[i]
        gens.append("".join(g))
    gen_pairs, gen_viol = 0, []
    for gmap in gens:
        m = str.maketrans(LET, gmap)
        for v in PERMS:
            vv = v.translate(m)
            for t in PERMS:
                gen_pairs += 1
                if kind(v, t) != kind(vv, t.translate(m)):
                    gen_viol.append((gmap, v, t))

    return dict(seconds=round(time.time() - t0, 1),
                group_elements=len(group), ports=len(PERMS),
                left_S6_transitive_on_ports=transitive,
                generators=gens,
                generator_equivariance_pairs=gen_pairs,
                generator_equivariance_exhaustive_in_v_and_t=True,
                generator_violations=len(gen_viol),
                generators_generate_S6=True,
                orbit_of_123456=len(reach),
                stabiliser_size=min(reach.values()),
                equivariance_pairs=pairs, violations=len(viol),
                examples=[list(x) for x in viol[:4]],
                ok=transitive and not viol and not gen_viol)


# ---------------------------------------------------------------- H.feas
def feas_dual(max_orbits=8, max_u=4, max_tok=5):
    """The Round-150 dual certificate, re-derived and checked exhaustively.

      claim (a)  for every T with |T| <= k:  sum_{q not in T} u_q
                     >= sum_q min(u_q, L) - k*L        for every L >= 0
      claim (b)  max over L in 0..max_u of the right side EQUALS
                     min over |T| <= k of the left side
    """
    t0 = time.time()
    checked = bad_a = 0
    mismatch = []
    for m in range(0, max_orbits + 1):
        for us in itertools.combinations_with_replacement(
                range(max_u + 1), m):
            for k in range(0, max_tok + 1):
                # exact subset optimum: drop the k largest
                srt = sorted(us, reverse=True)
                exact = sum(srt[k:])
                # dual bound
                dual = max(sum(min(u, L) for u in us) - k * L
                           for L in range(0, max_u + 1))
                checked += 1
                if dual != exact:
                    mismatch.append(dict(u=list(us), k=k, dual=dual,
                                         exact=exact))
                # claim (a) against EVERY admissible T, not just the best
                idx = range(m)
                for size in range(0, min(k, m) + 1):
                    for T in itertools.combinations(idx, size):
                        left = sum(u for i, u in enumerate(us) if i not in T)
                        for L in range(0, max_u + 1):
                            if left < sum(min(u, L) for u in us) - k * L:
                                bad_a += 1
    return dict(seconds=round(time.time() - t0, 1),
                multisets_checked=checked,
                max_noncurrent_orbits=max_orbits, max_deficit=max_u,
                max_tokens=max_tok, exhaustive=True,
                dual_equals_subset_optimum=not mismatch,
                mismatches=mismatch[:4], claim_a_violations=bad_a,
                ok=not mismatch and bad_a == 0)


def feas_operational(max_orbits=27, max_tok=6):
    """The SAME lemma, exhaustive over the whole operational domain.

    Everything the prune computes depends only on the multiset of unused-phase
    counts u_q in 0..4 over the already-opened NON-CURRENT orbits, plus the
    remaining token budget.  A u_q of 0 contributes nothing, so the state is
    the histogram (n1, n2, n3, n4).  For t <= 4 the chain opens O = 24 + k <= 28
    tau-orbits, so at most 27 of them are non-current: n1+n2+n3+n4 <= 27 covers
    every state the production search can ever be in.

    Three quantities are compared on every one of those states:
      exact   drop the k largest deficits            (the subset optimum L)
      dual    max over lambda of sum min(u,lambda) - k*lambda
      greedy  the production histogram loop: for d = 4..1, erase
              min(hist[d], left) orbits, add (hist[d]-take)*d
    """
    t0 = time.time()
    checked = 0
    bad_dual, bad_greedy = [], []
    for n1 in range(max_orbits + 1):
        for n2 in range(max_orbits - n1 + 1):
            for n3 in range(max_orbits - n1 - n2 + 1):
                for n4 in range(max_orbits - n1 - n2 - n3 + 1):
                    hist = {1: n1, 2: n2, 3: n3, 4: n4}
                    desc = [4] * n4 + [3] * n3 + [2] * n2 + [1] * n1
                    tot_all = sum(desc)
                    for k in range(max_tok + 1):
                        checked += 1
                        exact = sum(desc[k:])
                        dual = max(sum(min(u, L) for u in desc) - k * L
                                   for L in range(0, 5))
                        left, greedy = k, 0
                        for dd in (4, 3, 2, 1):
                            take = min(hist[dd], left)
                            left -= take
                            greedy += (hist[dd] - take) * dd
                        if dual != exact:
                            bad_dual.append(dict(hist=[n1, n2, n3, n4], k=k,
                                                 dual=dual, exact=exact))
                        if greedy != exact:
                            bad_greedy.append(dict(hist=[n1, n2, n3, n4], k=k,
                                                   greedy=greedy, exact=exact))
    return dict(seconds=round(time.time() - t0, 1),
                states_checked=checked,
                max_noncurrent_orbits=max_orbits, max_tokens=max_tok,
                exhaustive_over_the_operational_domain=True,
                why_27="for t <= 4 the chain opens O = 24 + k <= 28 orbits",
                dual_mismatches=bad_dual[:4],
                greedy_mismatches=bad_greedy[:4],
                dual_equals_subset_optimum=not bad_dual,
                production_greedy_equals_subset_optimum=not bad_greedy,
                ok=not bad_dual and not bad_greedy)


def main():
    cat = catalogue()
    wl = wlog()
    fe = feas_dual()
    fo = feas_operational()
    out = dict(catalogue=cat, wlog=wl, feas_dual=fe, feas_operational=fo,
               ok=cat["ok"] and wl["ok"] and fe["ok"] and fo["ok"])
    (ROOT / "r163" / "certs" / "recheck_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:2600])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
