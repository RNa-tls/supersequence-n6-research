/* 라운드 121 — `(k,F) = (2,1)` 정확 탐색기 (라운드 120 엔진의 확장).
 *
 * 새로 들어간 것:
 *
 *  1. **무게-5 tail 71개**.  무게 w 이음매는 z = (y[w..5], y[pi(0..w-1)]) 이고 pi 는
 *     {0..w-1} 의 분해불가 순열이다 (1,1,3,13,71,461 -> 합 550).  무게-5 는 S 에 1,
 *     H 에 2 를 낸다.  `hw` 비트마스크로 무게-4(1)·무게-5(2)를 따로 켠다.
 *  2. **`shcap`** — `cost + hub <= shcap` 을 직접 강제한다.  `S+H <= 26` 이 곧
 *     `e + x + H <= 1 + f_out` 이므로 이 하나가 자원 행 전체를 정확히 가둔다.
 *  3. **`fod` — 신선 궤도 결손 프룬 (새 정확 프룬).**  `O = 26` 이 정확히 고정이므로
 *     앞으로 정확히 `26 - orbits` 개의 신선 궤도를 더 열어야 한다.  신선 궤도 Q 의 다섯
 *     육각형 중 **이미 쓰인 것**은 영원히 진입할 수 없으므로 `d_Q >= blk(Q)` 다.
 *     따라서 신선 궤도들의 `blk` 중 **작은 것 `26-orbits` 개의 합**이 남은 D 예산을
 *     넘으면 그 가지는 죽는다.  이미 떠난 궤도의 결손과는 서로 다른 궤도를 세므로
 *     그냥 더하면 된다.  `h*` 만 두 번 진입되는데 두 번째 진입은 Y 이므로,
 *     **X 의 육각형은 Y 가 놓일 때까지 막지 않는다**.
 *  4. **`hubmin`** — 잎에서 최종 `hub >= hubmin` 을 요구해 H-그룹을 서로소로 만든다.
 *  5. **`hjcap`** — 무거운 이음매 **개수** 상한 (H=2 의 두 조성 4+4 와 5 를 가른다).
 *  6. 끝점에서 **`orbits == ORBCAP` 을 정확히** 요구한다 (궤도가 적으면 다른 칸이다).
 *
 * 라운드 120 정정은 그대로 유지한다: `W4_0`(작용 [4 5 1 2 3 0])은 `ell=5` 에서
 * 궤도 내부(phase +3)이고, `W5_0`(작용 [5 1 2 3 4 0])은 `ell=5` 에서 궤도 내부
 * (phase +4)다.  둘 다 **run 내부 비용-1 이음매**로서 `x` 를 1 쓴다.  불건전한
 * `if (same && hb) continue;` 는 **복원하지 않는다** — 이 라운드는 xcap>0 과 hcap>0 이
 * 동시에 양수인 실행을 실제로 돈다.
 *
 * seam / revonly / yfresh 는 라운드 120 의 `B_ii` 전용 논증에서 나온 것이라
 * `k=2` 에서는 **쓰지 않는다** (인자는 재현 대조를 위해 남겨 둔다).
 *
 * 원래 주석:
 * 라운드 120 — 라운드 119 탐색기 + **궤도-덮개 잉여 한계**(브리프 §4·§5·§12).
 *
 * 새 불변량 (정확 · 이 라운드의 핵심).  전수 확인된 기하: 궤도 하나는 정확히
 * **5개의 서로 다른 육각형**을 만나고, 육각형 하나는 정확히 **6개의 서로 다른 궤도**를
 * 만난다.  F=1 walk 의 진입 단어는 육각형마다 정확히 하나(h* 만 둘)이므로 **쓰인 궤도
 * 집합 Q 는 120개 육각형을 전부 덮어야 한다.**  |Q| = O = 24+k 이므로
 *
 *     sum_h m_h = 5*O ,   m_h := #{Q in Q : Q 가 h 를 만남} >= 1
 *     =>  EXC := sum_h (m_h - 1) = 5*O - 120 = 5k          (k=3 이면 **정확히 15**)
 *
 * EXC 는 궤도를 새로 열 때만 증가하는 **단조** 량이므로 `EXC <= 5k` 는 정확한 프룬이다
 * (실제 walk 의 가지는 절대 자르지 않는다).
 *
 * 얼마나 빡빡한가: 무작위 27-궤도 집합의 잉여는 20,000 표본에서 **최소 34 · 중앙값 49**
 * 인데 여기서 요구하는 값은 **15** 다.  라운드 119 의 접두 용량 한계가 **완전히 무시하던
 * 좌표**(육각형 접촉 상관)를 정확히 붙잡는다.  공허하지 않다: 24-궤도 **정확 덮개**가
 * 실제로 존재하고 거기에 궤도 3개를 더하면 잉여가 정확히 15 인 덮는 27-집합이 나온다.
 *
 * `exccap` 인자를 -1 로 주면 프룬이 꺼진다 (라운드 119 노드 수 재현 대조용).
 *
 * 원래 주석:
 * 라운드 119 — 라운드 118 탐색기 + **접두 용량 하한**(브리프 §6/§7).
 *
 * 라운드 118 의 `dcap` 은 "이미 떠난 궤도들의 결손 합 <= D" 라는 **한쪽** 프룬이다.
 * 그런데 `O = 24 + k` 는 **정확히** 고정이므로 반대쪽도 강제된다: 남은 pass 를 담을
 * 자리가 실제로 있어야 한다.
 *
 *     남은 pass = 121 - passes
 *     담을 수 있는 자리 =   (5 - |현재 궤도의 사용 phase|)          현재 run 연장
 *                        + 5 * (ORBCAP - orbits)                    아직 안 쓴 궤도
 *                        + (떠난 궤도 결손 중 큰 것 ECAP-rev 개)    재방문으로 회수
 *
 * 남은 pass 가 그보다 크면 **어떤 실제 walk 도 될 수 없다** — 정확한 상한이므로
 * 실제 walk 의 가지는 자르지 않는다.  `dcap` 과 합쳐 양쪽 회랑이 된다.
 *
 * 원래 주석:
 * 라운드 118 — `F = 1` 칸의 정확한 탐색기 (라운드 117 탐색기 + 허브세 1단위).
 *
 * 라운드 117 판(`src/f1_all_light_117.c`)은 그대로 두고 여기서 확장한다.
 * 새 인자 두 개:
 *   rmax  — run 수 상한을 명시한다 (하위경우마다 r = 24+k+e 로 정확히 정해진다).
 *           run 결손 상한 SHRUNCAP = 5*rmax - 121 이 그만큼 빡빡해진다.
 *   hcap  — 쓸 수 있는 무게-4 joint 수 (허브세).  H = sum (w-3)_+ 이므로 hcap = H.
 *           무게-4 tail 은 13개이고 전수 확인에 따르면 **전부 궤도를 바꾸고**
 *           **출발 육각형을 떠난다**; 12개는 육각형-서로소, 1개는 육각형 2개를 공유한다.
 *           무게-4 joint 는 S 에 1, H 에 1 을 낸다.
 *
 * 원래 주석:
 * 라운드 117 — `F = 1`, `H = 0` (all-light) walk 뼈대의 정확한 탐색기.
 *
 * 라운드 116 이 확정한 구조와 라운드 117 의 보조정리 E 만 쓴다 (Q2 가정 없음):
 *   * pass 121개, 육각형 120개 — 정확히 한 육각형 h* 만 두 번 진입된다
 *   * h* 의 두 pass 는 6-순환의 상보 호: 먼저 오는 것이 길이 b (진입 v),
 *     나중 것이 길이 6-b (진입 sigma^b(v)) — b 는 실행 인자다
 *   * 다른 119개 pass 는 길이가 정확히 6
 *   * H = 0 이므로 모든 joint 는 경량: W2(비용 0) · W3a/W3b/W3c(비용 1)
 *   * 진입 단어 u, pass 길이 len 이면 탈출 단어는 sigma^(len-1)(u) 이고
 *     joint 는 거기에 작용한다.  ell < 5 에서는 네 이동이 전부 궤도를 바꾼다.
 *   * S = 비용-1 joint 수,  L = 845 + S + H = 845 + S  ->  L <= 871 <=> S <= 26
 *   * 보조정리 E:  f_out <= 1 + e
 *
 * 판정: SAT / UNSAT_COMPLETE / UNKNOWN_CAP.  캡 도달은 UNSAT 이 아니다.
 *
 * 사용법: ./f1_all_light_117 <b> <costcap> <orbcap> <xcap> <foutcap> <ecap> [nodecap]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define NW 720
#define NO 144
#define NH 120
#define TARGET 121

static int hexid[NW], orbid[NW], phse[NW];
static int SIG[6][NW];
static int M2[NW], M3a[NW], M3b[NW], M3c[NW];
#define NH4 13
#define NH5 71
static int M4[NH4][NW];
static int H4ACT[NH4][6];
static int M5[NH5][NW];
static int H5ACT[NH5][6];
static uint64_t hlo[NW], hhi[NW];
static int perm[NW][6];
static int ohex[NO][5];
static int hexorb[NH][6];   /* the 6 orbits meeting each hexagon */
static int blk[NO];        /* how many of this orbit's 5 hexagons are already used */
static int freshcnt[6];    /* fresh orbits by blk value */        /* the 5 distinct hexagons each orbit meets */
static int mcnt[NH];          /* how many USED orbits meet this hexagon */
static int EXC;               /* sum_h (mcnt[h] - 1)_+  over used orbits */

