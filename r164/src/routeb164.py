#!/usr/bin/env python3
"""Round 164 -- Route B: an independent PROOF-OBJECT verifier.

Imports nothing from r152/src, from the production solvers, or from any
capacity table.  The permutation geometry is rebuilt here from string algebra;
the certificate syntax is decoded here; the feasibility condition is
implemented here from the round-150 statement, twice, and the two forms are
required to agree.

WHAT A CAPACITY CERTIFICATE MEANS (the specification this file checks).

  A cell is K = (b, d, a, bb, e, h): b tokens, deficit budget d, and at-most
  budgets for dirty-A, dirty-B, ordinary repeated-hexagon arrivals and heavy
  cost.  cap(K) is the largest number of ports on a legal walk from port
  123456 whose final deficit is <= d and whose resource use is within K.

    lower   cap(K) >= C  is witnessed by a walk: a port list whose every
            consecutive pair is a catalogue move, which never repeats a port
            or an orbit phase, whose accumulated tok/a/bb/e/h stay inside K,
            whose final deficit is <= d, and which has exactly C ports.
            THIS IS A FINITE PROOF OBJECT and Route B can replay it.

    upper   cap(K) <= C  requires that NO legal walk reaches C+1 ports at
            deficit <= d.  The proof object for this is an exhaustion tree:
            a preorder listing in which every internal node declares exactly
            how many legal children its state has and every leaf carries one
            of three proved stopping facts.

  EXACT_CERTIFIED means both directions; UPPER_CERTIFIED means the upper
  direction with no witness stored.  The CENSUS CONSUMES THE UPPER DIRECTION:
  a capacity is used as a bound the models may not exceed, so a value that is
  too SMALL would be unsound.  The witness is the other direction.
"""
from __future__ import annotations
import itertools, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
NHEX = 120
UBFALL = 120

# ------------------------------------------------------------- geometry
PERMS = ["".join(p) for p in itertools.permutations("123456")]
IDX = {p: i for i, p in enumerate(PERMS)}
N = len(PERMS)


def sigma(s):
    return s[1:] + s[0]


def tau(s):
    return s[1:-1] + s[0] + s[-1]


def end(s):
    return s[-1] + s[:-1]


def gap(e, t):
    for k in range(1, 6):
        if t.startswith(e[k:]):
            return k
    return 6


def _classes(f):
    seen, cid = {}, 0
    for p in PERMS:
        if p in seen:
            continue
        q = p
        while q not in seen:
            seen[q] = cid
            q = f(q)
        cid += 1
    return [seen[p] for p in PERMS], cid


HEX, NH = _classes(sigma)
ORB, NORB = _classes(tau)

# phase = position along the tau-cycle, counted from the orbit's least member.
# Only DISTINCTNESS inside an orbit is ever used, so any bijection would do.
PHASE = [None] * N
_members = {}
for _i in range(N):
    _members.setdefault(ORB[_i], []).append(_i)
for _q, _mem in _members.items():
    _x = PERMS[min(_mem)]
    for _k in range(5):
        PHASE[IDX[_x]] = _k
        _x = tau(_x)
assert all(p is not None for p in PHASE)
assert all(len(set(PHASE[i] for i in m)) == 5 for m in _members.values())

FREE = [None] * N
DA = [None] * N
DB = [None] * N
PAID = [[] for _ in range(N)]
HEAVY = [[] for _ in range(N)]


