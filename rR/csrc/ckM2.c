// Round R -- backward relaxed DP for bracket trees with AT MOST TWO cycles (c = 1, 2), the case that decides P = 32,
// V = 32 after the detour reduction (rR/csrc/l2check.c, rR/lean/BracketTree.lean).  SIGMA = P ++ Z_1' (++ Z_2'),
// every cycle opened at its anchor:  G = c + [cut first = 2] + sum_{non-junction edges} e + sum_i beta_i.
// Anchor bounds: a cycle segment with at least two trails closes with >= hout(last) + hin(first) (decoupled); a cycle
// with ONE main z (no A trail beside it) closes with exactly loop1(z) = min_u e(z -> u) + e(u -> z) (>= 3 here).
// Tables over the canonical states of ckB.c (values per remaining A count c and option orbit i):
//   HZ0(S, t, c): inside the LAST cycle segment, which has >= 2 trails including t (end pays hout of its last option);
//   HZ1(S, t, c): inside a cycle segment with >= 2 trails, at most one more junction;
//   HP (S, t, c): inside P, one or two junctions still to come.
// One-trail segments (just after a junction, no A trail yet) are evaluated on the fly ("s" values, not stored):
// they may close at once with loop1 - hin (hin was paid at the start).  The forward search may use HZ0/HZ1 for them
// (HZ_J <= HZ_J^s, so this stays a lower bound).
// Storage: 4-bit values per layer with offset off_k = layer minimum, value min(v - off_k, 15) (a valid lower bound;
// exact up to off_k + 14).  Files OUT/{HZ0,HZ1,HP}%02d.nib, OUT/offsets.txt; PL0/PL1 (new-segment completions) in
// OUT/PL0.bin, OUT/PL1.bin.  Prints the relaxed minimum of G over all bracket trees with 1 <= c <= 2.
// usage: ckM2 DIR(runs.bin, group.bin) OUT
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
static uint8_t Q0red[NCN][NPH][NOR], Qhred[NCN][NPH][NOR], Sred[NCN][NPH][NOR], Fhred[NCN][NPH][NOR], L1red[NPH][NOR];
static inline void amin8(uint8_t *p, uint8_t v) { uint8_t old = __atomic_load_n(p, __ATOMIC_RELAXED); while (v < old && !__atomic_compare_exchange_n(p, &old, v, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {} }
static inline uint64_t keyof(uint32_t m, int t) { return (rk(m) << 5) | (uint64_t)t; }
static inline uint32_t pmB(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
static inline uint64_t canB(uint32_t m, int t, int *gg) { uint64_t best = 0; int bg = -1; for (int g = 0; g < 6; g++) { uint64_t k = keyof(pmB(g, m), ptr[g][t]); if (bg < 0 || k > best) { best = k; bg = g; } } *gg = bg; return best; }
typedef struct { uint64_t *k; uint8_t *z0, *z1, *p; uint64_t n; } Lay;
static int64_t fnd(const Lay *L, uint64_t key) { int64_t lo = 0, hi = (int64_t)L->n - 1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (L->k[mid] < key) lo = mid + 1; else if (L->k[mid] > key) hi = mid - 1; else return mid; } return -1; }
static int cmp(const void *a, const void *b) { uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b; return (x > y) - (x < y); }
#define VSZ (NCN * NOR)
static void mklay(Lay *L, int k) {
    uint64_t nm = bn[NPH][k]; uint64_t cap = nm * k / 2 + 100; L->k = malloc(8 * cap); L->n = 0;
    for (uint64_t r = 0; r < nm; r++) { uint32_t m = urk(r, k);
        for (int t = 0; t < NPH; t++) { if (!(m >> t & 1)) continue; int g; uint64_t c = canB(m, t, &g); if (c == keyof(m, t)) { if (L->n >= cap) { fprintf(stderr, "cap\n"); exit(3); } L->k[L->n++] = c; } } }
    qsort(L->k, L->n, 8, cmp); L->z0 = malloc(L->n * VSZ + 64); L->z1 = malloc(L->n * VSZ + 64); L->p = malloc(L->n * VSZ + 64);
}
static void lfree(Lay *L) { free(L->k); free(L->z0); free(L->z1); free(L->p); }
// 4-bit storage: value min(v - off, 15) (15 also for BIG); returns the offset used
static int write_nib(const char *path, const uint8_t *v, uint64_t n) { int off = 255; for (uint64_t i = 0; i < n * VSZ; i++) if (v[i] < BIG && v[i] < off) off = v[i]; if (off == 255) off = 0;
    FILE *f = fopen(path, "wb"); uint8_t *buf = malloc(n * VSZ / 2 + 8); for (uint64_t i = 0; i < n * VSZ; i += 2) { int a = v[i] >= BIG ? 15 : (v[i] - off > 15 ? 15 : v[i] - off), b = v[i + 1] >= BIG ? 15 : (v[i + 1] - off > 15 ? 15 : v[i + 1] - off); buf[i / 2] = (uint8_t)(a | b << 4); }
    fwrite(buf, 1, n * VSZ / 2, f); fclose(f); free(buf); return off; }
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
    // loop1(z) = min_u e(z -> u) + e(u -> z): exact closing of a cycle whose only main is z
    uint8_t *loop1 = malloc(NOPT);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int o = 0; o < NOPT; o++) { int m = BIG; for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[o]) continue; int v = e[(size_t)o * NOPT + u] + e[(size_t)u * NOPT + o]; if (v < m) m = v; } loop1[o] = m; }
    int loop1A = BIG; for (int a = 0; a < 6; a++) for (int q = 0; q < tcnt[Alist[a]]; q++) { int o = tofs[Alist[a]] + q; if (loop1[o] < loop1A) loop1A = loop1[o]; }
    { long bl = 0; for (int g = 0; g < G; g++) for (int o = 0; o < NOPT; o++) if (loop1[gop[(size_t)g * NOPT + o]] != loop1[o]) bl++; if (bl) return 17;
      int lmin = BIG; for (int o = 0; o < NOPT; o++) if (loop1[o] < lmin) lmin = loop1[o]; fprintf(stderr, "loop1: least %d, least over A options %d\n", lmin, loop1A); }
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
    for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { int o = tofs[phl[t]] + orep[t][i]; int v = loop1[o] - hin[o]; if (v < 0) return 18; L1red[t][i] = (uint8_t)v;
        if (loop1[kap[o]] != loop1[o] || hin[kap[o]] != hin[o]) return 19; }
    free(Kc); free(e);
    // PL0[R][c] / PL1[R][c]: relaxed least completion that starts a NEW cycle segment covering exactly the phi set R and c
    // A trails, with no / at most one further junction.  R empty: A-only segment(s).
    uint32_t FULL = (1u << NPH) - 1; size_t NU = (size_t)1 << NPH;
    uint8_t *PL0 = malloc(NU * NCN), *PL1 = malloc(NU * NCN); memset(PL0, BIG, NU * NCN); memset(PL1, BIG, NU * NCN);
    int AZ2 = hinA + houtA;                                    // A-only segment with >= 2 trails (decoupled)
    #define AZSEG(a) ((a) == 1 ? loop1A : AZ2)
    for (int c = 1; c < NCN; c++) PL0[c] = (uint8_t)AZSEG(c);
    for (int c = 1; c < NCN; c++) { int m = PL0[c]; for (int a2 = 1; a2 < c; a2++) { int v = AZSEG(a2) + 1 + PL0[c - a2]; if (v < m) m = v; } PL1[c] = (uint8_t)m; }
    FILE *offf; snprintf(p, sizeof p, "%s/offsets.txt", out); offf = fopen(p, "w");
    Lay Lnext; Lnext.n = 0; Lnext.k = NULL; Lnext.z0 = Lnext.z1 = Lnext.p = NULL;
    long double tw = 0;
    for (int k = NPH; k >= 1; k--) {
        double t0 = omp_get_wtime(); Lay L; mklay(&L, k);
        #pragma omp parallel for schedule(dynamic, 64)
        for (uint64_t x = 0; x < L.n; x++) {
            int t = L.k[x] & 31; uint32_t S = urk(L.k[x] >> 5, k);
            int n0[NCN][NOR], n1[NCN][NOR], npp[NCN][NOR];
            for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) n0[c][i] = n1[c][i] = npp[c][i] = BIG;
            if (k < NPH) for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue;
                int g; uint64_t ck = canB(S | 1u << u, u, &g); int64_t id = fnd(&Lnext, ck); if (id < 0) { fprintf(stderr, "missing\n"); exit(12); }
                const uint8_t *h0 = Lnext.z0 + id * VSZ, *h1 = Lnext.z1 + id * VSZ, *hp = Lnext.p + id * VSZ; int a0[NCN][NOR], a1_[NCN][NOR], ap[NCN][NOR];
                for (int c = 0; c < NCN; c++) for (int j = 0; j < NOR; j++) { int jj = omapB[g][u][j]; a0[c][j] = h0[c * NOR + jj]; a1_[c][j] = h1[c * NOR + jj]; ap[c][j] = hp[c * NOR + jj]; }
                for (int c = 0; c < NCN; c++) for (int a = 0; a <= c; a++) { int cc = c - a;
                    for (int i = 0; i < NOR; i++) { const uint8_t *kr = Kred[a][t][u][i]; int m0 = n0[c][i], m1 = n1[c][i], mp = npp[c][i];
                        for (int j = 0; j < NOR; j++) { int kk = kr[j]; int w = kk + a0[cc][j]; if (w < m0) m0 = w; w = kk + a1_[cc][j]; if (w < m1) m1 = w; w = kk + ap[cc][j]; if (w < mp) mp = w; }
                        n0[c][i] = m0; n1[c][i] = m1; npp[c][i] = mp; } } }
            const uint8_t *pl0 = PL0 + (size_t)(FULL & ~S) * NCN, *pl1 = PL1 + (size_t)(FULL & ~S) * NCN;
            uint8_t *d0 = L.z0 + x * VSZ, *d1 = L.z1 + x * VSZ, *dp = L.p + x * VSZ; uint8_t s0[VSZ], s1[VSZ];   // s-variants: one-trail segments, not stored
            for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) {
                int full = (k == NPH);
                int z0 = full ? Qhred[c][t][i] : n0[c][i];
                int zs0 = full ? (c == 0 ? L1red[t][i] : Qhred[c][t][i]) : n0[c][i];
                int z1 = full ? Qhred[c][t][i] : n1[c][i], zs1 = zs0 < n1[c][i] ? zs0 : n1[c][i]; if (full) zs1 = zs0;
                int pp = npp[c][i];
                for (int a1 = 0; a1 <= c; a1++) { int rest = c - a1;
                    int j1 = Qhred[a1][t][i] + 1 + pl0[rest]; if (j1 < z1) z1 = j1;
                    int js = (a1 == 0 ? L1red[t][i] : Qhred[a1][t][i]) + 1 + pl0[rest]; if (js < zs1) zs1 = js;
                    int jp = Q0red[a1][t][i] + 1 + pl1[rest]; if (jp < pp) pp = jp; }
                d0[c * NOR + i] = z0 > BIG ? BIG : z0; d1[c * NOR + i] = z1 > BIG ? BIG : z1; dp[c * NOR + i] = pp > BIG ? BIG : pp;
                s0[c * NOR + i] = zs0 > BIG ? BIG : zs0; s1[c * NOR + i] = zs1 > BIG ? BIG : zs1; }
            // PL0 / PL1 for R' = (FULL \ S) + t, |R'| = 25 - k: a new segment starting at t (a2 = 0: hin + one-trail value;
            // a2 >= 1: free-start chain of a2 A trails into t, then the segment already has >= 2 trails).  Sizes 25 - k are
            // written here while this pass reads only sizes 24 - k.
            { int v0[NCN], v1[NCN];
              for (int c = 0; c < NCN; c++) { int m0 = BIG, m1 = BIG;
                  for (int i = 0; i < NOR; i++) { int hi = Fhred[0][t][i]; int w = hi + s0[c * NOR + i]; if (w < m0) m0 = w; w = hi + s1[c * NOR + i]; if (w < m1) m1 = w; }
                  for (int a = 1; a <= c; a++) for (int i = 0; i < NOR; i++) { int w = Fhred[a][t][i] + d0[(c - a) * NOR + i]; if (w < m0) m0 = w; w = Fhred[a][t][i] + d1[(c - a) * NOR + i]; if (w < m1) m1 = w; }
                  v0[c] = m0; v1[c] = m1; }
              uint32_t R = (FULL & ~S) | (1u << t);
              for (int g = 0; g < 6; g++) { uint32_t Rg = pmB(g, R); for (int c = 0; c < NCN; c++) { if (v0[c] < BIG) amin8(PL0 + (size_t)Rg * NCN + c, (uint8_t)v0[c]); if (v1[c] < BIG) amin8(PL1 + (size_t)Rg * NCN + c, (uint8_t)v1[c]); } } }
        }
        if (Lnext.k) lfree(&Lnext); Lnext = L;
        int o0, o1, op;
        snprintf(p, sizeof p, "%s/HZ0%02d.nib", out, k); o0 = write_nib(p, Lnext.z0, Lnext.n);
        snprintf(p, sizeof p, "%s/HZ1%02d.nib", out, k); o1 = write_nib(p, Lnext.z1, Lnext.n);
        snprintf(p, sizeof p, "%s/HP%02d.nib", out, k); op = write_nib(p, Lnext.p, Lnext.n);
        fprintf(offf, "%d %d %d %d\n", k, o0, o1, op); fflush(offf);
        // PL1: an A-only cycle segment first, then a junction, then the last segment over R
        { int sz = NPH - k + 1;
          #pragma omp parallel for schedule(dynamic, 65536)
          for (size_t R = 1; R < NU; R++) { if (__builtin_popcount((uint32_t)R) != sz) continue;
              for (int c = 1; c < NCN; c++) for (int a2 = 1; a2 <= c; a2++) { int v = AZSEG(a2) + 1 + PL0[R * NCN + c - a2]; if (v < PL1[R * NCN + c]) PL1[R * NCN + c] = (uint8_t)(v > BIG ? BIG : v); } } }
        fprintf(stderr, "backward layer %d: %llu canonical states, offsets %d %d %d, %.1fs\n", k, (unsigned long long)Lnext.n, o0, o1, op, omp_get_wtime() - t0); tw += omp_get_wtime() - t0;
    }
    fclose(offf);
    snprintf(p, sizeof p, "%s/PL0.bin", out); f = fopen(p, "wb"); fwrite(PL0, 1, NU * NCN, f); fclose(f);
    snprintf(p, sizeof p, "%s/PL1.bin", out); f = fopen(p, "wb"); fwrite(PL1, 1, NU * NCN, f); fclose(f);
    int best = 1000, bestA = 1000;
    for (uint64_t x = 0; x < Lnext.n; x++) { int t = Lnext.k[x] & 31; const uint8_t *v = Lnext.p + x * VSZ;
        for (int a = 0; a < NCN; a++) for (int i = 0; i < NOR; i++) { int w = Sred[a][t][i] + v[(6 - a) * NOR + i]; if (w < best) best = w; } }
    for (int a1 = 1; a1 <= 6; a1++) { int w = 0 + 1 + PL1[(size_t)FULL * NCN + 6 - a1]; if (w < bestA) bestA = w; }
    printf("{\"checker\": \"M2\", \"max_cycles\": 2, \"relaxed_min_G_P_has_phi\": %d, \"relaxed_min_G_P_A_only\": %d, \"relaxed_G_lower_bound\": %d, \"loop1A\": %d, \"AZ2\": %d, \"sec\": %.1f}\n",
           best, bestA, best < bestA ? best : bestA, loop1A, AZ2, (double)tw);
    snprintf(p, sizeof p, "%s/meta.bin", out); f = fopen(p, "wb");
    fwrite(phl, 4, NPH, f); fwrite(ptr, 4, 6 * NPH, f); fwrite(orep, 4, NPH * NOR, f); fwrite(oorb, 4, NPH * NOP, f); fwrite(omapB, 4, 6 * NPH * NOR, f); fclose(f);
    return 0;
}