/* NTAB[s] = 라운드 115 가 전수로 구한, run 결손이 s 이하인 R115-모델 all-light 사슬
   하나의 최대 pass 수 (b = g = 0, 캡 도달 0).  두 짧은 pass (그리고 W3a jump / 궤도
   재방문) 가 F=1 walk 을 그런 사슬 여러 개로 자르므로 각 조각의 상한이 된다.
   s > 20 은 라운드 115 가 표로 만들지 않았으므로 120 (자명한 상한) 을 쓴다. */
static const int NTAB[25] = {20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70,
                             74, 83, 83, 96, 96, 96, 103, 103, 103, 103,
                             120, 120, 120, 120};
static int BESTSEG[8][25];

static int rank_of(const int *p) {
    int used[6] = {0}, r = 0, f[6] = {120, 24, 6, 2, 1, 1};
    for (int i = 0; i < 6; i++) {
        int c = 0;
        for (int v = 0; v < p[i]; v++) if (!used[v]) c++;
        r += c * f[i];
        used[p[i]] = 1;
    }
    return r;
}
static void sig_(const int *x, int *o) { for (int i = 0; i < 5; i++) o[i] = x[i + 1]; o[5] = x[0]; }
static void tau_(const int *x, int *o) { o[0]=x[1];o[1]=x[2];o[2]=x[3];o[3]=x[4];o[4]=x[0];o[5]=x[5]; }

