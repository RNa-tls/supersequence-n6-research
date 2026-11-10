#!/usr/bin/env python3
"""Round S -- the Monge reduction of a route of the 6A+24phi family to a bracket tree (Theorem S1), as an algorithm.

A route is a Hamiltonian path of the 5040 runs of a version vector; its length is 35288 + sum of the link weights, so
G = sum w - 10874.  The NATURAL links are the links k -> k+1 of the 30 version cycles.  A CUT is a natural link the
route does not use (the run after it starts a piece), a JUNCTION is a link of the route that is not natural.

Cover.  Vertices = cuts u (entry run u, exit run pred(u)).  The piece that ends at pred(u) is followed by the piece
that starts at tau(u): the cover arcs u -> tau(u) form one path and some cycles.

Monge step (cut deletion).  For a cut u with in-junction a -> u and out-junction b -> y (b = pred(u)), replacing the two
junctions by a -> y and the natural link b -> u changes the total weight by
        w(a, y) + c(u) - w(a, u) - w(b, y)  <=  0      whenever  c(u) <= min(w(a, u), w(b, y))
(Monge four-point inequality of string overlaps; rR/lean/Monge.lean, rR/csrc/monge_nat.c).  c(u) is 2 or 3, and the only
links of weight 2 are the natural w2 links and the WRAPS C_6 -> C_0 of the full chains.  Hence a cut can always be deleted
unless it is a chain start (c = 3) next to a wrap arc of the cover.

Reduction.  Take a spanning tree of the bipartite incidence graph (cover components x trails, one edge per cut), keep the
tree cuts (K), delete the others (D).  The kept structure is a bracket tree (every trail has one MAIN, every cycle has one
ANCHOR and at least one main) and is realized by an explicit word (function realize).  The deletions are made in a SAFE
order: a deletion is safe when the new junction has weight >= 3, i.e. its two cover neighbours (l, r) are not a TIGHT
pair: a wrap pair (T(N_0), T(C_0)) (N_0 the chain start after the full chain C; weight 2) or a singleton pair l = succ(r)
(the piece between the two cuts is the single run r; weight 1).  When no safe deletion exists the remaining deletable
cuts form LADDERS (two trails alternating, between two kept cuts); a ladder is deleted in one step and its exact weight
change is checked directly (it is <= 0: Lemma S1.4, rR/csrc/ladders.c).

This module implements the reduction for routes WITHOUT wraps, checks every step (side condition, weight change <= 0),
rebuilds the reduced route, and checks that it is a Hamiltonian path whose weight equals the original weight plus the
sum of the step changes.

usage: monge_reduce.py RUNS.bin WORD.txt FAMILY.json [OUT_WORD.txt]      (reduce one word)
       monge_reduce.py RUNS.bin --random N SEED [--moves M]               (N random wrap-free routes, self-check)
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import runs_io, chains

n = 8

class Family:
    def __init__(self, runs_path, cache=None):
        self.runs, self.tv, self.tofs, self.mlen = runs_io.load(runs_path)
        self.N = len(self.runs)
        if cache and os.path.exists(cache): self.W = np.load(cache)
        else:
            self.W = runs_io.weight_matrix(self.runs)
            if cache: np.save(cache, self.W)
        ci = chains.chain_info(self.W, self.tofs, self.mlen)
        self.cid, self.pos, self.clen, self.full, self.cut = ci["cid"], ci["pos"], ci["clen"], ci["full"], ci["cut"]
        self.chains = ci["chains"]
        self.T = np.array([x[0] for x in self.tv]); self.V = np.array([x[1] for x in self.tv])
        self.pred = np.zeros(self.N, np.int64); self.succ = np.zeros(self.N, np.int64)
        for t in range(30):
            for v in range(2):
                o0 = self.tofs[t] + v * self.mlen[t]; m = self.mlen[t]
                for k in range(m): self.pred[o0 + k] = o0 + (k - 1) % m; self.succ[o0 + k] = o0 + (k + 1) % m
        self.index = {}
        for o, r in enumerate(self.runs): self.index.setdefault(r, []).append(o)
    def w(self, a, b): return int(self.W[a, b])
    def base(self, t, v): return self.tofs[t] + v * self.mlen[t]
    def wrap_pair(self, p, q):
        """(p, q) is a wrap pair: p = cut after the full chain that starts at q (same trail version)."""
        if self.T[p] != self.T[q] or self.V[p] != self.V[q]: return False
        if self.pos[q] != 0 or not self.full[q]: return False
        last = self.chains[self.cid[q]]["runs"][-1]
        return int(self.succ[last]) == p
    def tight_pair(self, p, q):
        """the junction pred(p) -> q would have weight < 3: singleton pair (p = succ(q), weight 1) or wrap pair (weight 2)."""
        return int(self.pred[p]) == q or self.wrap_pair(p, q)
    def weight(self, route): return int(self.W[np.array(route[:-1]), np.array(route[1:])].sum())

def word_route(F, path, fam_json):
    """run indices (global, version chosen per trail by majority) of the word's route."""
    t = "".join(ch for ch in open(path).read() if not ch.isspace()); al = sorted(set(t)); w = [al.index(c) for c in t]
    seen = set(); perms = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); perms.append(p)
    st = perms[0::n]
    assert len(st) == 5040, len(st)
    votes = {}
    for r in st:
        for o in F.index.get(tuple(r), []): votes[(int(F.T[o]), int(F.V[o]))] = votes.get((int(F.T[o]), int(F.V[o])), 0) + 1
    usev = {t: max((0, 1), key=lambda v: votes.get((t, v), 0)) for t in range(30)}
    route = []
    for r in st:
        c = [o for o in F.index.get(tuple(r), []) if F.V[o] == usev[int(F.T[o])]]
        assert len(c) == 1, ("run not in the chosen version", r)
        route.append(c[0])
    return route

