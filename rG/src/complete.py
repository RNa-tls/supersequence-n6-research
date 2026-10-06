#!/usr/bin/env python3
"""Final attack, upper thread -- forest COMPLETION of a kernel (a ModelTrail of omission-free rows):
find payload blocks, added one at a time, each meeting the covered class set in exactly one class,
until every class is covered.  Kernel rows contribute only their VISIBLE classes; their blocks are
excluded from the payload.  Sound prune: an uncovered class is dead if every block containing it is
used or already meets >= 2 covered classes (covered set only grows).  Branching: most-constrained
uncovered class among those with an attachable block; DFS with node limit and random restarts.
A completion of a kernel with k rows and charge G yields (generalized Theorem E, realization by
T-cycle traversal) a superpermutation of length CONST + ((n-2)! - (k - G))/(n-2)."""
import sys, os, math, random, itertools, time, json

def canon(t): return min(t[i:] + t[:i] for i in range(len(t)))


class World:
    def __init__(self, n):
        self.n = n
        classes = sorted({canon(p) for p in itertools.permutations(range(n))})
        self.cid = {c: i for i, c in enumerate(classes)}; self.C = len(classes)
        blocks = []; bid = {}
        for c in classes:
            for t in range(n):
                i = c.index(t); W = canon(c[i + 1:] + c[:i])
                if (W, t) not in bid: bid[(W, t)] = len(blocks); blocks.append((W, t))
        self.blocks = blocks; self.bid = bid
        self.bcls = [[self.cid[canon(W[:g] + (t,) + W[g:])] for g in range(n - 1)] for W, t in blocks]
        self.cblk = [[] for _ in range(self.C)]
        for b, cl in enumerate(self.bcls):
            for c in cl: self.cblk[c].append(b)

    def row_visible(self, row):
        p, l, om = row; n = self.n
        F = lambda s: s[1:n - 1] + (s[0], s[n - 1])
        x = p; vis = []
        for i in range(l):
            if i not in om: vis.append(self.cid[canon(x)])
            x = F(x)
        return vis


def complete(world, kernel_rows, nodes=10**6, seed=0):
    """COMPLETE search over attachment forests.
    Branch on the owner of the most constrained unreserved uncovered class c: a block b that is still
    possible (unused, meets <= 1 covered class).  If b is addable now (meets exactly one covered class,
    no uncovered class of b reserved by another block) it is added; otherwise b is COMMITTED and
    reserves c.  Committed blocks are added as soon as addable (WLOG: the unique covered class of b at
    that moment must be its attachment class in every completion extending the state)."""
    W = world; n = W.n; rng = random.Random(seed)
    NB = len(W.blocks)
    covered = [False] * W.C; cnt = [0] * NB; used = [False] * NB
    reserved = [-1] * W.C; committed = set()
    for r in kernel_rows: used[W.bid[(canon(r[0][:n - 1]), r[0][n - 1])]] = True
    ncov = [0]; order = []
    def cover(c, log):
        covered[c] = True; ncov[0] += 1; log.append(('c', c))
        for b in W.cblk[c]: cnt[b] += 1
    for r in kernel_rows:
        for c in W.row_visible(r):
            if covered[c]: raise ValueError("kernel rows not class-disjoint")
            cover(c, [])
    def undo(log):
        for item in reversed(log):
            kind, v = item[0], item[1]
            if kind == 'c':
                covered[v] = False; ncov[0] -= 1
                for b in W.cblk[v]: cnt[b] -= 1
            elif kind == 'u': used[v] = False; order.pop()
            elif kind == 'r': reserved[v] = item[2]
            elif kind == 'k': committed.discard(v)
            elif kind == 'K': committed.add(v)
    def possible(b): return not used[b] and cnt[b] <= 1
    def addable(b):
        if used[b] or cnt[b] != 1: return False
        for c2 in W.bcls[b]:
            if not covered[c2] and reserved[c2] != -1 and reserved[c2] != b: return False
        return True
    def add(b, log):
        used[b] = True; order.append(b); log.append(('u', b))
        if b in committed: committed.discard(b); log.append(('K', b))
        for c2 in W.bcls[b]:
            if not covered[c2]: cover(c2, log)
    def propagate(log):
        changed = True
        while changed:
            changed = False
            for b in list(committed):
                if cnt[b] >= 2: return False
                if addable(b): add(b, log); changed = True
        return True
    def alive():
        for c in range(W.C):
            if covered[c]: continue
            if reserved[c] != -1:
                if not possible(reserved[c]): return False
                continue
            if not any(possible(b) for b in W.cblk[c]): return False
        return True
    calls = [0]
    sys.setrecursionlimit(1000000)
    def dfs():
        calls[0] += 1
        if calls[0] > nodes: return False
        if ncov[0] == W.C: return not committed
        best = None
        for c in range(W.C):
            if covered[c] or reserved[c] != -1: continue
            via = [b for b in W.cblk[c] if possible(b)]
            if not via: return False
            if best is None or len(via) < len(best[1]):
                best = (c, via)
                if len(via) == 1: break
        if best is None:
            return False      # all uncovered classes reserved, none addable (propagate already ran)
        c, via = best
        rng.shuffle(via); via.sort(key=lambda b: 0 if addable(b) else 1)
        for b in via:
            log = []
            if addable(b): add(b, log)
            else:
                if b not in committed: committed.add(b); log.append(('k', b))
                log.append(('r', c, reserved[c])); reserved[c] = b
            if propagate(log) and alive() and dfs(): return True
            undo(log)
            if calls[0] > nodes: return False
        return False
    ok = dfs()
    return (list(order) if ok else None), f"calls {calls[0]}"


def kernel_from_lengths(n, lengths):
    """single-special kernel from a length sequence, start = identity (special n-1)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from kernels import next_start
    p = tuple(range(n)); rows = []
    for l in lengths: rows.append((p, l, ())); p = next_start(p, l, n)
    return rows


def std_kernel(n):
    s = n - 1; f = (1,) + tuple(range(2, n - 1))
    return [(f[j:] + f[:j] + (0, s), n - 1, ()) for j in range(n - 2)]


if __name__ == "__main__":
    n = int(sys.argv[1]); spec = sys.argv[2]; nodes = int(sys.argv[3]); seeds = int(sys.argv[4])
    W = World(n)
    rows = std_kernel(n) if spec == "std" else kernel_from_lengths(n, [int(ch) for ch in spec])
    k = len(rows); G = sum(n - 1 - r[1] for r in rows); v = k - G
    CONST = math.factorial(n) + math.factorial(n - 1) + math.factorial(n - 2) + n - 3
    target = CONST + (math.factorial(n - 2) - v) / (n - 2)
    print(f"n={n} kernel rows={k} charge={G} score={v} -> target length {target}", flush=True)
    for sd in range(seeds):
        t0 = time.time(); order, info = complete(W, rows, nodes, sd)
        print(f"  seed {sd}: {'COMPLETED with ' + str(len(order)) + ' payload blocks' if order else 'no completion'} ({info}, {time.time() - t0:.0f}s)", flush=True)
        if order:
            json.dump(dict(n=n, kernel=[[list(r[0]), r[1]] for r in rows],
                           payload=[[list(W.blocks[b][0]), W.blocks[b][1]] for b in order]),
                      open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certs", f"completion_n{n}_v{v}.json"), "w"))
            break