static void build(void) {
    int p[6] = {0, 1, 2, 3, 4, 5};
    memcpy(perm[rank_of(p)], p, sizeof p);
    for (int cnt = 1; cnt < NW; cnt++) {
        int i = 4;
        while (i >= 0 && p[i] >= p[i + 1]) i--;
        if (i < 0) break;
        int j = 5; while (p[j] <= p[i]) j--;
        int t = p[i]; p[i] = p[j]; p[j] = t;
        for (int a = i + 1, b = 5; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; }
        memcpy(perm[rank_of(p)], p, sizeof p);
    }
    int hrep[NW], orep[NW];
    for (int w = 0; w < NW; w++) {
        int y[6], best;
        memcpy(y, perm[w], sizeof y); best = w;
        for (int i = 0; i < 5; i++) { int o[6]; sig_(y, o); memcpy(y, o, sizeof y);
            int rr = rank_of(y); if (rr < best) best = rr; }
        hrep[w] = best;
        memcpy(y, perm[w], sizeof y); best = w;
        for (int i = 0; i < 4; i++) { int o[6]; tau_(y, o); memcpy(y, o, sizeof y);
            int rr = rank_of(y); if (rr < best) best = rr; }
        orep[w] = best;
    }
    int hmap[NW], omap[NW], nh = 0, no = 0;
    for (int w = 0; w < NW; w++) { hmap[w] = -1; omap[w] = -1; }
    for (int w = 0; w < NW; w++) {
        if (hmap[hrep[w]] < 0) hmap[hrep[w]] = nh++;
        if (omap[orep[w]] < 0) omap[orep[w]] = no++;
        hexid[w] = hmap[hrep[w]]; orbid[w] = omap[orep[w]];
    }
    if (nh != NH || no != NO) { fprintf(stderr, "geometry mismatch\n"); exit(2); }
    for (int w = 0; w < NW; w++) {
        int y[6]; memcpy(y, perm[orep[w]], sizeof y);
        for (int i = 0; i < 5; i++) {
            if (rank_of(y) == w) { phse[w] = i; break; }
            int o[6]; tau_(y, o); memcpy(y, o, sizeof y);
        }
        hlo[w] = (hexid[w] < 64) ? (1ULL << hexid[w]) : 0ULL;
        hhi[w] = (hexid[w] >= 64) ? (1ULL << (hexid[w] - 64)) : 0ULL;
    }
    for (int w = 0; w < NW; w++) {
        int y[6]; memcpy(y, perm[w], sizeof y);
        SIG[0][w] = w;
        for (int kk = 1; kk < 6; kk++) { int o[6]; sig_(y, o); memcpy(y, o, sizeof y);
            SIG[kk][w] = rank_of(y); }
    }
    {   /* every orbit meets exactly 5 distinct hexagons (exhaustively verified) */
        int nseen[NO];
        for (int q = 0; q < NO; q++) nseen[q] = 0;
        for (int w = 0; w < NW; w++) {
            int q = orbid[w], h = hexid[w], dup = 0;
            for (int j = 0; j < nseen[q]; j++) if (ohex[q][j] == h) dup = 1;
            if (!dup) {
                if (nseen[q] >= 5) { fprintf(stderr, "orbit meets >5 hexagons\n"); exit(2); }
                ohex[q][nseen[q]++] = h;
            }
        }
        for (int q = 0; q < NO; q++)
            if (nseen[q] != 5) { fprintf(stderr, "orbit meets %d hexagons\n", nseen[q]); exit(2); }
    }
    for (int y = 0; y < NW; y++) {                 /* moves act on the EXIT word */
        int *q = perm[y];
        int a2[6]  = {q[2], q[3], q[4], q[5], q[1], q[0]};
        int a3a[6] = {q[3], q[4], q[5], q[1], q[2], q[0]};
        int a3b[6] = {q[3], q[4], q[5], q[2], q[0], q[1]};
        int a3c[6] = {q[3], q[4], q[5], q[2], q[1], q[0]};
        M2[y] = rank_of(a2); M3a[y] = rank_of(a3a);
        M3b[y] = rank_of(a3b); M3c[y] = rank_of(a3c);
    }
    /* the 13 indecomposable weight-4 tails, in the same order the engine generates them:
       action = [4, 5] followed by a permutation pi of {0..3} that is indecomposable. */
    {
        int idx = 0, pi[4];
        for (pi[0] = 0; pi[0] < 4; pi[0]++)
        for (pi[1] = 0; pi[1] < 4; pi[1]++) {
            if (pi[1] == pi[0]) continue;
            for (pi[2] = 0; pi[2] < 4; pi[2]++) {
                if (pi[2] == pi[0] || pi[2] == pi[1]) continue;
                pi[3] = 6 - pi[0] - pi[1] - pi[2];
                /* indecomposable: no proper prefix of pi is {0..j} */
                int ok = 1, mx = -1;
                for (int j = 0; j < 3; j++) { if (pi[j] > mx) mx = pi[j];
                    if (mx == j) { ok = 0; break; } }
                if (!ok) continue;
                if (idx >= NH4) { fprintf(stderr, "too many weight-4 tails\n"); exit(2); }
                H4ACT[idx][0] = 4; H4ACT[idx][1] = 5;
                for (int j = 0; j < 4; j++) H4ACT[idx][2 + j] = pi[j];
                idx++;
            }
        }
        if (idx != NH4) { fprintf(stderr, "weight-4 tail count %d != 13\n", idx); exit(2); }
        for (int y = 0; y < NW; y++)
            for (int h = 0; h < NH4; h++) {
                int a[6];
                for (int j = 0; j < 6; j++) a[j] = perm[y][H4ACT[h][j]];
                M4[h][y] = rank_of(a);
            }
    }
    {   /* the 71 indecomposable weight-5 tails: action = [5] then pi over {0..4} */
        int idx = 0, pi[5], used[5];
        for (pi[0] = 0; pi[0] < 5; pi[0]++)
        for (pi[1] = 0; pi[1] < 5; pi[1]++)
        for (pi[2] = 0; pi[2] < 5; pi[2]++)
        for (pi[3] = 0; pi[3] < 5; pi[3]++)
        for (pi[4] = 0; pi[4] < 5; pi[4]++) {
            for (int j = 0; j < 5; j++) used[j] = 0;
            int dup = 0;
            for (int j = 0; j < 5; j++) { if (used[pi[j]]) { dup = 1; break; } used[pi[j]] = 1; }
            if (dup) continue;
            int ok = 1, mx = -1;
            for (int j = 0; j < 4; j++) { if (pi[j] > mx) mx = pi[j];
                if (mx == j) { ok = 0; break; } }
            if (!ok) continue;
            if (idx >= NH5) { fprintf(stderr, "too many weight-5 tails\n"); exit(2); }
            H5ACT[idx][0] = 5;
            for (int j = 0; j < 5; j++) H5ACT[idx][1 + j] = pi[j];
            idx++;
        }
        if (idx != NH5) { fprintf(stderr, "weight-5 tail count %d != 71\n", idx); exit(2); }
        for (int y = 0; y < NW; y++)
            for (int h = 0; h < NH5; h++) {
                int a[6];
                for (int j = 0; j < 6; j++) a[j] = perm[y][H5ACT[h][j]];
                M5[h][y] = rank_of(a);
            }
    }
    {   /* the 6 orbits meeting each hexagon */
        int n[NH];
        for (int h = 0; h < NH; h++) n[h] = 0;
        for (int w = 0; w < NW; w++) {
            int h = hexid[w], q = orbid[w], dup = 0;
            for (int j = 0; j < n[h]; j++) if (hexorb[h][j] == q) dup = 1;
            if (!dup) {
                if (n[h] >= 6) { fprintf(stderr, "hexagon meets >6 orbits\n"); exit(2); }
                hexorb[h][n[h]++] = q;
            }
        }
        for (int h = 0; h < NH; h++)
            if (n[h] != 6) { fprintf(stderr, "hexagon meets %d orbits\n", n[h]); exit(2); }
    }
}