def build_word(F, route):
    w = list(F.runs[route[0]])
    for k, r in enumerate(route):
        if k > 0: kk = F.w(route[k - 1], r); w += list(F.runs[r][8 - kk:])
        w += list(F.runs[r][:7])
    return w

class Cover:
    """cuts and cover arcs of a route."""
    def __init__(self, F, route):
        self.F = F; self.route = list(route); N = len(route)
        assert sorted(route) == sorted(set(route)) and len(route) == 5040
        vers = {}
        for o in route:
            t = int(F.T[o]); v = int(F.V[o]); assert vers.setdefault(t, v) == v, "mixed versions"
        self.vers = vers
        nxt = {route[i]: route[i + 1] for i in range(N - 1)}
        self.nxt = nxt
        # cuts: runs u whose natural in-link pred(u) -> u is not used
        used_in = {b: a for a, b in nxt.items()}          # run -> its predecessor in the route
        self.cuts = [u for u in route if used_in.get(u) != int(F.pred[u])]
        cutset = set(self.cuts)
        # pieces and cover arcs:  exit cut of a piece = succ(last run);  tau(exit cut) = entry cut of the next piece
        self.tau = {}; self.first_cut = route[0]; self.last_cut = int(F.succ[route[-1]])
        self.junction = {}                                 # cover arc (u -> v) -> (exit run, entry run)
        for a, b in nxt.items():
            if int(F.succ[a]) != b:
                u = int(F.succ[a]); assert u in cutset and b in cutset
                self.tau[u] = b; self.junction[u] = (a, b)
        assert self.last_cut in cutset and self.last_cut not in self.tau
        self.P = len(self.cuts)
    def components(self):
        """list of components; component 0 is the path (ordered list of cuts), the others are cycles."""
        comp = {}; comps = []
        u = self.first_cut; path = []
        while True:
            path.append(u); comp[u] = 0
            if u not in self.tau: break
            u = self.tau[u]
        assert path[-1] == self.last_cut
        comps.append(path)
        for u in self.cuts:
            if u in comp: continue
            cyc = []; x = u
            while x not in comp:
                comp[x] = len(comps); cyc.append(x); x = self.tau[x]
            assert x == u
            comps.append(cyc)
        return comps, comp
    def has_wrap(self):
        F = self.F
        return [(a, b) for (a, b) in self.junction.values() if F.w(a, b) == 2]

class ReductionError(Exception): pass

