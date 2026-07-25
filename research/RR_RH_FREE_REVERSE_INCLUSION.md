# Rh-free 역포함 — 의도한 경로가 닫혔다 (라운드 23)

산출: `outputs/rr_branch_transport_map.json`,
`outputs/rr_rh_free_language_check.json`(라운드22).

## 16. 5단계 중 어디서 실패하는가

| 단계 | 상태 |
|---|---|
| 1. ell=4 Rh-free exact preparation path 선택 | **가능** (관측된 5개) |
| 2. boundary와 visited 구조 transport | **불가능 — 손증명** (`RR_BRANCH_TRANSPORT_EXACT.md`: root의 visited 크기가 6 vs 2) |
| 3. E/F legality 보존 | 2단계 없이는 진술 불가 |
| 4. ell=0 completer와 \(X_h\) tail 연결 | 미도달 |
| 5. same-component/chaining 보존 | 미도달 |

> **2단계에서 확정적으로 실패한다.** §16이 요구한 "어느 단계가
> 실패하는지 명확히 기록하라"에 대한 답이다.

## 현재 지위 정리

| 포함 | 등급 |
|---|---|
| \(\mathcal P_0\subseteq\mathcal P_4\cap\{E,F\}^*\) | **손증명**(라운드22: ell=0에서는 completer=R1이 강제되어 앞선 Rh가 불가능) |
| \(\mathcal P_4\cap\{E,F\}^*\subseteq\mathcal P_0\) | **root-local exhaustive**(길이 2·4·6에서 확인, 길이 6은 라운드21의 예측-후-검증) — **일반 증명 미완료, 의도한 transport 경로는 반증됨** |

**성공 기준 4 평가: 미달성.** 다만 왜 미달성인지가 이번에
정확해졌다 — 상태 수준 transport는 원리적으로 불가능하므로,
언어 동일성을 증명하려면 symbolic 수준에서 직접 논증하는
다른 방법이 필요하다.
