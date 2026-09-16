#!/usr/bin/env python3
"""Round 163 phase 5 -- hidden load-bearing claims in the census.

The census (r152/src/rows152.py) is a machine node, but the SHAPE of its row
space and the caps inside its three capacity models are hand-proof statements.
Round 158 found two of them (the piece-model lower bounds a >= D2-d and
a+bb >= D2+Qs-d) missing from every DAG `what`.  This module repeats that audit
for the whole row generator.

It reimplements the census independently -- same certified capacity tables,
freshly written enumeration and bounds -- with every candidate assumption on a
switch.  A constraint is LOAD-BEARING exactly when turning it off re-opens
rows.  With nothing switched off the reimplementation must reproduce the stored
certificate (1,607 strictly closed + 2 equality rows) or the whole ablation is
worthless.
"""
from __future__ import annotations
import json, re, sys, time
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY = ROOT / "r152" / "certs" / "verify_all_c152.json"
VPIECE = ROOT / "r152" / "certs" / "verify_piece_c152.json"
DAG = ROOT / "r162" / "certs" / "dag_162.json"
HEXCAP, NEG = 120, -10 ** 9
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
CERT, PCERT = {}, {}

# Every candidate assumption, with the file:line in the audited row generator
# that enforces it and the DAG node that ought to own it.
CLAIMS = {
    "G<=5k":        ("r152/src/rows152.py:47-49", "H.models (r149 Lemma 1.1)"),
    "G=2g+c+d":     ("r152/src/rows152.py:50-52", "H.extract / H.incidence"),
    "sigma>=0":     ("r152/src/rows152.py:61-63", "H.extract Claim 4"),
    "t=k+Z+H+B*":   ("r152/src/rows152.py:55-59", "H.master"),
    "1<=h<=H":      ("r152/src/rows152.py:58",    "H.master (H is the COST)"),
    "D2<=2g":       ("r152/src/rows152.py:56",    "H.samehex + H.incidence"),
    "D2>=0":        ("r152/src/rows152.py:56",    "H.envelope (Z = z - D2)"),
    "Qs<=Z":        ("r152/src/rows152.py:60",    "H.samehex"),
    "Qs<=2g-D2":    ("r152/src/rows152.py:60",    "H.samehex + H.incidence"),
    "required=120+G-5c": ("r152/src/rows152.py:69", "H.extract Claim 1"),
    "a<=D2":        ("r152/src/rows152.py:212",   "H.envelope"),
    "bb<=Qs":       ("r152/src/rows152.py:212",   "H.envelope"),
    "e<=Z-Qs":      ("r152/src/rows152.py:213",   "H.envelope"),
    "a+bb+e<=2g":   ("r152/src/rows152.py:210",   "H.extract (5) + H.incidence"),
    "a>=D2-d":      ("r152/src/rows152.py:176",   "H.envelope (piece LOWER)"),
    "a+bb>=D2+Qs-d": ("r152/src/rows152.py:179",  "H.envelope (piece LOWER)"),
    "sigma<=B*":    ("r152/src/rows152.py:60",    "H.extract Claim 4"),
    "model:piece":  ("r152/src/rows152.py:204",   "H.models + C.piececaps"),
    "model:split":  ("r152/src/rows152.py:205",   "H.models + C.chaincaps"),
    "model:merged": ("r152/src/rows152.py:217",   "H.models + C.chaincaps"),
}


# Some single switches are MASKED by a neighbouring constraint (dropping
# D2 <= 2g alone leaves Qs <= 2g - D2 to empty the same rows).  These bundles
# test the assumption that actually shapes the row space.
COMBOS = {
    "bundle:samehex+incidence row budget":
        ("D2<=2g", "Qs<=Z", "Qs<=2g-D2"),
    "bundle:Qs caps": ("Qs<=Z", "Qs<=2g-D2"),
    "bundle:envelope upper bounds": ("a<=D2", "bb<=Qs", "e<=Z-Qs"),
    "bundle:piece lower bounds": ("a>=D2-d", "a+bb>=D2+Qs-d"),
}