def choose_tree(F, C, comps, comp, rng=None, choose="random", prefer=(), avoid=()):
    """kept cuts of a spanning tree of the incidence graph (components x trails, one edge per cut); leaf cycles (only
    the anchor kept) are pruned.  Greedy (Kruskal) with the cuts in the order: `prefer`, ordinary, `avoid` -- so the tree
    uses as few `avoid` cuts as possible (a spanning tree without them is found whenever one exists)."""
    ncomp = len(comps); T = F.T
    cuts = list(C.cuts)
    if rng and choose == "random": rng.shuffle(cuts)
    cuts.sort(key=lambda u: 0 if u in prefer else (2 if u in avoid else 1))
    parent = list(range(ncomp + 30))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    keep = set()
    for u in cuts:
        a = find(comp[u]); b = find(ncomp + int(T[u]))
        if a != b: parent[a] = b; keep.add(u)
    if len(keep) != ncomp + 30 - 1: raise ReductionError("incidence graph not connected")
    kept_in = {i: [u for u in comps[i] if u in keep] for i in range(ncomp)}
    for i in range(1, ncomp):
        if len(kept_in[i]) == 1: keep.discard(kept_in[i][0]); kept_in[i] = []
    return keep, kept_in

def tau_of_keep(comps, keep):
    tauK = {}
    for i, cs in enumerate(comps):
        ks = [u for u in cs if u in keep]
        for j, u in enumerate(ks):
            if i == 0: tauK[u] = ks[j + 1] if j + 1 < len(ks) else None
            else: tauK[u] = ks[(j + 1) % len(ks)]
    return tauK

def direct_tree(F, route, rng=None, prefer=(), avoid=()):
    """bracket tree of a random spanning tree, realized directly (no deletion order): (new_route, weight change)."""
    C = Cover(F, route); comps, comp = C.components()
    keep, kept_in = choose_tree(F, C, comps, comp, rng, prefer=prefer, avoid=avoid)
    new_route = realize(F, keep, tau_of_keep(comps, keep), comps[0], C.vers)
    if sorted(new_route) != sorted(route): raise ReductionError("direct tree: not a permutation of the runs")
    return new_route, F.weight(new_route) - F.weight(route)

def wrap_blocks(F, C, comps, comp):
    """maximal chains of consecutive wrap arcs of the cover.  A block with k wraps has the cuts
    T(N_0), T(C^k_0), ..., T(C^1_0) (consecutive full chains C^1..C^k, N_0 the chain start after C^k).
    Returns dicts: cuts, k, comp, closed (the block is a whole cover cycle: k wraps + the skip arc),
    s = weight of the in-junction (None at the path start), r = weight of the out-junction (None at the path end)."""
    pred = F.pred
    def aw(u): return F.w(int(pred[u]), C.tau[u]) if u in C.tau else None
    wrap_from = {u for u in C.tau if aw(u) == 2}
    inv = {v: u for u, v in C.tau.items()}
    blocks = []; seen = set()
    for u in wrap_from:
        if u in seen: continue
        a = u
        while a in inv and inv[a] in wrap_from and inv[a] != u: a = inv[a]
        cuts = [a]; x = a
        while x in wrap_from and C.tau[x] != a: x = C.tau[x]; cuts.append(x)
        if x in wrap_from and C.tau[x] == a: closed_all_wraps = True
        else: closed_all_wraps = False
        for y in cuts: seen.add(y)
        k = len(cuts) - 1 if not closed_all_wraps else len(cuts)
        first, last = cuts[0], cuts[-1]
        closed = (not closed_all_wraps) and C.tau.get(last) == first
        s = None if first not in inv else F.w(int(pred[inv[first]]), first)
        r = aw(last)
        blocks.append(dict(cuts=cuts, k=k, comp=comp[first], closed=closed, all_wraps_cycle=closed_all_wraps, s=s, r=r,
                           left=inv.get(first), right=C.tau.get(last)))
    return blocks

def classify(F, route):
    """wrap structure of a route: 'wrap-free', 'closed' (every wrap block is a skip cycle), or 'open'."""
    C = Cover(F, route); comps, comp = C.components(); bl = wrap_blocks(F, C, comps, comp)
    if not bl: return "wrap-free", bl
    if all(b["closed"] for b in bl): return "closed", bl
    return "open", bl

