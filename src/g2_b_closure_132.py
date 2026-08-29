#!/usr/bin/env python3
"""라운드 132 — `(k, G) = (4, 2)` 유형 B hard core (`B/e=1`, `B/e=2`) 드라이버.

라운드 130·131 이 `A/e=0`·`B/e=0`·`A/e=1` 을 닫았다.  남은 것은 유형 B 둘이고
이 드라이버가 그 **정확한 클래스 집합**을 정의한다.

### 갈래 (정리 131.1 + 정리 132.1)

`LOCK0MODE` 는 `opener₀` 의 lock 에 대한 **구조 모형**이다:

| 모드 | 뜻 | `opener₀` lock | 궤도 조건 |
|---|---|---|---|
| 2 | auto (라운드 131 의미) | 안전할 때만 건다 | 없음 |
| 4 | plain α | **성립한다고 가정** | 없음 |
| 1 | D-α | **성립한다고 가정** | `Q₁ ≠ Q₀` |
| 3 | 모형 T | **성립한다고 가정** | `Q₁ = Q₀` |
| 0 | D-β₀ | **깨진다** | `T₀ = Q₁` (필요조건) |

`ORDPIN` 은 증명된 walk 순서를 못박는다: 1 = α 사슬, 2 = β 둥지.

* **`B/e=1`** — 자유 closer 가 `closer₀` 면 두 lock 이 **무조건**(정리 132.1 포함)이라
  갈래 하나(mode 2, ORDPIN 1).  자유 closer 가 `closer₁` 이면 `opener₀` 의 lock 을
  lock 시점에 판정할 수 없어 **{mode 4, mode 0}** 두 갈래로 망라한다.
  `B/e=1` 에는 반복 궤도가 하나뿐이라 모형 T/D 분해가 없다 — 그래서 mode 1 이 아니라
  **mode 4** 를 쓴다 (mode 1 의 `Q₁ ≠ Q₀` 조건은 `Q₁ = Q₀` 인 walk 을 떨어뜨린다).
  ⇒ 25 분할 × (1 + 2) = **75 클래스**.
* **`B/e=2`** — `{mode 3(T), mode 1(D-α), mode 0(D-β₀)}` 가 망라적이고 `D-β₁` 은
  정리 132.1 로 **공집합**이다.  ⇒ 25 분할 × 3 = **75 클래스**.

합계 **150 클래스**.  `n = 4` 양성 대조가 이 갈래 집합의 망라성을 확인한다
(`src/verify_b_machine_132.py`, 유형 B 등호 walk 434개 전부 덮임, 거짓 기각 0).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
BIN = ROOT / "src" / "g2_cell_132.bin"
SRC = ROOT / "src" / "g2_cell_132.c"
JSONL = OUT / "rr_b_132.jsonl"
NODECAP = 60_000_000_000

ORBCAP, COSTCAP, XCAP, DCAP, EXCCAP, SHCAP = 28, 25, 0, 18, 20, 25


def type_b_splits():
    return [(b1, b2) for b1 in range(1, 6) for b2 in range(1, 6)]


def groups():
    out = []
    for (b1, b2) in type_b_splits():
        # ---- B/e=1 : 자유 closer 가 closer_0 -----------------------------------
        out.append(dict(label=f"B_e1_b{b1}{b2}_P0", subcase="B_e1", split=f"{b1}{b2}",
                        e=1, fout=3, p1=b1, p2=b2, freespec=0b0111, lockspec=0b0101,
                        revspec=0b0010, lock0mode=2, ordpin=1, branch="P0"))
        # ---- B/e=1 : 자유 closer 가 closer_1 (alpha / beta) ---------------------
        for lm, pin, tag in ((4, 1, "P1a"), (0, 2, "P1b")):
            out.append(dict(label=f"B_e1_b{b1}{b2}_{tag}", subcase="B_e1",
                            split=f"{b1}{b2}", e=1, fout=3, p1=b1, p2=b2,
                            freespec=0b1101, lockspec=0b0101, revspec=0b1000,
                            lock0mode=lm, ordpin=pin, branch=tag))
    for (b1, b2) in type_b_splits():
        # ---- B/e=2 : Model T / D-alpha / D-beta0 --------------------------------
        for lm, pin, tag in ((3, 1, "T"), (1, 1, "Da"), (0, 2, "Db")):
            out.append(dict(label=f"B_e2_b{b1}{b2}_{tag}", subcase="B_e2",
                            split=f"{b1}{b2}", e=2, fout=4, p1=b1, p2=b2,
                            freespec=0b1111, lockspec=0b0101, revspec=0b1010,
                            lock0mode=lm, ordpin=pin, branch=tag))
    return out


def build():
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        subprocess.run(["gcc", "-O2", "-o", str(BIN), str(SRC)], check=True)


def argv_of(g, nodecap=NODECAP):
    return [str(v) for v in [
        1, ORBCAP, COSTCAP, XCAP, g["fout"], g["fout"], g["e"], DCAP, EXCCAP, 1,
        g["p1"], g["p2"], SHCAP, ORBCAP + g["e"], 0, 0, 0, 0, nodecap, 1,
        g["freespec"], 1, g["lockspec"], g["revspec"], g["lock0mode"], g["ordpin"]]]


def lineage():
    """§ 감사 — 실행 계보: 소스 커밋, 소스/바이너리 해시."""
    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                                    capture_output=True, text=True,
                                    check=True).stdout.strip())
    except Exception:
        commit, dirty = None, None
    return dict(source_commit=commit, worktree_dirty=dirty,
                source_sha256=sha(SRC), binary_sha256=sha(BIN),
                t121_binary_sha256=sha(ROOT / "src" / "g2_cell_132_t121.bin"),
                driver_sha256=sha(Path(__file__)),
                gcc="gcc -O2", target="TARGET=122 (compiled-in default)")


def done():
    if not JSONL.exists():
        return set()
    return {json.loads(l)["label"] for l in JSONL.read_text().splitlines() if l.strip()}


def run(g, nodecap=NODECAP, record=True):
    t0 = time.time()
    p = subprocess.run([str(BIN)] + argv_of(g, nodecap), capture_output=True,
                       text=True, check=True)
    lines = p.stdout.strip().splitlines()
    row = json.loads(lines[0])
    row.update({k: g[k] for k in ("label", "subcase", "split", "branch")})
    row["nodecap"] = nodecap
    row["seconds"] = round(time.time() - t0, 1)
    if row["verdict"] == "SAT" and len(lines) > 1:
        row["witness"] = json.loads(lines[1])
    if record:
        with JSONL.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def main(nodecap=NODECAP, only=None):
    build()
    have = done()
    gs = [g for g in groups() if not only or g["subcase"] in only]
    print(f"{len(gs)} runs planned", flush=True)
    for g in gs:
        if g["label"] in have:
            continue
        r = run(g, nodecap)
        print("%-22s nodes=%15s passes=%3d %-14s %8.1fs"
              % (r["label"], f'{r["nodes"]:,}', r["best_passes"], r["verdict"],
                 r["seconds"]), flush=True)
        if r["verdict"] == "SAT":
            print("!!! SAT in", r["label"], flush=True)
            return


if __name__ == "__main__":
    import sys
    from collections import Counter
    if len(sys.argv) > 1 and sys.argv[1] == "plan":
        gs = groups()
        print(json.dumps(dict(total_runs=len(gs),
                              by_subcase=dict(Counter(g["subcase"] for g in gs)),
                              by_branch=dict(Counter(g["branch"] for g in gs)),
                              lineage=lineage()), indent=1))
    else:
        only = None
        cap = NODECAP
        for a in sys.argv[1:]:
            if a.isdigit():
                cap = int(a)
            else:
                only = set(a.split(","))
        main(cap, only)