/* ------------------------------------------------------------------ search */
static int BSPLIT, COSTCAP, ORBCAP, SHRUNCAP, RMAX, XCAP, FOUTCAP, ECAP, FOUTMIN,
           YGAP, HCAP, RMAXARG, DCAP, BFORCE, REVONLY, HREGION, YFRESH, EXCCAP,
           SEAM, PMAX, SYMCUT, SHCAP, HW, HJCAP, HUBMIN, FOD;
static long long NODECAP, nodes;
static int capped, found, bestPasses;
static unsigned char omask[NO];
static int defcnt[5];
static uint64_t HLO, HHI;
static int witness[TARGET + 2], wlen_[TARGET + 2];

/* orbit-deficit prune (Round 115 style): D = sum over orbits of (5 - |B_q|) is fixed at
   5*O - 121, so the orbits already left behind must fit inside it.  The current orbit may
   still grow, and up to (ECAP - rev) further orbits may be revisited and completed, so those
   are dropped optimistically — the prune never cuts a branch a real walk could take. */
/* prefix capacity bound: can the remaining passes still be placed at all? */
static int capacity_ok(int curorb, int slots, int passes, int orbits) {
    int c[5];
    for (int i = 0; i < 5; i++) c[i] = defcnt[i];
    int d = 5 - __builtin_popcount(omask[curorb]);
    c[d]--;                                   /* the current orbit is handled separately */
    int room = d + 5 * (ORBCAP - orbits);
    int tok = slots;
    for (int dd = 4; dd >= 1 && tok > 0; dd--) {
        int take = c[dd] < tok ? c[dd] : tok;
        tok -= take;
        room += take * dd;
    }
    return (TARGET - passes) <= room;
}