def reduce_to_bracket_tree(F, route, rng=None, verbose=False, choose="random", prefer=()):
    """Monge reduction to a bracket tree.  Works for wrap-free routes (Theorem S1) and for routes whose wrap blocks are
    skip cycles (Theorem S2); open wrap blocks are bypassed when both neighbour junctions have weight >= 3 + k and the
    block is not needed by the tree (Theorem S3), otherwise ReductionError.  Returns (new_route, info)."""
    C = Cover(F, route)
    comps, comp = C.components()
    ncomp = len(comps); T = F.T
    blocks = wrap_blocks(F, C, comps, comp)
    block_cuts = set(u for b in blocks for u in b["cuts"])
    keep, kept_in = choose_tree(F, C, comps, comp, rng, choose=choose, prefer=prefer, avoid=block_cuts)
    D = set(C.cuts) - keep
    # linked lists
    L = {}; R = {}
    for i, cs in enumerate(comps):
        m = len(cs)
        for j, u in enumerate(cs):
            if i == 0: L[u] = cs[j - 1] if j > 0 else None; R[u] = cs[j + 1] if j + 1 < m else None
            else: L[u] = cs[(j - 1) % m]; R[u] = cs[(j + 1) % m]
    pred = F.pred; cut = F.cut
    delta = 0; steps = 0; ladders = []; tight = 0; alive = set(C.cuts)
    def arc_w(p, q): return F.w(int(pred[p]), q)            # junction weight of the cover arc p -> q
    # phase 0: components without kept cuts are deleted as a whole (exact weight change; 0 for a skip cycle)
    whole = []
    for i in range(1, ncomp):
        if kept_in[i]: continue
        cs = comps[i]; m = len(cs)
        d = sum(int(cut[u]) for u in cs) - sum(arc_w(cs[j], cs[(j + 1) % m]) for j in range(m))
        if d > 0: raise ReductionError("deleting a whole cover cycle of %d cuts increases the weight by %d" % (m, d))
        delta += d; steps += m; whole.append((m, d))
        for u in cs: alive.discard(u)
    # phase 1: open wrap blocks in components with kept cuts
    bypassed = []
    for b in blocks:
        if b["cuts"][0] not in alive: continue
        if any(u in keep for u in b["cuts"]): raise ReductionError("open wrap block needed by the tree (gap cut): k=%d s=%s r=%s" % (b["k"], b["s"], b["r"]))
        if b["all_wraps_cycle"]: raise ReductionError("cycle of wraps only inside a kept component")
        cs = b["cuts"]; k = b["k"]; l = L[cs[0]]; r = R[cs[-1]]
        inside = sum(arc_w(cs[j], cs[j + 1]) for j in range(len(cs) - 1))
        if l is None and r is None: raise ReductionError("path would become empty")
        if l == cs[-1]: raise ReductionError("closed block inside a kept component")
        if l is None: d = 3 * (k + 1) - inside - arc_w(cs[-1], r)
        elif r is None: d = 3 * (k + 1) - inside - arc_w(l, cs[0])
        else:
            if F.tight_pair(l, r) or l == r: raise ReductionError("bypassing a wrap block would create a tight arc")
            d = arc_w(l, r) + 3 * (k + 1) - inside - arc_w(l, cs[0]) - arc_w(cs[-1], r)
        if d > 0: raise ReductionError("wrap block with a light neighbour: k=%d s=%s r=%s, bypass costs %d" % (k, b["s"], b["r"], d))
        delta += d; steps += len(cs); bypassed.append((k, b["s"], b["r"], d))
        for u in cs: alive.discard(u)
        if l is not None: R[l] = r
        if r is not None: L[r] = l
    def is_safe(v):
        l, r = L[v], R[v]
        if l is None or r is None: return True
        if l == v: return True                               # 1-cycle (self loop): trivial cut
        if l == r: return True                               # 2-cycle
        return not F.tight_pair(l, r)
    def eliminate(v):
        nonlocal delta, steps, tight
        l, r = L[v], R[v]; c = int(cut[v]); d = None
        if l == v:                                           # self loop: the link is natural again, nothing changes
            d = 0
        elif l is None and r is None: raise ReductionError("path would become empty")
        elif l is None:                                      # first cut of the path: junction pred(v) -> r disappears
            wout = arc_w(v, r)
            if wout < c: raise ReductionError("side condition fails at path start")
            d = c - wout
        elif r is None:
            win = arc_w(l, v)
            if win < c: raise ReductionError("side condition fails at path end")
            d = c - win
        else:
            win = arc_w(l, v); wout = arc_w(v, r)
            if c > min(win, wout): raise ReductionError("Monge side condition fails: c=%d win=%d wout=%d" % (c, win, wout))
            if l == r:                                       # 2-cycle {l, v}: the new arc l -> l is the natural link of l
                d = int(cut[l]) + c - win - wout             # (l becomes a self loop; counted here, l removed below)
            else:
                d = arc_w(l, r) + c - win - wout
        if d > 0: raise ReductionError("weight increases by %d in a Monge step" % d)
        if d == 0: tight += 1
        delta += d; steps += 1; alive.discard(v)
        if l == v: return
        if l is not None: R[l] = r
        if r is not None: L[r] = l
        if l is not None and l == r:                         # l is now a self loop
            L[l] = R[l] = l
    # greedy safe eliminations
    pending = [v for v in D if v in alive]
    if rng: rng.shuffle(pending)
    while pending:
        progress = False; rest = []
        for v in pending:
            if v not in alive: continue
            if L[v] == v:
                if v in keep: raise ReductionError("kept cut became a self loop")
                eliminate(v); progress = True; continue
            if is_safe(v): eliminate(v); progress = True
            else: rest.append(v)
        pending = [v for v in rest if v in alive]
        if pending and not progress:
            # deadlock: every remaining deletable cut is unsafe -> ladders between two kept cuts
            pend = set(pending); done_any = False
            for v in list(pending):
                if v not in alive or v not in pend: continue
                a = v
                while L[a] is not None and L[a] in pend and L[a] != v: a = L[a]
                run = [a]; x = a
                while R[x] is not None and R[x] in pend and R[x] != a: x = R[x]; run.append(x)
                kl, kr = L[run[0]], R[run[-1]]
                if kl in pend or kr in pend: raise ReductionError("pending cycle inside a kept component")
                if kl is None or kr is None: raise ReductionError("unsafe run at a path end")
                seq = [kl] + run + [kr]
                wsum = sum(arc_w(seq[i], seq[i + 1]) for i in range(len(seq) - 1))
                d = arc_w(kl, kr) + sum(int(cut[u]) for u in run) - wsum
                if F.tight_pair(kl, kr): raise ReductionError("ladder ends are a tight pair")
                if d > 0: raise ReductionError("ladder deletion increases the weight by %d (m = %d)" % (d, len(run)))
                delta += d; steps += len(run); ladders.append(("ladder", len(run), d))
                for u in run: alive.discard(u); pend.discard(u)
                R[kl] = kr; L[kr] = kl; done_any = True
            pending = [v for v in pending if v in alive]
            if not done_any: raise ReductionError("stuck")
    assert alive == keep, (len(alive), len(keep))
    # realize the bracket tree
    tauK = {u: R[u] for u in keep}
    new_route = realize(F, keep, tauK, comps[0], C.vers)
    info = dict(P=C.P, components=ncomp, cycles=ncomp - 1, kept=len(keep), deleted=steps, delta=delta, tight_steps=tight, ladders=ladders,
                whole_cycles=whole, wrap_blocks=len(blocks), bypassed=bypassed,
                weight_before=F.weight(route), weight_after=F.weight(new_route))
    if sorted(new_route) != sorted(route): raise ReductionError("reduced route is not a permutation of the runs")
    if info["weight_after"] != info["weight_before"] + delta: raise ReductionError("bookkeeping mismatch: %d + %d != %d" % (info["weight_before"], delta, info["weight_after"]))
    # the result is a bracket tree: V = P, c = P - 30
    C2 = Cover(F, new_route); comps2, comp2 = C2.components()
    if C2.P != len(keep): raise ReductionError("piece count of the reduced route is %d, expected %d" % (C2.P, len(keep)))
    if len(comps2) - 1 != C2.P - 30: raise ReductionError("reduced route is not a bracket tree (c != P - 30)")
    for (a, b) in C2.junction.values():
        if T[a] == T[b]: raise ReductionError("reduced route has a jump")
    info["P_after"] = C2.P; info["cycles_after"] = len(comps2) - 1
    return new_route, info

