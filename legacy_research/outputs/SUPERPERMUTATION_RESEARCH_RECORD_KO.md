# n=6 초순열 최단 길이 연구: 전체 연구 기록과 다음 단계

> 마지막 갱신: 2026-07-22  
> 범위: 초순열을 **무반복 순열 워크**로 볼 수 있다는 조건 아래의 하한 연구, 및 그 조건과 무관한 유한 incidence 정리.

## 0. 한 문장 요약

이 연구는 n=6 초순열 최단 길이의 조건부 하한을, 표준 재귀 구성의 역산이 아니라
순열 전이·`E`-궤도·헥사곤 덮개·유한 군 계산으로 재구성한 것이다.

현재 가장 강한 순수 유한 성과는 다음이다.

> **포화 25-`E`-궤도 커버의 genus는 항상 0이고, 다중도는 항상
> \(115\times1+5\times2\)이다.**
>
> 따라서 포트의 weight-2 순열 \(f\)에 대해
> \[
> c(f)=20\iff\text{5-간선 충돌 그래프가 숲이다}.
> \]

이 정리는 초순열 단어나 무반복 가정을 전혀 쓰지 않는다. 다만 전체 목표
`L_6 >= 872`의 조건부 증명은 아직 완결되지 않았다. 남은 핵심은 숲 cover 전체의
port-lift 실패와, fragment가 있는 `F<5` 가지의 부분카세트 상태공간이다.

---

## 1. 연구의 목표와 논리적 범위

### 1.1 목표

`n=6`에서 알려진 872 길이 구성과 맞물려 다음을 보이는 것이 목표다.

\[
L_6=872,
\qquad\text{동치로 } C_{\mathrm{geom}}(6)=1.
\]

여기서 기존 표기 아래

\[
\Phi_n=n!\,n-M_n^{\mathrm{standard}}-C_{\mathrm{geom}}(n),
\qquad
M_n^{\mathrm{standard}}=\sum_{j=1}^{n-1}j^2j!
\]

이다.

### 1.2 조건부 전제: 무반복 순열 워크

아래의 워크 하한은 다음 전제 아래에서 증명된다.

> **NR6 가정.** 최소 n=6 초순열은 720개의 순열을 각각 정확히 한 번씩 순열창으로 방문한다.

이 가정은 데이터와 통상적 직관에는 부합하지만, 일반 최소 초순열에 대해 별도 증명된 정리는 아니다. 따라서 최종 논문의 정확한 논리 형식은 다음이어야 한다.

> **조건부 정리.** NR6 가정 아래 `L_6 >= 872`.

872 길이의 상계 구성은 별도의 재현 가능한 문자열·검증 파일로 접지되어야 한다. 현재 이 workspace에는 고전 표준 873 구성의 독립 생성·검증은 있으나, Egan 872 문자열 자체는 포함되어 있지 않다.

### 1.3 증거 등급

이 기록에서는 다음 네 등급을 엄격히 구분한다.

| 표기 | 의미 |
|---|---|
| **증명됨** | 손증명 또는 유한 완전 탐색으로 닫힌 정리 |
| **유한 계산 인증** | 명시된 유한 상태공간을 코드가 완주한 결과 |
| **실험** | 표본·아카이브·무작위 탐색으로 지지되지만 전수가 아님 |
| **반증됨** | 명시적 반례 또는 완전 계산으로 폐기된 주장 |

---

## 2. 기본 모델과 군 작용

순열을 단어

\[
x=x_0x_1\cdots x_{n-1}
\]

로 쓰고 위치에 대한 우작용을 쓴다.

- 회전
  \[
  r(x)=x_1\cdots x_{n-1}x_0,
  \qquad \sigma(i)=i+1\pmod n;
  \]
- flip
  \[
  \operatorname{flip}(x)=x_2x_3\cdots x_{n-1}x_1x_0,
  \]
  \[
  \tau(i)=i+2\ (i\le n-3),\qquad
  \tau(n-2)=1,\quad\tau(n-1)=0.
  \]

길이 \(\ell\) 회전 패스 뒤 flip으로 생기는 전이는

