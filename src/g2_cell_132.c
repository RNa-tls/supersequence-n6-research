/* 라운드 132 — 일반 `(k,G) = (4,2)` 칸을 끝까지 도는 정확 solver.
 *
 * 바깥 좌표는 `(k, G)` 다 (`F` 는 내부 좌표일 뿐이다).  `G = 2` 이므로
 *
 *     P = 122,   O = 24 + k = 28,   D = 5k - G = 18,   L = 846 + S + H
 *     L <= 871  <=>  k + e + x + H - f_out <= 2
 *
 * 이고 `k = 4` 를 넣으면 `f_out >= e + x + H + 2` 인데 라운드 129 의 `f_out <= F + e`
 * (`F <= 2`) 와 맞물려 **`x = H = 0`, `F = 2`, `f_out = e + 2`, `S = 25`** 가 강제된다.
 *
 * 따라서 이 엔진은
 *   * 무거운 이음매(무게 4/5/6)를 **하나도 제공하지 않는다** (`H = 0`);
 *   * `x = 0` 이라 궤도 내부 비용-1 이음매를 전부 거부한다 (`XCAP = 0`);
 *   * `G = 2` 의 **짧은 pass 상태 기계**를 새로 갖는다 — 라운드 125 의 `sstate 0->1->2`
 *     기계는 "두 번 진입된 육각형 하나 + 짧은 pass 둘" 전용이라 여기서는 쓸 수 없다.
 *
 * ### 유형 A — 육각형 하나를 세 번 진입
 * 세 호(arc)는 육각형의 sigma-순환을 자르며 진입 단어가 `v`, `sigma^{l0}(v)`,
 * `sigma^{l0+l1}(v)`, 길이가 `l0, l1, l2` (`l0+l1+l2 = 6`) 다.  `F = 2` 는 세 pass 의
 * walk 순서가 `nu`-순서의 순환 회전인 것과 동치이므로(라운드 129), walk 에서 세 호는
 * **정확히 `nu` 순서로** 나타난다.  상태는 `astate in {0,1,2,3}` 와 첫 호의 진입 단어뿐이다.
 *
 * ### 유형 B — 서로 다른 두 육각형을 두 번씩 진입
 * 각 육각형은 `(v, b)` 와 `(sigma^b(v), 6-b)` 두 호를 갖는다.  두 슬롯을 독립으로 열고
 * 닫으며(끼워넣기 허용), 새 슬롯은 반드시 **신선한 육각형**에서 열린다.
 *
 * 인자: mtype orbcap costcap xcap foutcap foutmin ecap dcap exccap fod p1 p2 shcap rmax nodecap
 *       (mtype 0 = A: p1 = l0, p2 = l1;  mtype 1 = B: p1 = b1, p2 = b2)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define NW 720
#define NO 144
#define NH 120
#ifndef TARGET
#define TARGET 122
#endif

static int hexid[NW], orbid[NW], phse[NW];
static int SIG[6][NW];
static int M2[NW], M3a[NW], M3b[NW], M3c[NW];
#define NH4 13
#define NH5 71
#define NH6 308
static int M4[NH4][NW];
static int H4ACT[NH4][6];
static int M5[NH5][NW];
static int H5ACT[NH5][6];
static int M6[NH6][NW];
static int H6ACT[NH6][6];
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
    {   /* 진짜 무게-6 이음매 308개: action = {0..5} 의 분해불가 순열 pi 중
           omega(y, y∘pi) = 6 인 것.  omega < 6 은 pi(i) = k+i (i <= 5-k) 와 동치이므로
           그런 pi 를 걸러 내면 된다 (라운드 125 §4). */
        int pi[6], idx = 0;
        for (int c = 0; c < 720; c++) {
            int t = c, used[6] = {0};
            for (int i = 0; i < 6; i++) {          /* c 번째 순열 (사전순) */
                int f[6] = {120, 24, 6, 2, 1, 1};
                int q = t / f[i]; t %= f[i];
                int v = 0;
                for (int j = 0; j < 6; j++) { if (used[j]) continue; if (q == 0) { v = j; break; } q--; }
                pi[i] = v; used[v] = 1;
            }
            int mx = -1, ok = 1;                    /* 분해불가 */
            for (int j = 0; j < 5; j++) { if (pi[j] > mx) mx = pi[j]; if (mx == j) { ok = 0; break; } }
            if (!ok) continue;
            int degen = 0;                          /* omega < 6 이면 버린다 */
            for (int k = 1; k < 6 && !degen; k++) {
                int hit = 1;
                for (int i = 0; i <= 5 - k; i++) if (pi[i] != k + i) { hit = 0; break; }
                if (hit) degen = 1;
            }
            if (degen) continue;
            if (idx >= NH6) { fprintf(stderr, "weight-6 overflow\n"); exit(2); }
            for (int j = 0; j < 6; j++) H6ACT[idx][j] = pi[j];
            idx++;
        }
        if (idx != NH6) { fprintf(stderr, "genuine weight-6 tail count %d != 308\n", idx); exit(2); }
        for (int y = 0; y < NW; y++)
            for (int h = 0; h < NH6; h++) {
                int a[6];
                for (int j = 0; j < 6; j++) a[j] = perm[y][H6ACT[h][j]];
                M6[h][y] = rank_of(a);
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
static int COSTCAP, ORBCAP, SHRUNCAP, RMAX, XCAP, FOUTCAP, ECAP, FOUTMIN,
           HCAP, DCAP, EXCCAP, SHCAP, HW, HJCAP, HUBMIN, FOD;
static long long NODECAP, nodes;
static int capped, found, bestPasses;
static unsigned char omask[NO];
static int defcnt[5];
static uint64_t HLO, HHI;
#ifdef CHECKMASK
static long long maskchecks = 0, maskfail = 0;
#endif
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
/* ------------------------------------------------- G = 2 short-pass state machine ---- */
static int MTYPE;                 /* 0 = type A (one tripled hexagon), 1 = type B */
static int P1, P2;                /* A: l0, l1   B: b1, b2 */
static int L2;                    /* A: l2 = 6 - l0 - l1 */
static int AORDER;                /* A: 1 = nu-order only (F = 2); 0 = any order (control) */
/* ---- forced free-exit pattern (Round 130 section 3) --------------------------------
   With e = 0 every free exit is case (i), hence a nu-ASCENT.  In type A with F = 2 the
   walk order is arc0 < arc1 < arc2, so the ascents are arc0 and arc1 and arc2 can NEVER
   exit freely.  In type B each 2-cycle has exactly one ascent - the pass that opens the
   slot - so with e = 0 exactly the two openers exit freely.  When f_out equals the number
   of short passes every one of them exits freely.  FREESPEC names the short passes that
   MUST exit free; when FREEON is set, every other short pass must NOT.
   slot ids:  type A -> arc index 0,1,2      type B -> 2*slot + (0 = open, 1 = close)  */
static int FREESPEC, FREEON;
/* ---- case-(i) locality lock (Round 130 section 4/5) --------------------------------
   A free-exiting pass p in CASE (i) has its successor tau(entry(nu(p))) starting the very
   run that contains nu(p).  So from that successor until nu(p) is placed the walk cannot
   leave that orbit.  Case (i) is FORCED when e = 0 (a case-(ii) pass would need an orbit
   with two runs), and in type A with e = 1 and f_out = 3 exactly one pass is case (ii) and
   it must be arc2, so arcs 0 and 1 are case (i).  LOCKSPEC names the passes known to be
   case (i).  Sound only for the subcases where that is proved. */
static int LOCKSPEC;
/* ---- Round 131: Theorem 131.1 -----------------------------------------------------
   Under the equality f_out = F + e that every (k,G) = (4,2) subcase forces:
     (a) every nu-ASCENT short pass exits freely;
     (b) exactly e short passes are free nu-DESCENTS and they open EVERY repeat run, so
         no omega >= 3 joint may open one and the repeat orbits are exactly
         orb(entry(nu(d))) for the free descents d;
     (c) an ascent's locality lock can break ONLY IF its target orbit Q(p) is one of the
         repeat orbits of (b).  (The n = 4 census REFUTES the stronger "no lock ever
         breaks": 288 of 1734 equality walks break one.)
   REVSPEC names the short passes allowed to open a repeat run - the free descents.
   LOCK0MODE resolves the one case where (c) cannot be decided when the lock would be
   applied (type B opener 0, while opener 1 is still unplaced):
     2 = auto   - apply unless a KNOWN repeat orbit equals the target (no unknown arises)
     1 = alpha  - assume the lock holds and apply it
     0 = beta   - do not apply it, and REQUIRE orb(entry(opener1)) == Q(opener0), the
                  necessary condition for the lock to break.
   alpha and beta together cover every walk. */
/* ---- Round 132 ---------------------------------------------------------------------
   Theorem 132.1: in every type-B (4,2) subcase the LATER opener's locality lock holds
   unconditionally, so a branch where T_1 equals a known repeat orbit is EMPTY - we PRUNE
   there instead of merely dropping the lock (Round 131 only dropped it).

   LOCK0MODE now names the structural model, not just a lock guess:
     2 = auto        - Round-131 behaviour (apply unless a known repeat orbit matches)
     1 = D-alpha     - opener_0's lock HOLDS and orb(entry(opener1)) != orb(entry(opener0))
     3 = Model T     - opener_0's lock HOLDS and orb(entry(opener1)) == orb(entry(opener0))
     0 = D-beta0     - opener_0's lock BREAKS; requires orb(entry(opener1)) == Q(opener0)
   1 and 3 together cover exactly the walks where opener_0's lock holds, and 0 covers the
   rest, so {0,1,3} is exhaustive.  D-beta1 does not exist (Theorem 132.1).

   ORDPIN pins the proved walk-order chain (0 = off, keeps Round-131 node counts exactly):
     1 = alpha chain: closer_X = opener_X + 5 for both slots, and opener_1 > closer_0
     2 = beta  nest : opener_1 = opener_0 + u with 1 <= u <= 4,
                      closer_1 = opener_1 + 5,  closer_0 = opener_0 + 10               */
static int REVSPEC, LOCK0MODE, ORDPIN;
static int bpos[2];               /* type B: walk position of each slot's opener */
static int amask, av;             /* type A: which of the 3 arcs are placed, and arc 0's entry */
static int bo, bc, bpend[2], bplen[2], bov[2];

static int revorb_of(int d, int *known) {
    if (MTYPE == 0) {             /* nu(arc2) = arc0 */
        if (amask & 1) { *known = 1; return orbid[av]; }
        *known = 0; return -1;
    }
    int s = d >> 1;               /* nu(close_s) = open_s */
    if (s < bo) { *known = 1; return orbid[bov[s]]; }
    *known = 0; return -1;
}

static int nusid(int sid) {
    if (MTYPE == 0) return (sid + 1) % 3;
    return (sid & 1) ? (sid - 1) : (sid + 1);      /* open_s <-> close_s */
}

static int NSLOT;                 /* type B: 2 slots; mtype 2 (G = 1 control): 1 slot */

/* the three arcs of the tripled hexagon, in nu-order starting from the WALK-FIRST arc */
static int a_word(int i) {
    if (i == 0) return av;
    if (i == 1) return SIG[P1][av];
    return SIG[P1 + P2][av];
}
static int a_len(int i) { return i == 0 ? P1 : (i == 1 ? P2 : L2); }

static int all_short_placed(void) {
    return MTYPE == 0 ? (amask == 7) : (bc == NSLOT);
}
static int shorts_total(void) { return MTYPE == 0 ? 3 : 2 * NSLOT; }
static int shorts_placed(void) {
    return MTYPE == 0 ? __builtin_popcount(amask) : (bo + bc);
}

static void dfs(int u, int len, int passes, int cost, int orbits, int runs,
                int shrun, int runlen, int fout, int nrev, int xj, int hub,
                int njoint, int segpasses, int segsh, int curfree,
                int lockorb, int lockwait, int pend, int cursid, int q0orb) {
    if (found) return;
    if (++nodes > NODECAP) { capped = 1; return; }
#ifdef CHECKMASK
    /* Round 131 section 18 - EVERY pass, short or full, marks its hexagon as entered.
       #entered hexagons must equal #passes minus the re-entries of an already
       entered hexagon (type A: the 2nd and 3rd arc; type B: each closer). */
    {
        int pc = __builtin_popcountll(HLO) + __builtin_popcountll(HHI);
        int extra = (MTYPE == 0)
                  ? (amask ? __builtin_popcount(amask) - 1 : 0)
                  : bc;
        maskchecks++;
        if (pc != passes - extra) { maskfail++; }
    }
#endif
    if (passes > bestPasses) bestPasses = passes;
    if (passes == TARGET) {
        /* r = O + e and #repeat runs = e are both EXACT for the subcase. */
        if (orbits == ORBCAP && all_short_placed() && fout >= FOUTMIN && hub >= HUBMIN
            && nrev == ECAP && runs == RMAX)
            found = 1;
        return;
    }
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
    {
        int sleft = SHRUNCAP - shrun;
        if (sleft < 0) return;
        if (sleft > 24) sleft = 24;
        int idx = segsh + sleft; if (idx > 24) idx = 24;
        int segs = (shorts_total() - shorts_placed()) + (XCAP - xj)
                 + (ECAP - nrev) + (HCAP - hub);
        if (segs > 7) segs = 7;
        int bound = (passes - segpasses) + NTAB[idx] + BESTSEG[segs][sleft];
        if (bound < TARGET) return;
    }
    if (DCAP >= 0 && !dfeasible(orbid[u], ECAP - nrev)) return;
    if (!capacity_ok(orbid[u], ECAP - nrev, passes, orbits)) return;
    if (FOD && DCAP >= 0
        && dcommitted(orbid[u], ECAP - nrev) + freshdeficit(ORBCAP - orbits) > DCAP) return;
    {
        int isshort = (len < 6);
        int avail = (shorts_total() - shorts_placed()) + (isshort ? 1 : 0);
        if (fout + avail < FOUTMIN) return;
    }

    int isshort_ = (len < 6);
    int avail_ = (shorts_total() - shorts_placed()) + (isshort_ ? 1 : 0);
    int forcefree = (isshort_ && fout + avail_ == FOUTMIN);
    int exitw = SIG[len - 1][u];
    int curorb = orbid[u];
    int succ[4 + NH4 + NH5 + NH6];
    int scost[4 + NH4 + NH5 + NH6], shub[4 + NH4 + NH5 + NH6];
    succ[0] = M2[exitw];  succ[1] = M3a[exitw];
    succ[2] = M3b[exitw]; succ[3] = M3c[exitw];
    scost[0] = 0; scost[1] = 1; scost[2] = 1; scost[3] = 1;
    shub[0] = shub[1] = shub[2] = shub[3] = 0;
    int nsucc = 4;
    if (njoint < HJCAP) {
        if ((HW & 1) && hub + 1 <= HCAP)
            for (int h = 0; h < NH4; h++) {
                succ[nsucc] = M4[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 1; nsucc++;
            }
        if ((HW & 2) && hub + 2 <= HCAP)
            for (int h = 0; h < NH5; h++) {
                succ[nsucc] = M5[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 2; nsucc++;
            }
        if ((HW & 4) && hub + 3 <= HCAP)
            for (int h = 0; h < NH6; h++) {
                succ[nsucc] = M6[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 3; nsucc++;
            }
    }

    int silo = (curfree == 2) ? 1 : 0;
    int sihi = (curfree == 1) ? 1 : (forcefree ? 1 : nsucc);
    for (int si = silo; si < sihi && !found; si++) {
        int w = succ[si];
        int c = scost[si];
        int hb = shub[si];
        if (cost + c > COSTCAP) continue;
        if (SHCAP >= 0 && cost + c + hub + hb > SHCAP) continue;
        int nq = orbid[w];
        if (lockorb >= 0 && nq != lockorb) continue;      /* case-(i) locality lock */
        int same = (nq == curorb);
        int nruns = runs, nsh = shrun, nrunlen = runlen + 1, nfout = fout;
        int nxj = xj, nnrev = nrev, nhub = hub + hb, nnj = njoint + (hb ? 1 : 0);
        if (same) {
            if (c == 1) { nxj = xj + 1; if (nxj > XCAP) continue; }
            if (runlen + 1 > 5) continue;
        } else {
            if (c == 0) {
                nfout = fout + 1;
                if (nfout > FOUTCAP) continue;
            }
            nruns = runs + 1;
            nsh = shrun + (5 - runlen);
            if (nsh > SHRUNCAP) continue;
            if (nruns > RMAX) continue;
            nrunlen = 1;
        }
        int hexused = (HLO & hlo[w]) || (HHI & hhi[w]);
        int fresh = (omask[nq] == 0);
        int rv = (!same && !fresh) ? 1 : 0;
        /* Theorem 131.1(b): a repeat run is opened by a FREE exit of a designated
           nu-descent short pass and by nothing else. */
        if (rv && REVSPEC >= 0) {          /* REVSPEC < 0 disables the rule entirely */
            if (c != 0) continue;
            if (cursid < 0 || !((REVSPEC >> cursid) & 1)) continue;
        }
        if (nnrev + rv > ECAP) continue;
        if (fresh && orbits + 1 > ORBCAP) continue;
        if (omask[nq] >> phse[w] & 1) continue;
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

        int opt_len[4], opt_kind[4], opt_slot[4], nopt = 0;
        /* kind 0 = full pass; 1 = type-A arc; 2 = type-B open; 3 = type-B close */
        if (!hexused) { opt_len[nopt] = 6; opt_kind[nopt] = 0; opt_slot[nopt] = -1; nopt++; }
        if (MTYPE == 0) {
            if (amask == 0) {
                if (!hexused) { opt_len[nopt] = P1; opt_kind[nopt] = 1; opt_slot[nopt] = 0; nopt++; }
            } else if (amask != 7 && hexused) {
                int lo = AORDER ? __builtin_popcount(amask) : 0;
                int hi = AORDER ? __builtin_popcount(amask) : 2;
                for (int i = lo; i <= hi; i++)
                    if (!(amask >> i & 1) && w == a_word(i)) {
                        opt_len[nopt] = a_len(i); opt_kind[nopt] = 1; opt_slot[nopt] = i; nopt++;
                    }
            }
        } else {
            if (bo < NSLOT && !hexused) {
                opt_len[nopt] = (bo == 0) ? P1 : P2;
                opt_kind[nopt] = 2; opt_slot[nopt] = bo; nopt++;
            }
            for (int s = 0; s < bo; s++)
                if (bpend[s] >= 0 && w == bpend[s] && hexused) {
                    opt_len[nopt] = bplen[s]; opt_kind[nopt] = 3; opt_slot[nopt] = s; nopt++;
                }
        }

        for (int oi = 0; oi < nopt && !found; oi++) {
            int nlen = opt_len[oi], kind = opt_kind[oi], slot = opt_slot[oi];
            /* ---- Round 132: structural model of the second opener ------------------ */
            if (MTYPE != 0 && kind == 2 && slot == 1 && bov[0] >= 0) {
                /* beta: opener_0's lock breaks only if orb(entry(opener1)) = Q(opener0). */
                if (LOCK0MODE == 0 && (q0orb < 0 || nq != q0orb)) continue;
                /* Model T needs the two openers to share an orbit; D-alpha forbids it. */
                if (LOCK0MODE == 3 && nq != orbid[bov[0]]) continue;
                if (LOCK0MODE == 1 && nq == orbid[bov[0]]) continue;
            }
            /* ---- Round 132: proved walk-order chains ------------------------------- */
            if (ORDPIN == 1 && MTYPE != 0) {          /* alpha chain */
                if (kind == 3 && bpos[slot] >= 0 && passes != bpos[slot] + 5) continue;
                if (kind == 2 && slot == 1 && bpos[0] >= 0 && passes <= bpos[0] + 5) continue;
            } else if (ORDPIN == 2 && MTYPE != 0) {   /* beta nest */
                if (kind == 2 && slot == 1 && bpos[0] >= 0
                    && (passes < bpos[0] + 1 || passes > bpos[0] + 4)) continue;
                if (kind == 3 && slot == 1 && bpos[1] >= 0 && passes != bpos[1] + 5) continue;
                if (kind == 3 && slot == 0 && bpos[0] >= 0 && passes != bpos[0] + 10) continue;
            }
            int completes = (kind == 0) || (kind == 1 && amask == 3) || (kind == 3);
            int d0 = 5 - __builtin_popcount(omask[nq]);
            if (fresh) defcnt[4]++; else { defcnt[d0]--; defcnt[d0 - 1]++; }
            if (FOD) {
                if (completes) markhex(hexid[w], 1);
                if (fresh) freshcnt[blk[nq]]--;
            }
            omask[nq] |= 1 << phse[w];
            /* EVERY pass marks its hexagon as entered - that is what blocks a later full
               pass or a second slot from re-entering it.  `completes` is a DIFFERENT
               notion: the hexagon is fully consumed only on its LAST arc, and only then
               does it block fresh orbits (markhex). */
            uint64_t slo = hlo[w], shi = hhi[w];
            int hadlo = (HLO & slo) != 0, hadhi = (HHI & shi) != 0;
            HLO |= slo; HHI |= shi;
            int sa = amask, sav = av, sbo = bo, sbc = bc;
            int sp0 = bpend[0], sp1 = bpend[1], sl0 = bplen[0], sl1 = bplen[1];
            int sv0 = bov[0], sv1 = bov[1], sq0 = bpos[0], sq1 = bpos[1];
            if (kind == 1) { if (amask == 0) av = w; amask |= 1 << slot; }
            else if (kind == 2) { bpend[slot] = SIG[nlen][w]; bplen[slot] = 6 - nlen;
                                  bov[slot] = w; bpos[slot] = passes; bo++; }
            else if (kind == 3) { bpend[slot] = -1; bc++; }
            int sid = (kind == 1) ? slot : ((kind == 2) ? 2 * slot : 2 * slot + 1);
            int cf = (kind == 0) ? 0
                     : (!FREEON ? 0 : ((FREESPEC >> sid & 1) ? 1 : 2));
            int nlo = lockorb, nlw = lockwait, nq0 = q0orb;
            if (pend >= 0 && c == 0 && REVSPEC < 0) {
                nlo = nq; nlw = nusid(pend);   /* Round-130 unconditional lock */
            } else if (pend >= 0 && c == 0) {
                int unknown = 0, risky = 0;
                for (int d = 0; d < 4; d++) {
                    if (!((REVSPEC >> d) & 1)) continue;
                    int kn, ro = revorb_of(d, &kn);
                    if (!kn) unknown = 1; else if (ro == nq) risky = 1;
                }
                /* Theorem 132.1 - the LATER opener's lock cannot break, so a risky
                   branch there is empty and we prune rather than drop the lock. */
                if (MTYPE != 0 && pend == 2 && risky) goto undo;
                int apply;
                if (MTYPE != 0 && pend == 0 && (LOCK0MODE == 1 || LOCK0MODE == 3))
                    apply = 1;              /* alpha/T branch: the lock is assumed to hold */
                else
                    apply = risky ? 0 : (unknown ? 0 : 1);
                if (apply) { nlo = nq; nlw = nusid(pend); }
                if (LOCK0MODE == 0 && MTYPE != 0 && pend == 0) nq0 = nq;
            }
            if (kind != 0 && nlw == sid) { nlo = -1; nlw = -1; }
            int npend = (kind != 0 && (LOCKSPEC >> sid & 1)) ? sid : -1;
            witness[passes] = w; wlen_[passes] = nlen;
            dfs(w, nlen, passes + 1, cost + c, orbits + (fresh ? 1 : 0), nruns, nsh,
                nrunlen, nfout, nnrev + rv, nxj, nhub, nnj,
                (kind != 0) ? 0 : (hb ? 1 : nsegp),
                (kind != 0) ? 0 : (hb ? 0 : nsegs), cf, nlo, nlw, npend,
                (kind == 0) ? -1 : sid, nq0);
        undo:
            amask = sa; av = sav; bo = sbo; bc = sbc;
            bpend[0] = sp0; bpend[1] = sp1; bplen[0] = sl0; bplen[1] = sl1;
            bov[0] = sv0; bov[1] = sv1; bpos[0] = sq0; bpos[1] = sq1;
            if (!hadlo) HLO &= ~slo;
            if (!hadhi) HHI &= ~shi;
            omask[nq] &= ~(1 << phse[w]);
            if (FOD) {
                if (fresh) freshcnt[blk[nq]]++;
                if (completes) markhex(hexid[w], -1);
            }
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
    if (argc < 18) {
        fprintf(stderr, "usage: %s mtype orbcap costcap xcap foutcap foutmin ecap dcap "
                        "exccap fod p1 p2 shcap rmax hcap hw hjcap [hubmin] [nodecap] "
                        "[aorder] [freespec] [freeon] [lockspec] [revspec] [lock0mode] [ordpin]\n",
                argv[0]);
        return 1;
    }
    build();
    MTYPE   = atoi(argv[1]);
    ORBCAP  = atoi(argv[2]);
    COSTCAP = atoi(argv[3]);
    XCAP    = atoi(argv[4]);
    FOUTCAP = atoi(argv[5]);
    FOUTMIN = atoi(argv[6]);
    ECAP    = atoi(argv[7]);
    DCAP    = atoi(argv[8]);
    EXCCAP  = atoi(argv[9]);
    FOD     = atoi(argv[10]);
    P1      = atoi(argv[11]);
    P2      = atoi(argv[12]);
    SHCAP   = atoi(argv[13]);
    RMAX    = atoi(argv[14]);
    HCAP    = atoi(argv[15]);
    HW      = atoi(argv[16]);
    HJCAP   = atoi(argv[17]);
    HUBMIN  = (argc > 18) ? atoi(argv[18]) : 0;
    NODECAP = (argc > 19) ? atoll(argv[19]) : 200000000000LL;
    AORDER  = (argc > 20) ? atoi(argv[20]) : 1;
    FREESPEC = (argc > 21) ? atoi(argv[21]) : 0;
    FREEON   = (argc > 22) ? atoi(argv[22]) : 0;
    LOCKSPEC = (argc > 23) ? atoi(argv[23]) : 0;
    REVSPEC   = (argc > 24) ? atoi(argv[24]) : -1;   /* -1 = Round-130 behaviour */
    LOCK0MODE = (argc > 25) ? atoi(argv[25]) : 2;
    ORDPIN    = (argc > 26) ? atoi(argv[26]) : 0;
    L2 = 6 - P1 - P2;
    if (MTYPE == 0 && (P1 < 1 || P2 < 1 || L2 < 1)) {
        fprintf(stderr, "type A needs l0,l1,l2 >= 1\n"); return 2;
    }
    if (MTYPE >= 1 && (P1 < 1 || P1 > 5 || P2 < 1 || P2 > 5)) {
        fprintf(stderr, "type B needs b1,b2 in 1..5\n"); return 2;
    }
    NSLOT = (MTYPE == 2) ? 1 : 2;
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
    nodes = 0; capped = 0; found = 0; bestPasses = 0;

    int start = 0;
    int firstlens[2], firstkinds[2], nfirst = 0;
    firstlens[nfirst] = 6; firstkinds[nfirst] = 0; nfirst++;
    firstlens[nfirst] = P1; firstkinds[nfirst] = (MTYPE == 0) ? 1 : 2; nfirst++;
    for (int fi = 0; fi < nfirst && !found; fi++) {
        int len = firstlens[fi], kind = firstkinds[fi];
        memset(omask, 0, sizeof omask);
        memset(defcnt, 0, sizeof defcnt);
        memset(mcnt, 0, sizeof mcnt);
        memset(blk, 0, sizeof blk);
        for (int j = 0; j < 6; j++) freshcnt[j] = 0;
        freshcnt[0] = NO;
        EXC = 0; HLO = HHI = 0;
        amask = 0; av = -1; bo = bc = 0;
        bpend[0] = bpend[1] = -1; bplen[0] = bplen[1] = 0;
        bov[0] = bov[1] = -1; bpos[0] = bpos[1] = -1;
        int completes = (kind == 0);
        if (FOD) {
            if (completes) markhex(hexid[start], 1);
            freshcnt[blk[orbid[start]]]--;
        }
        omask[orbid[start]] = 1 << phse[start];
        defcnt[4] = 1;
        for (int j = 0; j < 5; j++) mcnt[ohex[orbid[start]][j]] = 1;
        HLO = hlo[start]; HHI = hhi[start];   /* every pass marks its hexagon entered */
        if (kind == 1) { av = start; amask = 1; }
        if (kind == 2) { bpend[0] = SIG[len][start]; bplen[0] = 6 - len;
                         bov[0] = start; bpos[0] = 0; bo = 1; }
        witness[0] = start; wlen_[0] = len;
        int cf0 = (kind == 0) ? 0 : (!FREEON ? 0 : ((FREESPEC & 1) ? 1 : 2));
        int pd0 = (kind != 0 && (LOCKSPEC & 1)) ? 0 : -1;
        dfs(start, len, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, completes ? 1 : 0, 0, cf0,
            -1, -1, pd0, (kind == 0) ? -1 : 0, -1);
    }

    printf("{\"mtype\": %d, \"orbcap\": %d, \"costcap\": %d, \"xcap\": %d, \"foutcap\": %d,"
           " \"foutmin\": %d, \"ecap\": %d, \"dcap\": %d, \"exccap\": %d, \"fod\": %d,"
           " \"p1\": %d, \"p2\": %d, \"p3\": %d, \"shcap\": %d, \"rmax\": %d, \"hcap\": %d,"
           " \"hw\": %d, \"hjcap\": %d, \"hubmin\": %d, \"freespec\": %d, \"freeon\": %d, \"lockspec\": %d,"
           " \"revspec\": %d, \"lock0mode\": %d, \"ordpin\": %d,"
           " \"shruncap\": %d, \"verdict\": \"%s\", \"best_passes\": %d, \"nodes\": %lld}\n",
           MTYPE, ORBCAP, COSTCAP, XCAP, FOUTCAP, FOUTMIN, ECAP, DCAP, EXCCAP, FOD,
           P1, P2, MTYPE == 0 ? L2 : 6 - P2, SHCAP, RMAX, HCAP, HW, HJCAP, HUBMIN,
           FREESPEC, FREEON, LOCKSPEC, REVSPEC, LOCK0MODE, ORDPIN, SHRUNCAP,
           found ? "SAT" : (capped ? "UNKNOWN_CAP" : "UNSAT_COMPLETE"),
           bestPasses, nodes);
#ifdef CHECKMASK
    fprintf(stderr, "{\"maskchecks\": %lld, \"maskfail\": %lld}\n", maskchecks, maskfail);
#endif
    if (found) {
        printf("{\"witness_words\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", witness[i], i + 1 < TARGET ? ", " : "");
        printf("], \"witness_lengths\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", wlen_[i], i + 1 < TARGET ? ", " : "");
        printf("]}\n");
    }
    return 0;
}