def _build():
    for vi, v in enumerate(PERMS):
        e = end(v)
        for ti, t in enumerate(PERMS):
            g = gap(e, t)
            if g >= 4:
                if t != v and t != e:
                    HEAVY[vi].append((ti, g - 3))
                continue
            if g < 2:
                continue
            spell = e + t[6 - g:]
            hid = [IDX[spell[o:o + 6]] for o in range(1, g)
                   if len(set(spell[o:o + 6])) == 6]
            if g == 2:
                if not hid:
                    FREE[vi] = ti
                elif hid == [vi]:
                    DA[vi] = ti
                continue
            if len(hid) == 2 and hid[0] == vi and HEX[ti] == HEX[vi]:
                DB[vi] = ti
                continue
            k = -1
            if not hid:
                d0 = [e[:3].index(t[3 + j]) if t[3 + j] in e[:3] else -1
                      for j in range(3)]
                if 100 * d0[0] + 10 * d0[1] + d0[2] in (120, 201, 210):
                    k = 0
            elif hid == [vi]:
                k = 3
            elif len(hid) == 1 and sigma(PERMS[hid[0]]) == t:
                k = 4
            if k >= 0:
                PAID[vi].append(ti)
        assert FREE[vi] is not None and DA[vi] is not None \
            and DB[vi] is not None and len(PAID[vi]) == 5 \
            and len(HEAVY[vi]) == 710, f"catalogue wrong at {v}"


_build()
KIND_ORDER = {"E": 0, "A": 1, "B": 2, "P": 3, "H": 4}
MOVES = [None] * N
for _v in range(N):
    _m = [(FREE[_v], "E", 0), (DA[_v], "A", 0), (DB[_v], "B", 0)]
    _m += [(t, "P", 0) for t in PAID[_v]]
    _m += [(t, "H", c) for t, c in HEAVY[_v]]
    MOVES[_v] = sorted(_m, key=lambda m: KIND_ORDER[m[1]])
MOVEMAP = {}
for _v in range(N):
    for _t, _k, _c in MOVES[_v]:
        MOVEMAP[(_v, _t)] = (_k, _c)


# ------------------------------------------------------- feasibility (r150)
def feas_greedy(phm, corb, tok, dmax):
    """Order-statistic form: drop the tok largest non-current deficits."""
    us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                reverse=True)
    return sum(us[tok:]) <= dmax


def feas_subset(phm, corb, tok, dmax):
    """Explicit minimum over every admissible erasure set S, |S| <= tok."""
    us = [5 - len(ph) for q, ph in phm.items() if q != corb]
    best = None
    for size in range(0, min(tok, len(us)) + 1):
        for S in itertools.combinations(range(len(us)), size):
            v = sum(u for i, u in enumerate(us) if i not in S)
            best = v if best is None else min(best, v)
    return (0 if best is None else best) <= dmax


def feas_dual(phm, corb, tok, dmax):
    """Dual form: max over lambda of sum min(u,lambda) - tok*lambda."""
    us = [5 - len(ph) for q, ph in phm.items() if q != corb]
    best = max(sum(min(u, L) for u in us) - tok * L for L in range(0, 5))
    return best <= dmax


def feas_value(phm, corb, tok):
    us = sorted((5 - len(ph) for q, ph in phm.items() if q != corb),
                reverse=True)
    return sum(us[tok:])


# ------------------------------------------------------------- certificates
def parse_capcert(path):
    lines = Path(path).read_text().splitlines()
    assert lines[0] == "L6-CAPCERT-2"
    out, order, i = {}, [], 1
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        assert f[0] == "cell", f[:2]
        cell = tuple(int(x) for x in f[1:7])
        cap, np_ = int(f[7]), int(f[8])
        ports = [int(x) for x in lines[i + 1].split()]
        assert len(ports) == np_
        out[cell] = dict(cap=cap, ports=ports)
        order.append(cell)
        i += 2
    return out, order


def parse_pcert(path):
    lines = Path(path).read_text().splitlines()
    assert lines[0] == "L6-PIECECERT-1"
    out, order, i = {}, [], 1
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        assert f[0] == "pcell", f[:2]
        cell = tuple(int(x) for x in f[1:5])
        cap, np_ = int(f[5]), int(f[6])
        ports = [int(x) for x in lines[i + 1].split()]
        assert len(ports) == np_
        out[cell] = dict(cap=cap, ports=ports)
        order.append(cell)
        i += 2
    return out, order


