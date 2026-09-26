#!/usr/bin/env python3
"""Round 178 -- generic (n-parametric) coarsening map, i.e. the construction of the
Bridge(n) theorem of r178/BRIDGE_REPORT.md, executed on concrete routes.

Nothing here is specific to n: the constants are N = n!, HEX = (n-1)!, ORB = (n-2)!.
Every structural lemma used by the proof is ASSERTED on the route at hand (the proof
is symbolic; the assertions are falsification tests):

  route      a Hamiltonian path of S_n (list of permutations), normalized: no edge x -> R^2 x
  S          run starts (not entered by a cost-1 edge);  |S| = HEX + r
  A          next run start in R-order inside the class (a permutation of S)
  U          union of touched F-blocks (blocks meeting S); M blocks;  holes = U \\ S
  Q          blocks joined along the A-cycles (r transpositions);  k components
  T          F o A on U (A = id on holes)                         [Lemma B-T]
  chains     maximal cost-1/proper-cost-2 segments;  q of them       [Lemma B-C]
  paths      pieces after deleting cost >= 4 edges;  p = eta + 1
  gaps       maximal hole runs / absent cost-2 edges on T-cycles;  #gaps = q
  surgery    merge cyclically adjacent arcs (paper Lemma 5.2), then keep one T-cycle per
             component and delete the others (trail splits)
  rows       complementary row of the retained gap; omitted = holes inside the interval
Output instance must satisfy CoarsenedInstance(k = ORB+m-r+a, tau = eta+1+b,
u = (n-1)m - r, b), checked by the independent checkers A and B of r176."""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "r176", "src"))
from checkA176 import CheckerA
from checkB176 import CheckerB


class BridgeError(AssertionError):
    pass


def need(cond, msg):
    if not cond:
        raise BridgeError(msg)


def cost(x, y, n):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]:
            return n - j
    return n


def normalize(route, n):
    """Paper Lemma 2.2 (general n): repeatedly move u = R x between x and R^2 x.
    Weight never increases, the number of cost-1 edges strictly increases."""
    R = lambda s: s[1:] + s[:1]
    route = list(route)
    while True:
        pos = {v: i for i, v in enumerate(route)}
        bad = next((i for i in range(len(route) - 1) if route[i + 1] == R(R(route[i]))), None)
        if bad is None:
            return route
        w0 = sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1))
        c10 = sum(cost(route[i], route[i + 1], n) == 1 for i in range(len(route) - 1))
        x = route[bad]; u = R(x)
        route.pop(pos[u])
        i = route.index(x)
        route.insert(i + 1, u)
        w1 = sum(cost(route[i], route[i + 1], n) for i in range(len(route) - 1))
        c11 = sum(cost(route[i], route[i + 1], n) == 1 for i in range(len(route) - 1))
        need(w1 <= w0 and c11 > c10, "normalization step")


def route_of_word(word, n):
    first = {}
    for i in range(len(word) - n + 1):
        t = word[i:i + n]
        if len(set(t)) == n and t not in first:
            first[t] = i
    need(len(first) == math.factorial(n), "not a superpermutation")
    return [t for t, _ in sorted(first.items(), key=lambda kv: kv[1])]


