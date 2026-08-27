/* 라운드 124 — 일반 `(1,1)` 뿌리의 **미래-동치 서명** 세기.
 *
 * 라운드 123 은 완전한 뿌리 가족을 얻었지만 뿌리가 10^10~10^11 개였다.  이 라운드는
 * 뿌리를 **저장하지 않고**, 첫 짧은 pass 에서 **서명**만 해시 집합에 넣어 **서로 다른
 * 서명의 개수**를 센다.
 *
 * ### 서명 (§1, §2, §4)
 *
 *     Sig = ( v, b, omask[144], cost, hub, x, e )
 *
 * `v` = X 의 진입 단어, `b` = X 의 길이.  나머지 좌표가 왜 빠지는지:
 *
 *  * **사용 육각형 120비트** — 진입 단어와 `(궤도, phase)` 쌍이 720 대 720 **전단사**이므로
 *    `omask` 가 진입 단어 집합을 정하고, 따라서 사용 육각형 집합도 정한다. **파생값이다.**
 *  * **orbits · runs · defcnt · EXC · mcnt · blk · freshcnt** — 전부 `omask`(와 사용 육각형)
 *    에서 계산된다. `runs = orbits + e` 다. **파생값이다.**
 *  * **runlen** — run 이 5 pass 를 넘을 수 없다는 것은 phase 단사성이 이미 강제한다
 *    (궤도에 phase 가 5개뿐이다). 나머지 쓰임(`shrun`, 조각 용량)은 **프룬 회계**일 뿐
 *    합법성이 아니다. **미래 언어에 영향이 없다.**
 *  * **f_out** — 짧은 pass 의 탈출에서만 생기는데 뿌리 시점에 X 의 탈출은 아직 고르지
 *    않았으므로 언제나 0 이다.
 *  * **접두의 순서/이력** — 미래는 "무엇이 소비됐는가"와 "지금 어디인가"만 본다.
 *
 * `(v, b)` 가 `h*`, 두 번째 방문 단어 `σ^b v`, 그 길이 `6−b`, 그리고 X 의 탈출 단어
 * `σ^{b−1} v` 를 전부 결정한다.
 *
 * 접두 서명도 함께 센다: `PSig = ( u, omask, cost, hub, x, e )` (여기서 `q` 는
 * `omask` 의 popcount 합이라 파생값이다) — §17 의 frontier-DP 가 가능한지 재는 값이다.
 *
 * 인자: b qcap costcap orbcap xcap ecap hcap dcap exccap fod nodecap tablebits dump
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
static int hexorb[NH][6];
static int OWORD[NO][5];   /* the word at (orbit, phase) */   /* the 6 orbits meeting each hexagon */
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
    for (int w = 0; w < NW; w++) OWORD[orbid[w]][phse[w]] = w;
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


/* ---- the 461 indecomposable weight-6 tails (Round 121 catalogue: 1,1,3,13,71,461) ---- */
#define NH6 461
static int M6[NH6][NW];
static int H6ACT[NH6][6];

static void build_w6(void) {
    int idx = 0, pi[6], used[6];
    int c[6] = {0, 0, 0, 0, 0, 0};
    /* iterate over all permutations of {0..5} in lexicographic order */
    for (pi[0] = 0; pi[0] < 6; pi[0]++)
    for (pi[1] = 0; pi[1] < 6; pi[1]++)
    for (pi[2] = 0; pi[2] < 6; pi[2]++)
    for (pi[3] = 0; pi[3] < 6; pi[3]++)
    for (pi[4] = 0; pi[4] < 6; pi[4]++)
    for (pi[5] = 0; pi[5] < 6; pi[5]++) {
        for (int j = 0; j < 6; j++) used[j] = 0;
        int dup = 0;
        for (int j = 0; j < 6; j++) { if (used[pi[j]]) { dup = 1; break; } used[pi[j]] = 1; }
        if (dup) continue;
        int ok = 1, mx = -1;
        for (int j = 0; j < 5; j++) { if (pi[j] > mx) mx = pi[j];
            if (mx == j) { ok = 0; break; } }
        if (!ok) continue;
        if (idx >= NH6) { fprintf(stderr, "too many weight-6 tails\n"); exit(2); }
        for (int j = 0; j < 6; j++) H6ACT[idx][j] = pi[j];
        idx++;
    }
    (void)c;
    if (idx != NH6) { fprintf(stderr, "weight-6 tail count %d != 461\n", idx); exit(2); }
    for (int y = 0; y < NW; y++)
        for (int h = 0; h < NH6; h++) {
            int a[6];
            for (int j = 0; j < 6; j++) a[j] = perm[y][H6ACT[h][j]];
            M6[h][y] = rank_of(a);
        }
}