def realize(F, keep, tauK, path_cuts_all, vers):
    """explicit word of a bracket tree: kept cuts `keep`, cover successor tauK among kept cuts, path component order."""
    T = F.T; succ = F.succ
    path = [u for u in path_cuts_all if u in keep]
    out = []
    # iterative depth-first emission
    def emit_visit(v):
        # visit trail of cut v starting at run v; at every other kept cut u of the trail: emit the cycle hanging at u
        stack = [("visit", v, v, True)]
        while stack:
            item = stack.pop()
            if item[0] == "visit":
                _, v0, r, first = item
                # emit runs from r until the next kept cut (exclusive) or back to v0
                x = r
                while True:
                    if not first and x == v0: break
                    if not first and x in keep and x != v0:
                        # anchor at x: emit its cycle, then continue the visit at x
                        stack.append(("cont", v0, x))
                        z = tauK[x]; cyc = []
                        while z != x: cyc.append(z); z = tauK[z]
                        for z in reversed(cyc): stack.append(("visit", z, z, True))
                        break
                    out.append(x); first = False; x = int(succ[x])
            else:
                _, v0, x = item
                # continue the visit of v0's trail at run x (x is an anchor whose cycle has been emitted)
                y = x; firstrun = True
                while True:
                    if not firstrun and y == v0: break
                    if not firstrun and y in keep and y != v0:
                        stack.append(("cont", v0, y))
                        z = tauK[y]; cyc = []
                        while z != y: cyc.append(z); z = tauK[z]
                        for z in reversed(cyc): stack.append(("visit", z, z, True))
                        break
                    out.append(y); firstrun = False; y = int(succ[y])
    for v in path: emit_visit(v)
    return out

