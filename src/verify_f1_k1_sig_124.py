#!/usr/bin/env python3
"""라운드 124 — 서명 이론의 **독립 파이썬 재유도**와 §20 양성 대조.

`src/f1_k1_sig_124.c` 가 쓰는 기하(hexid / orbid / phse / OWORD)를 파이썬에서 **처음부터
다시** 만들고, C 가 뱉은 뿌리 서명 덤프를 파싱해서

* 덤프 줄 수 == 보고된 `roots`  (오탈락 0),
* 서로 다른 fine 서명 수 == 보고된 `distinct_root_signatures`,
* fine 에서 파이썬이 다시 계산한 coarse / ceiling 서명 수 == C 가 보고한 수

를 확인한다.  fine → coarse → ceiling 이 진짜 **몫(quotient)** 임을 보이므로 압축률
사다리 `1 <= fine <= coarse <= ceiling` 이 성립하고, ceiling 이 어떤 건전한 서명의
압축률에도 상한이 된다.
"""
from __future__ import annotations

import itertools
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "src" / "f1_k1_sig_124.bin"
SRC = ROOT / "src" / "f1_k1_sig_124.c"

WORDS = sorted(itertools.permutations(range(6)))
RANK = {w: i for i, w in enumerate(WORDS)}


def sigma(y):
    return y[1:] + y[:1]


def tau(y):
    return (y[1], y[2], y[3], y[4], y[0], y[5])


def geometry():
    """returns (hexid, orbid, phse, oword) exactly as the C build() computes them"""
    hrep, orep = [0] * 720, [0] * 720
    for w, y in enumerate(WORDS):
        z, best = y, w
        for _ in range(5):
            z = sigma(z)
            best = min(best, RANK[z])
        hrep[w] = best
        z, best = y, w
        for _ in range(4):
            z = tau(z)
            best = min(best, RANK[z])
        orep[w] = best
    hmap, omap = {}, {}
    hexid, orbid = [0] * 720, [0] * 720
    for w in range(720):
        hmap.setdefault(hrep[w], len(hmap))
        omap.setdefault(orep[w], len(omap))
        hexid[w] = hmap[hrep[w]]
        orbid[w] = omap[orep[w]]
    assert len(hmap) == 120 and len(omap) == 144
    phse = [0] * 720
    oword = [[0] * 5 for _ in range(144)]
    for w in range(720):
        z = WORDS[orep[w]]
        for i in range(5):
            if RANK[z] == w:
                phse[w] = i
                break
            z = tau(z)
        oword[orbid[w]][phse[w]] = w
    return hexid, orbid, phse, oword


def orbit_hexagon_facts():
    """the two structural facts Round 124 leans on, re-derived independently"""
    hexid, orbid, phse, _ = geometry()
    bad_phase, bad_hex = 0, 0
    for q in range(144):
        ws = [w for w in range(720) if orbid[w] == q]
        if len({phse[w] for w in ws}) != 5:
            bad_phase += 1
        if len({hexid[w] for w in ws}) != 5:
            bad_hex += 1
    perhex = {}
    for w in range(720):
        perhex.setdefault(hexid[w], set()).add(orbid[w])
    return dict(orbits=144, hexagons=120,
                orbits_without_5_distinct_phases=bad_phase,
                orbits_without_5_distinct_hexagons=bad_hex,
                hexagons_not_meeting_6_orbits=sum(1 for v in perhex.values() if len(v) != 6),
                phase_injectivity_implied_by_hexagon_injectivity=(bad_hex == 0))


def parse_fine(line, hexid, oword):
    """(word, b, cost, hub, x, e, frozenset(orbit -> phase mask))"""
    raw = bytes.fromhex(line)
    word = raw[0] | (raw[1] << 8)
    b, cost, hub, xj, rev = raw[2], raw[3], raw[4], raw[5], raw[6]
    om = []
    i = 7
    while i < len(raw):
        q = raw[i] | (raw[i + 1] << 8)
        om.append((q, raw[i + 2]))
        i += 3
    return (word, b, cost, hub, xj, rev, tuple(om))


def coarse_of(fine, hexid, oword):
    word, b, cost, hub, xj, rev, om = fine
    hexes = frozenset(hexid[oword[q][ph]] for (q, m) in om for ph in range(5) if m >> ph & 1)
    orbs = frozenset(q for (q, _) in om)
    return (word, b, cost, hub, xj, rev, hexes, orbs)


def ceiling_of(fine, hexid, oword):
    word, b, _, _, _, _, om = fine
    hexes = frozenset(hexid[oword[q][ph]] for (q, m) in om for ph in range(5) if m >> ph & 1)
    return (word, b, hexes)


def build_bin():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def replay(x=0, e=0, h=0, qcap=119, tbits=22):
    """run the counter with DUMP on and re-derive every count in Python"""
    build_bin()
    args = [str(BIN), "0", str(qcap), "26", "25", str(x), str(e), str(h), "4", "5", "1",
            "100000000000", str(tbits), "1"]
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    lines = p.stdout.splitlines()
    dumped = [l[2:] for l in lines if l.startswith("R ")]
    rep = json.loads(lines[-1])
    hexid, _, _, oword = geometry()
    fines = [parse_fine(l, hexid, oword) for l in dumped]
    return dict(
        reported=rep,
        dumped=len(dumped),
        python_distinct_fine=len(set(fines)),
        python_distinct_coarse=len({coarse_of(f, hexid, oword) for f in fines}),
        python_distinct_ceiling=len({ceiling_of(f, hexid, oword) for f in fines}),
        x_within_budget=all(f[4] <= x for f in fines),
        cost_within_budget=all(f[2] <= 26 for f in fines),
        every_orbit_phase_mask_nonzero=all(m != 0 for f in fines for (_, m) in f[6]),
        orbits_used=sorted({len(f[6]) for f in fines}),
    )


def report(cells=((0, 0, 0), (1, 0, 0), (0, 1, 0))):
    out = dict(geometry=orbit_hexagon_facts(), replays={})
    for (x, e, h) in cells:
        r = replay(x=x, e=e, h=h)
        rep = r.pop("reported")
        r["c_roots"] = rep["roots"]
        r["c_distinct_fine"] = rep["distinct_root_signatures"]
        r["c_distinct_coarse"] = rep["distinct_coarse_signatures"]
        r["c_ceiling"] = rep["floor_signatures"]
        r["agrees"] = (r["dumped"] == r["c_roots"]
                       and r["python_distinct_fine"] == r["c_distinct_fine"]
                       and r["python_distinct_coarse"] == r["c_distinct_coarse"]
                       and r["python_distinct_ceiling"] == r["c_ceiling"])
        out["replays"][f"e{e}_x{x}_H{h}"] = r
    return out


if __name__ == "__main__":
    print(json.dumps(report(), indent=1))
