#!/usr/bin/env python3
"""Round M (section 17) -- EXACT trail-level neighbourhoods of a single-opening r = 0 word.

Model (single opening, any version): every closed trail T of the family is visited in one piece,
opened at any cyclic edge of any of its versions; for a fixed ORDER of the 30 trails the best
choice of versions and cuts is a layered shortest path and
        L = 8 + sum_T (9|T| + k_T) + sum_boundaries w_b - sum_T w(cut_T)          (exact).
The shortest path is computed EXACTLY over all boundary weights 2..8: for a layer transition and
every k = 2..7 the minimum label over exits with suffix s (|s| = 8-k) is tabulated, and an entry e
receives min_k (table_k[e[:8-k]] + k) and (global min + 8); since w(x, e) = min{k : x[k:] = e[:8-k]}
this equals min_x (label(x) + w(x, e)).
Neighbourhoods evaluated exhaustively (every order, its own optimal cuts/versions):
  RELOC  : move one trail to any other position;
  SWAP   : exchange two trails;
  BLOCK(b): move a block of b <= BMAX consecutive trails to any other position;
  WIN(k) : every permutation of every window of k <= KMAX consecutive trails.
usage: trail_order_exact.py FAMILY.json DESCRIPTION.json [KMAX] [BMAX]"""
import sys, os, json, time, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