/* ---- search state (same coordinates as the Round 121 engine) ---- */
static unsigned char omask[NO];
static int defcnt[5];
static uint64_t HLO, HHI;

static void markhex(int h, int delta) {
    for (int j = 0; j < 6; j++) {
        int q = hexorb[h][j];
        int fresh = (omask[q] == 0);
        if (fresh) freshcnt[blk[q]]--;
        blk[q] += delta;
        if (fresh) freshcnt[blk[q]]++;
    }
}

/* ------------------------------------------------- exact signature hash set */
static int TBITS;
static int DUMP;   /* section 20 positive control: print every root signature */
static uint64_t TMASK;
static unsigned char **slot;          /* NULL or pointer to a length-prefixed signature */
static long long n_distinct, n_probe_overflow;
static unsigned char *arena; static size_t arena_used, arena_cap;

static unsigned char **slot2;
static long long n_distinct2;
static unsigned char **slot3;
static long long n_distinct3;
static unsigned char **slot4;
static long long n_distinct4;

static uint64_t fnv(const unsigned char *p, int n) {
    uint64_t h = 1469598103934665603ULL;
    for (int i = 0; i < n; i++) { h ^= p[i]; h *= 1099511628211ULL; }
    h ^= h >> 29; h *= 0xbf58476d1ce4e5b9ULL; h ^= h >> 32;
    return h;
}

static unsigned char *arena_put(const unsigned char *p, int n) {
    if (arena_used + n + 1 > arena_cap) {
        arena_cap = arena_cap ? arena_cap * 2 : (1ULL << 24);
        unsigned char *na = malloc(arena_cap);
        if (!na) { fprintf(stderr, "arena OOM\n"); exit(3); }
        memcpy(na, arena, arena_used);
        arena = na;                     /* leaked on purpose; short-lived process */
    }
    unsigned char *dst = arena + arena_used;
    dst[0] = (unsigned char)n;
    memcpy(dst + 1, p, n);
    arena_used += n + 1;
    return dst;
}

/* section 20 positive control: print a signature as hex so an independent Python
   re-derivation can check the counts and the fine -> coarse -> ceiling quotients. */
static void dump_sig(const unsigned char *sig, int n) {
    fputs("R ", stdout);
    for (int i = 0; i < n; i++) printf("%02x", sig[i]);
    putchar('\n');
}

/* insert into `tab`; returns 1 if newly inserted.  Exact comparison, no hash collisions. */
static int hs_insert(unsigned char **tab, long long *cnt, const unsigned char *sig, int n) {
    uint64_t h = fnv(sig, n) & TMASK;
    for (uint64_t step = 0; step <= TMASK; step++) {
        uint64_t i = (h + step) & TMASK;
        if (!tab[i]) {
            tab[i] = arena_put(sig, n);
            (*cnt)++;
            return 1;
        }
        if (tab[i][0] == n && memcmp(tab[i] + 1, sig, n) == 0) return 0;
    }
    n_probe_overflow++;
    return 0;
}

/* Round 124 COARSE signature (section 15).  The future language depends only on:
     - the current word and the pending h* obligation, i.e. (v, b);
     - which hexagons are still free  -- because "available entry word" = "word of an unused
       hexagon" (phase injectivity is IMPLIED by hexagon injectivity: an orbit's five words sit
       in five DISTINCT hexagons, so phase(w) is occupied only when w itself was an entry);
     - which orbits are already OPEN -- needed only for the O = 25 count (and D = 5O - P = 4 is
       that same constraint restated, not an independent one);
     - the remaining budgets.
   Which particular word of a used hexagon was the entry is NOT needed. */