\[
g_\ell=\sigma^{\ell-1}\tau.
\]

특히

\[
E=g_n=\sigma^{n-1}\tau=(0\ 1\ \cdots\ n-2),
\qquad E(n-1)=n-1.
\]

따라서 `E`의 위수는 \(n-1\)이고, `E`-궤도의 크기는 \(n-1\)이다. `E`가 마지막 위치를 고정하므로 한 `E`-궤도 안의 모든 순열은 마지막 심볼을 공유한다.

n=6에서는 다음 수가 기본 좌표다.

| 대상 | 개수 |
|---|---:|
| 순열 | 720 |
| 회전 헥사곤 \(S_6/\langle\sigma\rangle\) | 120 |
| `E`-궤도 \(S_6/\langle E\rangle\) | 144 |
| `E`-궤도의 크기 | 5 |

핵심 항등식은 우작용 convention에서

\[
\operatorname{flip}\circ r^{-1}=E,
\qquad\text{즉}\qquad
\sigma^{-1}\tau=E.
\]

이다.

---

## 3. 초기에 닫힌 구조 정리들

아래 정리들은 현재 연구의 출발점이며, 각 세부 증명은 기존 원고·검증 코드에 있다.

### 3.1 구성요소와 전이군

**증명됨.** 짝수 n에서 overlap `n-2` 전이 그래프의 성분 수는

\[
f(n)=\frac{(n-1)!}{2^{n/2-1}}.
\]

관련 전이군은

\[
G_n\cong(\mathbb Z_2)^m\rtimes C_m,
\qquad |G_n|=m2^m
\]

형태이며, `G_n`의 자유 작용과 Burnside 계산으로 성분 수 공식을 얻는다. 홀수 n에서는 해당 전이 그래프가 완전 연결이다.

### 3.2 overlap 에지 분포

**증명됨.** 무게/overlap 층의 에지 수는

\[
E_k=(k+1)!-k!=k\,k!.
\]

특히 다음 홀짝 구조가 확인됐다.

- `E_{n-1}`: 100% 외부;
- `E_{n-2}`: 100% 내부;
- `E_{n-3}`: 외부;
- `E_{n-4}`의 내부 비율: \(1/6\).

마지막 비율은 “\(\tau\)의 마지막 쌍 = \(\sigma\)의 첫 쌍” 조건을 24가지 중 4가지로 세어 얻는다.

### 3.3 심볼 보존 보조정리

풀패스 뒤 indecomposable tail \(\pi\in S_w\)가 `E`-궤도의 마지막 심볼을 보존할 필요충분조건은

\[
\boxed{\pi(w-1)=0}.
\]

그러한 indecomposable tail의 수는

\[
\boxed{(w-1)!}
\]

이다. 실제 표는

\[
1,1,2,6,24,120 \qquad(w=1,\ldots,6)
\]

이다. \(\pi(w-1)=0\)이면 어떤 진초기 구간도 0을 포함하지 못하므로 그 구간을 보존할 수 없고, 따라서 자동으로 indecomposable이다.

---

## 4. 정리 A: 덮개 부등식

### 4.1 용어

- **순열 워크**: `n!`개 순열을 각각 정확히 한 번 방문하는 문자열.
- **전이 무게** \(w\): 새로 추가한 문자 수.
- **패스**: 무게 1 회전 전이의 극대 연속 구간. 한 패스는 한 회전 헥사곤 안에 있다.
- **방기** `F`: 패스 끝에서 다음 회전 상대가 아직 미방문인 경우의 수.
- **패스 수** `P`: frag 항등식에 의해
  \[
  P=(n-1)!+F.
  \]
- **스트랜드 수** `S`: 무게 \(\ge3\) 전이로 나뉜 극대 구간의 수.

### 4.2 정리

> **정리 A (덮개 부등식).** \(n\ge4\)인 무반복 커버링 워크에서
> \[
> \boxed{(n-1)S+(n-2)F\ge(n-1)!}.
> \]

특히 n=6에서는

\[
5S+4F\ge120.
\]