def load():
    for row in json.loads(VERIFY.read_text())["rows"]:
        if row["status"] in GOOD:
            CERT[tuple(int(x) for x in row["cell"].split("|"))] = row["cap"]
    for row in json.loads(VPIECE.read_text())["rows"]:
        if row["status"] in GOOD:
            PCERT[(row["b"], row["d"], row["fp"], row["lp"])] = row["cap"]


def CC(b, d, a, bb, e, h=0):
    v = CERT.get((b, d, a, bb, e, h))
    return HEXCAP + a + bb + e if v is None else v


def PC(b, d, fp, lp):
    if b < 0 or d < 0:
        return HEXCAP
    v = PCERT.get((b, d, fp, lp))
    if v is None:
        return HEXCAP
    return None if v < 0 else v


@lru_cache(maxsize=4_000_000)
def best(n, b, D, a, bb, e, tot):
    """split model: n chains sharing the budgets."""
    r = NEG
    for xa in range(min(a, tot) + 1):
        for xb2 in range(min(bb, tot - xa) + 1):
            for xe in range(min(e, tot - xa - xb2) + 1):
                for xb in range(b + 1):
                    for xd in range(D + 1):
                        v = CC(xb, xd, xa, xb2, xe)
                        if n == 1:
                            if xb == b and xd == D:
                                r = max(r, v)
                            continue
                        q = best(n - 1, b - xb, D - xd, a - xa, bb - xb2,
                                 e - xe, tot - xa - xb2 - xe)
                        if q > NEG // 2:
                            r = max(r, v + q)
    return r


def best_chain(m, btot, Dtot, nmark):
    @lru_cache(maxsize=None)
    def go(j, b, d, a, forced_fp):
        if j == m:
            return 0 if (a == 0 and not forced_fp) else NEG
        if a > m - j - 1:
            return NEG
        bv = NEG
        for fp in ((1,) if forced_fp else (0, 1)):
            for lp in (0, 1):
                for bb in range(b + 1):
                    for dd in range(d + 1):
                        v = PC(bb, dd, fp, lp)
                        if v is None:
                            continue
                        r = go(j + 1, b - bb, d - dd, a, 0)
                        if r > NEG // 2:
                            bv = max(bv, v + r)
                        if j < m - 1 and a > 0:
                            if lp:
                                r = go(j + 1, b - bb, d - dd, a - 1, 0)
                                if r > NEG // 2:
                                    bv = max(bv, v + r)
                            r = go(j + 1, b - bb, d - dd, a - 1, 1)
                            if r > NEG // 2:
                                bv = max(bv, v + r)
        return bv
    r = go(0, btot, Dtot, nmark, 0)
    go.cache_clear()
    return r


COORD = ("k", "Z", "H", "Bstar", "G", "g", "c", "d", "D2", "Qs", "h")


