/* 라운드 115 — F=0 잔여 하위경우를 위한 **결합 다중-사슬** 전수 탐색기.
 *
 * 사슬별 용량 상한만으로 닫히지 않는 하위경우가 셋 남는다.  그 셋은 사슬들이
 *   (a) 서로 육각형-서로소이고
 *   (b) 합쳐서 120개 육각형을 정확히 덮어야 한다
 * 는 전역 제약을 쓰지 않았기 때문에 살아남았다.  여기서는 그 제약을 그대로 넣고
 * walk 뼈대 전체를 찾는다 — 완화 없음.
 *
 *   RTOT  = 총 run 수 = 24 + k + e
 *   OTOT  = 총 궤도 수 = 24 + k
 *   TCH   = 사슬 수 t
 * 목표: pass 120개 (= 육각형 120개 전부).  F=0 이면 pass 하나가 육각형 하나이므로
 * pass 수가 곧 덮인 육각형 수다.
 *
 * 가지치기 (전부 admissible — 실제 walk 이 지나갈 가지는 절대 자르지 않는다):
 *   P1  passes + 5*(RTOT - runs) >= 120
 *   P2  orbits <= OTOT
 *   P3  사슬 용량: 현재 사슬의 최종 pass 수 <= N[sigma_c + S_rem],
 *       남은 사슬은 BEST[남은 개수][S_rem]
 *
 * 첫 사슬의 시작 단어는 S6 재라벨 대칭(720 단어에 추이적, sigma/tau/W3b/W3c 와 교환)
 * 으로 0 으로 고정한다.
 *
 * 사용법: ./joint_walk_115 <RTOT> <OTOT> <TCH> [nodecap]
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

/* N[s] = 전수로 구한 단일 사슬 최대 pass 수 (b=g=0), s = 그 사슬의 run 결손 총합 */
static const int NTAB[21] = {20, 20, 33, 33, 46, 46, 49, 58, 62, 66, 70,
                             74, 83, 83, 96, 96, 96, 103, 103, 103, 103};
static int BEST[8][21];

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
        word_at[orbid[w]][phse[w]] = w;
        hlo[w] = (hexid[w] < 64) ? (1ULL << hexid[w]) : 0ULL;
        hhi[w] = (hexid[w] >= 64) ? (1ULL << (hexid[w] - 64)) : 0ULL;
    }
    for (int w = 0; w < NW; w++) {
        int y[6]; memcpy(y, perm[w], sizeof y);
        for (int i = 0; i < 5; i++) { int o[6]; sig_(y, o); memcpy(y, o, sizeof y); }
        int b[6] = {y[3], y[4], y[5], y[2], y[0], y[1]};
        int c2[6] = {y[3], y[4], y[5], y[2], y[1], y[0]};
        mvW3b[w] = rank_of(b); mvW3c[w] = rank_of(c2);
    }
    for (int s = 0; s <= 20; s++) BEST[0][s] = 0;
    for (int m = 1; m < 8; m++)
        for (int s = 0; s <= 20; s++) {
            int b = 0;
            for (int a = 0; a <= s; a++) {
                int v = NTAB[a] + BEST[m - 1][s - a];
                if (v > b) b = v;
            }
            BEST[m][s] = b;
        }
}

static int RTOT, OTOT, TCH, POOL;
static long long NODECAP, nodes;
static int capped, found;
static unsigned char omask[NO];         /* 전역: 궤도별 사용 phase */
static unsigned char inchain[NO];       /* 현재 사슬이 쓴 궤도인가 (0/1) */
static unsigned char entry[NO];         /* 그 궤도에 이번 사슬이 들어올 때의 phase 집합 */
static int chainlist[64], nchainlist;
static uint64_t HLO, HHI;
static int hit_runs, hit_orbits;