### 4.3 보조정리

1. **풀패스.** 길이 n 패스 뒤의 다음 시작점은 \(xE\)이므로 같은 `E`-궤도에 있다.

2. **부분패스.** \(\ell<n\)이면
   \[
   g_\ell(n-1)=\ell-1\ne n-1,
   \]
   이므로 마지막 심볼이 바뀌고, 따라서 `E`-궤도도 바뀐다.

3. **블록된 패스.** 패스가 \(b\)에서 끝나고 \(r(b)\)가 이미 방문됐다면, \(r(b)\)는 이전 패스 시작점 \(a'\)여야 한다. 그렇지 않으면 \(b=r^{-1}(r(b))\)도 이전에 방문됐어야 한다. 따라서
   \[
   b=r^{-1}(a'),
   \qquad
   \operatorname{flip}(b)=\operatorname{flip}(r^{-1}(a'))=E(a').
   \]
   다음 시작점은 이미 사용한 `E`-궤도에 속한다.

### 4.4 증명

사용된 `E`-궤도 수를 `O`라 하자. 새 궤도를 여는 패스 시작점은 다음 경우에만 가능하다.

1. 스트랜드의 첫 패스: 최대 \(S\)회;
2. 방기로 끝난 부분패스 뒤: 최대 \(F\)회.

풀패스 뒤에는 같은 궤도이고, 블록된 부분패스 뒤에는 위 보조정리에 따라 기존 궤도다. 따라서

\[
O\le S+F.
\]

한 `E`-궤도에는 순열이 \(n-1\)개뿐이고 패스 시작점은 무반복이므로

\[
P\le(n-1)O\le(n-1)(S+F).
\]

여기에 \(P=(n-1)!+F\)를 대입하면

\[
(n-1)!+F\le(n-1)S+(n-1)F,
\]

즉

\[
(n-1)!\le(n-1)S+(n-2)F.
\]

이다. \(\square\)

### 4.5 기계 검증

기존 `theorem_A_verify.py` 및 아카이브 396개 워크에서 다음이 확인됐다.

| 항목 | 결과 |
|---|---|
| \(\operatorname{flip}\circ r^{-1}=E\) | 720/720 |
| `E` 위수·마지막 위치 고정 | 확인 |
| 144 `E`-궤도 \(\times5\) 순열 | 확인 |
| 풀패스는 같은 궤도 | 720/720 |
| 부분패스는 다른 궤도 | 3600/3600 |
| 블록은 기존 궤도 | 396/396 |
| \(P=120+F\) | 396/396 |
| \(O\le S+F\) | 396/396 |
| \(5S+4F\ge120\) | 396/396 |

정리 A만으로 n=6에서 얻는 것은 `cost >= 24`이고, 목표 `cost >=29`까지는 다섯 단위가 남는다.

---

## 5. n=6 좌표계: 하한을 정확히 어디까지 줄였는가

n=6에서 다음을 정의한다.

\[
D=5O-P,
\qquad N=S+F-O,
\qquad k=O-24,
\qquad H=\sum (w-3)_+.
\]

`D`는 열린 `E`-궤도 안에서 비어 있는 패스 시작 위상 수의 총량이고, `N`은 정리 A의 \(O\le S+F\)에서의 결손이다.

정의와 frag 항등식만으로

\[
P=120+F,
\qquad D=5k-F,
\qquad N=S+F-O,
\]

그리고

\[
\operatorname{cost}:=F+S+H=O+N+H=24+k+N+H.
\]

길이는 정확히

\[
\boxed{L=843+\operatorname{cost}=867+(k+N+H)}.
\]

여기서 867은 고전 하한이다. 따라서 조건부 목표는 정확히

\[
\boxed{k+N+H\ge5}.
\]

이다.

`L<=871`인 가상의 반례는 다음 유한 slab 중 하나에만 놓인다.

| \(k\) | \(F\) 범위 | 남는 예산 |
|---:|---:|---:|
| 1 | \(1\le F\le5\) | \(N+H\le3\) |
| 2 | \(1\le F\le10\) | \(N+H\le2\) |
| 3 | \(1\le F\le15\) | \(N+H\le1\) |
| 4 | \(1\le F\le20\) | \(N=H=0\) |

`F=0`은 별도의 full-cassette 군론으로 이미 873 이상임이 닫혔으므로 이 표에서는 제외된다.

상세는 [COUNTEREXAMPLE_REDUCTION.md](COUNTEREXAMPLE_REDUCTION.md)에 고정되어 있다.

---

## 6. `F=0` full-cassette 가지: G2

### 6.1 범위

이 결과는 다음 범위에 한정된다.

- `F=0`;
- 24개의 완전 카세트;
- 각 카세트와 weight-3 사슬을 완주;
- 헥사곤 충돌과 사슬 충돌을 각각 \(\mathcal K(x)\), \(\mathcal L(x)\)로 판정.

### 6.2 결과

유효 weight-3 tail은 본질적으로

\[
x\mapsto xA,
\qquad A=(0\ 1\ 2\ 3),
\qquad A^4=1
\]

만 남는다. 따라서 weight-3 사슬 길이는 최대 4다.

사슬 끝의 유효 weight-4 tail은 `3201`, `3210` 두 개뿐이며, 둘 다 블록 몫에서

\[
\mathcal L(x)\mapsto\mathcal L(xP),
\qquad P=(0\ 1\ 2),
\qquad P^3=1
\]

로 작용한다. 그 결과 full-cassette 범위에서

\[
\sum(w-3)\ge6.
\]

따라서

\[
F=0\Longrightarrow H\ge6\Longrightarrow L\ge873.
\]

이는 `F=0` 전체의 자동 정리가 아니라 명시된 full-cassette 범위의 군론 정리라는 점을 유지해야 한다.

---

## 7. 포화 25-`E`-궤도 cover와 port 모델

### 7.1 포화 가지

가장 조여진 `k=1` 코너는

\[
(F,D,N)=(5,0,0),\qquad H\le3.
\]

이때

\[
P=125,\qquad O=25,\qquad S=20.
\]

25개의 사용된 `E`-궤도는 모두 다섯 패스 시작을 갖는다. 이를 **port**라 부르면 port 수는 125다.

### 7.2 내재적 weight-2 순열

한 헥사곤 안의 port를 회전 순서로 정렬하고, 다음 port로 보내는 순열을 \(\rho\)라 하자. port \(u\)에서 시작한 회전 패스의 끝은

\[
b=\rho(u)\sigma^{-1}
\]

이고, 유일한 weight-2 연속은

\[
b\tau=\rho(u)\sigma^{-1}\tau=\rho(u)E.
\]

따라서

\[
\boxed{f(u)=\rho(u)E}
\]

는 125 port 위의 순열이다.

### 7.3 cycle 하한과 exact lift

헥사곤 \(H\)가 \(m_H\)개의 port를 가지면 \(\rho\)의 해당 cycle은 전치 길이 \(m_H-1\)을 갖는다. 전체 incidence excess는 5이므로

\[
\sum_H(m_H-1)=5.
\]

`E`는 25개의 5-cycle이고 짝순열, \(\rho\)는 홀순열이므로

\[
c(f)\ge20,
\qquad c(f)\equiv0\pmod2.
\]

한편 이 가지에는 deep joint가 \(S-1=19\)개뿐이다. `f`-cycle마다 하나의 deep exit가 필요하고, 끝점이 속한 한 cycle만 예외이므로

\[
c(f)-1\le19.
\]

따라서 실제 워크가 존재한다면

\[
c(f)=20.
\]

20개의 `f`-cycle 각각에서 출구는 하나뿐이다. cycle에 port \(v\)로 들어오면 `f`를 따라가다가 \(f^{-1}(v)\)에서 나갈 수밖에 없다. deep tail이 \(u\)에서 \(t\)로 갈 때 다음 cycle의 강제 출구는

\[
u_{\mathrm{next}}=f^{-1}(t).
\]

이를 전부 보존하는 것이 **port-lift DP**다. 이 DP의 실패는 포화 가지의 유효한 필요조건 반증이다. 성공은 fragment 시간순서를 아직 보지 않으므로 워크 존재를 의미하지 않는다.

---

## 8. 순수 유한 정리 I: genus-zero

### 8.1 ribbon Euler 항등식

25개의 `E`-궤도를 black 꼭짓점, 120 헥사곤을 white 꼭짓점, 125 port를 간선으로 하는 이분 incidence graph를 생각한다. black 꼭짓점의 순환순서는 `E`, white 꼭짓점의 순환순서는 회전이다.

그 ribbon surface의 Betti 수와 genus를 각각 \(\beta,g\)라 하면

\[
\boxed{c(f)=20+2\beta-2g}.
\]

### 8.2 genus-zero 정리

> **정리 (genus-zero).** 모든 포화 25-`E`-궤도 cover \(C\)에 대해 \(g(C)=0\).

**핵심 축약.** 총 excess가 5이므로 1중 헥사곤은 pendant다. 양의 genus가 있다면 2-core에만 남아 있고, 2-core의 다중 헥사곤 총 차수는 최대 10이다. core의 black 꼭짓점 차수는 각각 적어도 2이므로, positive-genus core에는 많아야 다섯 `E`-궤도만 있다.

연결된 \(\le5\)-궤도, excess \(\le5\) family를 좌 `S_6` 동치까지 완전 열거하면 다음 표가 나온다.

| 궤도 수 | 연결 동형류 | positive-genus 류 |
|---:|---:|---:|
| 1 | 1 | 0 |
| 2 | 3 | 0 |
| 3 | 32 | 1 |
| 4 | 542 | 29 |
| 5 | 7,121 | 0 |

최소 positive-genus 류는 정확히 세 개다.

\[
\{0,1,3\},\qquad
\{0,1,33,138\},\qquad
\{0,1,9,13\}.
\]

각각의 비분할 포화 확장 탐색은 717, 4, 3 노드에서 완전히 소진되어 실패했다. 분해가능 cover는 exact-partition-plus-one 족이고, 그 족은 이미 완전 검사되어 genus 0이다. 따라서 모든 포화 cover에서 genus 0이다.

이제 안전하게

\[
\boxed{c(f)=20+2\beta}
\]

를 쓰며, 특히 \(c(f)=20\iff\beta=0\)이다.

완전한 증명·코드 명령은 [GENUS_ZERO_CERTIFICATE.md](GENUS_ZERO_CERTIFICATE.md)를 본다.

---

## 9. 순수 유한 정리 II: 다중도-2와 충돌 숲

> **정리 (다중도-2).** 모든 포화 25-`E`-궤도 cover의 헥사곤 다중도는
> \[
> 115\times1+5\times2
> \]
> 이다. 즉 triple 이상 헥사곤은 없다.

증명은 다음 유한 분류에 기반한다.

1. triple 이상 헥사곤이 있으면, 그 헥사곤을 공유하는 세 `E`-궤도 triple이 있다.
2. excess \(\le5\)인 그러한 triple은 좌 `S_6` 아래 정확히 네 종류다.
   \[
   \{0,1,3\},\quad\{0,1,9\},\quad\{0,1,33\},\quad\{0,3,33\}.
   \]
3. 네 종류 모두 비분할 포화 cover로의 complete-seed 확장 탐색에서 실패한다. 노드 수는 각각 717, 4,721, 8,069, 27,014다.
4. 분해가능 cover는 24-궤도 exact partition에 25번째 궤도를 추가한 것이므로 자동으로 정확히 다섯 double과 triple 없음이다.

따라서 115개의 단일 헥사곤을 수축하고, 다섯 double 헥사곤을 두 `E`-궤도 사이의 간선으로 바꾸면 25 꼭짓점·5 간선의 **충돌 multigraph**가 된다. 그 cycle rank가 incidence graph의 \(\beta\)와 같다.

genus-zero 정리와 결합하면

\[
\boxed{
c(f)=20
\iff
\text{다섯 간선 충돌 multigraph가 숲이다}.
}
\]

상세는 [MULTIPLICITY_TWO_THEOREM.md](MULTIPLICITY_TWO_THEOREM.md)에 있다.

---

## 10. 계산 성과: exact partition, 일반 cover, port lift

### 10.1 exact-partition-plus-one 부분류

**유한 계산 인증.**

- labelled 24-`E`-궤도 exact partition: 10,068개;
- 좌 `S_6` 동형류: 29개;
- 각 partition 대표와 가능한 25번째 궤도를 더한 3,480 사례를 검사;
- \(c(f)=20\)인 좌 `S_6` 류: 248개;
- 248개 모두 heavy budget \(H\le3\)에서 port-lift DP 실패;
- 나머지는 \(c=22\) 또는 \(24\)로 19개 deep exit 예산에서 즉시 탈락.

이는 “24 exact partition + 하나” 부분류에 대한 완전 computer-assisted 결과다.

### 10.2 정상형의 반증

**반증됨.** 모든 25-궤도 포화 cover가 24 exact partition에 한 궤도를 더한 꼴이라는 정상형은 거짓이다.

명시적 비분할 cover가 존재하며, 115 single+5 double incidence를 가지지만 어느 한 궤도를 빼도 24 exact partition이 남지 않는다. 따라서 일반 cover 탐색이 필요하다.

### 10.3 일반 비분할 cover 탐색

완전성을 보존하는 방법은 부분집합 자체를 “사전식 최소”라고 강제하는 것이 아니라, child를 좌 `S_6` 정준 대표로 옮기는 **canonical augmentation**이다. 비정준 부분집합이 정준 완성 cover로 이어질 수 있으므로 단순 depth-wise lexicographic pruning은 불완전하다.

6개의 정준 깊이-2 branch를 각각 5,000,000 노드까지 탐색한 현재 표본은 다음과 같다.

| 항목 | 결과 |
|---|---:|
| raw 비분할 cover leaf | 7,799 |
| 정준 병합 좌 `S_6` class | 1,743 |
| 숲 \((c,\beta,g)=(20,0,0)\) | 313 |
| \((22,1,0)\) | 1,182 |
| \((24,2,0)\) | 248 |
| 313개 숲 cover의 `H<=3` port-lift | 313/313 실패 |

위 6개 branch는 모두 노드 상한에서 중단됐으므로, 이 표는 **실험적·부분적 계산**이다. 전수 실패라고 쓰면 안 된다.

### 10.4 collision forest의 계산상 의미

이제 partial incidence graph에서 \(\beta>0\)이 된 순간, 간선·꼭짓점을 더해도 \(\beta\)는 감소하지 않는다. 따라서 그 branch는 어떤 완성에서도 \(c=20\)이 될 수 없다.

이는 forest-only canonical augmentation의 안전한 가지치기다. 일반 포화 cover가 아니라 다섯 충돌 간선이 cycle을 만들지 않는 cover만 직접 열거하면 된다.

초기 sanity check로 seed \(\{0,2\}\) branch를 forest-only 모드에서 1,000,000 노드까지 돌렸을 때 219개의 forest leaf를 얻었고, 이는 같은 branch의 더 큰 일반 탐색에서 나중에 판정된 219개 \(c=20\) leaf와 일치했다. 다만 이 실행도 노드 상한에서 멈췄으므로 전수 완료의 증거는 아니다.

---

## 11. 안티포달 구조와 C_geom 관찰

다음은 n=6 데이터에서 발견·검증된 기하학적 층이다.

- 30개 component의 overlap-5 그래프는 8-정규, 120 에지다.
- 각 component에는 거리 3인 유일한 antipode가 있어 15 antipodal pair를 이룬다.
- 표준 873 경로의 시작·끝 component는 antipodal 관계다.
- 조사한 872 최적 경로들은 해당 antipodal pair를 직접 사용하지 않는 패턴을 보였다.

그러나 다음 직접 설명은 **반증됨**이다.

> “antipodal pair 회피만이 \(C_{\mathrm{geom}}(6)=1\)의 이득을 만든다.”

관측상 일부 antipodal pair만 떼어 보면 순손해가 나고, 나머지 component의 재배치가 이를 상쇄한다. 따라서 antipodal 구조는 중요한 군론적 기하학이지만, 현재로서는 872 하한의 단독 메커니즘이 아니다.

---

## 12. 명시적으로 폐기한 길

다음은 재시도하지 않거나, 적어도 새 불변량 없이는 재사용하지 말아야 할 방향이다.

| 방향 | 판정 | 이유 |
|---|---|---|
| Burnside만으로 \(C_{\mathrm{geom}}\) 계산 | 불충분 | 성분 수는 주지만 경로 비용을 주지 않음 |
| 표현론·대수기하학적 역산 | 보류/폐기 | 데이터 독립 하한을 제공하지 못함 |
| antipodal 회피만 | 반증 | 부분 분해에서 순손해 |
| “혼합 심볼 `F=0` 불가능” | 반증 | 길이 884 혼합 `F=0` 예 존재 |
| 무조건 \(N=0\) | 반증 | 비최적 워크에서 \(N>0\) |
| 런 길이 \(\{3,5\}\) | 반증 | 873 해와 비최적 워크에서 다른 길이 출현 |
| free-transport 성분 크기 상한 | 실패 | repair가 성분을 임의로 이어 붙임 |
| fragment macrograph의 \(\mathbb Z_5\) holonomy | 실패 | 저비용 경우 macrograph가 숲일 수 있음 |
| cycle-transition graph 비연결성 | 반증 | 일반 `c=20` 표본은 강연결인데 lift DP 실패 |
| 24-partition-plus-one 정상형 | 반증 | 명시적 비분할 포화 cover 존재 |

---

## 13. 현재 열린 문제

### 13.1 가장 가까운 병목: forest cover의 port lift

포화 가지

\[
(F,D,N)=(5,0,0),\qquad H\le3
\]

에서 genus-zero·다중도-2 정리에 의해 남는 것은 정확히 다섯 간선 충돌 graph가 숲인 cover다.

남은 명제는 다음이다.

> **Forest port-lift 명제.** 모든 비분할 포화 forest cover에 대해 heavy budget \(H\le3\)의 port-lift DP는 실패한다.

이 명제가 전수 cover에 대해 닫히면 `k=1,F=5,D=N=0` 코너가 닫힌다.

### 13.2 `F<5`와 부분카세트

`F<5` 또는 `D>0`에서는 어떤 `E`-궤도가 5개 위상을 모두 쓰지 않을 수 있다. 포화 port model은 더 이상 충분하지 않다.

안전한 정확 상태는

\[
\Omega_{\mathrm{exact}}=
\bigl(p;(M_H)_{H\in\mathcal H};(B_Q)_{Q\in\mathcal Q};F,S,H\bigr),
\]

이다.

- \(M_H\): 헥사곤 `H`에서 이미 방문한 순열의 6비트 회전 마스크;
- \(B_Q\): `E`-궤도 `Q`에서 이미 사용한 패스 시작의 5위상 마스크;
- \(p\): 현재 끝 순열.

이 상태는 다음 tail의 합법성·다음 상태·\(F,S,H\) 증분을 모두 결정하므로 Markov 충분하다. `B_Q`만으로는 패스 내부 회전 vertex의 방문 여부를 잃으므로 충분하지 않다.

상세는 [PARTIAL_CASSETTE_STATE.md](PARTIAL_CASSETTE_STATE.md)에 있다.

### 13.3 NR6 가정 자체

최종 무조건 초순열 정리에는 NR6 가정의 제거가 필요하다. 이 문제는 현재 조합론적 하한 연구와 분리해 조건부 논문으로 정직하게 제시하는 것이 적절하다.

---

## 14. 다음 연구 방향

### 방향 A — forest-only 완전 열거와 port lift

가장 직접적인 다음 단계다.

1. canonical augmentation에 partial collision forest 조건을 넣는다.
2. \(\beta>0\) branch는 즉시 제거한다. 이는 genus-zero 정리 이후 안전하다.
3. 모든 최종 forest cover 대표에 exact port-lift DP를 적용한다.
4. DP 실패를 certificate로 저장한다: cycle 수, reachable layer 수, 상태 해시, 최소 heavy.

이 방향은 `F=5,D=N=0`을 완전히 닫는 가장 짧은 계산 경로다.

### 방향 B — forest의 조합론적 분해

다섯 간선 충돌 forest의 component 크기 분할은 매우 적다. 각 tree component에 대해

- 어떤 `E`-궤도 위상들이 double 헥사곤에 쓰이는지;
- weight-2 순열 \(f\)가 tree를 따라 어떻게 20개의 cycle을 만드는지;
- deep tail의 `f^{-1}(t)` lift가 tree component 사이에 어떤 제약을 갖는지

를 추출한다.

목표는 DP의 “최대 9–14 cycle만 도달” 현상을, cycle graph 연결성과는 다른 포트 위상 불변량으로 압축하는 것이다.

### 방향 C — `F<5`의 exact-state 탐색

`k=1`의 나머지 \(F=1,2,3,4\)와 \(k=2,3,4\) slab에는 \(\Omega_{\mathrm{exact}}\)를 사용한다.

우선순위는 전 상태공간 전수가 아니라 다음이다.

1. fragment 수가 작을 때 도달 가능한 부분카세트 상태의 정준화;
2. fragment cut/repair의 port·헥사곤 mask 전이표;
3. `N` 또는 `H`를 강제하는 잠재함수;
4. `F=1` 상태공간의 완전 분류.

### 방향 D — 재현성과 논문화

논문은 적어도 다음 산출물을 분리해야 한다.

- NR6 아래의 정리 A와 좌표계;
- NR6와 무관한 genus-zero·다중도-2 유한 정리;
- forest-only enumeration 코드와 검증 해시;
- 872 상계 문자열의 독립 verifier 출력;
- 증명, 완전 계산, 실험, 반증의 명확한 라벨.

---

## 15. 현재 재현 파일

| 파일 | 내용 |
|---|---|
| `work/superperm_port_lift.py` | `E`-궤도, exact partition, canonical augmentation, genus core, triple seed, port lift 코드 |
| `F5_PORT_LIFT_LEMMA.md` | 포화 `F=5,D=N=0` port-lift 보조정리 |
| `GENUS_ZERO_CERTIFICATE.md` | 모든 포화 cover의 genus-zero computer-assisted 증명 |
| `MULTIPLICITY_TWO_THEOREM.md` | 모든 포화 cover의 \(115\times1+5\times2\) 다중도 정리 |
| `PORT_SURFACE_INVARIANT.md` | ribbon Euler 항등식 |
| `CANONICAL_AUGMENTATION.md` | 대칭 가지치기의 완전성 논증 |
| `PARTIAL_CASSETTE_STATE.md` | fragment 가지의 정확 Markov 상태 |
| `COUNTEREXAMPLE_REDUCTION.md` | \(L\le871\) 반례 slab 축소 |
| `EXECUTION_LOG.md` | 실행 명령·해시·유한 계산 기록 |

---

## 16. 최종 상태표

| 층 | 상태 |
|---|---|
| 정리 A: \((n-1)S+(n-2)F\ge(n-1)!\) | **증명됨** |
| n=6 좌표 \(L=867+k+N+H\) | **정의상 유도됨** |
| `F=0` full-cassette \(L\ge873\) | **해당 범위에서 증명됨** |
| 포화 cover genus-zero | **유한 계산 인증으로 증명됨** |
| 포화 cover 다중도 \(115\times1+5\times2\) | **유한 계산 인증으로 증명됨** |
| `c=20 \iff` 충돌 forest | **증명됨** |
| exact-partition-plus-one의 `H<=3` port-lift 실패 | **완전 계산 인증** |
| 일반 forest cover의 `H<=3` port-lift 실패 | **현재 표본은 전부 실패, 전수는 미완** |
| `F<5` 가지 | **열림** |
| NR6 가정 제거 | **열림** |
| 조건부 \(L_6\ge872\) | **열림** |
| 무조건 \(L_6=872\) | **열림** |
