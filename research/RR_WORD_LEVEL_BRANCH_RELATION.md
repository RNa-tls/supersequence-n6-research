# Word-level branch relation (라운드 24)

§10은 parity 증명이 끝나기 전에는 이 문제에 과도한 시간을 쓰지
말라고 명시했다. parity가 아직 닫히지 않았으므로 **이번 라운드는
이 항목에 새 계산을 하지 않았다.**

## 현재 지위 (변경 없음)

- 상태 수준 transport는 **불가능**(라운드23 손증명:
  \(\mathrm{visited}(\mathrm{root}_\ell)=\ell+2\)이므로 root(0)과
  root(4)의 방문 집합 크기가 다르고, legality 보존은 그 크기를
  보존해야 한다).
- 따라서 §10이 제안한 약한 형태 — 같은 symbolic word가 두 분기에서
  **각각 독립적으로** exact 실현되는지 — 만이 남는다.
- \(\mathcal P_0=\mathcal P_4\cap\{E,F\}^*\)는 길이 2·4·6에서
  **root-local exhaustive**로 확인됐고(길이 6은 라운드21의
  예측-후-검증), 일반 증명은 **미완료**다.

**미완료 — 지시에 따라 보류.**
