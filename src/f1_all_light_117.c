/* 라운드 117 — `F = 1`, `H = 0` (all-light) walk 뼈대의 정확한 탐색기.
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
static uint64_t hlo[NW], hhi[NW];
static int perm[NW][6];

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
    for (int y = 0; y < NW; y++) {                 /* moves act on the EXIT word */
        int *q = perm[y];
        int a2[6]  = {q[2], q[3], q[4], q[5], q[1], q[0]};
        int a3a[6] = {q[3], q[4], q[5], q[1], q[2], q[0]};
        int a3b[6] = {q[3], q[4], q[5], q[2], q[0], q[1]};
        int a3c[6] = {q[3], q[4], q[5], q[2], q[1], q[0]};
        M2[y] = rank_of(a2); M3a[y] = rank_of(a3a);
        M3b[y] = rank_of(a3b); M3c[y] = rank_of(a3c);
    }
}

/* ------------------------------------------------------------------ search */
static int BSPLIT, COSTCAP, ORBCAP, SHRUNCAP, RMAX, XCAP, FOUTCAP, ECAP, FOUTMIN, YGAP;
static long long NODECAP, nodes;
static int capped, found, bestPasses;
static unsigned char omask[NO];
static uint64_t HLO, HHI;
static int witness[TARGET + 2], wlen_[TARGET + 2];

static void dfs(int u, int len, int passes, int cost, int orbits, int runs,
                int shrun, int runlen, int sstate, int vword, int fout,
                int xj, int rev, int segpasses, int segsh, int pX) {
    if (found) return;
    if (++nodes > NODECAP) { capped = 1; return; }
    if (passes > bestPasses) bestPasses = passes;
    if (passes == TARGET) { found = 1; return; }
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
        int segs = (2 - sstate) + (XCAP - xj) + (ECAP - rev);
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
    if (YGAP && sstate == 1 && passes - pX > YGAP - 1) return;
    int isshort = (len < 6);
    int avail = (2 - sstate) + (isshort ? 1 : 0);
    if (fout + avail < FOUTMIN) return;
    int forcefree = (isshort && fout + avail == FOUTMIN);
    int exitw = SIG[len - 1][u];
    int curorb = orbid[u];
    int succ[4] = {M2[exitw], M3a[exitw], M3b[exitw], M3c[exitw]};
    int scost[4] = {0, 1, 1, 1};
    for (int si = 0; si < (forcefree ? 1 : 4) && !found; si++) {
        int w = succ[si];
        int c = scost[si];
        if (cost + c > COSTCAP) continue;
        int nq = orbid[w];
        int same = (nq == curorb);
        int nruns = runs, nsh = shrun, nrunlen = runlen + 1, nfout = fout;
        int nxj = xj, nrev = rev;
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
        if (fresh && orbits + 1 > ORBCAP) continue;
        if (omask[nq] >> phse[w] & 1) continue;
        int brk = (nxj > xj || rv);
        int nsegp = brk ? 1 : segpasses + 1;
        int nsegs = brk ? 0 : segsh + (same ? 0 : (5 - runlen));
        /* --- case 1: fresh hexagon, FULL pass --- */
        if (!hexused) {
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            witness[passes] = w; wlen_[passes] = 6;
            dfs(w, 6, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, sstate, vword, nfout, nxj, nrev + rv, nsegp, nsegs, pX);
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
        }
        if (found) return;
        /* --- case 2: fresh hexagon, FIRST short pass (length BSPLIT) --- */
        if (!hexused && sstate == 0) {
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            witness[passes] = w; wlen_[passes] = BSPLIT;
            dfs(w, BSPLIT, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, 1, w, nfout, nxj, nrev + rv, 0, 0, passes + 1);
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
        }
        if (found) return;
        /* --- case 3: the SECOND h* visit (forced word, length 6-BSPLIT) --- */
        if (hexused && sstate == 1 && w == SIG[BSPLIT][vword]
            && (!YGAP || passes + 1 == pX + YGAP)) {
            omask[nq] |= 1 << phse[w];
            witness[passes] = w; wlen_[passes] = 6 - BSPLIT;
            dfs(w, 6 - BSPLIT, passes + 1, cost + c, orbits + (fresh ? 1 : 0),
                nruns, nsh, nrunlen, 2, vword, nfout, nxj, nrev + rv, 0, 0, pX);
            omask[nq] &= ~(1 << phse[w]);
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 7) {
        fprintf(stderr, "usage: %s b costcap orbcap xcap foutcap ecap [nodecap]\n", argv[0]);
        return 1;
    }
    build();
    BSPLIT = atoi(argv[1]); COSTCAP = atoi(argv[2]); ORBCAP = atoi(argv[3]);
    XCAP = atoi(argv[4]); FOUTCAP = atoi(argv[5]); ECAP = atoi(argv[6]);
    FOUTMIN = (argc > 7) ? atoi(argv[7]) : 0;
    YGAP = (argc > 8) ? atoi(argv[8]) : 0;
    NODECAP = (argc > 9) ? atoll(argv[9]) : 200000000000LL;
    RMAX = COSTCAP + 1 + FOUTCAP;
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
    nodes = 0; capped = 0; found = 0; bestPasses = 0;
    HLO = HHI = 0;
    /* S6 relabelling is simply transitive on the 720 words and commutes with sigma, tau
       and all four light moves, so fixing the FIRST entry word is a complete reduction. */
    int start = 0;
    for (int firstIsShort = 0; firstIsShort < 2 && !found; firstIsShort++) {
        int len = firstIsShort ? BSPLIT : 6;
        omask[orbid[start]] = 1 << phse[start];
        HLO = hlo[start]; HHI = hhi[start];
        witness[0] = start; wlen_[0] = len;
        dfs(start, len, 1, 0, 1, 1, 0, 1, firstIsShort ? 1 : 0, start, 0, 0, 0,
            firstIsShort ? 0 : 1, 0, firstIsShort ? 1 : 0);
        HLO = HHI = 0;
        omask[orbid[start]] = 0;
    }
    printf("{\"b\": %d, \"costcap\": %d, \"orbcap\": %d, \"xcap\": %d, \"foutcap\": %d,"
           " \"ecap\": %d, \"foutmin\": %d, \"ygap\": %d, \"rmax\": %d, \"shruncap\": %d,"
           " \"verdict\": \"%s\", \"best_passes\": %d, \"nodes\": %lld}\n",
           BSPLIT, COSTCAP, ORBCAP, XCAP, FOUTCAP, ECAP, FOUTMIN, YGAP, RMAX, SHRUNCAP,
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