def rows(t, off=()):
    out = []
    kmin0 = 0
    for G in range(0, 5 * t + 1):
        klo = 0 if "G<=5k" in off else (G + 4) // 5
        for k in range(klo, t + 1):
            if "G<=5k" not in off and G > 5 * k:
                continue
            ghi = G // 2 if "G=2g+c+d" not in off else 5 * t
            for g in range(0, ghi + 1):
                crange = (range(0, G - 2 * g + 1) if "G=2g+c+d" not in off
                          else range(0, G + 1))
                for c in crange:
                    d = G - 2 * g - c
                    if d < 0 and "G=2g+c+d" not in off:
                        continue
                    d = max(d, 0)
                    z = 2 * g + d
                    for Z in range(0, t - k + 1):
                        D2 = z - Z
                        if "D2>=0" not in off and D2 < 0:
                            continue
                        if "D2<=2g" not in off and D2 > 2 * g:
                            continue
                        D2 = max(D2, 0)
                        for H in range(0, t - k - Z + 1):
                            Bs = t - k - Z - H
                            if "t=k+Z+H+B*" in off:
                                Bs += 1
                            if "1<=h<=H" in off:
                                hs = list(range(0, H + 3))
                            else:
                                hs = [0] if H == 0 else list(range(1, H + 1))
                            qhi = Z if "Qs<=Z" not in off else 5 * t
                            if "Qs<=2g-D2" not in off:
                                qhi = min(qhi, 2 * g - D2)
                            for Qs in range(0, max(qhi, -1) + 1):
                                shi = Bs + (2 if "sigma<=B*" in off else 0)
                                for s in range(0, shi + 1):
                                    Dsum = 5 * k - G + 5 * s
                                    if Dsum < 0:
                                        if "sigma>=0" not in off:
                                            continue
                                        Dsum = 0
                                    req = 120 + G - 5 * c
                                    if "required=120+G-5c" in off:
                                        req -= 5      # one more pure circuit
                                    for h in hs:
                                        out.append(dict(
                                            t=t, k=k, Z=Z, H=H, Bstar=Bs, G=G,
                                            g=g, c=c, d=d, D2=D2, Qs=Qs, s=s,
                                            h=h, m_max=z + 1 + h, required=req,
                                            D_sum=Dsum, b_sum=Bs - s))
    return out


def bounds(variants, off=()):
    req = variants[0]["required"]
    res = {}
    BIG = 10 ** 3
    if "model:piece" not in off:
        pv = NEG
        for r in variants:
            nA = 0 if "a>=D2-d" in off else max(0, r["D2"] - r["d"])
            badmax = max(0, r["Z"] - r["Qs"])
            nmark = max(0, nA - badmax)
            m_lo = (1 if "a+bb>=D2+Qs-d" in off
                    else max(1, r["D2"] + r["Qs"] - r["d"] + 1))
            if m_lo > r["m_max"]:
                continue
            for m in range(m_lo, r["m_max"] + 1):
                v = best_chain(m, r["b_sum"], r["D_sum"], min(nmark, m - 1))
                pv = max(pv, v)
        res["piece"] = pv
    if "model:split" not in off:
        sv = NEG
        for r in variants:
            n = r["d"] + 1 + r["h"]
            if n == 1 and r["s"] != 0:
                continue
            tot = 2 * r["g"] if "a+bb+e<=2g" not in off else 5 * r["t"] + 8
            A = tot if "a<=D2" in off else min(r["D2"], tot)
            B = tot if "bb<=Qs" in off else min(r["Qs"], tot)
            E = tot if "e<=Z-Qs" in off else min(max(0, r["Z"] - r["Qs"]), tot)
            sv = max(sv, best(n, r["b_sum"], r["D_sum"], A, B, E, tot))
        if sv > NEG // 2:
            res["split"] = sv
    if "model:merged" not in off:
        mv = None
        for r in variants:
            if r["H"] == 0 or r["d"] + 1 != 1 or r["s"] != 0:
                continue
            tot = 2 * r["g"] if "a+bb+e<=2g" not in off else 5 * r["t"] + 8
            A = tot if "a<=D2" in off else min(r["D2"], tot)
            B = tot if "bb<=Qs" in off else min(r["Qs"], tot)
            E = tot if "e<=Z-Qs" in off else min(max(0, r["Z"] - r["Qs"]), tot)
            v = CC(r["b_sum"], r["D_sum"], A, B, E, r["H"])
            mv = v if mv is None else max(mv, v)
        if mv is not None:
            res["merged"] = mv
    return req, res


def census(t, off=()):
    groups = {}
    for r in rows(t, off):
        groups.setdefault(tuple(r[c] for c in COORD), []).append(r)
    tally, closers = Counter(), Counter()
    for key, variants in sorted(groups.items()):
        req, res = bounds(variants, off)
        closing = {k: v for k, v in res.items() if v < req}
        if closing:
            tally["STRICTLY_CLOSED"] += 1
            closers[min(closing, key=lambda k: closing[k])] += 1
            continue
        tally["EQUALITY" if res and min(res.values()) == req
              else "SURVIVING"] += 1
    return dict(rows=len(groups), tally=dict(tally), closed_by=dict(closers))