static int build_coarse(unsigned char *out, int word, int b, int cost, int hub, int xj, int rev) {
    int n = 0;
    out[n++] = (unsigned char)(word & 0xff);
    out[n++] = (unsigned char)(word >> 8);
    out[n++] = (unsigned char)(b & 0xff);
    out[n++] = (unsigned char)cost;
    out[n++] = (unsigned char)hub;
    out[n++] = (unsigned char)xj;
    out[n++] = (unsigned char)rev;
    unsigned char hx[15];
    memset(hx, 0, sizeof hx);
    for (int q = 0; q < NO; q++)
        if (omask[q])
            for (int ph = 0; ph < 5; ph++)
                if (omask[q] >> ph & 1) { int h = hexid[OWORD[q][ph]]; hx[h >> 3] |= 1 << (h & 7); }
    for (int i = 0; i < 15; i++) out[n++] = hx[i];
    unsigned char ob[18];
    memset(ob, 0, sizeof ob);
    for (int q = 0; q < NO; q++) if (omask[q]) ob[q >> 3] |= 1 << (q & 7);
    for (int i = 0; i < 18; i++) out[n++] = ob[i];
    return n;
}

/* DIAGNOSTIC ONLY (section 18): the crudest conceivable signature (v, b, used hexagons).
   It drops the opened-orbit set and every budget, so it is NOT sound - it exists only to put a
   CEILING on how much any correct signature could possibly compress. */
static int build_floor(unsigned char *out, int word, int b) {
    int n = 0;
    out[n++] = (unsigned char)(word & 0xff);
    out[n++] = (unsigned char)(word >> 8);
    out[n++] = (unsigned char)(b & 0xff);
    unsigned char hx[15];
    memset(hx, 0, sizeof hx);
    for (int q = 0; q < NO; q++)
        if (omask[q])
            for (int ph = 0; ph < 5; ph++)
                if (omask[q] >> ph & 1) { int h = hexid[OWORD[q][ph]]; hx[h >> 3] |= 1 << (h & 7); }
    for (int i = 0; i < 15; i++) out[n++] = hx[i];
    return n;
}

/* build the compact signature; extra = the X entry word v and its length b (or -1 for a
   prefix signature, where `u` is the current entry word instead) */
static int build_sig(unsigned char *out, int word, int b, int cost, int hub, int xj, int rev) {
    int n = 0;
    out[n++] = (unsigned char)(word & 0xff);
    out[n++] = (unsigned char)(word >> 8);
    out[n++] = (unsigned char)(b & 0xff);
    out[n++] = (unsigned char)cost;
    out[n++] = (unsigned char)hub;
    out[n++] = (unsigned char)xj;
    out[n++] = (unsigned char)rev;
    for (int q = 0; q < NO; q++)
        if (omask[q]) {
            out[n++] = (unsigned char)(q & 0xff);
            out[n++] = (unsigned char)(q >> 8);
            out[n++] = omask[q];
        }
    return n;
}

/* ------------------------------------------------------------- root search */
#define OCAP 25
static int BSPLIT, QCAP, COSTCAP, ORBCAP, XCAP, ECAP, HCAP, DCAP, EXCCAP, FOD;
static long long NODECAP, nodes, roots, capped_flag;
static int maxq;

