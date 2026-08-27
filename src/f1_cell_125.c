/* 라운드 125 — 일반 `(k,F) = (1,1)` **끝까지 한 번에** 도는 정확 solver.
 *
 * 라운드 121 엔진(`src/f1_cell_121.c`)을 그대로 이어받되 세 가지가 다르다.
 *
 *  1. `O = 25`, `D = 4`, `EXC <= 5k = 5` — `(2,1)` 보다 훨씬 빡빡하다.
 *  2. `H` 가 **3 까지** 가므로 **진짜 무게-6 이음매 308개**를 새로 단다 (`HW` 비트 4).
 *  3. 무거운 이음매를 무게 다중집합으로 **조건화**한다 (`HW` + `HCAP` + `HUBMIN` + `HJCAP`).
 *
 * ### 라운드 125 §4 정정 — 무게-6 목록은 퇴화한다
 *
 * `{0..5}` 의 분해불가 순열은 461개지만, `w = 6` 은 강제 접두가 비어 있어서
 * `z = y∘pi` 의 실제 이음매 무게가 6 이 아닐 수 있다.  실측:
 *
 *     omega = 6 인 진짜 무게-6 이음매        308
 *     실제로는 더 가벼운 진짜 이음매          89  ( = 1+1+3+13+71, w<=5 목록과 일치)
 *     중간 순열이 끼어 단일 이음매가 아닌 것    64  ( = k! - indec(k) 의 합)
 *
 * `w < 6` 은 `z[:6-w] = y[w:]` 가 강제되어 `omega = w` 가 **항상** 성립한다(13/13, 71/71).
 * 이 엔진은 **308개만** 제공한다.  89개는 가벼운 목록이 이미 올바른 비용으로 제공하고,
 * 64개는 애초에 합법 전이가 아니다.  **거짓 기각 0.**
 *
 * 첫 짧은 pass `X` 는 뿌리로 방출하지 않고 DFS 내부의 상태 전이(`sstate` 0->1->2)로
 * 소비한다 (§8).  라운드 123 의 뿌리 폭발을 되풀이하지 않는다.
 *
 * 인자: b cost orb x fout e fmin ygap rmax hcap dcap bforce revonly hregion yfresh
 *       exccap seam pmax symcut shcap hw hjcap hubmin fod ygapmin nodecap rootmode
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
static int BSPLIT, COSTCAP, ORBCAP, SHRUNCAP, RMAX, XCAP, FOUTCAP, ECAP, FOUTMIN,
           YGAP, HCAP, RMAXARG, DCAP, BFORCE, REVONLY, HREGION, YFRESH, EXCCAP,
           SEAM, PMAX, SYMCUT, SHCAP, HW, HJCAP, HUBMIN, FOD, YGAPMIN;
static long long NODECAP, nodes;
static int ROOTMODE;                 /* §17 control: stop at the first short pass */
static long long roots, prefix_states;
static int maxq;
static long long psq[130], rtq[130];
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
    if (ROOTMODE && sstate == 0) { prefix_states++; if (passes < 130) psq[passes]++; }
    if (passes == TARGET) {
        /* O = 24 + k is exact, and H must really reach this group's value */
        if (orbits == ORBCAP && hub >= HUBMIN) found = 1;
        return;
    }
    /* admissible prune: finishing the current run yields at most 5 - runlen more passes,
       every further run yields at most 5, and every further run needs an inter-run joint
       which costs 1 unless it is one of the at most FOUTCAP free short-pass exits. */
    if (!ROOTMODE) {
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
    if (!ROOTMODE) {
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
    if (!ROOTMODE && !capacity_ok(orbid[u], ECAP - rev, passes, orbits)) return;
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
    int succ[4 + NH4 + NH5 + NH6];
    int scost[4 + NH4 + NH5 + NH6], shub[4 + NH4 + NH5 + NH6];
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
        if ((HW & 4) && hub + 3 <= HCAP)
            for (int h = 0; h < NH6; h++) {
                succ[nsucc] = M6[h][exitw]; scost[nsucc] = 1; shub[nsucc] = 3; nsucc++;
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
            if (ROOTMODE) {
                roots++;
                if (passes < 130) rtq[passes]++;
                if (passes > maxq) maxq = passes;
            } else
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
            && !(SYMCUT && passes + 1 > 122 - pX)     /* prefix <= suffix canonical form */
            && !(YGAPMIN && passes + 1 < pX + YGAPMIN)) {  /* dist(X,Y) >= YGAPMIN */
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
    if (argc > 1 && atoi(argv[1]) == -6) {      /* self-check: dump the 308 weight-6 actions */
        build();
        for (int h = 0; h < NH6; h++)
            for (int j = 0; j < 6; j++) printf("%d%s", H6ACT[h][j], j == 5 ? "\n" : " ");
        return 0;
    }
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
    YGAPMIN = (argc > 25) ? atoi(argv[25]) : 0;
    NODECAP = (argc > 26) ? atoll(argv[26]) : 200000000000LL;
    ROOTMODE = (argc > 27) ? atoi(argv[27]) : 0;
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
    roots = 0; prefix_states = 0; maxq = 0;
    memset(psq, 0, sizeof psq); memset(rtq, 0, sizeof rtq);
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
           " \"hjcap\": %d, \"hubmin\": %d, \"fod\": %d, \"ygapmin\": %d, \"shruncap\": %d,"
           " \"verdict\": \"%s\", \"best_passes\": %d, \"nodes\": %lld,"
           " \"rootmode\": %d, \"roots\": %lld, \"prefix_states\": %lld,"
           " \"max_prefix_q\": %d}\n",
           BSPLIT, COSTCAP, ORBCAP, XCAP, FOUTCAP, ECAP, FOUTMIN, YGAP, RMAX, HCAP, DCAP,
           BFORCE, REVONLY, HREGION, YFRESH, EXCCAP, SEAM, PMAX, SYMCUT,
           SHCAP, HW, HJCAP, HUBMIN, FOD, YGAPMIN, SHRUNCAP,
           found ? "SAT" : (capped ? "UNKNOWN_CAP" : "UNSAT_COMPLETE"),
           bestPasses, nodes, ROOTMODE, roots, prefix_states, maxq);
    if (ROOTMODE) {
        printf("{\"prefix_states_by_q\": [");
        for (int q = 0; q <= maxq + 1; q++) printf("%lld%s", psq[q], q <= maxq ? ", " : "");
        printf("], \"roots_by_q\": [");
        for (int q = 0; q <= maxq + 1; q++) printf("%lld%s", rtq[q], q <= maxq ? ", " : "");
        printf("]}\n");
    }
    if (found) {
        printf("{\"witness_words\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", witness[i], i + 1 < TARGET ? ", " : "");
        printf("], \"witness_lengths\": [");
        for (int i = 0; i < TARGET; i++) printf("%d%s", wlen_[i], i + 1 < TARGET ? ", " : "");
        printf("]}\n");
    }
    return 0;
}
