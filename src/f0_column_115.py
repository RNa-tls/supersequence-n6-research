#!/usr/bin/env python3
"""라운드 115 — `F = 0` 열(k = 0..4)의 하위경우 전수 회계.

`L <= 871` 인 F=0 NR6 walk 이 존재하려면  k + e + x + t <= 5  이고
전체 pass 수가 정확히 120 이어야 한다.  사슬별 용량 `N*(b,g,s)` 를 C 탐색기
(`src/chain_capacity_115.c`) 로 전수 계산한 뒤, 모든 (k,e,x,t,h) 와 모든 예산 분배에
대해  sum_i N*(b_i,g_i,s_i) >= 120  이 가능한지 확인한다.

캡에 걸린 칸은 UNKNOWN 이며 그 하위경우는 **닫히지 않은 것으로** 기록한다.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "chain_capacity_115.bin"
SRC = ROOT / "src" / "chain_capacity_115.c"
NODECAP = 20_000_000_000


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def comps(n, t):
    if t == 1:
        yield (n,)
        return
    for i in range(n + 1):
        for r in comps(n - i, t - 1):
            yield (i,) + r


def cases():
    out = []
    for k in range(5):
        for e in range(6):
            for x in range(6):
                for t in range(1, 6):
                    if k + e + x + t > 5:
                        continue
                    for h in range(e + 1):
                        if t == 1 and h > 0:
                            continue        # 넘길 다른 사슬이 없다
                        out.append(dict(k=k, e=e, x=x, t=t, h=h,
                                        bp=(e - h) + x, gp=2 * h, sp=5 * k))
    return out


def main():
    build()
    cs = cases()
    cells = set()
    for c in cs:
        for bs in comps(c["bp"], c["t"]):
            for gs in comps(c["gp"], c["t"]):
                for ss in comps(c["sp"], c["t"]):
                    for i in range(c["t"]):
                        cells.add((bs[i], gs[i], ss[i]))
    order = sorted(cells, key=lambda z: (z[2] + 5 * z[0] + 5 * z[1], z))
    table, t0 = {}, time.time()
    for b, g, s in order:
        r = json.loads(subprocess.run([str(BIN), str(b), str(g), str(s), str(NODECAP)],
                                      capture_output=True, text=True, check=True).stdout)
        table[f"{b},{g},{s}"] = r
        print(f"  N*({b},{g},{s}) = {r['passes']} passes / {r['orbits']} orbits"
              f"  nodes={r['nodes']:,}{'  CAPPED' if r['capped'] else ''}"
              f"  [{time.time()-t0:.0f}s]", flush=True)

    def N(b, g, s):
        r = table[f"{b},{g},{s}"]
        return (None if r["capped"] else r["passes"])

    rows = []
    for c in cs:
        best, unknown = 0, False
        for bs in comps(c["bp"], c["t"]):
            for gs in comps(c["gp"], c["t"]):
                for ss in comps(c["sp"], c["t"]):
                    tot = 0
                    for i in range(c["t"]):
                        v = N(bs[i], gs[i], ss[i])
                        if v is None:
                            unknown = True
                            tot = None
                            break
                        tot += v
                    if tot is not None and tot > best:
                        best = tot
        rows.append(dict(**c, max_total_passes=best, has_unknown_cell=unknown,
                         closed=(not unknown) and best < 120))
    per_k = {}
    for k in range(5):
        rs = [r for r in rows if r["k"] == k]
        openr = [r for r in rs if not r["closed"]]
        per_k[k] = dict(subcases=len(rs), closed=len(rs) - len(openr),
                        open=len(openr),
                        cell_closed=(len(openr) == 0),
                        worst=max(r["max_total_passes"] for r in rs),
                        open_rows=[{q: r[q] for q in ("e", "x", "t", "h",
                                                      "max_total_passes",
                                                      "has_unknown_cell")}
                                   for r in openr])
    rep = dict(round=115, model="F=0 word-level all-light chain capacity",
               node_cap=NODECAP, cells=len(cells),
               capped_cells=sum(1 for v in table.values() if v["capped"]),
               table=table, subcases=rows, per_k=per_k,
               seconds=round(time.time() - t0))
    (OUT / "rr_f0_column_115.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in range(5):
        v = per_k[k]
        print(f"k={k}: {v['closed']}/{v['subcases']} subcases closed, "
              f"worst total passes {v['worst']}  -> cell "
              f"{'CLOSED' if v['cell_closed'] else 'OPEN'}")


if __name__ == "__main__":
    main()
