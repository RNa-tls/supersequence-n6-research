#!/usr/bin/env python3
"""Round L -- decomposition of an r = 0 word (n = 8) into chains / trails / worlds / hole components.

For each chain: special a (symbol in position n-1 of its run starts), the world-a orbit D (cyclic word
with a deleted), first gap g (a inserted after D[g]) and length l.  Join types (cost-3 joins) are
identified by sigma (bac, skip=(0,1,7), (0,7,1), (1,7,0), cba).
Reports
  E = sum_chains (7 - l)/7 (exact fragmentation identity), tau, lambda, the length identity,
  per-world |U_a|, |H_a| (holes: classes outside U_a whose world-a orbit meets U_a), the
  boundary bound E >= sum_a |H_a| / 7, seg>1 orbits,
  the hole graph (chain c -> chains covering O(c) minus c) and its connected components
  (class count, E, chains, worlds, pairs).
usage: r0_decompose.py WORDFILE [--json OUT]"""
import sys, os, json, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from worlds import World, canon_cyc

n = 8
W = World(n)

def load(path):
    w = "".join(ch for ch in open(path).read() if not ch.isspace())
    al = sorted(set(w)); mp = {c: i for i, c in enumerate(al)}
    return [mp[c] for c in w]

def cost(x, y):
    for j in range(n - 1, 0, -1):
        if x[n - j:] == y[:j]: return n - j
    return n

def runs_of(w):
    seen = set(); order = []
    for i in range(len(w) - n + 1):
        p = tuple(w[i:i + n])
        if len(set(p)) == n and p not in seen: seen.add(p); order.append(p)
    assert len(order) == math.factorial(n)
    starts = [order[i] for i in range(0, len(order), n)]
    for i in range(0, len(order), n):
        for k in range(1, n): assert order[i + k] == order[i + k - 1][1:] + order[i + k - 1][:1], "not r=0"
    return starts

def last(p): return p[-1:] + p[:-1]
def Fstep(p): return p[1:n - 1] + p[:1] + p[n - 1:]
SIG = {(1, 0, 7): "bac", (0, 1, 7): "skip", (0, 7, 1): "s071", (1, 7, 0): "s170", (7, 1, 0): "cba"}
def join_type(x, t):
    for s, name in SIG.items():
        if x[2:n - 1] + tuple(x[k] for k in s) == t: return name
    return None

def cls_id(p): return W.cid[canon_cyc(list(p))]

def decompose(starts):
    J = [cost(last(starts[i]), starts[i + 1]) for i in range(len(starts) - 1)]
    chains = [[0]]
    for i, c in enumerate(J):
        if c == 2:
            assert starts[i + 1] == Fstep(starts[i]); chains[-1].append(i + 1)
        else: chains.append([i + 1])
    info = []
    for ch in chains:
        p = starts[ch[0]]; a = p[n - 1]
        D = canon_cyc([x for x in p if x != a])
        info.append(dict(a=a, D=D, classes=[cls_id(starts[k]) for k in ch], l=len(ch),
                         first=starts[ch[0]], lastp=starts[ch[-1]]))
    cj = [J[ch[-1]] for ch in chains[:-1]]
    jt = [join_type(info[k]["lastp"], info[k + 1]["first"]) if c == 3 else None for k, c in enumerate(cj)]
    return J, info, cj, jt

def main():
    path = sys.argv[1]
    w = load(path); starts = runs_of(w)
    J, chains, cj, jt = decompose(starts)
    q = len(chains); tau = 1 + sum(c >= 4 for c in cj); lam = sum(c - 4 for c in cj if c >= 4)
    E = sum(7 - c["l"] for c in chains) / 7
    L = len(w)
    assert L == 46085 + (q - 720) + (tau - 1) + lam, "identity"
    spec = {}
    for k, c in enumerate(chains):
        for x in c["classes"]: spec[x] = c["a"]
    assert len(spec) == W.M
    U = defaultdict(set)
    for x, a in spec.items(): U[a].add(x)
    H = {}; seg = Counter(); partial = Counter()
    for a in range(n):
        Ha = set()
        for D, mem in W.orb_members[a].items():
            j = sum(1 for x in mem if spec[x] == a)
            if 0 < j < 7:
                Ha |= {x for x in mem if spec[x] != a}; partial[a] += 1
        H[a] = Ha
    for c in chains: seg[(c["a"], c["D"])] += 1
    extra_seg = sum(v - 1 for v in seg.values())
    bound = sum(len(H[a]) for a in range(n)) / 7
    # hole graph
    owner = {}
    for k, c in enumerate(chains):
        for x in c["classes"]: owner[x] = k
    adj = defaultdict(set)
    for k, c in enumerate(chains):
        if c["l"] < 7:
            for x in W.orb_members[c["a"]][c["D"]]:
                if owner[x] != k: adj[k].add(owner[x]); adj[owner[x]].add(k)
    comp = {}; comps = []
    for k in range(q):
        if k in comp: continue
        st = [k]; comp[k] = len(comps); cur = [k]
        while st:
            u = st.pop()
            for v in adj[u]:
                if v not in comp: comp[v] = len(comps); st.append(v); cur.append(v)
        comps.append(cur)
    csum = []
    for cc in comps:
        cl = sum(chains[k]["l"] for k in cc); e = sum(7 - chains[k]["l"] for k in cc) / 7
        csum.append((cl, len(cc), round(e, 4), tuple(sorted({chains[k]["a"] for k in cc}))))
    comp_hist = Counter(csum)
    # trails
    trails = [[0]]
    for k, c in enumerate(cj):
        if c == 3: trails[-1].append(k + 1)
        else: trails.append([k + 1])
    tr = []
    for t in trails:
        cl = sum(chains[k]["l"] for k in t)
        tr.append(dict(chains=len(t), classes=cl, E=round(sum(7 - chains[k]["l"] for k in t) / 7, 4),
                       worlds=sorted({chains[k]["a"] for k in t}),
                       lengths="".join(str(chains[k]["l"]) for k in t)))
    res = dict(file=os.path.basename(path), L=L, q=q, E=round(E, 4), tau=tau, lam=lam,
               E_plus_tau_minus1_plus_lam=round(E + tau - 1 + lam, 4),
               join_costs=dict(sorted(Counter(cj).items())), join_types=dict(Counter(x for x in jt if x)),
               U_sizes={a: len(U[a]) for a in range(n)}, H_sizes={a: len(H[a]) for a in range(n)},
               partial_orbits=dict(partial), extra_segments=extra_seg,
               boundary_bound=round(bound, 4), E_minus_bound=round(E - bound, 4),
               components=len(comps), component_types=[[list(k), v] for k, v in sorted(comp_hist.items(), key=lambda z: -z[0][0])],
               trails=tr)
    print(json.dumps({k: v for k, v in res.items() if k != "trails"}, indent=None))
    for t in tr: print(json.dumps(t))
    if "--json" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)

if __name__ == "__main__":
    main()