static void dfs(int cur, int corb, int runs, int orbits, int passes,
                int chains, int sh_used, int chain_passes, int chain_sh) {
    if (found) return;
    if (++nodes > NODECAP) { capped = 1; return; }
    if (passes == 120) { found = 1; hit_runs = runs; hit_orbits = orbits; return; }
    int ellc = __builtin_popcount(omask[corb]) - __builtin_popcount(entry[corb]);
    if (passes + (5 - ellc) + 5 * (RTOT - runs) < 120) return;
    if (sh_used > POOL) return;
    {   /* P3 사슬 용량 */
        int srem = POOL - sh_used;
        int idx = chain_sh + srem; if (idx > 20) idx = 20;
        int bound = (passes - chain_passes) + NTAB[idx] + BEST[TCH - chains][srem];
        if (bound < 120) return;
    }
    int p = phse[cur];
    /* (1) run 연장 — x = 0 이므로 tau 스텝만 */
    {
        int np = (p + 1) % 5;
        if (!(omask[corb] >> np & 1)) {
            int w = word_at[corb][np];
            if (!((HLO & hlo[w]) || (HHI & hhi[w]))) {
                omask[corb] |= 1 << np;
                HLO |= hlo[w]; HHI |= hhi[w];
                dfs(w, corb, runs, orbits, passes + 1, chains, sh_used,
                    chain_passes + 1, chain_sh);
                HLO &= ~hlo[w]; HHI &= ~hhi[w];
                omask[corb] &= ~(1 << np);
            }
        }
    }
    if (found) return;
    /* 이 run 이 여기서 끝난다면 결손은 얼마인가 */
    int ell = ellc;
    int nsh = sh_used + (5 - ell);
    if (nsh > POOL) return;
    /* (2) 경량 연결자 — 같은 사슬 안에서 다음 run 으로 */
    if (runs + 1 <= RTOT) {
        int succ[2] = {mvW3c[cur], mvW3b[cur]};
        for (int si = 0; si < 2 && !found; si++) {
            int w = succ[si];
            if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
            int nq = orbid[w];
            if (inchain[nq]) continue;             /* 사슬 안 재진입 금지 (h 분리) */
            int fresh = (omask[nq] == 0);
            if (fresh && orbits + 1 > OTOT) continue;
            inchain[nq] = 1; entry[nq] = omask[nq];
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            chainlist[nchainlist++] = nq;
            dfs(w, nq, runs + 1, orbits + (fresh ? 1 : 0), passes + 1, chains,
                nsh, chain_passes + 1, chain_sh + (5 - ell));
            nchainlist--;
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
            inchain[nq] = 0; entry[nq] = 0;
        }
    }
    if (found) return;
    /* (3) 무거운 연결자 — 사슬을 끝내고 아무 데서나 새 사슬을 연다 */
    if (chains + 1 <= TCH && runs + 1 <= RTOT) {
        int saved[64], ns = nchainlist;
        unsigned char sment[64];
        for (int i = 0; i < ns; i++) {
            saved[i] = chainlist[i];
            sment[i] = entry[saved[i]];
            inchain[saved[i]] = 0; entry[saved[i]] = 0;
        }
        nchainlist = 0;
        for (int w = 0; w < NW && !found; w++) {
            if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
            int nq = orbid[w];
            if (nq == corb) continue;          /* 같은 궤도면 run 이 끝나지 않는다 (x=0) */
            int fresh = (omask[nq] == 0);
            if (fresh && orbits + 1 > OTOT) continue;
            inchain[nq] = 1; entry[nq] = omask[nq];
            omask[nq] |= 1 << phse[w];
            HLO |= hlo[w]; HHI |= hhi[w];
            chainlist[nchainlist++] = nq;
            dfs(w, nq, runs + 1, orbits + (fresh ? 1 : 0), passes + 1, chains + 1,
                nsh, 1, 0);
            nchainlist--;
            HLO &= ~hlo[w]; HHI &= ~hhi[w];
            omask[nq] &= ~(1 << phse[w]);
            inchain[nq] = 0; entry[nq] = 0;
        }
        nchainlist = ns;
        for (int i = 0; i < ns; i++) {
            chainlist[i] = saved[i];
            inchain[saved[i]] = 1; entry[saved[i]] = sment[i];
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s RTOT OTOT TCH [nodecap]\n", argv[0]); return 1; }
    build();
    RTOT = atoi(argv[1]); OTOT = atoi(argv[2]); TCH = atoi(argv[3]);
    NODECAP = (argc > 4) ? atoll(argv[4]) : 20000000000LL;
    POOL = 5 * RTOT - 120;
    memset(omask, 0, sizeof omask);
    memset(inchain, 0, sizeof inchain);
    memset(entry, 0, sizeof entry);
    nodes = 0; capped = 0; found = 0; nchainlist = 0;
    int start = 0, q = orbid[start];
    inchain[q] = 1; entry[q] = 0;
    omask[q] = 1 << phse[start];
    HLO = hlo[start]; HHI = hhi[start];
    chainlist[nchainlist++] = q;
    dfs(start, q, 1, 1, 1, 1, 0, 1, 0);
    printf("{\"RTOT\": %d, \"OTOT\": %d, \"TCH\": %d, \"pool\": %d, \"found\": %s,"
           " \"nodes\": %lld, \"capped\": %s, \"hit_runs\": %d, \"hit_orbits\": %d}\n",
           RTOT, OTOT, TCH, POOL, found ? "true" : "false", nodes,
           capped ? "true" : "false", hit_runs, hit_orbits);
    return 0;
}