/* Round 121: how much of D is already committed by orbits we have LEFT behind.  The
   current orbit and up to `slots` revisitable ones are dropped optimistically, so the
   value never over-counts and the prune never cuts a branch a real walk could take. */
static int dcommitted(int curorb, int slots) {
    int c[5];
    for (int i = 0; i < 5; i++) c[i] = defcnt[i];
    int d = 5 - __builtin_popcount(omask[curorb]);
    c[d]--;
    int sum = 0, tok = slots;
    for (int dd = 4; dd >= 1; dd--) {
        int take = c[dd] < tok ? c[dd] : tok;
        tok -= take;
        sum += (c[dd] - take) * dd;
    }
    return sum;
}

/* Round 121: a FRESH orbit Q can never enter a hexagon that is already used, so its final
   deficit is at least blk(Q).  Exactly `need` more orbits must be opened (O = 26 exactly),
   so the `need` smallest blk values are a lower bound on the deficit they will contribute.
   Those are different orbits from the ones dcommitted() counts, so the two add. */
static int freshdeficit(int need) {
    int sum = 0, left = need;
    for (int j = 0; j <= 5 && left > 0; j++) {
        int take = freshcnt[j] < left ? freshcnt[j] : left;
        left -= take;
        sum += take * j;
    }
    if (left > 0) return 1 << 20;          /* not even enough fresh orbits remain */
    return sum;
}

/* mark hexagon h as used (delta = +1) or unused (delta = -1) for the blk bookkeeping */
static void markhex(int h, int delta) {
    for (int j = 0; j < 6; j++) {
        int q = hexorb[h][j];
        int fresh = (omask[q] == 0);
        if (fresh) freshcnt[blk[q]]--;
        blk[q] += delta;
        if (fresh) freshcnt[blk[q]]++;
    }
}

static int dfeasible(int curorb, int slots) {
    int c[5];
    for (int i = 0; i < 5; i++) c[i] = defcnt[i];
    int d = 5 - __builtin_popcount(omask[curorb]);
    c[d]--;
    int sum = 0, tok = slots;
    for (int dd = 4; dd >= 1; dd--) {
        int take = c[dd] < tok ? c[dd] : tok;
        tok -= take;
        sum += (c[dd] - take) * dd;
    }
    return sum <= DCAP;
}

