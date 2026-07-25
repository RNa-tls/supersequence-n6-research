# Endpoint-role automaton — §3 가설 반증 (라운드 24)

산출: `src/build_rr_endpoint_role_automaton.py` ->
`outputs/rr_endpoint_role_automaton.json`.

## 3. 검사한 가설

> zero-charge 사건이 endpoint role의 두 상태를 뒤집고, abandonment
> 직후와 completer 직전의 role이 같으므로 zero-charge 사건 수가
> 짝수다.

## 결과 — 반증됨

시도한 role(계수기가 아니라 독립적으로 정의됨):

\[
\text{role} = (\text{hub 내부인가},\ \text{orbit이 } O_*\text{인가},\
\text{orbit이 이미 다중 방문인가},\ O_*\text{의 방문 phase 수})
\]

| 분기 | role 수 | 전이 수 | zero-charge에서만 뒤집히는가 |
|---|---:|---:|---|
| ell=0 | 19 | 46 | **아니오** |
| ell=4 | 16 | 39 | **아니오** |

## 왜 어떤 role도 성립할 수 없는가 (손증명)

전이가 **사건종류에만** 의존하는 role은 정의상 가법적
\(\mathbb Z/2\) 불변량을 만든다. 그런데
`RR_PREPARATION_R_PARITY_THEOREM.md`의 불가능성 정리가 **가법
불변량으로는 이 parity를 순환 없이 증명할 수 없음**을 손증명한다.

따라서 성립 가능한 role은 **사건종류보다 더 많은 정보에 의존**해야
한다. 이번에 시도한 더 풍부한 role(hub 소속·\(O_*\) 소속·재방문
여부·phase 수)도 일관되게 뒤집히지 않았다.

**§3·§7이 제안한 role/pairing 경로는 반증됨.**
