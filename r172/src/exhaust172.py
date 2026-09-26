#!/usr/bin/env python3
"""Round 172 V2 (EXPERIMENTAL) -- EXHAUSTIVE check of the R1 theorem on small cells.

Uses only the model definitions (routeb164 geometry and charging rules) and
the proven feasibility prune (f) (H.feas: removes only prefixes that cannot
reach final deficit <= dmax).  No certificate, no historical value.

For a target cell K every legal walk W from 123456 with final deficit <= dmax
is enumerated.  For EVERY split index m of EVERY such W it checks, directly:

  T1  0 <= r_W <= t                               (Lemma 3a)
  T2  0 <= final_S <= d0 + 5 r_W                  (Lemma 3b)
  T3  identities I1, I2 exactly and I3 (e_S <= e_W,suffix; a, bb, h equal)
  T4  S is a LEGAL walk under the branch budgets (t - r_W, Res): every step
      re-checked with S's own history (E stays in orbit, budgets, e-charge,
      token charge <= remaining)                  (Lemma 1)
  T5  the S6 relabelling g with g(w_m) = 123456 maps S to a walk that starts
      at port 0, has the same move kinds/costs at every step, preserves the
      same-orbit / same-hexagon relation on all pairs, and has identical
      standalone accounting                       (H.wlog, made concrete)
  T6  |S| <= cap(t - r_W, d0 + 5 r_W, Res) with cap computed EXACTLY by the
      same enumeration (skipped, and counted, when that cell is too large)
  T7  n <= m - 1 + max_{r in Live(s)} cap(branch r)   (the R1 leaf statement)

Exact capacities are memoised in r172/certs/v2/exact_caps.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
import routeb164 as R                                             # noqa: E402

sys.setrecursionlimit(20000)
CAPS = ROOT / "r172/certs/v2/exact_caps.json"


class Limit(Exception):
    pass


def enumerate_cell(cell, limit, collect=False):
    """(status, exact cap, nodes, valid walks[list of port lists] or None)."""
    b, dmax, amax, bmax, emax, hmax = cell
    phm = {R.ORB[0]: {R.PHASE[0]}}
    hexc = {R.HEX[0]: 1}
    path = [0]
    st = dict(nodes=0, cap=0)
    walks = [] if collect else None

    def rec(v, corb, ports, tok, au, bu, eu, hu, deficit):
        st["nodes"] += 1
        if st["nodes"] > limit:
            raise Limit
        if deficit <= dmax:
            if ports > st["cap"]:
                st["cap"] = ports
            if collect:
                walks.append(list(path))
        if not R.feas_greedy(phm, corb, tok, dmax):
            return
        for t, kind, cost in R.MOVES[v]:
            q = R.ORB[t]
            ph = phm.get(q)
            if ph is not None and R.PHASE[t] in ph:
                continue
            if kind == "E" and q != corb:
                continue
            if kind == "A" and au >= amax:
                continue
            if kind == "B" and bu >= bmax:
                continue
            if kind == "H" and hu + cost > hmax:
                continue
            newhex = R.HEX[t] not in hexc
            se = 0
            if not newhex and kind not in ("A", "B"):
                if eu >= emax:
                    continue
                se = 1
            fresh = ph is None
            c = 0 if (kind == "E" or fresh) else 1
            if c > tok:
                continue
            if fresh:
                phm[q] = {R.PHASE[t]}
            else:
                phm[q].add(R.PHASE[t])
            hexc[R.HEX[t]] = hexc.get(R.HEX[t], 0) + 1
            path.append(t)
            rec(t, q, ports + 1, tok - c, au + (kind == "A"), bu + (kind == "B"),
                eu + se, hu + (cost if kind == "H" else 0),
                deficit + (4 if fresh else -1))
            path.pop()
            hexc[R.HEX[t]] -= 1
            if hexc[R.HEX[t]] == 0:
                del hexc[R.HEX[t]]
            if fresh:
                del phm[q]
            else:
                phm[q].discard(R.PHASE[t])

    try:
        rec(0, R.ORB[0], 1, b, 0, 0, 0, 0, 4)
    except Limit:
        return "LIMIT", None, st["nodes"], None
    return "EXACT", st["cap"], st["nodes"], walks


class CapTable:
    def __init__(self, limit, path=CAPS):
        self.limit = limit
        self.path = path
        self.t = json.loads(path.read_text()) if path.exists() else {}
        if not self.t and CAPS.exists():            # shared seed, read-only
            self.t = json.loads(CAPS.read_text())

    def get(self, K):
        k = "|".join(map(str, K))
        if K[1] < 0:
            return None
        if k not in self.t and K[0] == 0 and K[1] >= 9:
            return None             # measured: (0,10) alone needs 13.8M nodes
        if k not in self.t or (self.t[k]["status"] == "LIMIT"
                               and self.t[k]["limit"] < self.limit):
            s, cap, n, _w = enumerate_cell(K, self.limit)
            self.t[k] = dict(status=s, cap=cap, nodes=n, limit=self.limit)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.t, indent=0, sort_keys=True) + "\n")
        r = self.t[k]
        return r["cap"] if r["status"] == "EXACT" else None


def account(ports, budget, check_legal):
    """standalone accounting of a walk from its own first port; optional
    legality check against budget=(tok, a, bb, e, h).  Returns dict or error."""
    v0 = ports[0]
    orbs = {R.ORB[v0]: {R.PHASE[v0]}}
    hexs = {R.HEX[v0]}
    tok = a = bb = e = h = 0
    d = 4
    for s, t in zip(ports, ports[1:]):
        kind, cost = R.MOVEMAP[(s, t)]
        q = R.ORB[t]
        fresh = q not in orbs
        if not fresh and R.PHASE[t] in orbs[q]:
            return "repeated phase"
        if kind == "E" and q != R.ORB[s]:
            return "E leaves orbit"
        c = 0 if (kind == "E" or fresh) else 1
        se = 1 if (R.HEX[t] in hexs and kind not in ("A", "B")) else 0
        if check_legal:
            B = budget
            if kind == "A" and a >= B[1]:
                return "A budget"
            if kind == "B" and bb >= B[2]:
                return "B budget"
            if kind == "H" and h + cost > B[4]:
                return "H budget"
            if se and e >= B[3]:
                return "e budget"
            if tok + c > B[0]:
                return "token budget"
        tok += c
        e += se
        a += kind == "A"
        bb += kind == "B"
        h += cost if kind == "H" else 0
        if fresh:
            orbs[q] = {R.PHASE[t]}
            d += 4
        else:
            orbs[q].add(R.PHASE[t])
            d -= 1
        hexs.add(R.HEX[t])
    return dict(tok=tok, a=a, bb=bb, e=e, h=h, deficit=d, n=len(ports))


def relabel(ports):
    """g: symbol map sending PERMS[ports[0]] to '123456'."""
    first = R.PERMS[ports[0]]
    g = {ch: str(i + 1) for i, ch in enumerate(first)}
    return [R.IDX["".join(g[ch] for ch in R.PERMS[p])] for p in ports]


def check_cell(cell, walk_limit, caps, relabel_all=None):
    b, dmax, amax, bmax, emax, hmax = cell
    status, capK, nodes, walks = enumerate_cell(cell, walk_limit, collect=True)
    out = dict(cell="|".join(map(str, cell)), enumeration=status, nodes=nodes)
    if status != "EXACT":
        return out
    out.update(exact_cap=capK, valid_walks=len(walks))
    if relabel_all is None:                  # adaptive: full below 20k walks
        relabel_all = len(walks) <= 20000
    sample_every = 1 if relabel_all else 50
    cnt = dict(relabel_mode="all splits" if relabel_all else "every 50th split",
               splits=0, splits_r_ge_1=0, T6_checked=0, T6_skipped_unknown_cap=0,
               T7_checked=0, T7_skipped=0, relabel_checked=0)
    fails = []
    for W in walks:
        n = len(W)
        # forward prefix accounting of W
        orbs, hexs = {}, set()
        tok = a = bb = e = h = 0
        D = 0
        pref = []
        for i, p in enumerate(W):
            if i:
                kind, cost = R.MOVEMAP[(W[i - 1], p)]
                q = R.ORB[p]
                fresh = q not in orbs
                tok += 0 if (kind == "E" or fresh) else 1
                e += 1 if (R.HEX[p] in hexs and kind not in ("A", "B")) else 0
                a += kind == "A"
                bb += kind == "B"
                h += cost if kind == "H" else 0
            q = R.ORB[p]
            if q in orbs:
                orbs[q].add(R.PHASE[p])
                D -= 1
            else:
                orbs[q] = {R.PHASE[p]}
                D += 4
            hexs.add(R.HEX[p])
            pref.append((tok, a, bb, e, h, D, {k: len(v) for k, v in orbs.items()}))
        finW = pref[-1][5]
        for m in range(n):
            tokm, am, bbm, em, hm, Dm, phc = pref[m]
            t = b - tokm
            d0 = dmax - Dm + 4
            res = (amax - am, bmax - bbm, emax - em, hmax - hm)
            c0 = R.ORB[W[m]]
            P = set(phc) - {c0}
            seen, r = set(), 0
            for p in W[m + 1:]:
                q = R.ORB[p]
                if q in P and q not in seen:
                    r += 1
                seen.add(q)
            S = W[m:]
            cnt["splits"] += 1
            cnt["splits_r_ge_1"] += r > 0
            acc = account(S, (t - r, *res), True)
            if isinstance(acc, str):
                fails.append(("T4", W, m, acc))
                continue
            sufW = (pref[-1][0] - tokm, pref[-1][1] - am, pref[-1][2] - bbm,
                    pref[-1][3] - em, pref[-1][4] - hm)
            if not (0 <= r <= t):
                fails.append(("T1", W, m, r, t))
            if not (0 <= acc["deficit"] <= d0 + 5 * r):
                fails.append(("T2", W, m, acc["deficit"], d0, r))
            if not (acc["deficit"] == finW - Dm + 4 + 5 * r
                    and acc["tok"] == sufW[0] - r and acc["e"] <= sufW[3]
                    and (acc["a"], acc["bb"], acc["h"]) == (sufW[1], sufW[2], sufW[4])):
                fails.append(("T3", W, m))
            if cnt["splits"] % sample_every == 0:
                gS = relabel(S)
                ok = gS[0] == 0 and all(
                    R.MOVEMAP.get((x, y)) == R.MOVEMAP[(u, w)]
                    for (x, y), (u, w) in zip(zip(gS, gS[1:]), zip(S, S[1:])))
                if ok:
                    for i in range(len(S)):
                        for j in range(i + 1, len(S)):
                            if (R.ORB[S[i]] == R.ORB[S[j]]) != (R.ORB[gS[i]] == R.ORB[gS[j]]) \
                                    or (R.HEX[S[i]] == R.HEX[S[j]]) != (R.HEX[gS[i]] == R.HEX[gS[j]]):
                                ok = False
                                break
                        if not ok:
                            break
                if ok:
                    ok = account(gS, (t - r, *res), True) == acc
                cnt["relabel_checked"] += 1
                if not ok:
                    fails.append(("T5", W, m))
            cb = caps.get((t - r, d0 + 5 * r, *res))
            if cb is None:
                cnt["T6_skipped_unknown_cap"] += 1
            else:
                cnt["T6_checked"] += 1
                if len(S) > cb:
                    fails.append(("T6", W, m, len(S), cb))
            live = [q for q in range(t + 1) if d0 + 5 * q >= 0]
            vals = [caps.get((t - q, d0 + 5 * q, *res)) for q in live]
            if live and all(x is not None for x in vals):
                cnt["T7_checked"] += 1
                if n > (m + 1) - 1 + max(vals):
                    fails.append(("T7", W, m, n, vals))
            else:
                cnt["T7_skipped"] += 1
    out.update(cnt, failures=len(fails), first_failures=[str(f)[:300] for f in fails[:5]])
    return out


def main():
    cells = []
    for d in range(0, 5):
        for extra in [(0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0),
                      (0, 0, 0, 1), (1, 0, 1, 0), (0, 0, 0, 2), (2, 1, 1, 0)]:
            cells.append((1, d, *extra))
    for d in range(0, 3):
        for extra in [(0, 0, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]:
            cells.append((2, d, *extra))
    cells += [(3, 0, 0, 0, 0, 0), (3, 1, 0, 0, 0, 0)]
    if len(sys.argv) > 5 and sys.argv[5] == "limit-pass":
        # second pass: only the cells that hit the enumeration limit before
        prev = [r for f in sorted((ROOT / "r172/certs/v2").glob("exhaustive_part*of3.json"))
                for r in json.loads(f.read_text())["rows"]]
        cells = [tuple(int(x) for x in r["cell"].split("|")) for r in prev
                 if r["enumeration"] != "EXACT"]
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    nparts = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    walk_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 3_000_000
    cap_limit = int(sys.argv[4]) if len(sys.argv) > 4 else 3_000_000
    caps = CapTable(cap_limit, ROOT / f"r172/certs/v2/exact_caps_part{part}.json")
    rows = []
    tag = "pass2_" if len(sys.argv) > 5 else ""
    rel = ROOT / f"r172/certs/v2/exhaustive_{tag}part{part}of{nparts}.json"
    rel.parent.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cells):
        if i % nparts != part:
            continue
        t0 = time.time()
        row = check_cell(c, walk_limit, caps)
        row["seconds_noncanonical"] = round(time.time() - t0, 1)
        rows.append(row)
        rel.write_text(json.dumps(dict(walk_limit=walk_limit, cap_limit=cap_limit,
                                       rows=rows), indent=1) + "\n")
        print(json.dumps({k: v for k, v in row.items() if k != "first_failures"}),
              flush=True)


if __name__ == "__main__":
    main()