static void dfs(int u, int len, int passes, int cost, int orbits, int runs,
                int shrun, int runlen, int sstate, int vword, int fout,
                int xj, int rev, int segpasses, int segsh, int pX, int hub,
                int njoint) {
    if (found) return;
    if (++nodes > NODECAP) { capped = 1; return; }
    if (passes > bestPasses) bestPasses = passes;
    if (passes == TARGET) {
        /* O = 24 + k is exact, and H must really reach this group's value */
        if (orbits == ORBCAP && hub >= HUBMIN) found = 1;
        return;
    }
    /* admissible prune: finishing the current run yields at most 5 - runlen more passes,
       every further run yields at most 5, and every further run needs an inter-run joint
       which costs 1 unless it is one of the at most FOUTCAP free short-pass exits. */
    {
        int rem = TARGET - passes - (5 - runlen);
        if (rem > 0) {
            int need = (rem + 4) / 5;
            int freeleft = FOUTCAP - fout;
            int extra = need - freeleft;
            if (extra < 0) extra = 0;
            if (cost + extra > COSTCAP) return;
        }
    }
    /* segment-capacity prune: the passes since the last segment break (a short pass, a
       W3a jump, or an orbit revisit) form an R115-model all-light chain. */
    {
        int sleft = SHRUNCAP - shrun;
        if (sleft < 0) return;
        if (sleft > 24) sleft = 24;
        int idx = segsh + sleft; if (idx > 24) idx = 24;
        int segs = (2 - sstate) + (XCAP - xj) + (ECAP - rev) + (HCAP - hub);
        if (segs > 7) segs = 7;
        int bound = (passes - segpasses) + NTAB[idx] + BESTSEG[segs][sleft];
        if (bound < TARGET) return;
    }
    /* f_out must reach FOUTMIN and only a SHORT pass can supply a free inter-run exit.
       avail = free exits still obtainable, counting this pass if it is short (its exit has
       not been chosen yet). */
    /* Round 117 section 5.2: when f_out = 2, e = 1 and x = 0, the FIRST h* pass X must be
       in case (ii) (case (i) would place Y before X) and the SECOND, Y, must be in case (i),
       so Y sits exactly 5 passes after X.  YGAP = 5 switches that on. */
    /* YGAP is an UPPER bound on the gap between the two h* passes (Round 117 section 5.2
       gives exactly 5 when x = 0; one W3a jump inside the forced block can shorten it to 4,
       so "<= YGAP" is the sound form). */
    /* Round 120 (B_ii only, from the reversal theorem): the first short pass X sits at
       position p and the walk has p-1 passes before it and 121-q after Y.  Reversal swaps
       those two counts, so we may assume p-1 <= 121-q; with q-p >= 4 in B_ii that forces
       p <= PMAX.  If X has not been placed by then the branch is dead. */
    if (PMAX && sstate == 0 && passes >= PMAX) return;
    if (YGAP && sstate == 1 && passes - pX >= YGAP) return;
    if (DCAP >= 0 && !dfeasible(orbid[u], ECAP - rev)) return;
    if (!capacity_ok(orbid[u], ECAP - rev, passes, orbits)) return;
    /* Round 121 fresh-orbit deficit prune (exact) */
    if (FOD && DCAP >= 0
        && dcommitted(orbid[u], ECAP - rev) + freshdeficit(ORBCAP - orbits) > DCAP) return;
    int isshort = (len < 6);
    int avail = (2 - sstate) + (isshort ? 1 : 0);
    if (fout + avail < FOUTMIN) return;
    /* In B1 the block between X and Y is forced: X exits free to tau(entry_Y) and the four
       following full passes each move by W2 = tau, ending at Y.  So every move from X up to
       the pass just before Y is the free move. */
    int forcefree = (isshort && fout + avail == FOUTMIN)
                    || (YGAP && (XCAP == 0 || BFORCE) && sstate == 1
                        && passes - pX <= YGAP - 1);
    int exitw = SIG[len - 1][u];
    int curorb = orbid[u];
    int succ[4 + NH4 + NH5];
    int scost[4 + NH4 + NH5], shub[4 + NH4 + NH5];
    succ[0] = M2[exitw]; succ[1] = M3a[exitw];
    succ[2] = M3b[exitw]; succ[3] = M3c[exitw];
    scost[0] = 0; scost[1] = 1; scost[2] = 1; scost[3] = 1;
    shub[0] = shub[1] = shub[2] = shub[3] = 0;
    int nsucc = 4;
    /* HREGION conditions on WHERE the single weight-4 edge sits.  It can never lie inside
       the forced X-Y block (those joints are intra-orbit and every weight-4 move changes
       orbit) nor be X's or Y's exit (both are forced free when f_out = 2), so the only
       regions are "before X" (sstate == 0) and "after Y" (sstate == 2). */
    int hregion_ok = (HREGION == 0) || (HREGION == 1 && sstate == 0)
                     || (HREGION == 2 && sstate == 2);
    if (!forcefree && hregion_ok && njoint < HJCAP) {
        if ((HW & 1) && hub + 1 <= HCAP)
            for (int h = 0; h < NH4; h++) {
                succ[nsucc] = M4[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 1; nsucc++;
            }
        if ((HW & 2) && hub + 2 <= HCAP)
            for (int h = 0; h < NH5; h++) {
                succ[nsucc] = M5[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 2; nsucc++;
            }
    }
    for (int si = 0; si < (forcefree ? 1 : nsucc) && !found; si++) {
        int w = succ[si];
        int c = scost[si];
        int hb = shub[si];
        if (cost + c > COSTCAP) continue;
        if (SHCAP >= 0 && cost + c + hub + hb > SHCAP) continue;
        int nq = orbid[w];
        int same = (nq == curorb);
        int nruns = runs, nsh = shrun, nrunlen = runlen + 1, nfout = fout;
        int nxj = xj, nrev = rev, nhub = hub + hb, nnj = njoint + (hb ? 1 : 0);
        /* Round 120 CORRECTION.  Round 118 recorded "all 13 weight-4 tails always change
           orbit (720/720)"; that is FALSE for one of them.  W4_0 (action [4 5 1 2 3 0])
           is intra-orbit for all 720 words at ell = 5 (and inter-orbit at every ell < 5);
           the other 12 are inter-orbit at every ell.  So a weight-4 joint CAN be intra-run,
           and it is then an intra-run cost-1 joint, i.e. it spends one unit of x.  The
           blanket `if (same && hb) continue;` of Rounds 118/119 was therefore unsound.
           The x-accounting below handles it correctly.  Every run executed in Rounds 118
           and 119 had xcap = 0 or hcap = 0, so none of them was affected: with xcap = 0
           the very next line rejects the same branch anyway. */
        if (same) { if (c == 1) { nxj = xj + 1; if (nxj > XCAP) continue; } }
        if (!same) {
            if (c == 0) {
                nfout = fout + 1;
                if (nfout > FOUTCAP) continue;
                if (nfout > 1 + ECAP) continue;      /* Lemma E: f_out <= 1 + e */
            }
            nruns = runs + 1;
            nsh = shrun + (5 - runlen);
            if (nsh > SHRUNCAP) continue;
            if (nruns > RMAX) continue;
            nrunlen = 1;
        } else {
            if (runlen + 1 > 5) continue;
        }
        int hexused = (HLO & hlo[w]) || (HHI & hhi[w]);
        int fresh = (omask[nq] == 0);
        int rv = (!same && !fresh) ? 1 : 0;
        if (nrev + rv > ECAP) continue;
        /* REVONLY: the only orbits that may get a second run are orb(entry_X) and
           orb(entry_Y) — used when the resource budget assigns every unit of e to them. */
        if (REVONLY && rv) {
            if (sstate == 0) continue;
            int oX = orbid[vword], oY = orbid[SIG[BSPLIT][vword]];
            if (nq != oX && nq != oY) continue;
        }
        if (fresh && orbits + 1 > ORBCAP) continue;
        /* YFRESH (case B-ii): orb(Y) has exactly two runs — the one X's free exit opens and
           the one ending at Y — so orb(Y) cannot have been touched before X.  Hence X's free
           exit must land in a FRESH orbit. */
        if (YFRESH && sstate == 1 && passes == pX && c == 0 && !fresh) continue;
        if (omask[nq] >> phse[w] & 1) continue;
        /* --- Round 120: orbit-cover excess.  Opening a fresh orbit adds its 5 hexagons to
           the incidence multiset; each of those hexagons already met by a used orbit raises
           EXC.  EXC is monotone and must finish at exactly 5k = 5*(ORBCAP-24), so EXC over
           the cap can never be repaired -> exact prune. --- */
        int addexc = 0;
        if (fresh) {
            for (int j = 0; j < 5; j++) if (mcnt[ohex[nq][j]]) addexc++;
            if (EXCCAP >= 0 && EXC + addexc > EXCCAP) continue;
            for (int j = 0; j < 5; j++) mcnt[ohex[nq][j]]++;
            EXC += addexc;
        }
        int brk = (nxj > xj || rv);
        int nsegp = brk ? 1 : segpasses + 1;
        int nsegs = brk ? 0 : segsh + (same ? 0 : (5 - runlen));
        /* --- case 1: fresh hexagon, FULL pass --- */
        if (!found && !hexused) {
            int d0 = 5 - __builtin_popcount(omask[nq]);
            if (fresh) defcnt[4]++; else { defcnt[d0]--; defcnt[d0 - 1]++; }
            if (FOD) { markhex(hexid[w], 1); if (fresh) freshcnt[blk[nq]]--; }
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            witness[passes] = w; wlen_[passes] = 6;
            dfs(w, 6, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, sstate, vword, nfout, nxj, nrev + rv,
                hb ? 1 : nsegp, hb ? 0 : nsegs, pX, nhub, nnj);
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
            if (FOD) { if (fresh) freshcnt[blk[nq]]++; markhex(hexid[w], -1); }
            if (fresh) defcnt[4]--; else { defcnt[d0 - 1]--; defcnt[d0]++; }
        }
        /* --- case 2: fresh hexagon, FIRST short pass (length BSPLIT) --- */
        if (!found && !hexused && sstate == 0 && !(SEAM && !same)) {
            int d0 = 5 - __builtin_popcount(omask[nq]);
            if (fresh) defcnt[4]++; else { defcnt[d0]--; defcnt[d0 - 1]++; }
            /* h* is entered TWICE, so X's hexagon must NOT block fresh orbits yet */
            if (FOD && fresh) freshcnt[blk[nq]]--;
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            witness[passes] = w; wlen_[passes] = BSPLIT;
            dfs(w, BSPLIT, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, 1, w, nfout, nxj, nrev + rv, 0, 0, passes + 1, nhub, nnj);
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
            if (FOD && fresh) freshcnt[blk[nq]]++;
            if (fresh) defcnt[4]--; else { defcnt[d0 - 1]--; defcnt[d0]++; }
        }
        /* --- case 3: the SECOND h* visit (forced word, length 6-BSPLIT) --- */
        if (!found && hexused && sstate == 1 && w == SIG[BSPLIT][vword]
            && (!YGAP || passes + 1 <= pX + YGAP)
            && !(SEAM && !same)                       /* t >= 2: the joint into Y is tau */
            && !(SYMCUT && passes + 1 > 122 - pX)) {  /* prefix <= suffix canonical form */
            int d0 = 5 - __builtin_popcount(omask[nq]);
            if (fresh) defcnt[4]++; else { defcnt[d0]--; defcnt[d0 - 1]++; }
            if (FOD) { markhex(hexid[w], 1); if (fresh) freshcnt[blk[nq]]--; }
            omask[nq] |= 1 << phse[w];
            witness[passes] = w; wlen_[passes] = 6 - BSPLIT;
            dfs(w, 6 - BSPLIT, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, 2, vword, nfout, nxj, nrev + rv, 0, 0, pX, nhub, nnj);
            omask[nq] &= ~(1 << phse[w]);
            if (FOD) { if (fresh) freshcnt[blk[nq]]++; markhex(hexid[w], -1); }
            if (fresh) defcnt[4]--; else { defcnt[d0 - 1]--; defcnt[d0]++; }
        }
        if (fresh) {
            EXC -= addexc;
            for (int j = 0; j < 5; j++) mcnt[ohex[nq][j]]--;
        }
        if (found) return;
    }
}

int main(int argc, char **argv) {
    if (argc < 7) {
        fprintf(stderr, "usage: %s b costcap orbcap xcap foutcap ecap [foutmin ygap rmax hcap dcap bforce revonly hregion yfresh exccap nodecap]\n", argv[0]);
        return 1;
    }
    build();
    BSPLIT = atoi(argv[1]); COSTCAP = atoi(argv[2]); ORBCAP = atoi(argv[3]);
    XCAP = atoi(argv[4]); FOUTCAP = atoi(argv[5]); ECAP = atoi(argv[6]);
    FOUTMIN = (argc > 7) ? atoi(argv[7]) : 0;
    YGAP = (argc > 8) ? atoi(argv[8]) : 0;
    RMAXARG = (argc > 9) ? atoi(argv[9]) : 0;
    HCAP = (argc > 10) ? atoi(argv[10]) : 0;
    DCAP = (argc > 11) ? atoi(argv[11]) : -1;
    BFORCE = (argc > 12) ? atoi(argv[12]) : 0;
    REVONLY = (argc > 13) ? atoi(argv[13]) : 0;
    HREGION = (argc > 14) ? atoi(argv[14]) : 0;
    YFRESH = (argc > 15) ? atoi(argv[15]) : 0;
    EXCCAP = (argc > 16) ? atoi(argv[16]) : (5 * (ORBCAP - 24));
    SEAM = (argc > 17) ? atoi(argv[17]) : 0;
    PMAX = (argc > 18) ? atoi(argv[18]) : 0;
    SYMCUT = (argc > 19) ? atoi(argv[19]) : 0;
    SHCAP = (argc > 20) ? atoi(argv[20]) : -1;
    HW = (argc > 21) ? atoi(argv[21]) : 1;
    HJCAP = (argc > 22) ? atoi(argv[22]) : 999;
    HUBMIN = (argc > 23) ? atoi(argv[23]) : 0;
    FOD = (argc > 24) ? atoi(argv[24]) : 0;
    NODECAP = (argc > 25) ? atoll(argv[25]) : 200000000000LL;
    RMAX = RMAXARG ? RMAXARG : (COSTCAP + 1 + FOUTCAP);
    SHRUNCAP = 5 * RMAX - TARGET;
    if (SHRUNCAP < 0) SHRUNCAP = 0;
    if (SHRUNCAP > 24) SHRUNCAP = 24;
    for (int s = 0; s <= 24; s++) BESTSEG[0][s] = 0;
    for (int m = 1; m < 8; m++)
        for (int s = 0; s <= 24; s++) {
            int b = 0;
            for (int a = 0; a <= s; a++) {
                int v = NTAB[a] + BESTSEG[m - 1][s - a];
                if (v > b) b = v;
            }
            BESTSEG[m][s] = b;
        }
    memset(omask, 0, sizeof omask);
    memset(defcnt, 0, sizeof defcnt);
    nodes = 0; capped = 0; found = 0; bestPasses = 0;
    HLO = HHI = 0;
    /* S6 relabelling is simply transitive on the 720 words and commutes with sigma, tau
       and all four light moves, so fixing the FIRST entry word is a complete reduction. */
    int start = 0;
    for (int firstIsShort = 0; firstIsShort < 2 && !found; firstIsShort++) {
        if (SEAM && firstIsShort) continue;   /* t' >= 2: X is never the first pass */
        int len = firstIsShort ? BSPLIT : 6;
        memset(blk, 0, sizeof blk);
        for (int j = 0; j < 6; j++) freshcnt[j] = 0;
        freshcnt[0] = NO;
        if (FOD) {
            if (!firstIsShort) markhex(hexid[start], 1);   /* a short first pass is X */
            freshcnt[blk[orbid[start]]]--;
        }
        omask[orbid[start]] = 1 << phse[start];
        defcnt[4] = 1;
        memset(mcnt, 0, sizeof mcnt);
        EXC = 0;
        for (int j = 0; j < 5; j++) mcnt[ohex[orbid[start]][j]] = 1;
        HLO = hlo[start]; HHI = hhi[start];
        witness[0] = start; wlen_[0] = len;
        dfs(start, len, 1, 0, 1, 1, 0, 1, firstIsShort ? 1 : 0, start, 0, 0, 0,
            firstIsShort ? 0 : 1, 0, firstIsShort ? 1 : 0, 0, 0);
        HLO = HHI = 0;
        omask[orbid[start]] = 0;
        memset(defcnt, 0, sizeof defcnt);
        memset(mcnt, 0, sizeof mcnt);
        EXC = 0;
    }
    printf("{\"b\": %d, \"costcap\": %d, \"orbcap\": %d, \"xcap\": %d, \"foutcap\": %d,"
           " \"ecap\": %d, \"foutmin\": %d, \"ygap\": %d, \"rmax\": %d, \"hcap\": %d, \"dcap\": %d, \"bforce\": %d,"
           " \"revonly\": %d, \"hregion\": %d, \"yfresh\": %d, \"exccap\": %d,"
           " \"seam\": %d, \"pmax\": %d, \"symcut\": %d, \"shcap\": %d, \"hw\": %d,"
           " \"hjcap\": %d, \"hubmin\": %d, \"fod\": %d, \"shruncap\": %d,"
           " \"verdict\": \"%s\", \"best_passes\": %d, \"nodes\": %lld}\n",
           BSPLIT, COSTCAP, ORBCAP, XCAP, FOUTCAP, ECAP, FOUTMIN, YGAP, RMAX, HCAP, DCAP,
           BFORCE, REVONLY, HREGION, YFRESH, EXCCAP, SEAM, PMAX, SYMCUT,
           SHCAP, HW, HJCAP, HUBMIN, FOD, SHRUNCAP,
           found ? "SAT" : (capped ? "UNKNOWN_CAP" : "UNSAT_COMPLETE"),
           bestPasses, nodes);
    if (found) {
        printf("{\"witness_words\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", witness[i], i + 1 < TARGET ? ", " : "");
        printf("], \"witness_lengths\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", wlen_[i], i + 1 < TARGET ? ", " : "");
        printf("]}\n");
    }
    return 0;
}
