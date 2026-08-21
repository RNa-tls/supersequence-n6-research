/* 라운드 115 — F=0 전용 all-light **사슬 용량** 전수 탐색기.
 *
 * 모델(정확한 F=0 구조에서 나온다):
 *   * pass 는 120개, 육각형도 120개이고 F=0 이면 각 육각형에 pass 가 정확히 하나다
 *     -> 사용된 두 단어는 절대 같은 육각형에 있을 수 없다  (하드 제약)
 *   * run = 한 E-궤도 안의 극대 연속 pass 구간.  run 길이 l 마다 (5-l) 을
 *     shortfall 풀에서 낸다.  전역 항등식:  sum_runs (5-l) = 5r - 120 = 5k + 5e
 *   * 사슬 = 경량 연결자(W3b/W3c)로 이어진 극대 run 열
 *   * b  = (사슬 안의 여분 run) + (run 내부 비자유 호)      전역 풀 e + x
 *   * g  = 다른 사슬로 넘기는 미완성 궤도 토큰               전역 풀 2e
 *   * s  = 영구 미사용 phase                                  전역 풀 5k
 *
 * 출력: 주어진 (b,g,s) 예산에서 사슬 하나가 가질 수 있는 최대 pass 수 / 궤도 수 / run 수.
 * 캡에 걸리면 UNKNOWN 을 출력한다 — 캡 도달은 절대 상한 증명이 아니다.
 *
 * 사용법:  ./chain_capacity_115 <b> <g> <s> [node_cap]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define NW 720
#define NO 144
#define NH 120

static int hexid[NW], orbid[NW], phse[NW];
static int word_at[NO][5];
static int mvW3b[NW], mvW3c[NW];
static uint64_t hlo[NW], hhi[NW];

static int perm[NW][6];

static int rank_of(const int *p) {
    /* lexicographic rank among permutations of 0..5 */
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
    int p[6] = {0, 1, 2, 3, 4, 5}, idx = 0;
    /* enumerate all permutations lexicographically */
    int c[6] = {0};
    memcpy(perm[rank_of(p)], p, sizeof p);
    idx = 1;
    while (idx < NW) {                                  /* Heap-free: next_permutation */
        int i = 4;
        while (i >= 0 && p[i] >= p[i + 1]) i--;
        if (i < 0) break;
        int j = 5; while (p[j] <= p[i]) j--;
        int t = p[i]; p[i] = p[j]; p[j] = t;
        for (int a = i + 1, b = 5; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; }
        memcpy(perm[rank_of(p)], p, sizeof p);
        idx++;
    }
    (void)c;
    /* hexagon / orbit representatives */
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
        hexid[w] = hmap[hrep[w]];
        orbid[w] = omap[orep[w]];
    }
    if (nh != NH || no != NO) { fprintf(stderr, "geometry mismatch %d %d\n", nh, no); exit(2); }
    for (int w = 0; w < NW; w++) {
        int y[6]; memcpy(y, perm[orep[w]], sizeof y);
        for (int i = 0; i < 5; i++) {
            if (rank_of(y) == w) { phse[w] = i; break; }
            int o[6]; tau_(y, o); memcpy(y, o, sizeof y);
        }
        word_at[orbid[w]][phse[w]] = w;
        hlo[w] = (hexid[w] < 64) ? (1ULL << hexid[w]) : 0ULL;
        hhi[w] = (hexid[w] >= 64) ? (1ULL << (hexid[w] - 64)) : 0ULL;
    }
    for (int w = 0; w < NW; w++) {
        int y[6]; memcpy(y, perm[w], sizeof y);
        for (int i = 0; i < 5; i++) { int o[6]; sig_(y, o); memcpy(y, o, sizeof y); }
        int b[6] = {y[3], y[4], y[5], y[2], y[0], y[1]};
        int c2[6] = {y[3], y[4], y[5], y[2], y[1], y[0]};
        mvW3b[w] = rank_of(b);
        mvW3c[w] = rank_of(c2);
    }
}

/* ------------------------------------------------------------------ search */
static int BCAP, GCAP, SCAP;
static long long NODECAP, nodes;
static int capped;
static int bestPass, bestOrb, bestRun;

static unsigned char omask[NO];      /* phase mask per orbit, 0 = untouched */
static int ntouch;
static int defcnt[5];                /* how many touched orbits have deficit d (d=0..4) */
static uint64_t HLO, HHI;