n = 8
def last(p): return p[-1:] + p[:-1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n

def load_layers(fam):
    """per trail: list of (entry, exit, cut weight, version, edge); const = 8 + sum_T (9|T| + k_T)"""
    layers = []; const = 8
    for tr in fam["trails"]:
        opts = []
        for v, s in enumerate(tr["versions"]):
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            for k in range(len(st)):
                opts.append((st[k], last(st[k - 1]), wt(last(st[k - 1]), st[k]), v, k))
        layers.append(opts)
        st0 = [tuple(int(c) for c in tr["versions"][0][8 * k:8 * k + 8]) for k in range(len(tr["versions"][0]) // 8)]
        const += 9 * len(st0) + sum(1 for k in range(len(st0)) if wt(last(st0[k - 1]), st0[k]) == 3)
    return layers, const

def evaluate(layers, const, order, want_path=False):
    """exact layered shortest path over versions/cuts for a fixed trail order (all weights 2..8)"""
    L0 = layers[order[0]]
    lab = [-o[2] for o in L0]; back = []
    prev = L0
    for t in order[1:]:
        cur = layers[t]
        tabs = []
        for k in range(2, 8):
            m = n - k; tab = {}
            for i, o in enumerate(prev):
                key = o[1][k:]; v = lab[i]
                if key not in tab or v < tab[key][0]: tab[key] = (v, i)
            tabs.append((k, m, tab))
        gi = min(range(len(prev)), key=lambda i: lab[i]); g = lab[gi]
        nl = []; nb = []
        for o in cur:
            best = g + 8; bi = gi
            e = o[0]
            for k, m, tab in tabs:
                r = tab.get(e[:m])
                if r is not None and r[0] + k < best: best = r[0] + k; bi = r[1]
            nl.append(best - o[2]); nb.append(bi)
        lab = nl; back.append(nb); prev = cur
    j = min(range(len(prev)), key=lambda i: lab[i])
    val = const + lab[j]
    if not want_path: return val
    path = [j]
    for nb in reversed(back): j = nb[j]; path.append(j)
    path.reverse()
    return val, [(order[i], layers[order[i]][path[i]]) for i in range(len(order))]

def build(fam, path):
    """rebuild the route of a (trail, option) path and measure its length from scratch"""
    route = []
    for t, o in path:
        v, k = o[3], o[4]
        s = fam["trails"][t]["versions"][v]
        st = [tuple(int(c) for c in s[8 * i:8 * i + 8]) for i in range(len(s) // 8)]
        m = len(st)
        for i in range(m):
            p = st[(k + i) % m]; route += [p[j:] + p[:j] for j in range(n)]
    assert len(route) == 40320 and len(set(route)) == 40320
    return 8 + sum(wt(x, y) for x, y in zip(route, route[1:]))

def main():
    fam = json.load(open(sys.argv[1])); desc = json.load(open(sys.argv[2]))
    KMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    BMAX = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    t0 = time.time()
    T = len(fam["trails"])
    layers = []                                   # per trail: list of (entry, exit, cut, version, k)
    const = 8
    for tr in fam["trails"]:
        opts = []
        for v, s in enumerate(tr["versions"]):
            st = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
            m = len(st)
            for k in range(m):
                opts.append((st[k], last(st[k - 1]), wt(last(st[k - 1]), st[k]), v, k))
        layers.append(opts)
        st0 = [tuple(int(c) for c in tr["versions"][0][8 * k:8 * k + 8]) for k in range(len(tr["versions"][0]) // 8)]
        const += 9 * len(st0) + sum(1 for k in range(len(st0)) if wt(last(st0[k - 1]), st0[k]) == 3)
    order0 = [p["trail"] if isinstance(p, dict) else p[0] for p in desc["description"]] if "description" in desc else None
    order0 = [d[0] for d in desc["description"]]
    assert sorted(order0) == list(range(T)), "description is not a single-opening word"

    def evaluate(order, want_path=False):
        L0 = layers[order[0]]
        lab = [-o[2] for o in L0]; back = []
        prev = L0
        for t in order[1:]:
            cur = layers[t]
            tabs = []
            for k in range(2, 8):
                m = n - k; tab = {}
                for i, o in enumerate(prev):
                    key = o[1][k:]; v = lab[i]
                    if key not in tab or v < tab[key][0]: tab[key] = (v, i)
                tabs.append((k, m, tab))
            gi = min(range(len(prev)), key=lambda i: lab[i]); g = lab[gi]
            nl = []; nb = []
            for o in cur:
                best = g + 8; bi = gi
                e = o[0]
                for k, m, tab in tabs:
                    r = tab.get(e[:m])
                    if r is not None and r[0] + k < best: best = r[0] + k; bi = r[1]
                nl.append(best - o[2]); nb.append(bi)
            lab = nl; back.append(nb); prev = cur
        j = min(range(len(prev)), key=lambda i: lab[i])
        val = const + lab[j]
        if not want_path: return val
        path = [j]
        for nb in reversed(back): j = nb[j]; path.append(j)
        path.reverse()
        return val, [(order[i], layers[order[i]][path[i]]) for i in range(len(order))]

    base, path0 = evaluate(order0, True)
    # rebuild the route of the optimal cuts for the base order and measure it from scratch
    def build(path):
        route = []
        for t, o in path:
            v, k = o[3], o[4]
            s = fam["trails"][t]["versions"][v]
            st = [tuple(int(c) for c in s[8 * i:8 * i + 8]) for i in range(len(s) // 8)]
            m = len(st)
            for i in range(m):
                p = st[(k + i) % m]; route += [p[j:] + p[:j] for j in range(n)]
        assert len(route) == 40320 and len(set(route)) == 40320
        return 8 + sum(wt(x, y) for x, y in zip(route, route[1:]))
    measured = build(path0)
    print(json.dumps(dict(base_order_value=base, measured=measured, layers=T, sec=round(time.time() - t0, 1))), flush=True)
    stats = {}
    best_seen = (base, None)
    def consider(name, order):
        nonlocal best_seen
        v = evaluate(order)
        s = stats.setdefault(name, dict(orders=0, best=10 ** 9, improving=0))
        s["orders"] += 1; s["best"] = min(s["best"], v); s["improving"] += (v < base)
        if v < best_seen[0]: best_seen = (v, list(order))
    o = order0
    for i in range(T):                                   # RELOC
        for j in range(T):
            if i == j: continue
            r = o[:i] + o[i + 1:]; r.insert(j, o[i]); consider("reloc", r)
    print(json.dumps(dict(stage="reloc", **stats["reloc"], sec=round(time.time() - t0, 1))), flush=True)
    for i in range(T):                                   # SWAP
        for j in range(i + 1, T):
            r = list(o); r[i], r[j] = r[j], r[i]; consider("swap", r)
    print(json.dumps(dict(stage="swap", **stats["swap"], sec=round(time.time() - t0, 1))), flush=True)
    for b in range(2, BMAX + 1):                         # BLOCK(b)
        for i in range(T - b + 1):
            blk = o[i:i + b]; rest = o[:i] + o[i + b:]
            for j in range(len(rest) + 1):
                if j == i: continue
                consider("block%d" % b, rest[:j] + blk + rest[j:])
        print(json.dumps(dict(stage="block%d" % b, **stats["block%d" % b], sec=round(time.time() - t0, 1))), flush=True)
    for k in range(2, KMAX + 1):                         # WIN(k)
        for i in range(T - k + 1):
            for perm in itertools.permutations(o[i:i + k]):
                if list(perm) == o[i:i + k]: continue
                consider("win%d" % k, o[:i] + list(perm) + o[i + k:])
        print(json.dumps(dict(stage="win%d" % k, **stats["win%d" % k], sec=round(time.time() - t0, 1))), flush=True)
    res = dict(word=desc.get("word"), base=base, measured=measured, best_found=best_seen[0],
               improving_order=best_seen[1], stats=stats, sec=round(time.time() - t0, 1))
    if best_seen[1] is not None:
        v, p = evaluate(best_seen[1], True); res["rebuilt"] = build(p)
    print(json.dumps(res), flush=True)

if __name__ == "__main__":
    main()