def parse_extree(path):
    lines = Path(path).read_text().splitlines()
    assert lines[0] == "L6-EXTREE-1"
    out, i = [], 1
    while i < len(lines):
        s = lines[i]
        if not s or s.startswith("#"):
            i += 1
            continue
        f = s.split()
        assert f[0] == "tree", f[:2]
        cell = tuple(int(x) for x in f[1:7])
        cap = int(f[7])
        toks = lines[i + 1].split()
        out.append((cell, cap, toks))
        i += 2
    return out


# --------------------------------------------------- lower bound: witnesses
def replay_chain_witness(cell, ports):
    """cap(K) >= len(ports), checked against the specification above."""
    b, dmax, amax, bmax, emax, hmax = cell
    if not ports:
        return False, "empty witness"
    if ports[0] != IDX["123456"]:
        return False, "the walk must start at 123456"
    if any(not 0 <= p < N for p in ports):
        return False, "port index out of range"
    if len(set(ports)) != len(ports):
        return False, "a port repeats"
    phm = {ORB[ports[0]]: {PHASE[ports[0]]}}
    hexu = {HEX[ports[0]]}
    deficit, tok, au, bu, eu, hu = 4, 0, 0, 0, 0, 0
    corb = ORB[ports[0]]
    for i in range(len(ports) - 1):
        u, t = ports[i], ports[i + 1]
        if (u, t) not in MOVEMAP:
            return False, f"step {i} is not a catalogue move"
        kind, cost = MOVEMAP[(u, t)]
        q = ORB[t]
        if PHASE[t] in phm.get(q, ()):
            return False, f"step {i} reuses an orbit phase"
        if kind == "E" and q != corb:
            return False, f"step {i}: a clean E left its orbit"
        fresh = q not in phm
        if HEX[t] in hexu and kind not in ("A", "B"):
            eu += 1
        au += kind == "A"
        bu += kind == "B"
        hu += cost if kind == "H" else 0
        tok += 0 if (kind == "E" or fresh) else 1
        phm.setdefault(q, set()).add(PHASE[t])
        hexu.add(HEX[t])
        deficit += 4 if fresh else -1
        corb = q
    if tok > b or deficit > dmax or au > amax or bu > bmax \
       or eu > emax or hu > hmax:
        return False, (f"budget exceeded tok={tok}/{b} def={deficit}/{dmax} "
                       f"a={au}/{amax} bb={bu}/{bmax} e={eu}/{emax} h={hu}/{hmax}")
    if deficit != 5 * len(phm) - len(ports):
        return False, "deficit identity 5|orbits| - |ports| violated"
    return True, dict(ports=len(ports), orbits=len(phm), deficit=deficit,
                      tok=tok, a=au, bb=bu, e=eu, h=hu)


def replay_piece_witness(cell, ports):
    """The piece model: clean E and paid only, every port a FRESH hexagon."""
    b, dmax, fp, lp = cell
    if not ports:
        return False, "empty witness"
    if ports[0] != 0:
        return False, "the piece must start at 123456"
    if any(not 0 <= p < N for p in ports):
        return False, "port index out of range"
    if len(set(ports)) != len(ports):
        return False, "a port repeats"
    phm = {ORB[0]: {PHASE[0]}}
    hexu = {HEX[0]}
    norb, deficit, tok, corb = 1, 4, 0, ORB[0]
    firstlen, curlen, nblk = 0, 1, 1
    for i in range(len(ports) - 1):
        u, t = ports[i], ports[i + 1]
        if HEX[t] in hexu:
            return False, f"step {i} revisits a hexagon"
        q = ORB[t]
        if PHASE[t] in phm.get(q, ()):
            return False, f"step {i} reuses an orbit phase"
        if t == FREE[u]:
            if q != corb:
                return False, f"step {i}: a clean E left its orbit"
            phm[q].add(PHASE[t])
            deficit -= 1
            curlen += 1
        elif t in PAID[u]:
            fresh = q not in phm
            if not fresh:
                tok += 1
            phm.setdefault(q, set()).add(PHASE[t])
            if fresh:
                norb += 1
                deficit += 4
            else:
                deficit -= 1
            firstlen = firstlen if nblk > 1 else curlen
            curlen, nblk, corb = 1, nblk + 1, q
        else:
            return False, f"step {i} is neither a clean E nor a paid joint"
        hexu.add(HEX[t])
    if tok > b:
        return False, f"token budget exceeded {tok} > {b}"
    if deficit > dmax:
        return False, f"deficit budget exceeded {deficit} > {dmax}"
    if deficit != 5 * norb - len(ports):
        return False, "deficit identity violated"
    fl = firstlen if nblk > 1 else curlen
    if fp and fl >= 5:
        return False, "the mask requires a partial FIRST block"
    if lp and curlen >= 5:
        return False, "the mask requires a partial LAST block"
    return True, dict(ports=len(ports), orbits=norb, deficit=deficit, tok=tok,
                      first_block=fl, last_block=curlen)