def run(off=(), layers=(0, 1, 2, 3, 4)):
    best.cache_clear()
    tot = Counter()
    per = {}
    for t in layers:
        c = census(t, off)
        per[f"L{867 + t}"] = c
        tot["rows"] += c["rows"]
        for k, v in c["tally"].items():
            tot[k] += v
    return dict(per_layer=per, totals=dict(tot))


# ------------------------------------------------- is the claim in the DAG?
def in_dag_text():
    dag = json.loads(DAG.read_text())["dag"]["nodes"]
    blob = {k: f"{v.get('what')} {v.get('derived_from')}"
            for k, v in dag.items()}
    PAT = {
        "G<=5k": r"G\s*<=\s*5\s*k",
        "G=2g+c+d": r"G\s*=\s*2\s*g\s*\+\s*c\s*\+\s*d|2g\s*\+\s*c\s*\+\s*d",
        "sigma>=0": r"sigma\w*\s*>=\s*0|Claims?\s*3,?\s*4|Claim 4",
        "t=k+Z+H+B*": r"867\s*\+\s*k\s*\+\s*Z\s*\+\s*H\s*\+\s*B",
        "1<=h<=H": r"heavy COUNT h|heavy COST",
        "D2<=2g": r"D2\s*<=\s*2g",
        "D2>=0": r"Z\s*=\s*z\s*-\s*D2|z\s*=\s*2g\s*\+\s*d",
        "Qs<=Z": r"Qs\s*<=\s*min\(Z|Z\s*>=\s*Qs",
        "Qs<=2g-D2": r"Qs\s*<=\s*min\(Z,\s*2g\s*-\s*D2\)|2g\s*-\s*D2",
        "required=120+G-5c": r"P\s*-\s*5c|HEX\s*\+\s*G\s*-\s*r\s*c|120\s*\+\s*G\s*-\s*5",
        "a<=D2": r"a\s*<=\s*D2",
        "bb<=Qs": r"bb\s*<=\s*Qs",
        "e<=Z-Qs": r"e\s*<=\s*Z\s*-\s*Qs",
        "a+bb+e<=2g": r"rep\s*<=\s*R_int\s*<=\s*2g|R_int\s*<=\s*2g",
        "a>=D2-d": r"a\s*>=\s*D2\s*-\s*d",
        "a+bb>=D2+Qs-d": r"a\s*\+\s*bb\s*>=\s*D2\s*\+\s*Qs\s*-\s*d",
        "sigma<=B*": r"0\s*<=\s*sigma\w*\s*<=\s*B|Claim 4",
        "model:piece": r"three upper-bound models|piece",
        "model:split": r"three upper-bound models",
        "model:merged": r"three upper-bound models",
    }
    out, eq = {}, {}
    for name, rx in PAT.items():
        out[name] = sorted(k for k, t in blob.items() if re.search(rx, t))
    for name, rx in EQUIV.items():
        eq[name] = sorted(k for k, t in blob.items() if re.search(rx, t))
    return out, eq


# How each switch acts, so a null result can be told from a masked one.
ROW_SPACE = {"G<=5k", "G=2g+c+d", "sigma>=0", "sigma<=B*", "t=k+Z+H+B*",
             "1<=h<=H", "D2<=2g", "D2>=0", "Qs<=Z", "Qs<=2g-D2"}
# switches whose relaxed rows carry a SMALLER budget than the real row would,
# so the ablation cannot re-open anything and proves nothing either way
CLAMPED = {"sigma>=0", "D2>=0"}
# an equivalent spelling of the same claim, used only to report honestly that
# a claim is present in the DAG under different coordinates
EQUIV = {"G<=5k": r"\(n-1\)O\s*>=\s*P|5\s*O\s*>=\s*P"}


