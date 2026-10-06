#!/usr/bin/env python3
"""Large-neighbourhood repair toward n = 7, kernel score 15 (length 5905).
Base: verified 5906 structure (score-10 kernel, 124 payload blocks, certs/base5906.json).
1. Enumerate single-special extensions of the base kernel by appending and/or prepending rows with
   total score gain exactly +5 (distinct words).
2. Screen: divisibility, orphan classes.
3. Repair: flow-completion CP-SAT where payload blocks of the base forest far (graph distance > d)
   from the conflict set are FIXED (chosen, same owned classes), the rest free, base used as hint.
Any solution is checked by flowsat.verify (independent forest check) and rebuilt as a route."""
import sys, os, json, time, itertools, random
from collections import deque
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from complete import World, canon
from candcore import analyse
from kernels import next_start
from flowsat import verify

n = 7; W = World(n)
base = json.load(open(os.path.join(HERE, "..", "certs", "base5906.json")))
rows0 = [(tuple(r[0]), r[1], tuple(r[2])) for r in base["rows"]]
pay0 = set(base["payload"])
s = rows0[0][0][-1]
allstarts = [p + (s,) for p in itertools.permutations([t for t in range(n) if t != s])]


def pred(q, l):
    return [p for p in allstarts if next_start(p, l, n) == q]


def extensions(maxadd=12):
    words0 = {canon(r[0][:n - 1]) for r in rows0}
    out = []
    # append
    def app(p, seq, gain, words, acc):
        if len(seq) >= maxadd: return
        w = canon(p[:n - 1])
        if w in words: return
        for l in (6, 4, 5):
            g = gain + l - 5
            if g == 5: acc.append(("app", tuple(seq + [l])))
            if g + (maxadd - len(seq) - 1) >= 5:
                app(next_start(p, l, n), seq + [l], g, words | {w}, acc)
    acc = []
    app(next_start(rows0[-1][0], rows0[-1][1], n), [], 0, words0, acc)
    # prepend
    def pre(q, seq, gain, words, acc):
        if len(seq) >= maxadd: return
        for l in (6, 4, 5):
            for p in pred(q, l):
                w = canon(p[:n - 1])
                if w in words: continue
                g = gain + l - 5
                if g == 5: acc.append(("pre", tuple([(p, l)] + seq)))
                if g + (maxadd - len(seq) - 1) >= 5:
                    pre(p, [(p, l)] + seq, g, words | {w}, acc)
    pre(rows0[0][0], [], 0, words0, acc)
    return acc


def build_rows(ext):
    kind, seq = ext
    if kind == "app":
        rows = list(rows0); p = next_start(rows0[-1][0], rows0[-1][1], n)
        for l in seq: rows.append((p, l, ())); p = next_start(p, l, n)
        return rows
    return [(p, l, ()) for p, l in seq] + list(rows0)


def repair(rows, d, tl, workers=4):
    A = analyse(W, rows)
    if A["stats"]["zero_deg_classes"]: return "ORPHAN", None, A
    U = A["U"]; Us = set(U); cand = set(A["cand"]); P = len(U) // (n - 2)
    vis_new = set(range(W.C)) - Us
    kb = A["kb"]
    conflict = {b for b in pay0 if b in kb or any(c in vis_new for c in W.bcls[b])}
    # block adjacency inside the base payload
    byc = {}
    for b in pay0:
        for c in W.bcls[b]: byc.setdefault(c, []).append(b)
    dist = {b: 0 for b in conflict}; q = deque(conflict)
    while q:
        b = q.popleft()
        if dist[b] >= d: continue
        for c in W.bcls[b]:
            for b2 in byc.get(c, []):
                if b2 not in dist: dist[b2] = dist[b] + 1; q.append(b2)
    fixed = {b for b in pay0 - set(dist) if b in cand}
    m = cp_model.CpModel()
    candl = sorted(cand)
    x = {b: m.NewBoolVar("") for b in candl}
    own = {}; att = {}; inner = {}
    for b in candl:
        cu = [c for c in W.bcls[b] if c in Us]
        inner[b] = len(cu) == n - 1
        for c in cu: own[c, b] = m.NewBoolVar(""); m.AddImplication(own[c, b], x[b])
        m.Add(sum(own[c, b] for c in cu) == (n - 2) * x[b])
        if inner[b]:
            for c in cu: att[b, c] = m.NewBoolVar(""); m.Add(own[c, b] + att[b, c] == x[b])
    bycl = {c: [] for c in U}
    for (c, b) in own: bycl[c].append(b)
    for c in U: m.AddExactlyOne(own[c, b] for b in bycl[c])
    m.Add(sum(x.values()) == P)
    for b in fixed: m.Add(x[b] == 1)
    for b in candl: m.AddHint(x[b], 1 if b in pay0 and b not in conflict else 0)
    infl = {b: [] for b in candl}; outf = {b: [] for b in candl}
    for c in U:
        for b2 in [b2 for b2 in bycl[c] if (b2, c) in att]:
            col = []
            for b in bycl[c]:
                if b == b2: continue
                v = m.NewIntVar(0, P, ""); m.Add(v <= P * own[c, b])
                col.append(v); infl[b2].append(v); outf[b].append(v)
            m.Add(sum(col) <= P * att[b2, c])
    for b in candl:
        if inner[b]: m.Add(sum(infl[b]) == x[b] + sum(outf[b]))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tl; sv.parameters.num_workers = workers
    st = sv.Solve(m)
    sol = [b for b in candl if sv.Value(x[b])] if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    return sv.StatusName(st), sol, dict(conflict=len(conflict), free=len(cand) - len(fixed), fixed=len(fixed))


if __name__ == "__main__":
    tl = float(sys.argv[1]); d = int(sys.argv[2]); maxc = int(sys.argv[3])
    exts = extensions()
    print(f"extensions with gain +5: {len(exts)}", flush=True)
    random.Random(0).shuffle(exts)
    screened = []
    for e in exts:
        rows = build_rows(e)
        A = analyse(W, rows)
        if A["stats"]["zero_deg_classes"] == 0: screened.append((e, rows))
    print(f"pass orphan screen: {len(screened)}", flush=True)
    for e, rows in screened[:maxc]:
        t0 = time.time(); st, sol, info = repair(rows, d, tl)
        line = dict(ext=(e[0], [x if isinstance(x, int) else x[1] for x in e[1]]), status=st, sec=round(time.time() - t0, 1), **info)
        if sol:
            ok, why = verify(W, rows, sol, n); line.update(cert=ok, why=why)
            if ok:
                json.dump(dict(n=n, rows=[[list(r[0]), r[1], list(r[2])] for r in rows], payload=sol),
                          open(os.path.join(HERE, "..", "certs", "completion_5905_candidate.json"), "w"))
        print(json.dumps(line), flush=True)
        if sol and line.get("cert"): break