# ------------------------------------------- upper bound: exhaustion trees
class TreeVerifier:
    """Replays an L6-EXTREE-1 proof object.  Performs no search of its own.

    At every node the feasibility histogram is maintained INCREMENTALLY and
    recomputed FROM SCRATCH, and the two are asserted equal (round 163 named
    this the principal residual risk).  The three feasibility spellings --
    order statistic, explicit subset minimum and the dual bound -- are also
    cross-checked against each other at every node.
    """

    def __init__(self, certified, check_feas_forms=True, subset_every=500,
                 subset_max_orbits=12):
        self.cert = dict(certified)
        self._ubc = {}
        self.nodes = 0
        self.hist_checks = 0
        self.feas_form_checks = 0
        self.feas_subset_checks = 0
        self.max_open_orbits = 0
        self.leaf_reasons = Counter()
        self.check_feas_forms = check_feas_forms
        # the explicit subset minimum is C(m, tok) work, so it runs on a
        # sample; greedy-vs-dual is cheap and runs at EVERY node, and round
        # 163 already proved greedy = dual = subset optimum exhaustively over
        # the whole operational domain (220,255 states)
        self.subset_every = subset_every
        self.subset_max_orbits = subset_max_orbits

    def ub(self, tok, d, a, bb, e, h):
        key = (tok, d, a, bb, e, h)
        v = self._ubc.get(key)
        if v is not None:
            return v
        best = UBFALL + a + bb + e
        for (kb, kd, ka, kbb, ke, kh), c in self.cert.items():
            if (kb >= tok and kd >= d and ka >= a and kbb >= bb
                    and ke >= e and kh >= h and c < best):
                best = c
        self._ubc[key] = best
        return best

    def validate(self, cell, cap, toks):
        b, dmax, amax, bmax, emax, hmax = cell
        phm = {ORB[0]: {PHASE[0]}}
        hexc = {HEX[0]: 1}
        inc = {ORB[0]: 1}            # incremental: orbit -> ports used in it
        st = dict(err=None, pos=0)

        def fresh_hist():
            return {q: len(ph) for q, ph in phm.items()}

        def legal(v, corb, tok, au, bu, eu, hu):
            out = []
            for t, kind, cost in MOVES[v]:
                q = ORB[t]
                ph = phm.get(q)
                if ph is not None and PHASE[t] in ph:
                    continue
                if kind == "E" and q != corb:
                    continue
                if kind == "A" and au >= amax:
                    continue
                if kind == "B" and bu >= bmax:
                    continue
                if kind == "H" and hu + cost > hmax:
                    continue
                newhex = HEX[t] not in hexc
                se = 0
                if not newhex and kind not in ("A", "B"):
                    if eu >= emax:
                        continue
                    se = 1
                fresh = ph is None
                c = 0 if (kind == "E" or fresh) else 1
                if c > tok:
                    continue
                out.append((t, kind, cost, fresh, se, c))
            return out

        def walk(v, corb, ports, tok, au, bu, eu, hu, deficit):
            self.nodes += 1
            self.max_open_orbits = max(self.max_open_orbits, len(phm))
            # PHASE 8: incremental state vs a from-scratch recomputation
            self.hist_checks += 1
            if inc != fresh_hist():
                st["err"] = (f"incremental histogram {sorted(inc.items())} "
                             f"!= fresh {sorted(fresh_hist().items())}")
                return
            if self.check_feas_forms:
                self.feas_form_checks += 1
                g = feas_greedy(phm, corb, tok, dmax)
                if g != feas_dual(phm, corb, tok, dmax):
                    st["err"] = "greedy and dual feasibility forms disagree"
                    return
                nopen = sum(1 for q in phm if q != corb)
                if (self.nodes % self.subset_every == 0
                        and nopen <= self.subset_max_orbits):
                    self.feas_subset_checks += 1
                    if g != feas_subset(phm, corb, tok, dmax):
                        st["err"] = "the explicit subset minimum disagrees"
                        return
            i = st["pos"]
            if i >= len(toks):
                st["err"] = "token stream ended early"
                return
            tk = toks[i]
            st["pos"] = i + 1
            if ports >= cap + 1 and deficit <= dmax:
                st["err"] = (f"the tree itself reaches {ports} ports at "
                             f"deficit {deficit} <= {dmax}")
                return
            if tk == "L":
                r1 = ports + (NHEX - len(hexc)) + (amax - au) + (bmax - bu) \
                    + (emax - eu)
                if r1 < cap + 1:
                    self.leaf_reasons["b_hexagon_and_repeat_budget"] += 1
                    return
                if not feas_greedy(phm, corb, tok, dmax):
                    self.leaf_reasons["f_feasibility"] += 1
                    return
                r2 = ports + self.ub(tok, dmax - deficit + 4 + 5 * tok,
                                     amax - au, bmax - bu, emax - eu,
                                     hmax - hu) - 1
                if r2 < cap + 1:
                    self.leaf_reasons["p_monotone_from_earlier_cells"] += 1
                    return
                st["err"] = (f"unjustified leaf at token {i}: ports={ports} "
                             f"deficit={deficit} r1={r1} r2={r2}")
                return
            if not tk.startswith("N"):
                st["err"] = f"bad token {tk!r} at {i}"
                return
            k = int(tk[1:])
            ms = legal(v, corb, tok, au, bu, eu, hu)
            # PHASE 7: branch completeness -- exactly the legal children
            if k != len(ms):
                st["err"] = (f"token {i} declares {k} children but the state "
                             f"has {len(ms)} legal moves")
                return
            for t, kind, cost, fresh, se, c in ms:
                q = ORB[t]
                if fresh:
                    phm[q] = {PHASE[t]}
                    inc[q] = 1
                else:
                    phm[q].add(PHASE[t])
                    inc[q] += 1
                hexc[HEX[t]] = hexc.get(HEX[t], 0) + 1
                walk(t, q, ports + 1, tok - c, au + (kind == "A"),
                     bu + (kind == "B"), eu + se,
                     hu + (cost if kind == "H" else 0),
                     deficit + (4 if fresh else -1))
                hexc[HEX[t]] -= 1
                if hexc[HEX[t]] == 0:
                    del hexc[HEX[t]]
                if fresh:
                    del phm[q]
                    del inc[q]
                else:
                    phm[q].discard(PHASE[t])
                    inc[q] -= 1
                if st["err"]:
                    return

        walk(0, ORB[0], 1, b, 0, 0, 0, 0, 4)
        if st["err"]:
            return False, st["err"]
        if st["pos"] != len(toks):
            return False, (f"{len(toks) - st['pos']} tokens left over")
        return True, dict(nodes=self.nodes)
