#!/usr/bin/env python3
"""Round 155 -- is the H.tight domain (g = 0 and d = 0) actually satisfied by
the two rows the certified-only census leaves standing, and by nothing else it
is applied to?

This reads r152/certs/census_152.json -- the census computed from independently
certified capacities only -- and checks, for every row it does NOT strictly
close, whether g = 0 and d = 0.  It then instantiates every quantity H.tight
mentions for each such row, purely from the row coordinates and the identities

    P = 120 + G,   K = G + 1 - 2g,   c = G - 2g - d,   d = K - 1 - c,
    chain ports = P - 5c = 120 + G - 5c = required,
    |F| = 120 - (P - 5c) = 5c - G,

so that the arithmetic can be read off rather than trusted.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    cen = json.loads((ROOT / "r152" / "certs" / "census_152.json").read_text())
    rows = []
    for L, v in cen["layers"].items():
        for r in v["non_strict"]:
            rows.append((L, r))
    out = dict(source="r152/certs/census_152.json", rows=[])
    for L, r in rows:
        G, g, c, d = r["G"], r["g"], r["c"], r["d"]
        k, Z, H, Bs = r["k"], r["Z"], r["H"], r["Bstar"]
        D2, Qs, h = r["D2"], r["Qs"], r["h"]
        P = 120 + G
        K = G + 1 - 2 * g
        chain_ports = P - 5 * c
        Fsize = 120 - chain_ports
        e = dict(
            layer=L, verdict=r["verdict"], required=r["required"],
            coords=dict(k=k, Z=Z, H=H, Bstar=Bs, G=G, g=g, c=c, d=d,
                        D2=D2, Qs=Qs, h=h),
            in_H_tight_domain=(g == 0 and d == 0),
            P=P, K=K, K_equals_c_plus_1=(K == c + 1), c_equals_G=(c == G),
            R_int_forced_zero_by_g=(g == 0),
            nonpure_components=d + 1,
            pure_circuits=c,
            chain_ports=chain_ports,
            chain_ports_equals_required=(chain_ports == r["required"]),
            F_size=Fsize, four_c=4 * c, F_equals_4c=(Fsize == 4 * c),
            deficit_budget_D_sum=5 * k - G,
            token_budget=Bs,
            cell="|".join(map(str, (Bs, 5 * k - G, min(D2, 2 * g),
                                    min(Qs, 2 * g),
                                    min(max(0, Z - Qs), 2 * g), H))))
        out["rows"].append(e)
    out["non_strict_rows"] = len(rows)
    out["all_in_domain"] = all(e["in_H_tight_domain"] for e in out["rows"])
    out["all_arithmetic_ok"] = all(
        e["K_equals_c_plus_1"] and e["c_equals_G"]
        and e["chain_ports_equals_required"] and e["F_equals_4c"]
        for e in out["rows"] if e["in_H_tight_domain"])
    out["ok"] = out["all_in_domain"] and out["all_arithmetic_ok"]
    (ROOT / "r155" / "certs" / "row_domain_155.json").write_text(
        json.dumps(out, indent=1) + "\n")
    for e in out["rows"]:
        print(f"  {e['layer']} {e['verdict']}: {json.dumps(e['coords'])}")
        print(f"      domain(g=0,d=0)={e['in_H_tight_domain']} P={e['P']} "
              f"K={e['K']}(=c+1:{e['K_equals_c_plus_1']}) c=G:{e['c_equals_G']} "
              f"nonpure={e['nonpure_components']} circuits={e['pure_circuits']}")
        print(f"      chain ports={e['chain_ports']} (=required "
              f"{e['required']}: {e['chain_ports_equals_required']}) "
              f"|F|={e['F_size']} 4c={e['four_c']} ({e['F_equals_4c']}) "
              f"cell={e['cell']} D_sum={e['deficit_budget_D_sum']}")
    print("all in domain:", out["all_in_domain"],
          " arithmetic ok:", out["all_arithmetic_ok"])
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
