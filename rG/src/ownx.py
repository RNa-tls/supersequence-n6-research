#!/usr/bin/env python3
"""Completion as exact cover (report sec. C3).
Primary items: the uncovered classes U.  Secondary items: candidate blocks (each used at most once).
Options: (block B, owned set O) with O = B & U if |B & U| = n-2 (attachment = B's kernel-visible class),
or O = (B & U) minus one class a (attachment a, which must then be owned by another option) if
|B & U| = n-1.  A completion = an exact cover of U by options whose parent relation
(B -> owner of a_B; B -> kernel when a_B is kernel-visible) is acyclic.
Algorithm X (Knuth) with secondary block items; for each exact cover found the parent relation is
checked; search continues past cyclic covers.  Unit propagation statistics are recorded."""
import sys, os, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from candcore import analyse, kernel_rows
from complete import World


def build(W, A):
    n = W.n; Us = set(A["U"])
    opts = []
    for b in A["cand"]:
        cu = [c for c in W.bcls[b] if c in Us]
        if len(cu) == n - 2: opts.append((b, None, frozenset(cu)))
        else:
            for a in cu: opts.append((b, a, frozenset(c for c in cu if c != a)))
    return opts


def search(W, A, nodes, seed, max_covers=10**9):
    rng = random.Random(seed)
    U = A["U"]; opts = build(W, A)
    X = {c: set() for c in U}
    byblock = {}
    for i, (b, a, O) in enumerate(opts):
        for c in O: X[c].add(i)
        byblock.setdefault(b, []).append(i)
    removed_stack = []
    cnt = [0]; covers = [0]; sol = []; found = [None]

    def remove_option(i, log):
        for c in opts[i][2]:
            if c in X and i in X[c]: X[c].discard(i); log.append((c, i))

    def select(i, log):
        b = opts[i][0]
        cols = []
        for c in opts[i][2]:
            for j in list(X[c]):
                remove_option(j, log)
            cols.append((c, X.pop(c)))
        for j in byblock[b]:                       # block used at most once
            remove_option(j, log)
        return cols

    def deselect(cols, log):
        for c, s in reversed(cols): X[c] = s
        for c, j in reversed(log): X[c].add(j)

    def acyclic(chosen):
        owner = {}
        for i in chosen:
            for c in opts[i][2]: owner[c] = opts[i][0]
        parent = {opts[i][0]: (owner[opts[i][1]] if opts[i][1] is not None else None) for i in chosen}
        state = {}
        for b in parent:
            path = []; x = b
            while x is not None and x not in state:
                state[x] = 1; path.append(x); x = parent[x]
                if x is not None and state.get(x) == 1 and x in path: return False
            for y in path: state[y] = 2
        return True

    sys.setrecursionlimit(100000)

    def solve():
        cnt[0] += 1
        if cnt[0] > nodes or found[0] is not None or covers[0] >= max_covers: return
        if not X:
            covers[0] += 1
            if acyclic(sol): found[0] = list(sol)
            return
        c = min(X, key=lambda c: (len(X[c]), rng.random()))
        if not X[c]: return
        cand = list(X[c]); rng.shuffle(cand)
        for i in cand:
            log = []; cols = select(i, log); sol.append(i)
            solve()
            sol.pop(); deselect(cols, log)
            if found[0] is not None or cnt[0] > nodes: return

    solve()
    return dict(nodes=cnt[0], exhausted=cnt[0] <= nodes and found[0] is None and covers[0] < max_covers,
                exact_covers_seen=covers[0], completion=found[0] is not None), (found[0], opts)


if __name__ == "__main__":
    nodes = int(sys.argv[1]); seeds = int(sys.argv[2])
    worlds = {}
    for job in sys.argv[3:]:
        n, spec = int(job.split("/")[0]), job.split("/")[1]
        W = worlds.setdefault(n, World(n)); rows = kernel_rows(n, spec)
        A = analyse(W, rows)
        for sd in range(seeds):
            t0 = time.time(); info, (sol, opts) = search(W, A, nodes, sd)
            print(json.dumps(dict(n=n, kernel=spec[:40], seed=sd, **info, seconds=round(time.time() - t0, 1))), flush=True)
            if sol:
                json.dump(dict(n=n, kernel=spec, payload=[[list(W.blocks[opts[i][0]][0]), W.blocks[opts[i][0]][1]] for i in sol]),
                          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs",
                                            f"ownx_completion_{n}_{spec.replace(':', '_')[:40]}.json"), "w"))
                break
            if info["exhausted"]: break
