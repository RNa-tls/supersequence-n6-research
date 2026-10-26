// Round R -- backward relaxed DP for the BRACKET-TREE family (all multi-openings with V = P, any number of brackets).
// By the detour lemmas L1/L2 (l2check.c) every V = P multi-opening reduces, without increasing G, to a bracket tree:
// a path P of mains (one cut per trail) plus c >= 0 cycles Z_i, each = (one anchor u_i, mains), u_i a second cut of
// a trail whose main lies outside Z_i.  Opening every cycle at its anchor and appending the cycles to P gives a
// sequence SIGMA of all 30 trails (each once) with c JUNCTIONS, and
//     G = c + [cut(first) = 2] + sum_{non-junction edges of SIGMA} e + sum_i beta_i,
//     beta_i = e(last of Z_i -> u_i) + e(u_i -> first of Z_i) >= hout(last of Z_i) + hin(first of Z_i),
// hin(y) = min_{u of another trail} e(u -> y), hout(x) = min_{u of another trail} e(x -> u).
// Two relaxed (A-identity-free, as ckB.c) completion tables over the canonical states of ckB.c:
//   HZ(S, t, c)[o]: completion while inside a cycle segment (its end pays hout of its last option);
//   HP(S, t, c)[o]: completion while inside P that contains AT LEAST ONE junction.
// A junction after t: end chain of a1 A trails (+ hout of the last option if leaving a cycle), + 1, then a new cycle
// segment: free start (+ hin of the first option) -- PLZ[R][c'] (any number of further junctions; A-only segments
// cost >= 1 + least hin + least hout over A options per extra junction, or least hin + hout when they end SIGMA).
// Layers OUT/HZ%02d.val, OUT/HP%02d.val (keys identical to ckB.c's H%02d.key, which are not rewritten).
// Prints the relaxed minimum of G over all bracket trees with c >= 1.
// usage: ckM DIR(runs.bin, group.bin) OUT
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define NPH 24
#define NOP 84
#define NOR 42
#define NCN 7
#define BIG 200
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT; static int otr[16384], over_[16384], ok_[16384]; static uint8_t oen[16384][8], oex[16384][8]; static int ocut[16384];
static int8_t *e;
static int isA[NTR], Alist[6], nA = 0, phl[NPH], nph = 0, tofs[NTR], tcnt[NTR];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static uint64_t bn[25][26];
static inline uint64_t rk(uint32_t m) { uint64_t r = 0; int i = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) { i++; r += bn[b][i]; } return r; }
static uint32_t urk(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 < NPH && bn[b + 1][i] <= r) b++; r -= bn[b][i]; m |= 1u << b; } return m; }
static int G, gt[12][NTR]; static int32_t *gop;
static int sel[6]; static int ptr[6][NPH];
static int kap[16384];
static int orep[NPH][NOR], oorb[NPH][NOP];
static int omapB[6][NPH][NOR];
static uint8_t Kred[NCN][NPH][NPH][NOR][NOR];
static uint8_t Q0red[NCN][NPH][NOR], Qhred[NCN][NPH][NOR], Sred[NCN][NPH][NOR], Fhred[NCN][NPH][NOR];
static inline void amin8(uint8_t *p, uint8_t v) { uint8_t old = __atomic_load_n(p, __ATOMIC_RELAXED); while (v < old && !__atomic_compare_exchange_n(p, &old, v, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {} }
static inline uint64_t keyof(uint32_t m, int t) { return (rk(m) << 5) | (uint64_t)t; }
static inline uint32_t pmB(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
static inline uint64_t canB(uint32_t m, int t, int *gg) { uint64_t best = 0; int bg = -1; for (int g = 0; g < 6; g++) { uint64_t k = keyof(pmB(g, m), ptr[g][t]); if (bg < 0 || k > best) { best = k; bg = g; } } *gg = bg; return best; }
typedef struct { uint64_t *k; uint8_t *z, *p; uint64_t n; } Lay;
static int64_t fnd(const Lay *L, uint64_t key) { int64_t lo = 0, hi = (int64_t)L->n - 1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (L->k[mid] < key) lo = mid + 1; else if (L->k[mid] > key) hi = mid - 1; else return mid; } return -1; }
static int cmp(const void *a, const void *b) { uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b; return (x > y) - (x < y); }
#define VSZ (NCN * NOR)
static void mklay(Lay *L, int k) {
    uint64_t nm = bn[NPH][k]; uint64_t cap = nm * k / 2 + 100; L->k = malloc(8 * cap); L->n = 0;
    for (uint64_t r = 0; r < nm; r++) { uint32_t m = urk(r, k);
        for (int t = 0; t < NPH; t++) { if (!(m >> t & 1)) continue; int g; uint64_t c = canB(m, t, &g); if (c == keyof(m, t)) { if (L->n >= cap) { fprintf(stderr, "cap\n"); exit(3); } L->k[L->n++] = c; } } }
    qsort(L->k, L->n, 8, cmp); L->z = malloc(L->n * VSZ + 64); L->p = malloc(L->n * VSZ + 64);
}
static void lfree(Lay *L) { free(L->k); free(L->z); free(L->p); }
int main(int argc, char **argv) {
    const char *dir = argv[1], *out = argv[2]; char p[2048];
    for (int n = 0; n <= 24; n++) for (int k = 0; k <= 25; k++) bn[n][k] = k == 0 ? 1 : (n == 0 ? 0 : bn[n - 1][k - 1] + bn[n - 1][k]);
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; ok_[o] = k;
            memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1];
            ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; else phl[nph++] = t; }
    if (nA != 6 || nph != NPH) return 4;
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for reduction(+:neg) schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) {
        if (otr[a] == otr[b]) { e[(size_t)a * NOPT + b] = 99; continue; }
        int v = wgt(oex[a], oen[b]) - ocut[b] - 1; if (v < 0) neg++; e[(size_t)a * NOPT + b] = v; }
    if (neg) return 5;
    const char *mut = getenv("CKB_MUT"); int nmut = 0;
    if (mut && *mut) { FILE *mf = fopen(mut, "r"); int a, b, v; while (mf && fscanf(mf, "%d %d %d", &a, &b, &v) == 3) { e[(size_t)a * NOPT + b] = (int8_t)v; nmut++; } if (mf) fclose(mf);
        fprintf(stderr, "mutations applied: %d\n", nmut); }
    snprintf(p, sizeof p, "%s/group.bin", dir); f = fopen(p, "rb"); if (fread(&G, 4, 1, f) != 1) return 2;
    int32_t *tpb = malloc(4 * G * NTR); if (fread(tpb, 4, G * NTR, f) != (size_t)(G * NTR)) return 2;
    gop = malloc(4 * (size_t)G * NOPT); if (fread(gop, 4, (size_t)G * NOPT, f) != (size_t)G * NOPT) return 2; fclose(f);
    for (int g = 0; g < G; g++) for (int t = 0; t < NTR; t++) gt[g][t] = tpb[g * NTR + t];
    long bad = 0;
    #pragma omp parallel for reduction(+:bad)
    for (int g = 0; g < G; g++) { const int32_t *P = gop + (size_t)g * NOPT;
        for (int a = 0; a < NOPT; a++) { if (otr[P[a]] != gt[g][otr[a]] || ocut[P[a]] != ocut[a]) bad++;
            for (int b = 0; b < NOPT; b++) if (e[(size_t)P[a] * NOPT + P[b]] != e[(size_t)a * NOPT + b]) bad++; } }
    if (bad) { fprintf(stderr, "group invariance violated %ld\n", bad); return 6; }
    int phidx[NTR]; for (int i = 0; i < NPH; i++) phidx[phl[i]] = i;
    int ns = 0, ki = -1;
    for (int g = 0; g < G; g++) { int idt = 1; for (int t = 0; t < NTR; t++) if (gt[g][t] != t) idt = 0;
        int ido = 1; for (int o = 0; o < NOPT; o++) if (gop[(size_t)g * NOPT + o] != o) { ido = 0; break; }
        if (idt && !ido) ki = g;
        int dup = 0; for (int s = 0; s < ns; s++) { int same = 1; for (int t = 0; t < NTR; t++) if (gt[sel[s]][t] != gt[g][t]) same = 0; if (same) dup = 1; }
        if (!dup) sel[ns++] = g; }
    if (ns != 6 || ki < 0) return 7;
    for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ptr[s][i] = phidx[gt[sel[s]][phl[i]]];
    for (int o = 0; o < NOPT; o++) kap[o] = gop[(size_t)ki * NOPT + o];
    for (int i = 0; i < NPH; i++) { int t = phl[i], c = 0; for (int q = 0; q < NOP; q++) oorb[i][q] = -1;
        for (int q = 0; q < NOP; q++) { int o = tofs[t] + q, o2 = kap[o]; int q2 = o2 - tofs[t]; if (q2 < 0 || q2 >= NOP || q2 == q) return 8;
            if (oorb[i][q] >= 0) continue; int r = q > q2 ? q : q2; orep[i][c] = r; oorb[i][q] = c; oorb[i][q2] = c; c++; }
        if (c != NOR) return 9; }
    for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) {
        int o = tofs[phl[i]] + orep[i][j]; int o2 = gop[(size_t)sel[s] * NOPT + o]; int i2 = ptr[s][i]; omapB[s][i][j] = oorb[i2][o2 - tofs[phl[i2]]]; }
    // anchor bounds hin / hout (over options of any other trail)
    uint8_t *hin = malloc(NOPT), *hout = malloc(NOPT);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int o = 0; o < NOPT; o++) { int mi = BIG, mo = BIG;
        for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[o]) continue; int a = e[(size_t)u * NOPT + o], b = e[(size_t)o * NOPT + u]; if (a < mi) mi = a; if (b < mo) mo = b; }
        hin[o] = mi; hout[o] = mo; }
    long bi = 0; for (int g = 0; g < G; g++) for (int o = 0; o < NOPT; o++) { int o2 = gop[(size_t)g * NOPT + o]; if (hin[o2] != hin[o] || hout[o2] != hout[o]) bi++; }
    int hinA = BIG, houtA = BIG; for (int a = 0; a < 6; a++) for (int q = 0; q < tcnt[Alist[a]]; q++) { int o = tofs[Alist[a]] + q; if (hin[o] < hinA) hinA = hin[o]; if (hout[o] < houtA) houtA = hout[o]; }
    int AZ = hinA + houtA;                 // least closing bound of an A-only cycle segment
    { long h0[3] = {0}, g0[3] = {0}; for (int o = 0; o < NOPT; o++) { if (hin[o] < 3) h0[hin[o]]++; if (hout[o] < 3) g0[hout[o]]++; }
      fprintf(stderr, "hin hist %ld %ld %ld, hout hist %ld %ld %ld, least over A options: hin %d hout %d, group violations %ld\n", h0[0], h0[1], h0[2], g0[0], g0[1], g0[2], hinA, houtA, bi); }
    if (bi) return 16;
    // chain tables
    int NPO = NPH * NOP; int NAO = tcnt[Alist[0]];
    uint8_t *Kc = malloc((size_t)NCN * NPO * NPO); memset(Kc, BIG, (size_t)NCN * NPO * NPO);
    uint8_t *Sc = malloc(NCN * NPO), *Q0c = malloc(NCN * NPO), *Qhc = malloc(NCN * NPO), *Fhc = malloc(NCN * NPO);
    memset(Sc, BIG, NCN * NPO); memset(Q0c, BIG, NCN * NPO); memset(Qhc, BIG, NCN * NPO); memset(Fhc, BIG, NCN * NPO);
    for (int y = 0; y < NPO; y++) for (int x = 0; x < NPO; x++) { int oy = tofs[phl[y / NOP]] + y % NOP, ox = tofs[phl[x / NOP]] + x % NOP; if (otr[oy] != otr[ox]) Kc[(size_t)y * NPO + x] = e[(size_t)oy * NOPT + ox]; }
    for (int x = 0; x < NPO; x++) { int ox = tofs[phl[x / NOP]] + x % NOP; Sc[x] = (ocut[ox] == 2); Q0c[x] = 0; Qhc[x] = hout[ox]; Fhc[x] = hin[ox]; }
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y <= NPO + 1; y++) {          // y = NPO: word start; y = NPO + 1: free start with hin
        uint8_t *cur = malloc(6 * NAO), *nx = malloc(6 * NAO);
        for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int oa = tofs[Alist[a]] + q;
            cur[a * NAO + q] = (y < NPO) ? e[(size_t)(tofs[phl[y / NOP]] + y % NOP) * NOPT + oa] : (y == NPO ? (ocut[oa] == 2) : hin[oa]); }
        for (int len = 1; len <= 6; len++) {
            uint8_t row[NPH * NOP]; memset(row, BIG, NPO); int qm = BIG, qh = BIG;
            for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; if (v < qm) qm = v; int vh = v + hout[tofs[Alist[a]] + q]; if (vh < qh) qh = vh;
                const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT;
                for (int x = 0; x < NPO; x++) { int w = v + er[tofs[phl[x / NOP]] + x % NOP]; if (w < row[x]) row[x] = w; } }
            if (y < NPO) { memcpy(Kc + ((size_t)len * NPO + y) * NPO, row, NPO); Q0c[len * NPO + y] = qm; Qhc[len * NPO + y] = qh > BIG ? BIG : qh; }
            else if (y == NPO) memcpy(Sc + len * NPO, row, NPO); else memcpy(Fhc + len * NPO, row, NPO);
            if (len == 6) break;
            memset(nx, BIG, 6 * NAO);
            for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue;
                const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT;
                for (int b = 0; b < 6; b++) { if (b == a) continue; const int8_t *eb = er + tofs[Alist[b]]; uint8_t *nb = nx + b * NAO;
                    for (int r = 0; r < NAO; r++) { int w = v + eb[r]; if (w < nb[r]) nb[r] = w; } } }
            uint8_t *tt = cur; cur = nx; nx = tt;
        }
        free(cur); free(nx);
    }
    fprintf(stderr, "chain tables done\n");
    long badc = 0;
    for (int s = 0; s < 6; s++) { int g = sel[s];
        for (int len = 0; len < NCN; len++) for (int y = 0; y < NPO; y += 7) for (int x = 0; x < NPO; x++) {
            int oy = tofs[phl[y / NOP]] + y % NOP, ox = tofs[phl[x / NOP]] + x % NOP; if (otr[oy] == otr[ox]) continue;
            int gy = gop[(size_t)g * NOPT + oy], gx = gop[(size_t)g * NOPT + ox];
            int yy = phidx[otr[gy]] * NOP + (gy - tofs[otr[gy]]), xx = phidx[otr[gx]] * NOP + (gx - tofs[otr[gx]]);
            if (Kc[((size_t)len * NPO + yy) * NPO + xx] != Kc[((size_t)len * NPO + y) * NPO + x]) badc++; } }
    if (badc) { fprintf(stderr, "chain-table invariance violations %ld\n", badc); return 10; }
    for (int a = 0; a < NCN; a++) for (int t = 0; t < NPH; t++) for (int u = 0; u < NPH; u++) for (int i = 0; i < NOR; i++) for (int j = 0; j < NOR; j++) {
        if (t == u) { Kred[a][t][u][i][j] = BIG; continue; }
        int y = t * NOP + orep[t][i]; int x1 = u * NOP + orep[u][j]; int ox1 = tofs[phl[u]] + orep[u][j]; int ox2 = kap[ox1]; int x2 = u * NOP + (ox2 - tofs[phl[u]]);
        int v1 = Kc[((size_t)a * NPO + y) * NPO + x1], v2 = Kc[((size_t)a * NPO + y) * NPO + x2]; Kred[a][t][u][i][j] = v1 < v2 ? v1 : v2; }
    for (int a = 0; a < NCN; a++) for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) {
        int q = orep[t][i], q2 = kap[tofs[phl[t]] + q] - tofs[phl[t]];
        Q0red[a][t][i] = Q0c[a * NPO + t * NOP + q]; Qhred[a][t][i] = Qhc[a * NPO + t * NOP + q]; Sred[a][t][i] = Sc[a * NPO + t * NOP + q]; Fhred[a][t][i] = Fhc[a * NPO + t * NOP + q];
        if (Q0c[a * NPO + t * NOP + q2] != Q0red[a][t][i] || Qhc[a * NPO + t * NOP + q2] != Qhred[a][t][i] || Sc[a * NPO + t * NOP + q2] != Sred[a][t][i] || Fhc[a * NPO + t * NOP + q2] != Fhred[a][t][i]) return 11; }
    free(Kc); free(e);
    // PLZ[R][c]: relaxed least completion that starts a NEW cycle segment covering exactly the phi set R and c A trails
    uint32_t FULL = (1u << NPH) - 1; size_t NU = (size_t)1 << NPH;
    uint8_t *PLZ = malloc(NU * NCN); memset(PLZ, BIG, NU * NCN);
    // R empty: A-only segment(s); PLZ[0][0] = BIG (empty segment impossible); one A-only segment that ends SIGMA costs >= AZ
    for (int c = 1; c < NCN; c++) PLZ[c] = (uint8_t)AZ;
    Lay Lnext; mklay(&Lnext, NPH);
    // layer 24
    for (uint64_t x = 0; x < Lnext.n; x++) { int t = Lnext.k[x] & 31; uint8_t *vz = Lnext.z + x * VSZ, *vp = Lnext.p + x * VSZ;
        for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) { int mz = Qhred[c][t][i], mp = BIG;
            for (int a1 = 0; a1 < c; a1++) { int j1 = Qhred[a1][t][i] + 1 + PLZ[c - a1], j0 = Q0red[a1][t][i] + 1 + PLZ[c - a1]; if (j1 < mz) mz = j1; if (j0 < mp) mp = j0; }
            vz[c * NOR + i] = mz > BIG ? BIG : mz; vp[c * NOR + i] = mp > BIG ? BIG : mp; } }
    long double tw = 0;
    for (int k = NPH; k >= 1; k--) {
        if (k < NPH) {
            double t0 = omp_get_wtime(); Lay L; mklay(&L, k);
            #pragma omp parallel for schedule(dynamic, 64)
            for (uint64_t x = 0; x < L.n; x++) {
                int t = L.k[x] & 31; uint32_t S = urk(L.k[x] >> 5, k);
                int az[NCN][NOR], ap[NCN][NOR]; const uint8_t *pl = PLZ + (size_t)(FULL & ~S) * NCN;
                for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) { int mz = BIG, mp = BIG;
                    for (int a1 = 0; a1 <= c; a1++) { int j1 = Qhred[a1][t][i] + 1 + pl[c - a1], j0 = Q0red[a1][t][i] + 1 + pl[c - a1]; if (j1 < mz) mz = j1; if (j0 < mp) mp = j0; }
                    az[c][i] = mz; ap[c][i] = mp; }
                for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue;
                    int g; uint64_t ck = canB(S | 1u << u, u, &g); int64_t id = fnd(&Lnext, ck); if (id < 0) { fprintf(stderr, "missing\n"); exit(12); }
                    const uint8_t *hz = Lnext.z + id * VSZ, *hp = Lnext.p + id * VSZ; int nz[NCN][NOR], np_[NCN][NOR];
                    for (int c = 0; c < NCN; c++) for (int j = 0; j < NOR; j++) { nz[c][j] = hz[c * NOR + omapB[g][u][j]]; np_[c][j] = hp[c * NOR + omapB[g][u][j]]; }
                    for (int c = 0; c < NCN; c++) for (int a = 0; a <= c; a++) { int cc = c - a;
                        for (int i = 0; i < NOR; i++) { const uint8_t *kr = Kred[a][t][u][i]; int mz = az[c][i], mp = ap[c][i];
                            for (int j = 0; j < NOR; j++) { int w = kr[j] + nz[cc][j]; if (w < mz) mz = w; int w2 = kr[j] + np_[cc][j]; if (w2 < mp) mp = w2; }
                            az[c][i] = mz; ap[c][i] = mp; } } }
                uint8_t *dz = L.z + x * VSZ, *dp = L.p + x * VSZ;
                for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) { dz[c * NOR + i] = az[c][i] > BIG ? BIG : az[c][i]; dp[c * NOR + i] = ap[c][i] > BIG ? BIG : ap[c][i]; }
            }
            lfree(&Lnext); Lnext = L;
            fprintf(stderr, "backward layer %d: %llu canonical states, %.1fs\n", k, (unsigned long long)L.n, omp_get_wtime() - t0); tw += omp_get_wtime() - t0;
        }
        snprintf(p, sizeof p, "%s/HZ%02d.val", out, k); f = fopen(p, "wb"); fwrite(Lnext.z, VSZ, Lnext.n, f); fclose(f);
        snprintf(p, sizeof p, "%s/HP%02d.val", out, k); f = fopen(p, "wb"); fwrite(Lnext.p, VSZ, Lnext.n, f); fclose(f);
        // update PLZ for the remaining sets R = (FULL \ S) + t, |R| = 25 - k, from this layer's HZ
        #pragma omp parallel for schedule(dynamic, 4096)
        for (uint64_t x = 0; x < Lnext.n; x++) { uint64_t key = Lnext.k[x]; int t = key & 31; uint32_t S = urk(key >> 5, k); const uint8_t *hv = Lnext.z + x * VSZ; int vp[NCN];
            for (int c = 0; c < NCN; c++) { int m = BIG; for (int a = 0; a <= c; a++) for (int i = 0; i < NOR; i++) { int v = Fhred[a][t][i] + hv[(c - a) * NOR + i]; if (v < m) m = v; } vp[c] = m; }
            uint32_t R = (FULL & ~S) | (1u << t);
            for (int g = 0; g < 6; g++) { uint32_t Rg = pmB(g, R); for (int c = 0; c < NCN; c++) if (vp[c] < BIG) amin8(PLZ + (size_t)Rg * NCN + c, (uint8_t)vp[c]); } }
        // A-only segments followed by another junction: PLZ[R][c] <= AZ + 1 + PLZ[R][c - a2], a2 >= 1 (increasing c)
        { int sz = NPH - k + 1;
          #pragma omp parallel for schedule(dynamic, 65536)
          for (size_t R = 1; R < NU; R++) { if (__builtin_popcount((uint32_t)R) != sz) continue;
              for (int c = 1; c < NCN; c++) for (int a2 = 1; a2 <= c; a2++) { int v = AZ + 1 + PLZ[R * NCN + c - a2]; if (v < PLZ[R * NCN + c]) PLZ[R * NCN + c] = (uint8_t)(v > BIG ? BIG : v); } } }
    }
    { long unset = 0; for (size_t R = 1; R < NU; R++) for (int c = 0; c < NCN; c++) if (PLZ[R * NCN + c] >= BIG) unset++; fprintf(stderr, "PLZ unset entries %ld\n", unset); }
    snprintf(p, sizeof p, "%s/PLZ.bin", out); f = fopen(p, "wb"); fwrite(PLZ, 1, NU * NCN, f); fclose(f);
    // root: P starts at phi trail t after a start chain of a A trails; or P is A-only (a1 >= 1 A trails) then a junction
    int best = 1000, bestA = 1000; int hist[64] = {0};
    for (uint64_t x = 0; x < Lnext.n; x++) { int t = Lnext.k[x] & 31; const uint8_t *v = Lnext.p + x * VSZ;
        for (int a = 0; a < NCN; a++) for (int i = 0; i < NOR; i++) { int w = Sred[a][t][i] + v[(6 - a) * NOR + i]; if (w < best) best = w; } }
    for (int a1 = 1; a1 <= 6; a1++) { int w = 0 + 1 + PLZ[(size_t)FULL * NCN + 6 - a1]; if (w < bestA) bestA = w; }
    (void)hist;
    printf("{\"checker\": \"M\", \"relaxed_min_G_bracket_trees_P_has_phi\": %d, \"relaxed_min_G_bracket_trees_P_A_only\": %d, \"relaxed_G_lower_bound\": %d, \"hinA\": %d, \"houtA\": %d, \"sec\": %.1f}\n",
           best, bestA, best < bestA ? best : bestA, hinA, houtA, (double)tw);
    snprintf(p, sizeof p, "%s/meta.bin", out); f = fopen(p, "wb");
    fwrite(phl, 4, NPH, f); fwrite(ptr, 4, 6 * NPH, f); fwrite(orep, 4, NPH * NOR, f); fwrite(oorb, 4, NPH * NOP, f); fwrite(omapB, 4, 6 * NPH * NOR, f); fclose(f);
    return 0;
}