static int dcommitted2(int curorb, int slots) {
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
static int freshdef(int need) {
    int sum = 0, left = need;
    for (int j = 0; j <= 5 && left > 0; j++) {
        int take = freshcnt[j] < left ? freshcnt[j] : left;
        left -= take;
        sum += take * j;
    }
    if (left > 0) return 1 << 20;
    return sum;
}
static int room_ok(int curorb, int slots, int passes, int orbits) {
    int c[5];
    for (int i = 0; i < 5; i++) c[i] = defcnt[i];
    int d = 5 - __builtin_popcount(omask[curorb]);
    c[d]--;
    int room = d + 5 * (ORBCAP - orbits);
    int tok = slots;
    for (int dd = 4; dd >= 1 && tok > 0; dd--) {
        int take = c[dd] < tok ? c[dd] : tok;
        tok -= take;
        room += take * dd;
    }
    return (121 - passes) <= room;
}

static void emit_roots(int u, int passes, int cost, int hub, int xj, int rev, int orbits)
{
    int exitw = SIG[5][u];
    int succ[4 + NH4 + NH5 + NH6], scost[4 + NH4 + NH5 + NH6], shub[4 + NH4 + NH5 + NH6];
    int n = 0;
    succ[n] = M2[exitw];  scost[n] = 0; shub[n++] = 0;
    succ[n] = M3a[exitw]; scost[n] = 1; shub[n++] = 0;
    succ[n] = M3b[exitw]; scost[n] = 1; shub[n++] = 0;
    succ[n] = M3c[exitw]; scost[n] = 1; shub[n++] = 0;
    if (hub + 1 <= HCAP) for (int h = 0; h < NH4; h++) { succ[n] = M4[h][exitw]; scost[n] = 1; shub[n++] = 1; }
    if (hub + 2 <= HCAP) for (int h = 0; h < NH5; h++) { succ[n] = M5[h][exitw]; scost[n] = 1; shub[n++] = 2; }
    if (hub + 3 <= HCAP) for (int h = 0; h < NH6; h++) { succ[n] = M6[h][exitw]; scost[n] = 1; shub[n++] = 3; }
    unsigned char sig[128];
    for (int i = 0; i < n; i++) {
        int w = succ[i], nq = orbid[w], same = (nq == orbid[u]);
        int nx = xj + ((same && scost[i] == 1) ? 1 : 0);
        int nrev = rev + ((!same && omask[nq] != 0) ? 1 : 0);
        int nhub = hub + shub[i], ncost = cost + scost[i];
        if (nx > XCAP || nrev > ECAP || nhub > HCAP) continue;
        if (nx + nhub > 3) continue;
        if (nrev + nx + nhub > 4) continue;
        if (ncost + nhub > COSTCAP) continue;
        if (omask[nq] >> phse[w] & 1) continue;
        if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
        if (!same && omask[nq] == 0 && orbits + 1 > ORBCAP) continue;
        /* X occupies (orbit of w, phase of w); add it to the mask for the signature */
        unsigned char save = omask[nq];
        omask[nq] |= 1 << phse[w];
        for (int b = 1; b <= 5; b++) {
            if (BSPLIT && b != BSPLIT) continue;
            roots++;
            int ln = build_sig(sig, w, b, ncost, nhub, nx, nrev);
            if (DUMP) dump_sig(sig, ln);
            hs_insert(slot, &n_distinct, sig, ln);
            unsigned char csig[64];
            int cl = build_coarse(csig, w, b, ncost, nhub, nx, nrev);
            hs_insert(slot3, &n_distinct3, csig, cl);
            int fl = build_floor(csig, w, b);
            hs_insert(slot4, &n_distinct4, csig, fl);
        }
        omask[nq] = save;
    }
}

static void dfs(int u, int passes, int cost, int hub, int orbits, int xj, int rev)
{
    if (++nodes > NODECAP) { capped_flag = 1; return; }
    if (passes > maxq) maxq = passes;
    {   /* prefix signature (section 17: frontier DP feasibility) */
        unsigned char psig[128];
        int ln = build_sig(psig, u, 0, cost, hub, xj, rev);
        hs_insert(slot2, &n_distinct2, psig, ln);
    }
    if (DCAP >= 0 && dcommitted2(orbid[u], ECAP - rev) > DCAP) return;
    if (FOD && DCAP >= 0
        && dcommitted2(orbid[u], ECAP - rev) + freshdef(ORBCAP - orbits) > DCAP) return;
    if (!room_ok(orbid[u], ECAP - rev, passes, orbits)) return;
    emit_roots(u, passes, cost, hub, xj, rev, orbits);
    if (passes >= QCAP) return;

    int exitw = SIG[5][u];
    int succ[4 + NH4 + NH5 + NH6], scost[4 + NH4 + NH5 + NH6], shub[4 + NH4 + NH5 + NH6];
    int n = 0;
    succ[n] = M2[exitw];  scost[n] = 0; shub[n++] = 0;
    succ[n] = M3a[exitw]; scost[n] = 1; shub[n++] = 0;
    succ[n] = M3b[exitw]; scost[n] = 1; shub[n++] = 0;
    succ[n] = M3c[exitw]; scost[n] = 1; shub[n++] = 0;
    if (hub + 1 <= HCAP) for (int h = 0; h < NH4; h++) { succ[n] = M4[h][exitw]; scost[n] = 1; shub[n++] = 1; }
    if (hub + 2 <= HCAP) for (int h = 0; h < NH5; h++) { succ[n] = M5[h][exitw]; scost[n] = 1; shub[n++] = 2; }
    if (hub + 3 <= HCAP) for (int h = 0; h < NH6; h++) { succ[n] = M6[h][exitw]; scost[n] = 1; shub[n++] = 3; }

    for (int i = 0; i < n; i++) {
        int w = succ[i], c = scost[i], hb = shub[i];
        int nq = orbid[w], curorb = orbid[u], same = (nq == curorb);
        int nxj = xj, nrev = rev, nhub = hub + hb;
        if (same) { if (c == 1) nxj = xj + 1; }
        int fresh = (omask[nq] == 0);
        if (!same && !fresh) nrev = rev + 1;
        if (nxj > XCAP || nrev > ECAP || nhub > HCAP) continue;
        if (nxj + nhub > 3) continue;
        if (nrev + nxj + nhub > 4) continue;
        if (cost + c + nhub > COSTCAP) continue;
        if (fresh && orbits + 1 > ORBCAP) continue;
        if (omask[nq] >> phse[w] & 1) continue;
        if ((HLO & hlo[w]) || (HHI & hhi[w])) continue;
        int addexc = 0;
        if (fresh) {
            for (int j = 0; j < 5; j++) if (mcnt[ohex[nq][j]]) addexc++;
            if (EXCCAP >= 0 && EXC + addexc > EXCCAP) continue;
            for (int j = 0; j < 5; j++) mcnt[ohex[nq][j]]++;
            EXC += addexc;
        }
        int d0 = 5 - __builtin_popcount(omask[nq]);
        if (fresh) defcnt[4]++; else { defcnt[d0]--; defcnt[d0 - 1]++; }
        if (FOD) { markhex(hexid[w], 1); if (fresh) freshcnt[blk[nq]]--; }
        omask[nq] |= 1 << phse[w];
        HLO |= hlo[w]; HHI |= hhi[w];
        dfs(w, passes + 1, cost + c, nhub, orbits + (fresh ? 1 : 0), nxj, nrev);
        HLO &= ~hlo[w]; HHI &= ~hhi[w];
        omask[nq] &= ~(1 << phse[w]);
        if (FOD) { if (fresh) freshcnt[blk[nq]]++; markhex(hexid[w], -1); }
        if (fresh) defcnt[4]--; else { defcnt[d0 - 1]--; defcnt[d0]++; }
        if (fresh) { EXC -= addexc; for (int j = 0; j < 5; j++) mcnt[ohex[nq][j]]--; }
    }
}

int main(int argc, char **argv) {
    build(); build_w6();
    BSPLIT  = (argc > 1) ? atoi(argv[1]) : 0;
    QCAP    = (argc > 2) ? atoi(argv[2]) : 119;
    COSTCAP = (argc > 3) ? atoi(argv[3]) : 26;
    ORBCAP  = (argc > 4) ? atoi(argv[4]) : OCAP;
    XCAP    = (argc > 5) ? atoi(argv[5]) : 3;
    ECAP    = (argc > 6) ? atoi(argv[6]) : 4;
    HCAP    = (argc > 7) ? atoi(argv[7]) : 3;
    DCAP    = (argc > 8) ? atoi(argv[8]) : 4;
    EXCCAP  = (argc > 9) ? atoi(argv[9]) : 5;
    FOD     = (argc > 10) ? atoi(argv[10]) : 1;
    NODECAP = (argc > 11) ? atoll(argv[11]) : 100000000000LL;
    TBITS   = (argc > 12) ? atoi(argv[12]) : 22;
    DUMP    = (argc > 13) ? atoi(argv[13]) : 0;
    TMASK   = (1ULL << TBITS) - 1;
    slot  = calloc((size_t)1 << TBITS, sizeof *slot);
    slot2 = calloc((size_t)1 << TBITS, sizeof *slot2);
    slot3 = calloc((size_t)1 << TBITS, sizeof *slot3);
    slot4 = calloc((size_t)1 << TBITS, sizeof *slot4);
    if (!slot || !slot2 || !slot3 || !slot4) { fprintf(stderr, "table OOM\n"); return 3; }

    memset(omask, 0, sizeof omask); memset(defcnt, 0, sizeof defcnt);
    memset(mcnt, 0, sizeof mcnt); memset(blk, 0, sizeof blk);
    for (int j = 0; j < 6; j++) freshcnt[j] = 0;
    freshcnt[0] = NO;
    nodes = roots = 0; capped_flag = 0; maxq = 0; EXC = 0; HLO = HHI = 0;
    n_distinct = n_distinct2 = n_distinct3 = n_distinct4 = n_probe_overflow = 0;

    /* q = 0 : the walk's first pass is already X.  Its signature has an empty prefix. */
    {
        unsigned char sig[128];
        for (int b = 1; b <= 5; b++) {
            if (BSPLIT && b != BSPLIT) continue;
            omask[orbid[0]] = 1 << phse[0];
            roots++;
            int ln = build_sig(sig, 0, b, 0, 0, 0, 0);
            if (DUMP) dump_sig(sig, ln);
            hs_insert(slot, &n_distinct, sig, ln);
            unsigned char csig[64];
            int cl = build_coarse(csig, 0, b, 0, 0, 0, 0);
            hs_insert(slot3, &n_distinct3, csig, cl);
            int fl = build_floor(csig, 0, b);
            hs_insert(slot4, &n_distinct4, csig, fl);
            omask[orbid[0]] = 0;
        }
    }
    int start = 0;
    omask[orbid[start]] = 1 << phse[start];
    defcnt[4] = 1;
    for (int j = 0; j < 5; j++) mcnt[ohex[orbid[start]][j]] = 1;
    if (FOD) { markhex(hexid[start], 1); freshcnt[blk[orbid[start]]]--; }
    HLO = hlo[start]; HHI = hhi[start];
    dfs(start, 1, 0, 0, 1, 0, 0);

    printf("{\"b\": %d, \"xcap\": %d, \"ecap\": %d, \"hcap\": %d, \"dcap\": %d,"
           " \"exccap\": %d, \"tablebits\": %d, \"verdict\": \"%s\","
           " \"prefix_states\": %lld, \"roots\": %lld,"
           " \"distinct_root_signatures\": %lld, \"distinct_coarse_signatures\": %lld,"
           " \"distinct_prefix_signatures\": %lld, \"floor_signatures\": %lld,"
           " \"probe_overflow\": %lld, \"max_prefix_q\": %d,"
           " \"root_compression\": %.4f, \"coarse_compression\": %.4f,"
           " \"prefix_compression\": %.4f}\n",
           BSPLIT, XCAP, ECAP, HCAP, DCAP, EXCCAP, TBITS,
           capped_flag ? "UNKNOWN_CAP" : "COMPLETE",
           nodes, roots, n_distinct, n_distinct3, n_distinct2, n_distinct4,
           n_probe_overflow, maxq,
           n_distinct ? (double)roots / (double)n_distinct : 0.0,
           n_distinct3 ? (double)roots / (double)n_distinct3 : 0.0,
           n_distinct2 ? (double)nodes / (double)n_distinct2 : 0.0);
    return 0;
}