# ---------------------------------------------------------------------------------------------------------------
def random_route(F, rng, vers=None, extra_cuts=(0, 3), shuffle_frac=1.0):
    """random multi-opening route: random cuts in every trail, the pieces in random order."""
    if vers is None: vers = {t: rng.randrange(2) for t in range(30)}
    pieces = []
    for t in range(30):
        m = F.mlen[t]; b = F.base(t, vers[t]); k = 1 + rng.randint(*extra_cuts)
        cs = sorted(rng.sample(range(m), k))
        for i in range(k):
            a = cs[i]; e = cs[(i + 1) % k]; Lp = (e - a) % m or m
            pieces.append([b + (a + j) % m for j in range(Lp)])
    rng.shuffle(pieces)
    return [r for p in pieces for r in p]

def perturb(F, route, rng, moves):
    """random segment moves (or-opt) on a route; keeps a Hamiltonian path."""
    r = list(route); N = len(r)
    for _ in range(moves):
        i = rng.randrange(N - 2); Lseg = rng.choice([1, 2, 3, 5, 7, 14, 21, 42, 100, 300]); j = min(N, i + Lseg)
        seg = r[i:j]; rest = r[:i] + r[j:]
        k = rng.randrange(len(rest) + 1)
        r = rest[:k] + seg + rest[k:]
    return r

def ladder_route(F, rng, typeT, typeS):
    """a wrap-free route that contains a ladder of two cuts (m = 2) between two kept cuts when the representatives
    returned in `prefer` are kept.  typeT / typeS in {"s", "w"}: singleton or wrap step on the T side / S side."""
    vers = {t: rng.randrange(2) for t in range(30)}
    T, S = rng.sample(range(30), 2)
    def side(t, typ):
        m = F.mlen[t]; b = F.base(t, vers[t])
        if typ == "s":
            a = b + rng.randrange(m)                       # single run piece [a]; long piece succ(a) .. pred(a)
            long_ = [int(F.succ[a])]
            while int(F.succ[long_[-1]]) != a: long_.append(int(F.succ[long_[-1]]))
            return long_, [a], int(F.succ[a]), a           # long piece, short piece, upper cut, lower cut
        fulls = [c for c in F.chains if c["t"] == t and c["v"] == vers[t] and c["full"]]
        c = rng.choice(fulls); D = c["runs"]; M0 = int(F.succ[D[-1]])
        long_ = [M0]
        while int(F.succ[long_[-1]]) != D[0]: long_.append(int(F.succ[long_[-1]]))
        return long_, list(D), M0, D[0]
    Tl, Ts, Tup, Tlo = side(T, typeT); Sl, Ss, Sup, Slo = side(S, typeS)
    # route segment:  T_long, S_short, T_short, S_long   ->  cover chain  Tup -> Sup -> Tlo -> Slo
    others = []
    for t in range(30):
        if t in (T, S): continue
        m = F.mlen[t]; b = F.base(t, vers[t]); k = rng.randint(1, 3); cs = sorted(rng.sample(range(m), k))
        for i in range(k):
            a = cs[i]; e = cs[(i + 1) % k]; Lp = (e - a) % m or m
            others.append([b + (a + j) % m for j in range(Lp)])
    rng.shuffle(others); cutpos = rng.randint(0, len(others))
    pieces = others[:cutpos] + [Tl, Ss, Ts, Sl] + others[cutpos:]
    return [r for p in pieces for r in p], {Tup, Slo}

