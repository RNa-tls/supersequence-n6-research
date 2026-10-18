// Round P, checker B (independent of prep_conn.c, prep_chain.c, symprep.py, phidp_sym*.c).
// Recomputes from the raw runs (runs.bin) the options, overlap weights, excesses e, the A-chain tables,
// verifies the symmetry group on its own tables, and runs the BACKWARD relaxed DP
//   H(S, t, c)[o] = min cost of finishing the word after phi trail t (option o), visiting the phi trails
//                   outside S, with exactly c more A trails (identity of A trails in different gaps free,
//                   chains with consecutive A trails distinct), including the end chain.
// Canonical states: MAX key over the 6 trail symmetries; option orbits under kappa represented by the
// LARGER local index.  Layers are written to OUT/Hk%02d.{key,val}.  Prints the relaxed optimum
//   min_t,a,o  S_a[o] + H({t}, t, 6 - a)[o].
// usage: ckB DIR OUT
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
static int8_t *e;     // NOPT x NOPT
static int isA[NTR], Alist[6], nA = 0, phl[NPH], nph = 0, tofs[NTR], tcnt[NTR];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static uint64_t bn[25][26];
static inline uint64_t rk(uint32_t m) { uint64_t r = 0; int i = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) { i++; r += bn[b][i]; } return r; }
static uint32_t urk(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 < NPH && bn[b + 1][i] <= r) b++; r -= bn[b][i]; m |= 1u << b; } return m; }
static int G, gt[12][NTR]; static int32_t *gop;          // option permutations
static int sel[6]; static int ptr[6][NPH];               // 6 distinct trail actions on phi indices
static int kap[16384];
static int orep[NPH][NOR], oorb[NPH][NOP];             // local option indices
static int omapB[6][NPH][NOR];
static uint8_t Kred[NCN][NPH][NPH][NOR][NOR];
static uint8_t Qred[NCN][NPH][NOR], Sred[NCN][NPH][NOR];
static inline uint64_t keyof(uint32_t m, int t) { return (rk(m) << 5) | (uint64_t)t; }
static inline uint32_t pmB(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
static inline uint64_t canB(uint32_t m, int t, int *gg) { uint64_t best = 0; int bg = -1; for (int g = 0; g < 6; g++) { uint64_t k = keyof(pmB(g, m), ptr[g][t]); if (bg < 0 || k > best) { best = k; bg = g; } } *gg = bg; return best; }
typedef struct { uint64_t *k; uint8_t *v; uint64_t n; } Lay;
static int64_t fnd(const Lay *L, uint64_t key) { int64_t lo = 0, hi = (int64_t)L->n - 1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (L->k[mid] < key) lo = mid + 1; else if (L->k[mid] > key) hi = mid - 1; else return mid; } return -1; }
static int cmp(const void *a, const void *b) { uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b; return (x > y) - (x < y); }
#define VSZ (NCN * NOR)
static void mklay(Lay *L, int k) {
    uint64_t nm = bn[NPH][k]; uint64_t cap = nm * k / 2 + 100; L->k = malloc(8 * cap); L->n = 0;
    for (uint64_t r = 0; r < nm; r++) { uint32_t m = urk(r, k);
        for (int t = 0; t < NPH; t++) { if (!(m >> t & 1)) continue; int g; uint64_t c = canB(m, t, &g); if (c == keyof(m, t)) { if (L->n >= cap) { fprintf(stderr, "cap\n"); exit(3); } L->k[L->n++] = c; } } }
    qsort(L->k, L->n, 8, cmp); L->v = malloc(L->n * VSZ + 64);
}
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
    fprintf(stderr, "options %d, A trails %d, phi trails %d\n", NOPT, nA, nph);
    if (nA != 6 || nph != NPH) return 4;
    e = malloc((size_t)NOPT * NOPT);
    long neg = 0;
    #pragma omp parallel for reduction(+:neg) schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) {
        if (otr[a] == otr[b]) { e[(size_t)a * NOPT + b] = 99; continue; }
        int v = wgt(oex[a], oen[b]) - ocut[b] - 1; if (v < 0) neg++; e[(size_t)a * NOPT + b] = v; }
    fprintf(stderr, "excess matrix done, negative entries %ld\n", neg); if (neg) return 5;
    // optional mutation (tests): env CKB_MUT = file of lines "a b v" -> e(a, b) := v
    const char *mut = getenv("CKB_MUT"); int nmut = 0;
    if (mut && *mut) { FILE *mf = fopen(mut, "r"); int a, b, v; while (mf && fscanf(mf, "%d %d %d", &a, &b, &v) == 3) { e[(size_t)a * NOPT + b] = (int8_t)v; nmut++; } if (mf) fclose(mf);
        fprintf(stderr, "mutations applied: %d\n", nmut); }
    // group: read and verify on e and cut
    snprintf(p, sizeof p, "%s/group.bin", dir); f = fopen(p, "rb"); if (fread(&G, 4, 1, f) != 1) return 2;
    int32_t *tpb = malloc(4 * G * NTR); if (fread(tpb, 4, G * NTR, f) != (size_t)(G * NTR)) return 2;
    gop = malloc(4 * (size_t)G * NOPT); if (fread(gop, 4, (size_t)G * NOPT, f) != (size_t)G * NOPT) return 2; fclose(f);
    for (int g = 0; g < G; g++) for (int t = 0; t < NTR; t++) gt[g][t] = tpb[g * NTR + t];
    long bad = 0;
    for (int g = 0; g < G; g++) { int seen[NTR] = {0}; for (int t = 0; t < NTR; t++) { int u = gt[g][t]; if (u < 0 || u >= NTR || seen[u]++ || (mrun[u][0] > 100) != (mrun[t][0] > 100)) bad++; }
        char *so = calloc(NOPT, 1); for (int o = 0; o < NOPT; o++) { int o2 = gop[(size_t)g * NOPT + o]; if (o2 < 0 || o2 >= NOPT || so[o2]++) bad++; } free(so); }
    if (bad) { printf("{\"checker\": \"B\", \"error\": \"group elements not bijective\", \"violations\": %ld}\n", bad); return 6; }
    #pragma omp parallel for reduction(+:bad)
    for (int g = 0; g < G; g++) { const int32_t *P = gop + (size_t)g * NOPT;
        for (int a = 0; a < NOPT; a++) { if (otr[P[a]] != gt[g][otr[a]] || ocut[P[a]] != ocut[a]) bad++;
            for (int b = 0; b < NOPT; b++) if (e[(size_t)P[a] * NOPT + P[b]] != e[(size_t)a * NOPT + b]) bad++; } }
    fprintf(stderr, "group: %d elements, invariance violations %ld\n", G, bad); if (bad) { printf("{\"checker\": \"B\", \"error\": \"group invariance violated\", \"violations\": %ld}\n", bad); return 6; }
    int phidx[NTR]; for (int i = 0; i < NPH; i++) phidx[phl[i]] = i;
    int ns = 0; int ki = -1;
    for (int g = 0; g < G; g++) { int idt = 1; for (int t = 0; t < NTR; t++) if (gt[g][t] != t) idt = 0;
        int ido = 1; for (int o = 0; o < NOPT; o++) if (gop[(size_t)g * NOPT + o] != o) { ido = 0; break; }
        if (idt && !ido) ki = g;
        int dup = 0; for (int s = 0; s < ns; s++) { int same = 1; for (int t = 0; t < NTR; t++) if (gt[sel[s]][t] != gt[g][t]) same = 0; if (same) dup = 1; }
        if (!dup) sel[ns++] = g; }
    if (ns != 6 || ki < 0) { fprintf(stderr, "group structure %d %d\n", ns, ki); return 7; }
    for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ptr[s][i] = phidx[gt[sel[s]][phl[i]]];
    for (int o = 0; o < NOPT; o++) kap[o] = gop[(size_t)ki * NOPT + o];
    for (int i = 0; i < NPH; i++) { int t = phl[i], c = 0; for (int q = 0; q < NOP; q++) oorb[i][q] = -1;
        for (int q = 0; q < NOP; q++) { int o = tofs[t] + q, o2 = kap[o]; int q2 = o2 - tofs[t]; if (q2 < 0 || q2 >= NOP || q2 == q) return 8;
            if (oorb[i][q] >= 0) continue; int r = q > q2 ? q : q2; orep[i][c] = r; oorb[i][q] = c; oorb[i][q2] = c; c++; }
        if (c != NOR) return 9; }
    for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) {
        int o = tofs[phl[i]] + orep[i][j]; int o2 = gop[(size_t)sel[s] * NOPT + o]; int i2 = ptr[s][i]; omapB[s][i][j] = oorb[i2][o2 - tofs[phl[i2]]]; }
    // chain tables on phi options (local index y = i*84 + q), chains of a A trails, consecutive distinct
    int NPO = NPH * NOP; int NAO = tcnt[Alist[0]];
    uint8_t *Kc = malloc((size_t)NCN * NPO * NPO); memset(Kc, BIG, (size_t)NCN * NPO * NPO);
    uint8_t *Sc = malloc(NCN * NPO), *Qc = malloc(NCN * NPO); memset(Sc, BIG, NCN * NPO); memset(Qc, BIG, NCN * NPO);
    for (int y = 0; y < NPO; y++) for (int x = 0; x < NPO; x++) { int oy = tofs[phl[y / NOP]] + y % NOP, ox = tofs[phl[x / NOP]] + x % NOP; if (otr[oy] != otr[ox]) Kc[(size_t)y * NPO + x] = e[(size_t)oy * NOPT + ox]; }
    for (int x = 0; x < NPO; x++) { int ox = tofs[phl[x / NOP]] + x % NOP; Sc[x] = (ocut[ox] == 2); Qc[x] = 0; }
    // reach[y][A][o] : min cost from phi option y (or from the word start, y = NPO) through a chain ending at option o of A
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y <= NPO; y++) {
        uint8_t *cur = malloc(6 * NAO), *nx = malloc(6 * NAO);
        for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int oa = tofs[Alist[a]] + q;
            cur[a * NAO + q] = (y < NPO) ? e[(size_t)(tofs[phl[y / NOP]] + y % NOP) * NOPT + oa] : (ocut[oa] == 2); }
        for (int len = 1; len <= 6; len++) {
            uint8_t row[NPH * NOP]; memset(row, BIG, NPO); int qm = BIG;
            for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; if (v < qm) qm = v;
                const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT;
                for (int x = 0; x < NPO; x++) { int w = v + er[tofs[phl[x / NOP]] + x % NOP]; if (w < row[x]) row[x] = w; } }
            if (y < NPO) { memcpy(Kc + ((size_t)len * NPO + y) * NPO, row, NPO); Qc[len * NPO + y] = qm; }
            else memcpy(Sc + len * NPO, row, NPO);
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
    // verify group invariance of the chain tables (option permutations restricted to phi options)
    long badc = 0;
    for (int s = 0; s < 6; s++) { int g = sel[s];
        for (int len = 0; len < NCN; len++) for (int y = 0; y < NPO; y += 7) for (int x = 0; x < NPO; x++) {
            int oy = tofs[phl[y / NOP]] + y % NOP, ox = tofs[phl[x / NOP]] + x % NOP; if (otr[oy] == otr[ox]) continue;
            int gy = gop[(size_t)g * NOPT + oy], gx = gop[(size_t)g * NOPT + ox];
            int yy = phidx[otr[gy]] * NOP + (gy - tofs[otr[gy]]), xx = phidx[otr[gx]] * NOP + (gx - tofs[otr[gx]]);
            if (Kc[((size_t)len * NPO + yy) * NPO + xx] != Kc[((size_t)len * NPO + y) * NPO + x]) badc++; } }
    fprintf(stderr, "chain-table invariance violations (sampled rows) %ld\n", badc); if (badc) return 10;
    // reduced tables: Kred[a][t][u][i][j] = min over the kappa pair of the TARGET orbit j of K_a[rep_t(i)][.]
    for (int a = 0; a < NCN; a++) for (int t = 0; t < NPH; t++) for (int u = 0; u < NPH; u++) for (int i = 0; i < NOR; i++) for (int j = 0; j < NOR; j++) {
        if (t == u) { Kred[a][t][u][i][j] = BIG; continue; }
        int y = t * NOP + orep[t][i]; int x1 = u * NOP + orep[u][j]; int ox1 = tofs[phl[u]] + orep[u][j]; int ox2 = kap[ox1]; int x2 = u * NOP + (ox2 - tofs[phl[u]]);
        int v1 = Kc[((size_t)a * NPO + y) * NPO + x1], v2 = Kc[((size_t)a * NPO + y) * NPO + x2]; Kred[a][t][u][i][j] = v1 < v2 ? v1 : v2; }
    for (int a = 0; a < NCN; a++) for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { Qred[a][t][i] = Qc[a * NPO + t * NOP + orep[t][i]]; Sred[a][t][i] = Sc[a * NPO + t * NOP + orep[t][i]];
        int o2 = kap[tofs[phl[t]] + orep[t][i]] - tofs[phl[t]]; if (Qc[a * NPO + t * NOP + o2] != Qred[a][t][i] || Sc[a * NPO + t * NOP + o2] != Sred[a][t][i]) return 11; }
    free(Kc); free(e);
    // backward DP
    Lay Lnext; mklay(&Lnext, NPH);
    for (uint64_t x = 0; x < Lnext.n; x++) { int t = Lnext.k[x] & 31; uint8_t *v = Lnext.v + x * VSZ; for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) v[c * NOR + i] = Qred[c][t][i]; }
    snprintf(p, sizeof p, "%s/H%02d.key", out, NPH); f = fopen(p, "wb"); fwrite(Lnext.k, 8, Lnext.n, f); fclose(f);
    snprintf(p, sizeof p, "%s/H%02d.val", out, NPH); f = fopen(p, "wb"); fwrite(Lnext.v, VSZ, Lnext.n, f); fclose(f);
    for (int k = NPH - 1; k >= 1; k--) {
        double t0 = omp_get_wtime(); Lay L; mklay(&L, k);
        #pragma omp parallel for schedule(dynamic, 64)
        for (uint64_t x = 0; x < L.n; x++) {
            int t = L.k[x] & 31; uint32_t S = urk(L.k[x] >> 5, k);
            int acc[NCN][NOR]; for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) acc[c][i] = BIG;
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue;
                int g; uint64_t ck = canB(S | 1u << u, u, &g); int64_t id = fnd(&Lnext, ck); if (id < 0) { fprintf(stderr, "missing\n"); exit(12); }
                const uint8_t *hv = Lnext.v + id * VSZ; int hn[NCN][NOR];
                for (int c = 0; c < NCN; c++) for (int j = 0; j < NOR; j++) hn[c][j] = hv[c * NOR + omapB[g][u][j]];
                for (int c = 0; c < NCN; c++) for (int a = 0; a <= c; a++) { int cc = c - a;
                    for (int i = 0; i < NOR; i++) { const uint8_t *kr = Kred[a][t][u][i]; int m = acc[c][i];
                        for (int j = 0; j < NOR; j++) { int w = kr[j] + hn[cc][j]; if (w < m) m = w; } acc[c][i] = m; } } }
            uint8_t *dst = L.v + x * VSZ; for (int c = 0; c < NCN; c++) for (int i = 0; i < NOR; i++) dst[c * NOR + i] = acc[c][i] > BIG ? BIG : acc[c][i];
        }
        snprintf(p, sizeof p, "%s/H%02d.key", out, k); f = fopen(p, "wb"); fwrite(L.k, 8, L.n, f); fclose(f);
        snprintf(p, sizeof p, "%s/H%02d.val", out, k); f = fopen(p, "wb"); fwrite(L.v, VSZ, L.n, f); fclose(f);
        free(Lnext.k); free(Lnext.v); Lnext = L;
        fprintf(stderr, "backward layer %d: %llu canonical states, %.1fs\n", k, (unsigned long long)L.n, omp_get_wtime() - t0);
    }
    int best = 1000;
    for (uint64_t x = 0; x < Lnext.n; x++) { int t = Lnext.k[x] & 31; const uint8_t *v = Lnext.v + x * VSZ;
        for (int a = 0; a < NCN; a++) for (int i = 0; i < NOR; i++) { int w = Sred[a][t][i] + v[(6 - a) * NOR + i]; if (w < best) best = w; } }
    printf("{\"checker\": \"B\", \"relaxed_optimum\": %d}\n", best);
    // store small tables for the identity-aware search
    snprintf(p, sizeof p, "%s/meta.bin", out); f = fopen(p, "wb");
    fwrite(phl, 4, NPH, f); fwrite(ptr, 4, 6 * NPH, f); fwrite(orep, 4, NPH * NOR, f); fwrite(oorb, 4, NPH * NOP, f); fwrite(omapB, 4, 6 * NPH * NOR, f); fclose(f);
    return 0;
}