def classify(name, a, base_rows, parts):
    if not a:
        return "NOT_RUN"
    if a.get("load_bearing"):
        return "LOAD_BEARING"
    if any(x in CLAMPED for x in parts):
        return "INCONCLUSIVE_CLAMPED_RELAXATION"
    if all(x in ROW_SPACE for x in parts) and a["rows"] == base_rows:
        return "MASKED_BY_A_NEIGHBOURING_CONSTRAINT"
    return "NOT_LOAD_BEARING_ALONE"


def main():
    t0 = time.time()
    load()
    base = run()
    ok_base = (base["totals"].get("STRICTLY_CLOSED") == 1607
               and base["totals"].get("EQUALITY") == 2
               and base["totals"].get("SURVIVING", 0) == 0)
    abl = {}
    if ok_base:
        for name in list(CLAIMS) + list(COMBOS):
            r = run(COMBOS.get(name, (name,)))
            t = r["totals"]
            abl[name] = dict(
                rows=t["rows"],
                strictly_closed=t.get("STRICTLY_CLOSED", 0),
                equality=t.get("EQUALITY", 0),
                surviving=t.get("SURVIVING", 0),
                rows_reopened=(t.get("SURVIVING", 0)
                               + t.get("EQUALITY", 0) - 2),
                load_bearing=(t.get("SURVIVING", 0) > 0
                              or t.get("EQUALITY", 0) > 2))
    owners, equiv = in_dag_text()
    table = {}
    allclaims = dict(CLAIMS)
    for b, parts in COMBOS.items():
        allclaims[b] = ("+".join(CLAIMS[x][0] for x in parts),
                        "+".join(sorted({CLAIMS[x][1] for x in parts})))
    for name, (where, expected) in allclaims.items():
        a = abl.get(name, {})
        parts = COMBOS.get(name, (name,))
        table[name] = dict(enforced_at=where, expected_owner=expected,
                           verdict=classify(name, a, base["totals"]["rows"],
                                            parts),
                           dag_nodes_stating_an_equivalent_form=equiv.get(
                               name, []),
                           dag_nodes_whose_text_states_it=owners.get(name, []),
                           represented_in_dag=(
                               bool(owners.get(name)) if name in CLAIMS
                               else all(owners.get(x)
                                        for x in COMBOS.get(name, ()))),
                           **a)
    out = dict(
        seconds=round(time.time() - t0, 1),
        certified_chain_cells=len(CERT), certified_piece_cells=len(PCERT),
        baseline=base["totals"],
        baseline_per_layer=base["per_layer"],
        baseline_reproduces_stored_census=ok_base,
        claims=table,
        load_bearing_claims=sorted(k for k, v in table.items()
                                   if v.get("load_bearing")),
        not_load_bearing_here=sorted(k for k, v in table.items()
                                     if v.get("load_bearing") is False),
        load_bearing_but_unrepresented=sorted(
            k for k, v in table.items()
            if v.get("load_bearing") and not v["represented_in_dag"]
            and not v["dag_nodes_stating_an_equivalent_form"]),
        load_bearing_only_in_an_equivalent_form=sorted(
            k for k, v in table.items()
            if v.get("load_bearing") and not v["represented_in_dag"]
            and v["dag_nodes_stating_an_equivalent_form"]),
        verdicts={k: v["verdict"] for k, v in table.items()},
    )
    # the audit succeeds when the baseline reproduces and every switch got a
    # verdict.  FINDINGS are the output, not a failure of the run.
    out["ok"] = ok_base and all(v != "NOT_RUN"
                                for v in out["verdicts"].values())
    (ROOT / "r163" / "certs" / "hidden_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("seconds", "baseline", "baseline_reproduces_stored_census",
                       "verdicts", "load_bearing_but_unrepresented",
                       "load_bearing_only_in_an_equivalent_form", "ok")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