def selftest(F, nroutes, seed, moves=0, base_routes=None):
    rng = random.Random(seed); stats = dict(routes=0, skipped_wrap=0, total_deleted=0, total_delta=0, max_P=0, ladders=0, ladder_list=[], tight_steps=0,
                                            jump_routes=0, max_cycles_before=0, max_cycles_after=0, min_delta=0)
    tries = 0
    while stats["routes"] < nroutes and tries < 50 * nroutes:
        tries += 1
        if base_routes: route = perturb(F, rng.choice(base_routes), rng, moves if moves else rng.randint(1, 12))
        else: route = random_route(F, rng, extra_cuts=(0, rng.choice([1, 2, 4, 8])))
        C = Cover(F, route)
        if C.has_wrap(): stats["skipped_wrap"] += 1; continue
        new_route, info = reduce_to_bracket_tree(F, route, rng)
        stats["routes"] += 1; stats["total_deleted"] += info["deleted"]; stats["total_delta"] += info["delta"]; stats["max_P"] = max(stats["max_P"], info["P"])
        stats["ladders"] += len(info["ladders"]); stats["ladder_list"] += info["ladders"]; stats["tight_steps"] += info["tight_steps"]
        stats["min_delta"] = min(stats["min_delta"], info["delta"])
        stats["max_cycles_before"] = max(stats["max_cycles_before"], info["cycles"]); stats["max_cycles_after"] = max(stats["max_cycles_after"], info["cycles_after"])
        if any(F.T[a] == F.T[b] for (a, b) in C.junction.values()): stats["jump_routes"] += 1
    stats["ladder_list"] = stats["ladder_list"][:20]
    return stats

def main():
    F = Family(sys.argv[1], cache=os.environ.get("W_CACHE"))
    if sys.argv[2] == "--ladders":
        nr = int(sys.argv[3]); rng = random.Random(int(sys.argv[4])); out = {}
        for tT in "sw":
            for tS in "sw":
                n = 0; nl = 0; worst = -10 ** 9; dsum = 0
                while n < nr:
                    route, prefer = ladder_route(F, rng, tT, tS)
                    if Cover(F, route).has_wrap(): continue
                    new_route, info = reduce_to_bracket_tree(F, route, rng, prefer=prefer)
                    n += 1; lad = [x for x in info["ladders"] if x[0] == "ladder"]; nl += len(lad)
                    for x in lad: worst = max(worst, x[2]); dsum += x[2]
                out[tT + tS] = dict(routes=n, ladders_deleted=nl, max_ladder_delta=worst if nl else None)
        print(json.dumps(out)); return
    if sys.argv[2] == "--random":
        nr = int(sys.argv[3]); seed = int(sys.argv[4]); moves = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[5] == "--moves" else 0
        base = None
        if os.environ.get("BASE_WORDS"):
            base = [word_route(F, p, None) for p in os.environ["BASE_WORDS"].split(":")]
        st = selftest(F, nr, seed, moves, base)
        print(json.dumps(st)); return
    route = word_route(F, sys.argv[2], None)
    C = Cover(F, route); comps, comp = C.components()
    print("word: P = %d, components = %d (cycles %d), wraps = %d, weight = %d (G = %d)" % (C.P, len(comps), len(comps) - 1, len(C.has_wrap()), F.weight(route), F.weight(route) - 10874))
    new_route, info = reduce_to_bracket_tree(F, route)
    print(json.dumps(info))
    if len(sys.argv) > 4:
        w = build_word(F, new_route); open(sys.argv[4], "w").write("".join(str(c + 1) for c in w) + "\n")

if __name__ == "__main__": main()