static int feasible(int extra_tokens, int skip_orb) {
    /* greedy: spend tokens on the largest deficits, rest must fit in SCAP */
    int c[5];
    for (int d = 0; d < 5; d++) c[d] = defcnt[d];
    if (skip_orb >= 0) { int d = 5 - __builtin_popcount(omask[skip_orb]); c[d]--; }
    int tok = extra_tokens, sum = 0;
    for (int d = 4; d >= 1; d--) {
        int take = c[d] < tok ? c[d] : tok;
        tok -= take;
        sum += (c[d] - take) * d;
    }
    return sum <= SCAP;
}

static void dfs(int cur, int corb, int bused, int passes, int nruns) {
    if (++nodes > NODECAP) { capped = 1; return; }
    if (capped) return;
    if (feasible(GCAP, -1)) {
        if (passes > bestPass) { bestPass = passes; bestOrb = ntouch; bestRun = nruns; }
    }
    /* optimistic prune: current orbit may still grow; (BCAP-bused)+GCAP orbits may be
       completed later or handed off — this only ever over-estimates, never prunes a
       branch that a real walk could take. */
    if (!feasible(GCAP + (BCAP - bused), corb)) return;

    /* (1) extend the current run */
    int p = phse[cur];
    for (int np = 0; np < 5; np++) {
        if (omask[corb] >> np & 1) continue;
        int w = word_at[corb][np];
        if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
        int extra = (np == (p + 1) % 5) ? 0 : 1;
        if (bused + extra > BCAP) continue;
        int d0 = 5 - __builtin_popcount(omask[corb]);
        defcnt[d0]--; defcnt[d0 - 1]++;
        omask[corb] |= 1 << np;
        HLO |= hlo[w]; HHI |= hhi[w];
        dfs(w, corb, bused + extra, passes + 1, nruns);
        HLO &= ~hlo[w]; HHI &= ~hhi[w];
        omask[corb] &= ~(1 << np);
        defcnt[d0 - 1]--; defcnt[d0]++;
    }
    /* (2) end the run, take a light connector */
    int succ[2] = {mvW3c[cur], mvW3b[cur]};
    for (int si = 0; si < 2; si++) {
        int w = succ[si];
        if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
        int nq = orbid[w];
        int fresh = (omask[nq] == 0);
        int nb = bused + (fresh ? 0 : 1);
        if (nb > BCAP) continue;
        if (fresh) { ntouch++; defcnt[4]++; }
        else { int d0 = 5 - __builtin_popcount(omask[nq]); defcnt[d0]--; defcnt[d0 - 1]++; }
        omask[nq] |= 1 << phse[w];
        HLO |= hlo[w]; HHI |= hhi[w];
        dfs(w, nq, nb, passes + 1, nruns + 1);
        HLO &= ~hlo[w]; HHI &= ~hhi[w];
        omask[nq] &= ~(1 << phse[w]);
        if (fresh) { ntouch--; defcnt[4]--; }
        else { int d0 = 5 - __builtin_popcount(omask[nq]); defcnt[d0 - 1]--; defcnt[d0]++; }
    }
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s b g s [nodecap]\n", argv[0]); return 1; }
    build();
    BCAP = atoi(argv[1]); GCAP = atoi(argv[2]); SCAP = atoi(argv[3]);
    NODECAP = (argc > 4) ? atoll(argv[4]) : 20000000000LL;
    int start = 0;                              /* S6 relabelling is transitive on the 720
                                                   words and commutes with sigma, tau, W3b,
                                                   W3c — one start word suffices. */
    memset(omask, 0, sizeof omask);
    memset(defcnt, 0, sizeof defcnt);
    ntouch = 0; nodes = 0; capped = 0;
    bestPass = bestOrb = bestRun = 0;
    int q = orbid[start];
    ntouch++; defcnt[4]++;
    omask[q] = 1 << phse[start];
    HLO = hlo[start]; HHI = hhi[start];
    dfs(start, q, 0, 1, 1);
    printf("{\"b\": %d, \"g\": %d, \"s\": %d, \"passes\": %d, \"orbits\": %d, \"runs\": %d,"
           " \"nodes\": %lld, \"capped\": %s}\n",
           BCAP, GCAP, SCAP, bestPass, bestOrb, bestRun, nodes, capped ? "true" : "false");
    return 0;
}
