#!/usr/bin/env python3
"""Round T -- exact ledger of a plan in run language, computed from the cyclic trail words and the plan only.
L = 46149 + J,  J = sum over openings (3 - c(cut)) + sum over joins (w - 3),  w = 8 - (overlap of the last
permutation of the previous piece with the first permutation of the next).  usage: plan_ledger.py SEL TSV BASE PLAN... OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model
N = 8
def ov(a, b, m):
    for k in range(m, 0, -1):
        if a[-k:] == b[:k]: return k
    return 0
def ledger(cyc, planp):
    ev = []
    for l in open(planp).read().split("\n")[1:]:
        p = l.split()
        if p: assert p[0] == "O"; ev.append((int(p[1]), int(p[2]), int(p[3])))
    rows = []; prev = None; total = 0
    for t, s, g in ev:
        c = cyc[t]; R = len(c); piece = (c[s:] + c * 2)[:R + N - g]
        assert model.isperm(piece[:N]) and model.isperm(piece[-N:])
        # the dropped cyclic windows: the g - 1 windows before s
        d = c + c; dropped = [d[(s - q) % R:(s - q) % R + N] for q in range(1, g)]; assert not any(model.isperm(x) for x in dropped)
        runs = model.runs_of(c); idx = [r[0] for r in runs].index(s) if s in [r[0] for r in runs] else None
        row = dict(trail=t, kind="D" if R == 384 else "W", start=s, g=g, opening_cost=3 - g, start_is_run_start=idx is not None, run_index=idx,
                   cut_link_weight=(runs[idx - 1][2] if idx is not None else None), cut_link_dup=(runs[idx - 1][3] if idx is not None else None),
                   first_perm=piece[:N], last_perm=piece[-N:])
        if prev is None: row.update(join_overlap8=None, join_weight=None, join_cost=None); total += len(piece)
        else:
            k = ov(prev, piece[:N], 7); row.update(join_overlap8=k, join_weight=N - k, join_cost=N - k - 3, join_overlap5=ov(prev[-5:], piece[:5], 5)); total += len(piece) - k
        prev = piece[-N:]; rows.append(row)
    oc = sum(r["opening_cost"] for r in rows); jc = sum(r["join_cost"] for r in rows[1:])
    return dict(plan=os.path.basename(planp), events=rows, opening_cost=oc, join_cost=jc, J=oc + jc, length=total, length_formula=46149 + oc + jc,
                join_cost_histogram={str(k): sum(1 for r in rows[1:] if r["join_cost"] == k) for k in sorted({r["join_cost"] for r in rows[1:]})})
if __name__ == "__main__":
    a = sys.argv[1:]; cyc = model.load(*a[:3]); out = [ledger(cyc, p) for p in a[3:-1]]
    for L in out:
        print(L["plan"], "opening", L["opening_cost"], "join", L["join_cost"], "J", L["J"], "length", L["length"], L["length_formula"], L["join_cost_histogram"])
        for r in L["events"]: print("  t%2d %s start %5d g%d run %4s cutw %s dup %s | join ov8 %s w %s cost %s | %s .. %s" % (r["trail"], r["kind"], r["start"], r["g"], r["run_index"], r["cut_link_weight"], r["cut_link_dup"], r["join_overlap8"], r["join_weight"], r["join_cost"], r["first_perm"], r["last_perm"]))
    json.dump(out, open(a[-1], "w"), indent=1)
