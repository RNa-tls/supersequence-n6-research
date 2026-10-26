// Round R -- exact evaluation of the bracket-tree patterns written by ckM_search.c.
// Independent of ckM.c / ckM_search.c: rebuilds the options and the excess e from runs.bin.
// A pattern is a token line split by junctions (-1) into segments: segment 0 = the path P, segments 1.. = cycles,
// each cycle opened at its anchor.  Tokens: phi trail ids (trail ids 0..29), A groups 1100 + mask / 1164 + i*6+j
// (ordered) and 1200 + mask (any order), 1300 + mask (A-only cycles covering mask: every split of mask into ordered
// blocks, one cycle per block), 1400 + mask (A-only path P, any order).
// For every concrete configuration (P, Z_1 .. Z_c) the bracket-tree cost is
//     G = c + [cut(first of P) = 2] + sum_{edges of P} e + sum_i ( sum_{edges of Z_i} e + e(last(Z_i) -> u_i) + e(u_i -> first(Z_i)) )
// with u_i an option of an anchor trail T_i not in Z_i, of the same version as T_i's main and a different run, and the
// parent relation (cycle i -> the segment holding T_i's main) a tree rooted at P.
// Stage A: decoupled lower bound (u_i any option of any trail outside Z_i, entry and exit minimised separately);
// Stage B: coupled closing (u_i any option of a trail outside Z_i, one u for both anchor edges);
// Stage C (c <= 2): exact, with versions, the run exclusion and every tree (including two cycles anchored on one trail,
// which then has three pieces and needs two distinct anchor runs); witnesses are written as JSON lines.
// usage: ckM_eval DIR PATTERNS THRG OUT.json [WITNESSES.jsonl]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 20)
#define MAXOPT 1344
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], okk[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA, phl[24], nph;
static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define E(a, b) ((int)e[(size_t)(a) * NOPT + (b)])
static uint8_t *hinT[NTR], *houtT[NTR];       // hinT[t][o] = min over options z of trail t of e(z -> o); houtT[t][o] = min_y e(o -> y)
static int SAME_ONLY = -1;     // env CKM_SAME_ONLY = trail: test mode, only configurations with both cycles anchored on that trail
static int THRG; static long nconf = 0, nA_pass = 0, nB_pass = 0, nC_eval = 0, nC_c3 = 0, nsame = 0; static int bestG = BIGI; static FILE *wit; static long hist[64];
typedef struct { int n; int tr[NTR]; } Seg;
// forward DP over a segment: start vector st (per option of the first trail), returns per option of the last trail
// one min-plus step of the DP from the options of trail tp to those of trail t (rows of e are contiguous in t's options)
static inline void step(const int *cur, int tp, int t, int *nx) {
    int nt = tcnt[t]; for (int q = 0; q < nt; q++) nx[q] = BIGI;
    for (int q2 = 0; q2 < tcnt[tp]; q2++) { int c = cur[q2]; if (c >= BIGI) continue; const int8_t *row = e + (size_t)(tofs[tp] + q2) * NOPT + tofs[t];
        for (int q = 0; q < nt; q++) { int w = c + row[q]; nx[q] = w < nx[q] ? w : nx[q]; } }
}
static void seg_dp(const Seg *s, const int *st, int *outv, int *buf1, int *buf2) {
    int *cur = buf1, *nx = buf2; int t0 = s->tr[0];
    for (int q = 0; q < tcnt[t0]; q++) cur[q] = st[q];
    for (int i = 1; i < s->n; i++) { int tp = s->tr[i - 1], t = s->tr[i];
        step(cur, tp, t, nx);
        int *tt = cur; cur = nx; nx = tt; }
    int tl = s->tr[s->n - 1]; for (int q = 0; q < tcnt[tl]; q++) outv[q] = cur[q];
}
static int inseg(const Seg *s, int t) { for (int i = 0; i < s->n; i++) if (s->tr[i] == t) return 1; return 0; }
// closing of cycle Z by an anchor of trail T, version v: for every run k of T_v, val(k) = min over the first / last options
// (a, b) of e(u_k -> z1_a) + path[a][b] + e(zl_b -> u_k).  Returns the three least values over distinct runs with their
// runs, r[0..5] = {v1, k1, v2, k2, v3, k3}: the exact closing for a main of T at run q is (q == k1 ? v2 : v1); two cycles
// anchored on the same trail need two distinct runs, both != q (pair_same below).
static int close3(const Seg *Z, int T, int v, const int *pathm, int n1, int nl, int *r, const int *rmin) {
    int bv[3] = {BIGI, BIGI, BIGI}, bk[3] = {-1, -1, -1}; int base = tofs[T] + v * mrun[T][0]; int t1 = Z->tr[0], tl = Z->tr[Z->n - 1];
    int X[MAXOPT];
    for (int k = 0; k < mrun[T][v]; k++) { int u = base + k;
        // cheap lower bound for this run: min_a (e(u -> a) + min_b path(a, b)) + min_b e(b -> u); a run whose bound is
        // >= the current third value cannot change the three least values (ties at the third place do not matter)
        if (rmin && bv[2] < BIGI) { int lb = BIGI; const int8_t *er = e + (size_t)u * NOPT + tofs[t1];
            for (int a = 0; a < n1; a++) { int w = er[a] + rmin[a]; if (w < lb) lb = w; }
            if (lb + hinT[tl][u] >= bv[2]) continue; }
        for (int b = 0; b < nl; b++) X[b] = BIGI;
        for (int a = 0; a < n1; a++) { int ea = E(u, tofs[t1] + a); if (ea >= bv[2]) continue; const int *pr = pathm + (size_t)a * nl;
            for (int b = 0; b < nl; b++) { int w = ea + pr[b]; if (w < X[b]) X[b] = w; } }
        int m = BIGI; for (int b = 0; b < nl; b++) { int w = X[b] + E(tofs[tl] + b, u); if (w < m) m = w; }
        if (m < bv[0]) { bv[2] = bv[1]; bk[2] = bk[1]; bv[1] = bv[0]; bk[1] = bk[0]; bv[0] = m; bk[0] = k; }
        else if (m < bv[1]) { bv[2] = bv[1]; bk[2] = bk[1]; bv[1] = m; bk[1] = k; }
        else if (m < bv[2]) { bv[2] = m; bk[2] = k; } }
    for (int i = 0; i < 3; i++) { r[2 * i] = bv[i]; r[2 * i + 1] = bk[i]; }
    return bv[0];
}
// least val1(k1) + val2(k2) over runs k1 != k2, both != q (two cycles anchored on the trail of the main at run q)
static int pair_same(const int *r1, const int *r2, int q) {
    int a[2][2], b[2][2], na = 0, nb = 0;     // two best (value, run) of each list without run q
    for (int i = 0; i < 3 && na < 2; i++) if (r1[2 * i + 1] != q) { a[na][0] = r1[2 * i]; a[na][1] = r1[2 * i + 1]; na++; }
    for (int i = 0; i < 3 && nb < 2; i++) if (r2[2 * i + 1] != q) { b[nb][0] = r2[2 * i]; b[nb][1] = r2[2 * i + 1]; nb++; }
    if (na < 1 || nb < 1) return BIGI;
    if (a[0][1] != b[0][1] || a[0][1] < 0) return a[0][0] + b[0][0] < BIGI ? a[0][0] + b[0][0] : BIGI;
    int best = BIGI; if (nb > 1 && b[1][0] < BIGI && a[0][0] + b[1][0] < best) best = a[0][0] + b[1][0]; if (na > 1 && a[1][0] < BIGI && a[1][0] + b[0][0] < best) best = a[1][0] + b[0][0];
    return best;
}
// memo of the stage-B closings per cycle sequence (the anchor closing of a cycle does not depend on the rest)
typedef struct CEnt { uint64_t h; int n, m; int8_t tr[NTR]; int cb[NTR][2][6]; struct CEnt *next; } CEnt;
#define CHB (1 << 20)
#define CMAX 2000000
static CEnt *ctab[CHB]; static long ncache = 0, nhit = 0, nmiss = 0;
static uint64_t seqhash(const Seg *s) { uint64_t h = 1469598103934665603ull ^ (uint64_t)s->n; for (int i = 0; i < s->n; i++) { h ^= (uint64_t)(s->tr[i] + 1); h *= 1099511628211ull; h ^= h >> 31; } return h; }
static CEnt *cfind(const Seg *s, uint64_t h) { for (CEnt *q = ctab[h & (CHB - 1)]; q; q = q->next) if (q->h == h && q->n == s->n) { int same = 1; for (int i = 0; i < s->n; i++) if (q->tr[i] != s->tr[i]) { same = 0; break; } if (same) return q; } return NULL; }
static int cache_get(const Seg *s, int (*cb)[2][6]) { uint64_t h = seqhash(s); int m = -1;
    #pragma omp critical(ccache)
    { CEnt *q = cfind(s, h); if (q) { memcpy(cb, q->cb, sizeof q->cb); m = q->m; nhit++; } else nmiss++; }
    return m; }
static void cache_put(const Seg *s, int (*cb)[2][6], int m) { uint64_t h = seqhash(s);
    #pragma omp critical(ccache)
    { if (ncache < CMAX && !cfind(s, h)) { CEnt *q = malloc(sizeof(CEnt)); q->h = h; q->n = s->n; q->m = m; for (int i = 0; i < s->n; i++) q->tr[i] = (int8_t)s->tr[i];
          memcpy(q->cb, cb, sizeof q->cb); q->next = ctab[h & (CHB - 1)]; ctab[h & (CHB - 1)] = q; ncache++; } } }
// memo of the stage-A values: tag 0 = least cost of the path P (from its first cut), tag 1 = decoupled cycle bound
typedef struct VEnt { uint64_t h; int n, tag, val; int8_t tr[NTR]; struct VEnt *next; } VEnt;
#define VHB (1 << 22)
#define VMAX 20000000
static VEnt **vtab; static long nvmemo = 0, nvhit = 0;
static int vmemo_get(int tag, const Seg *s) { uint64_t h = seqhash(s) ^ (uint64_t)(tag + 1) * 0x9E3779B97F4A7C15ull; int v = -1;
    #pragma omp critical(vmemo)
    { for (VEnt *q = vtab[h & (VHB - 1)]; q; q = q->next) if (q->h == h && q->tag == tag && q->n == s->n) { int same = 1; for (int i = 0; i < s->n; i++) if (q->tr[i] != s->tr[i]) { same = 0; break; } if (same) { v = q->val; nvhit++; break; } } }
    return v; }
static void vmemo_put(int tag, const Seg *s, int val) { uint64_t h = seqhash(s) ^ (uint64_t)(tag + 1) * 0x9E3779B97F4A7C15ull;
    #pragma omp critical(vmemo)
    { if (nvmemo < VMAX) { VEnt *q = malloc(sizeof(VEnt)); q->h = h; q->tag = tag; q->n = s->n; q->val = val; for (int i = 0; i < s->n; i++) q->tr[i] = (int8_t)s->tr[i];
          q->next = vtab[h & (VHB - 1)]; vtab[h & (VHB - 1)] = q; nvmemo++; } } }
static void eval_config(Seg *P, Seg *Z, int c, const char *line) {
    __atomic_add_fetch(&nconf, 1, __ATOMIC_RELAXED);
    int *b1 = malloc(4 * MAXOPT), *b2 = malloc(4 * MAXOPT), *st = malloc(4 * MAXOPT), *ov = malloc(4 * MAXOPT);
    // Stage A (the path part and every cycle part depend on their own sequence only: memoised)
    int minP = vmemo_get(0, P);
    if (minP < 0) { int t0 = P->tr[0]; for (int q = 0; q < tcnt[t0]; q++) st[q] = ocut[tofs[t0] + q] == 2;
        seg_dp(P, st, ov, b1, b2); minP = BIGI; { int tl = P->tr[P->n - 1]; for (int q = 0; q < tcnt[tl]; q++) if (ov[q] < minP) minP = ov[q]; }
        vmemo_put(0, P, minP); }
    int lbA = c + minP; int minZ[8];
    for (int i = 0; i < c; i++) { const Seg *s = &Z[i]; int t1 = s->tr[0], tl = s->tr[s->n - 1];
        int mz = vmemo_get(1, s);
        if (mz < 0) {
            for (int q = 0; q < tcnt[t1]; q++) { int m = BIGI; for (int T = 0; T < NTR; T++) if (!inseg(s, T)) { int v = hinT[T][tofs[t1] + q]; if (v < m) m = v; } st[q] = m; }
            seg_dp(s, st, ov, b1, b2); mz = BIGI;
            for (int q = 0; q < tcnt[tl]; q++) { if (ov[q] >= BIGI) continue; int m = BIGI; for (int T = 0; T < NTR; T++) if (!inseg(s, T)) { int v = houtT[T][tofs[tl] + q]; if (v < m) m = v; } if (ov[q] + m < mz) mz = ov[q] + m; }
            vmemo_put(1, s, mz); }
        minZ[i] = mz; lbA += mz; }
    if (lbA > THRG) goto done;
    __atomic_add_fetch(&nA_pass, 1, __ATOMIC_RELAXED);
    {   // Stage B: coupled closing over anchors of trails outside the cycle (both versions, any run)
        int lbB = c + minP; int *pathm[8]; int n1s[8], nls[8]; int ok = 1;
        int (*cb)[2][6] = calloc(8 * NTR, sizeof(int[2][6]));          // cb[i * NTR + T][v] = {v1, k1, v2, k2, v3, k3} (close3)
        for (int i = 0; i < c; i++) { const Seg *s = &Z[i]; int t1 = s->tr[0], tl = s->tr[s->n - 1]; int n1 = tcnt[t1], nl = tcnt[tl]; n1s[i] = n1; nls[i] = nl;
            pathm[i] = NULL; int slackmax = THRG - (lbA - minZ[i]);
            int m = cache_get(s, &cb[i * NTR]);           // the closings depend on the cycle sequence only: memoised
            if (m == -1) {
                pathm[i] = malloc(sizeof(int) * (size_t)n1 * nl);
                for (int aa = 0; aa < n1; aa++) { for (int q = 0; q < n1; q++) st[q] = q == aa ? 0 : BIGI; seg_dp(s, st, pathm[i] + (size_t)aa * nl, b1, b2); }
                m = BIGI;
                int *rmin = malloc(sizeof(int) * n1); for (int aa = 0; aa < n1; aa++) { int mm = BIGI; const int *pr = pathm[i] + (size_t)aa * nl; for (int b = 0; b < nl; b++) if (pr[b] < mm) mm = pr[b]; rmin[aa] = mm; }
                for (int T = 0; T < NTR; T++) { for (int v = 0; v < 2; v++) for (int j = 0; j < 3; j++) { cb[i * NTR + T][v][2 * j] = BIGI; cb[i * NTR + T][v][2 * j + 1] = -1; }
                    if (inseg(s, T)) continue;
                    for (int v = 0; v < 2; v++) { int val = close3(s, T, v, pathm[i], n1, nl, cb[i * NTR + T][v], rmin); if (val < m) m = val; } }
                free(rmin);
                cache_put(s, &cb[i * NTR], m); }
            if (m > slackmax) ok = 0; lbB += m; }
        if (!ok || lbB > THRG) { for (int i = 0; i < c; i++) free(pathm[i]); free(cb); goto done; }   /* free(NULL) is a no-op */
        __atomic_add_fetch(&nB_pass, 1, __ATOMIC_RELAXED);
        if (c > 2) { __atomic_add_fetch(&nC_c3, 1, __ATOMIC_RELAXED);
            #pragma omp critical
            { fprintf(wit, "{\"stage\": \"B-survivor-c>=3\", \"c\": %d, \"lbB\": %d, \"pattern\": \"%s\"}\n", c, lbB, line); fflush(wit); }
            for (int i = 0; i < c; i++) free(pathm[i]); free(cb); goto done; }
        __atomic_add_fetch(&nC_eval, 1, __ATOMIC_RELAXED);
        // Stage C (c <= 2): the anchor of cycle i belongs to a trail T_i whose main lies in another segment; its exact closing is
        // f_i(o) = (run(o) == k1 ? second : best)[T_i][version(o)], a node cost on T_i's option o in its segment.  Trees:
        // c = 1: T_1 in P.  c = 2: both in P, or one cycle (inner) anchored in the other (outer), the outer anchored in P.
        int best = BIGI; int bT[2] = {-1, -1}, bnest = -1; int *f1 = malloc(4 * MAXOPT), *f2 = malloc(4 * MAXOPT);
        #define FNODE(i, T, q) (over_[tofs[T] + (q)] , (okk[tofs[T] + (q)] == cb[(i) * NTR + (T)][over_[tofs[T] + (q)]][1] ? cb[(i) * NTR + (T)][over_[tofs[T] + (q)]][2] : cb[(i) * NTR + (T)][over_[tofs[T] + (q)]][0]))
        // P with node costs nA (trail TA, function fa) and nB (trail TB, function fb); returns least total P cost
        #define PDP(TA, FA, TB, FB, RES) { int *cur = b1, *nx = b2; int tpp = P->tr[0]; RES = BIGI; \
            for (int q = 0; q < tcnt[tpp]; q++) { int o = tofs[tpp] + q; int v0 = ocut[o] == 2; if (tpp == (TA)) v0 += (FA)[q]; if (tpp == (TB)) v0 += (FB)[q]; cur[q] = v0; } \
            for (int ii = 1; ii < P->n; ii++) { int tp = P->tr[ii - 1], t = P->tr[ii]; \
                step(cur, tp, t, nx); \
                for (int q = 0; q < tcnt[t]; q++) { int v = nx[q]; if (v < BIGI) { if (t == (TA)) v += (FA)[q]; if (t == (TB)) v += (FB)[q]; } nx[q] = v; } \
                int *tt = cur; cur = nx; nx = tt; } \
            int tlp = P->tr[P->n - 1]; for (int q = 0; q < tcnt[tlp]; q++) if (cur[q] < RES) RES = cur[q]; }
        int zero[MAXOPT]; memset(zero, 0, sizeof zero);
        if (c == 1) {
            for (int p1 = 0; p1 < P->n; p1++) { int T1 = P->tr[p1]; for (int q = 0; q < tcnt[T1]; q++) f1[q] = FNODE(0, T1, q);
                int r; PDP(T1, f1, -1, zero, r); if (r < BIGI && r + 1 < best) { best = r + 1; bT[0] = T1; } }
        } else {
            // both anchors in P
            for (int p1 = 0; p1 < P->n; p1++) for (int p2 = 0; p2 < P->n; p2++) { int T1 = P->tr[p1], T2 = P->tr[p2];
                if (SAME_ONLY >= 0 && (T1 != SAME_ONLY || T2 != SAME_ONLY)) continue;     // test mode: both anchors on one given trail
                for (int q = 0; q < tcnt[T1]; q++) f1[q] = FNODE(0, T1, q);
                for (int q = 0; q < tcnt[T2]; q++) f2[q] = FNODE(1, T2, q);
                int r; if (T1 == T2) {      // both cycles anchored on T1 (three pieces): two distinct anchor runs, both != the main's run
                    for (int q = 0; q < tcnt[T1]; q++) { int o = tofs[T1] + q, v = over_[o]; f1[q] = pair_same(cb[0 * NTR + T1][v], cb[1 * NTR + T1][v], okk[o]); }
                    PDP(T1, f1, -1, zero, r); if (r < BIGI && r + 2 <= THRG) __atomic_add_fetch(&nsame, 1, __ATOMIC_RELAXED); }
                else PDP(T1, f1, T2, f2, r);
                if (r < BIGI && r + 2 < best) { best = r + 2; bT[0] = T1; bT[1] = T2; bnest = -1; } }
            // nested: inner cycle in (0 or 1), anchored at a trail Tin of the outer cycle; outer anchored at Tout in P
            for (int inner = 0; inner < 2 && SAME_ONLY < 0; inner++) { int outer = 1 - inner; const Seg *so = &Z[outer]; int t1 = so->tr[0], tl = so->tr[so->n - 1]; int n1 = tcnt[t1], nl = tcnt[tl];
                int *pm2 = malloc(sizeof(int) * (size_t)n1 * nl);
                for (int pi = 0; pi < so->n; pi++) { int Tin = so->tr[pi]; int fin[MAXOPT]; for (int q = 0; q < tcnt[Tin]; q++) fin[q] = FNODE(inner, Tin, q);
                    for (int aa = 0; aa < n1; aa++) { int *cur = b1, *nx = b2;
                        for (int q = 0; q < n1; q++) cur[q] = q == aa ? (t1 == Tin ? fin[q] : 0) : BIGI;
                        for (int ii = 1; ii < so->n; ii++) { int tp = so->tr[ii - 1], t = so->tr[ii];
                            step(cur, tp, t, nx);
                            if (t == Tin) for (int q = 0; q < tcnt[t]; q++) if (nx[q] < BIGI) nx[q] += fin[q];
                            int *tt = cur; cur = nx; nx = tt; }
                        memcpy(pm2 + (size_t)aa * nl, cur, sizeof(int) * nl); }
                    for (int po = 0; po < P->n; po++) { int Tout = P->tr[po]; int fo2[MAXOPT];
                        int cc2[2][6]; for (int v = 0; v < 2; v++) close3(so, Tout, v, pm2, n1, nl, cc2[v], NULL);
                        for (int q = 0; q < tcnt[Tout]; q++) { int o = tofs[Tout] + q, v = over_[o]; fo2[q] = okk[o] == cc2[v][1] ? cc2[v][2] : cc2[v][0]; }
                        int r; PDP(Tout, fo2, -1, zero, r);
                        if (r < BIGI && r + 2 < best) { best = r + 2; bT[inner] = Tin; bT[outer] = Tout; bnest = inner; } } }
                free(pm2); }
        }
        free(f1); free(f2);
        for (int i = 0; i < c; i++) free(pathm[i]); free(cb);
        #pragma omp critical
        { if (best < 64) hist[best]++; if (best < bestG) bestG = best;
          if (best <= THRG) { fprintf(wit, "{\"stage\": \"C\", \"G\": %d, \"c\": %d, \"anchor_trails\": [%d, %d], \"nested_inner\": %d, \"P\": [", best, c, bT[0], bT[1], bnest);
              for (int i = 0; i < P->n; i++) fprintf(wit, "%s%d", i ? ", " : "", P->tr[i]); fprintf(wit, "], \"cycles\": [");
              for (int k = 0; k < c; k++) { fprintf(wit, "%s[", k ? ", " : ""); for (int i = 0; i < Z[k].n; i++) fprintf(wit, "%s%d", i ? ", " : "", Z[k].tr[i]); fprintf(wit, "]"); }
              fprintf(wit, "]}\n"); fflush(wit); } }
    }
done:
    free(b1); free(b2); free(st); free(ov);
}
// ---------------------------------------------------------------- pattern expansion
typedef struct { int kind; int n; int tr[6]; } Tok;   // kind 0 fixed sequence, 1 any order, 2 A-only cycles (split), 3 A-only path (any order)
static void perm_next(int *p, int n, int *done) { int i = n - 2; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) { *done = 1; return; } int j = n - 1; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t; for (int a = i + 1, b = n - 1; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
typedef struct { Tok tk[40]; int ntk; } SegT;
static SegT ST[16]; static int NSEG;
#pragma omp threadprivate(ST, NSEG)
static Seg CUR[16]; static int NC;                 // concrete segments being built (index 0 = P)
#pragma omp threadprivate(CUR, NC)
static const char *LINE;
#pragma omp threadprivate(LINE)
static void finish(void) {
    int seen[NTR] = {0}; for (int s = 0; s < NC; s++) for (int i = 0; i < CUR[s].n; i++) { int t = CUR[s].tr[i]; if (t < 0 || t >= NTR || seen[t]++) { fprintf(stderr, "pattern does not expand to a permutation of the 30 trails: %s\n", LINE); exit(9); } }
    for (int t = 0; t < NTR; t++) if (!seen[t]) { fprintf(stderr, "missing trail in pattern: %s\n", LINE); exit(9); }
    if (NC - 1 > 8) return;
    eval_config(&CUR[0], &CUR[1], NC - 1, LINE);
}
static void exp_seg(int s, int ti);
static void split_aonly(int s, int ti, int mask) {     // A-only cycles: choose the block containing the lowest A trail, all orders
    if (!mask) { CUR[NC].n = 0; exp_seg(s, ti + 1); return; }
    int low = __builtin_ctz(mask), rest = mask & ~(1 << low);
    for (int sub = rest; ; sub = (sub - 1) & rest) { int blk = sub | (1 << low); int tr[6], n = 0; for (int i = 0; i < 6; i++) if (blk >> i & 1) tr[n++] = Alist[i];
        int p[6]; for (int i = 0; i < n; i++) p[i] = i; int dn = 0;
        while (!dn) { Seg *z = &CUR[NC]; z->n = n; for (int i = 0; i < n; i++) z->tr[i] = tr[p[i]]; NC++; CUR[NC].n = 0; split_aonly(s, ti, mask & ~blk); NC--; perm_next(p, n, &dn); }
        if (!sub) break; }
}
static void exp_seg(int s, int ti) {
    if (s == NSEG) { finish(); return; }
    SegT *sg = &ST[s];
    if (ti == sg->ntk) { if (CUR[NC].n > 0) { int keep = CUR[NC].n; NC++; CUR[NC].n = 0; exp_seg(s + 1, 0); NC--; CUR[NC].n = keep; } else exp_seg(s + 1, 0); return; }
    Tok *t = &sg->tk[ti];
    if (t->kind == 2) { int mask = 0; for (int i = 0; i < t->n; i++) for (int a = 0; a < 6; a++) if (Alist[a] == t->tr[i]) mask |= 1 << a;
        int saveN = CUR[NC].n; if (saveN) { fprintf(stderr, "A-only cycle token inside a segment\n"); exit(9); }
        split_aonly(s, ti, mask); return; }
    Seg *cs = &CUR[NC]; int base = cs->n;
    if (t->kind == 0 || t->n <= 1) { for (int i = 0; i < t->n; i++) cs->tr[base + i] = t->tr[i]; cs->n = base + t->n; exp_seg(s, ti + 1); cs->n = base; return; }
    int p[6]; for (int i = 0; i < t->n; i++) p[i] = i; int dn = 0;
    while (!dn) { for (int i = 0; i < t->n; i++) cs->tr[base + i] = t->tr[p[i]]; cs->n = base + t->n; exp_seg(s, ti + 1); cs->n = base; perm_next(p, t->n, &dn); }
}
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: ckM_eval DIR PATTERNS THRG OUT.json [WITNESSES.jsonl]\n"); return 1; }
    const char *dir = argv[1]; THRG = atoi(argv[3]); char p[2048]; double T0 = omp_get_wtime();
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; okk[o] = k; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = nph = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; else phl[nph++] = t; }
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:neg)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) { int v = wgt(oex[a], oen[b]) - ocut[b] - 1; if (otr[a] != otr[b] && v < 0) neg++; e[(size_t)a * NOPT + b] = (int8_t)v; }
    if (neg) return 5;
    // optional mutation (tests): env CKB_MUT = file of lines "a b v" -> e(a, b) := v (same format as ckB.c / ckM2.c)
    { const char *mut = getenv("CKB_MUT"); int nmut = 0;
      if (mut && *mut) { FILE *mf = fopen(mut, "r"); int a, b, v; while (mf && fscanf(mf, "%d %d %d", &a, &b, &v) == 3) { e[(size_t)a * NOPT + b] = (int8_t)v; nmut++; } if (mf) fclose(mf); }
      if (nmut) fprintf(stderr, "mutations %d\n", nmut); }
    #pragma omp parallel for schedule(dynamic, 1)
    for (int t = 0; t < NTR; t++) { hinT[t] = malloc(NOPT); houtT[t] = malloc(NOPT);
        for (int o = 0; o < NOPT; o++) { int mi = 127, mo = 127; if (otr[o] != t) for (int q = 0; q < tcnt[t]; q++) { int x = tofs[t] + q; int a = E(x, o), b = E(o, x); if (a < mi) mi = a; if (b < mo) mo = b; }
            hinT[t][o] = mi; houtT[t][o] = mo; } }
    if (getenv("CKM_SAME_ONLY")) SAME_ONLY = atoi(getenv("CKM_SAME_ONLY"));
    vtab = calloc(VHB, sizeof(VEnt *));
    wit = fopen(argc > 5 ? argv[5] : "/dev/null", "w");
    FILE *pf = fopen(argv[2], "r"); if (!pf) return 2;
    char **lines = NULL; long nl = 0, cap = 0; char buf[8192];
    while (fgets(buf, sizeof buf, pf)) { if (nl == cap) { cap = cap ? 2 * cap : 1024; lines = realloc(lines, cap * sizeof(char *)); } buf[strcspn(buf, "\n")] = 0; lines[nl++] = strdup(buf); }
    fclose(pf);
    fprintf(stderr, "%ld patterns\n", nl);
    long npat = 0;
    #pragma omp parallel for schedule(dynamic, 4) reduction(+:npat)
    for (long li = 0; li < nl; li++) {
        LINE = lines[li]; NSEG = 1; ST[0].ntk = 0; char *s = lines[li]; int v, nch;
        while (sscanf(s, "%d%n", &v, &nch) == 1) { s += nch;
            if (v == -1) { NSEG++; ST[NSEG - 1].ntk = 0; continue; }
            Tok *t = &ST[NSEG - 1].tk[ST[NSEG - 1].ntk++]; t->n = 0; t->kind = 0;
            if (v < 1000) { t->tr[0] = v; t->n = 1; }
            else if (v >= 1400) { int m = v - 1400; for (int i = 0; i < 6; i++) if (m >> i & 1) t->tr[t->n++] = Alist[i]; t->kind = 1; }
            else if (v >= 1300) { int m = v - 1300; for (int i = 0; i < 6; i++) if (m >> i & 1) t->tr[t->n++] = Alist[i]; t->kind = 2; }
            else if (v >= 1200) { int m = v - 1200; for (int i = 0; i < 6; i++) if (m >> i & 1) t->tr[t->n++] = Alist[i]; t->kind = 1; }
            else { int d = v - 1100; if (d < 64) { for (int i = 0; i < 6; i++) if (d >> i & 1) t->tr[t->n++] = Alist[i]; } else { d -= 64; t->tr[0] = Alist[d / 6]; t->tr[1] = Alist[d % 6]; t->n = 2; } } }
        NC = 0; for (int i = 0; i < 16; i++) CUR[i].n = 0;
        exp_seg(0, 0); npat++;
    }
    FILE *fo = fopen(argv[4], "w");
    fprintf(fo, "{\"checker\": \"M-eval\", \"THRG\": %d, \"patterns\": %ld, \"configurations\": %ld, \"stageA_pass\": %ld, \"stageB_pass\": %ld, \"stageC_evaluated\": %ld, \"stageB_survivors_with_c_ge_3\": %ld, \"same_anchor_trail_le_thr_exact\": %ld, \"min_G_exact\": %d, \"G_hist\": {",
            THRG, npat, nconf, nA_pass, nB_pass, nC_eval, nC_c3, nsame, bestG < BIGI ? bestG : -1);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %ld", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    fclose(wit);
    fprintf(stderr, "stage-B cache: %ld cycles stored, %ld hits, %ld misses; stage-A memo: %ld entries, %ld hits\n", ncache, nhit, nmiss, nvmemo, nvhit);
    printf("{\"patterns\": %ld, \"configurations\": %ld, \"stageA_pass\": %ld, \"stageB_pass\": %ld, \"stageC_evaluated\": %ld, \"c_ge_3_survivors\": %ld, \"min_G_exact\": %d}\n", npat, nconf, nA_pass, nB_pass, nC_eval, nC_c3, bestG < BIGI ? bestG : -1);
    return 0;
}