def coarsen(route, n, rng=None):
    rng = rng or random.Random(0)
    N, HEX, ORB = math.factorial(n), math.factorial(n - 1), math.factorial(n - 2)
    R = lambda s: s[1:] + s[:1]
    Rinv = lambda s: s[-1:] + s[:-1]
    F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
    need(len(route) == N and len(set(route)) == N, "Hamiltonian")
    c = [cost(route[i], route[i + 1], n) for i in range(N - 1)]
    need(all(route[i + 1] != R(R(route[i])) for i in range(N - 1)), "normalized")
    idx = {v: i for i, v in enumerate(route)}
    # --- runs, S, A
    S = {route[0]} | {route[i + 1] for i in range(N - 1) if c[i] != 1}
    r = len(S) - HEX
    need(r >= 0, "every class meets S")
    def A(x):
        if x not in S: return x
        y = R(x)
        while y not in S: y = R(y)
        return y
    for s in S:   # run from s ends at R^{-1} A(s)
        e = s
        while idx[e] + 1 < N and c[idx[e]] == 1: e = route[idx[e] + 1]
        need(e == Rinv(A(s)), "run end = R^-1 A(s)")
    # --- blocks, U, Q
    def blk(x):
        out = [x]
        for _ in range(n - 2): out.append(F(out[-1]))
        return min(out)
    touched = {blk(s) for s in S}
    M = len(touched)
    U = set()
    for b0 in touched:
        x = b0
        for _ in range(n - 1): U.add(x); x = F(x)
    need(len(U) == (n - 1) * M, "U = union of touched blocks")
    holes = U - S
    par = {b0: b0 for b0 in touched}
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    seen = set(); nedges = 0
    for s in S:
        if s in seen: continue
        cyc = [s]; y = A(s)
        while y != s: cyc.append(y); y = A(y)
        seen.update(cyc)
        for u_, v_ in zip(cyc, cyc[1:]):           # a factorization into len-1 transpositions
            nedges += 1
            ra, rb = find(blk(u_)), find(blk(v_))
            if ra != rb: par[ra] = rb
    need(nedges == r, "factorization of A has r transpositions")
    comp = {b0: find(b0) for b0 in touched}
    k = len(set(comp.values()))
    # --- chains, paths
    T = lambda x: F(A(x))
    chain_starts = [route[0]] + [route[i + 1] for i in range(N - 1) if c[i] >= 3]
    q = len(chain_starts)
    p = sum(1 for x in c if x >= 4) + 1
    chains = []          # list of run-start lists
    chain_of = {}
    for cs in chain_starts:
        seq = [cs]; x = cs
        while True:
            e = Rinv(A(x))                         # run end
            i = idx[e]
            if i + 1 < N and c[i] == 2:
                nx = route[i + 1]
                need(nx == T(x), "proper cost-2 successor of the run end is T(s) = F(A(s))")
                seq.append(nx); x = nx
            else:
                break
        for s in seq: chain_of[s] = len(chains)
        chains.append(seq)
    need(sorted(chain_of) == sorted(S), "chains partition S")
    def head(ch): return chains[ch][0][:n - 3]
    def tail(ch): return Rinv(A(chains[ch][-1]))[3:]
    paths = [[]]
    for i, cs in enumerate(chain_starts):
        if i > 0:
            prev_end = Rinv(A(chains[i - 1][-1]))
            ci = cost(prev_end, cs, n)
            need(idx[cs] == idx[prev_end] + 1, "chains consecutive on the route")
            if ci >= 4: paths.append([])
            else: need(ci == 3 and tail(i - 1) == head(i), "cost-3 overlap = row compatibility")
        paths[-1].append(i)
    need(len(paths) == p, "p paths")
    m = M - ORB; a = r - (M - k); b = q - k; eta = p - 1
    need(m >= 0 and a >= 0 and b >= 0 and a <= r <= (n - 1) * m, "structural inequalities")
    u = (n - 1) * m - r
    need(len(holes) == u, "holes = (n-1)m - r")
    # --- T-cycles, gaps
    cyc_id = {}; cycles = []
    for x in U:
        if x in cyc_id: continue
        cyc = [x]; y = T(x)
        while y != x: cyc.append(y); y = T(y)
        for z in cyc: cyc_id[z] = len(cycles)
        need(any(z in S for z in cyc), "no hole-only T-cycle")
        need(len({comp[blk(z)] for z in cyc}) == 1, "T-cycle inside one component")
        cycles.append(cyc)
    # rotate each cycle to start right after a gap; list chains in cyclic order + gaps
    cyc_chains, gap_after = [], {}           # gap_after[chain] = ('hole', x, d) | ('art', s)
    total_gaps = 0
    for ci, cyc in enumerate(cycles):
        L = len(cyc)
        cpos = {z: j for j, z in enumerate(cyc)}
        # position j is a gap start if cyc[j] is a hole whose predecessor is selected,
        # or cyc[j] selected, last of its chain, and cyc[j+1] selected
        order = []
        for j, z in enumerate(cyc):
            if z in S and chains[chain_of[z]][0] == z:
                order.append(chain_of[z])
        # verify chains are contiguous T-arcs and determine the gap after each chain
        for ch in order:
            last = chains[ch][-1]
            j = cpos[last]
            nxt = cyc[(j + 1) % L]
            if nxt in holes:
                d = 0; y = nxt
                while y in holes: d += 1; y = cyc[(cpos[y] + 1) % L]
                need(all(blk(cyc[(j + 1 + t) % L]) == blk(nxt) for t in range(d)), "hole run in one block")
                gap_after[ch] = ("hole", nxt, d)
            else:
                need(nxt in S and chains[chain_of[nxt]][0] == nxt, "artificial gap")
                gap_after[ch] = ("art", last)
            total_gaps += 1
        # cyclic order of chains along the cycle
        pos = {ch: cpos[chains[ch][0]] for ch in order}
        cyc_chains.append(sorted(order, key=lambda ch: pos[ch]))
    need(total_gaps == q, "#gaps = q")
    # --- surgery.  arc = (cycle, list of chains in cyclic order)
    trails = [[("a", ch) for ch in pth] for pth in paths]
    arcs = {("a", ch): [ch] for ch in range(q)}
    def arc_head(aid): return head(arcs[aid][0])
    def arc_tail(aid): return tail(arcs[aid][-1])
    def check_trails():
        for t in trails:
            for x, y in zip(t, t[1:]):
                need(arc_tail(x) == arc_head(y), "trail compatibility")
    check_trails()
    t0 = len(trails); merges = 0; fresh = [0]
    for ci, order in enumerate(cyc_chains):
        cur = [("a", ch) for ch in order]           # arcs of this cycle in cyclic order
        while len(cur) > 1:
            loc = {}
            for ti, t in enumerate(trails):
                for pi, aid in enumerate(t): loc[aid] = (ti, pi)
            cand = [i for i in range(len(cur))
                    if loc[cur[i]][0] != loc[cur[(i + 1) % len(cur)]][0]
                    or loc[cur[i]][1] < loc[cur[(i + 1) % len(cur)]][1]]
            need(cand, "surgery lemma: some adjacent pair is usable")
            i = rng.choice(cand)
            X, Y = cur[i], cur[(i + 1) % len(cur)]
            fresh[0] += 1; Z = ("m", fresh[0]); arcs[Z] = arcs[X] + arcs[Y]
            (tx, px), (ty, py) = loc[X], loc[Y]
            before = len(trails)
            if tx != ty:
                P, Sx = trails[tx][:px], trails[tx][px + 1:]
                Qy, Ry = trails[ty][:py], trails[ty][py + 1:]
                new = [P + [Z] + Ry] + [part for part in (Sx, Qy) if part]
                trails = [t for ti, t in enumerate(trails) if ti not in (tx, ty)] + new
            else:
                t = trails[tx]; P, W, Rr = t[:px], t[px + 1:py], t[py + 1:]
                new = [P + [Z] + Rr] + ([W] if W else [])
                trails = [tt for ti, tt in enumerate(trails) if ti != tx] + new
            need(len(trails) <= before + 1, "surgery adds <= 1 trail")
            merges += 1
            cur = cur[:i] + [Z] + cur[i + 2:] if i + 1 < len(cur) else [Z] + cur[1:i]
            check_trails()
    need(merges == q - len(cycles), "q - cyc(T) merges")
    # --- keep one cycle per component
    keep = {}
    for ci, order in enumerate(cyc_chains):
        cm = comp[blk(cycles[ci][0])]
        keep.setdefault(cm, ci)
    kept = set(keep.values())
    cyc_of_arc = {aid: cyc_id[chains[arcs[aid][0]][0]] for t in trails for aid in t}
    t1 = len(trails)
    new_trails = []
    for t in trails:
        seg = []
        for aid in t:
            if cyc_of_arc[aid] in kept: seg.append(aid)
            else:
                if seg: new_trails.append(seg)
                seg = []
        if seg: new_trails.append(seg)
    need(len(new_trails) <= t1 + (len(cycles) - k), "deletions add <= cyc(T) - k trails")
    trails = new_trails
    check_trails()
    tau = eta + 1 + b
    need(len(trails) <= tau, "trail count <= eta + 1 + b")
    # --- rows
    rows_of = {}
    for t in trails:
        for aid in t:
            ch_list = arcs[aid]
            g = gap_after[ch_list[-1]]              # the retained gap: after the last chain
            if g[0] == "hole":
                x, d = g[1], g[2]
                st = x
                for _ in range(d): st = F(st)
                length = n - 1 - d
            else:
                st = T(g[1]); length = n - 1
            states = [st]
            for _ in range(length - 1): states.append(F(states[-1]))
            om = tuple(i for i, z in enumerate(states) if z in holes)
            row = (st, length, om)
            need(st[:n - 3] == arc_head(aid), "row alpha = arc head (complementary-row lemma)")
            last_state = states[-1]
            need(Rinv(last_state)[3:] == arc_tail(aid), "row beta = arc tail (complementary-row lemma)")
            nh = 0; z = st
            for _ in range(n - 1):
                nh += z in holes; z = F(z)
            need((n - 1 - length) + len(om) == nh, "charge(row) = holes of its block")
            need(all(0 < i < length - 1 for i in om), "omissions interior")
            rows_of[aid] = row
    inst = [[rows_of[aid] for aid in t] for t in trails]
    return dict(n=n, r=r, q=q, p=p, M=M, k=k, m=m, a=a, b=b, eta=eta, u=u, tau=tau,
                D=m + a + b + eta, cycles=len(cycles), weight=sum(c), holes=holes,
                instance=inst, blk=blk)


def check_instance(res, checker, claims=None):
    """CoarsenedInstance(k, tau, u, b) with the given checker; claims may override."""
    n = res["n"]; K = checker
    k = (claims or {}).get("k", math.factorial(n - 2) + res["m"] - res["r"] + res["a"])
    tau = (claims or {}).get("tau", res["eta"] + 1 + res["b"])
    u = (claims or {}).get("u", (n - 1) * res["m"] - res["r"])
    b = (claims or {}).get("b", res["b"])
    inst = res["instance"]
    flat = [x for t in inst for x in t]
    if len(inst) > tau: return False, "trail_count"
    if len(flat) != k: return False, "row_count"
    for x in flat:
        if not K.admissible(x): return False, "interior/admissible"
    for t in inst:
        for x, y in zip(t, t[1:]):
            if not K.compatible(x, y): return False, "compat"
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if not K.disjoint(flat[i], flat[j]): return False, "disjoint"
    if sum(K.charge(x) for x in flat) > u: return False, "charge"
    def runs(x):
        om = set(x[2]); return sum(1 for i in om if i - 1 not in om)
    if sum(runs(x) for x in flat) > b: return False, "runs"
    return True, "ok"
