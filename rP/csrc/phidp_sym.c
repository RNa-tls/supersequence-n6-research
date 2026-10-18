// Round P -- exact-A-count DP over subsets of the 24 phi trails, symmetry reduced.
// Relaxation (valid lower bound of F for every single-opening word):
//   phi options exact; between consecutive phi trails a chain of a A trails (a = 0, 1, 2 exact over all
//   choices of distinct A trails and their options; a >= 3 lower-bounded by PRE+SUF); the total number of A
//   uses is exactly 6 (tracked); the identity of the A used in different gaps is not tracked.
// State: canonical (mask, last trail t) under the 6 trail-level symmetries; vector D[c][i] (c = A uses so
// far 0..6, i = kappa-orbit of t's option, 42 orbits).  Value = min prefix cost (uint8, saturating).
// usage: phidp_sym DIR
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#include <immintrin.h>
#define NP 24
#define NR 42
#define NC 7
#define RS 48             // row stride (42 used)
#define VS (NC * RS)      // vector stride
#define CAP 200
static uint64_t binom[NP + 1][NP + 2];
static uint8_t R[4][NP][NP][NR][RS];
static uint8_t stv[4][NP][NR], env[4][NP][NR];
static int tg[6][NP]; static int omap[6][NP][NR];
static uint32_t ptab[6][3][256];
static void *rd(const char *p, size_t *n) { FILE *f = fopen(p, "rb"); if (!f) { perror(p); exit(1); } fseek(f, 0, SEEK_END); size_t s = ftell(f); fseek(f, 0, SEEK_SET); void *b = malloc(s); if (fread(b, 1, s, f) != s) exit(2); fclose(f); *n = s; return b; }
static inline uint64_t rank_mask(uint32_t m) { uint64_t r = 0; int i = 0; while (m) { int b = __builtin_ctz(m); r += binom[b][i + 1]; i++; m &= m - 1; } return r; }
static uint32_t unrank(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 <= NP - 1 && binom[b + 1][i] <= r) b++; r -= binom[b][i]; m |= 1u << b; } return m; }
static inline uint32_t pmask(int g, uint32_t m) { return ptab[g][0][m & 255] | ptab[g][1][(m >> 8) & 255] | ptab[g][2][(m >> 16) & 255]; }
static inline uint64_t key_of(uint32_t m, int t) { return (rank_mask(m) << 5) | (uint64_t)t; }
// canonical key of (m, t) and the group element achieving it
static inline uint64_t canon(uint32_t m, int t, int *gout) {
    uint64_t best = ~0ull; int bg = 0;
    for (int g = 0; g < 6; g++) { uint64_t k = key_of(pmask(g, m), tg[g][t]); if (k < best) { best = k; bg = g; } }
    *gout = bg; return best;
}
typedef struct { uint64_t *keys; uint8_t *vec; uint64_t n; } Layer;
static int64_t find(const Layer *L, uint64_t key) { int64_t lo = 0, hi = (int64_t)L->n - 1; while (lo <= hi) { int64_t mid = (lo + hi) >> 1; if (L->keys[mid] < key) lo = mid + 1; else if (L->keys[mid] > key) hi = mid - 1; else return mid; } return -1; }
static int cmpu64(const void *a, const void *b) { uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b; return x < y ? -1 : x > y; }
static void build_keys(Layer *L, int k) {
    uint64_t cm = binom[NP][k]; uint64_t cap = cm * k / 2 + 64; L->keys = malloc(sizeof(uint64_t) * cap); L->n = 0;
    #pragma omp parallel
    {
        uint64_t *loc = malloc(sizeof(uint64_t) * cap); uint64_t nl = 0;
        #pragma omp for schedule(static)
        for (uint64_t r = 0; r < cm; r++) { uint32_t m = unrank(r, k);
            for (uint32_t mt = m; mt; mt &= mt - 1) { int t = __builtin_ctz(mt); int g; uint64_t c = canon(m, t, &g); if (c == key_of(m, t)) loc[nl++] = c; } }
        #pragma omp critical
        { if (L->n + nl > cap) { fprintf(stderr, "key overflow\n"); exit(7); } memcpy(L->keys + L->n, loc, nl * sizeof(uint64_t)); L->n += nl; }
        free(loc);
    }
    qsort(L->keys, L->n, sizeof(uint64_t), cmpu64);
    L->vec = aligned_alloc(64, ((L->n * VS + 64 + 63) / 64) * 64);
}
int main(int argc, char **argv) {
    const char *dir = argv[1]; char p[1024]; size_t s; int kdump = argc > 2 ? atoi(argv[2]) : 0;
    for (int n = 0; n <= NP; n++) for (int k = 0; k <= NP + 1; k++) binom[n][k] = (k == 0) ? 1 : (n == 0 ? 0 : binom[n - 1][k - 1] + binom[n - 1][k]);
    snprintf(p, sizeof p, "%s/R.bin", dir); uint8_t *Rb = rd(p, &s);
    memset(R, CAP, sizeof R);
    for (int a = 0; a < 4; a++) for (int t = 0; t < NP; t++) for (int u = 0; u < NP; u++) for (int i = 0; i < NR; i++) for (int j = 0; j < NR; j++) {
        int v = Rb[((((size_t)a * NP + t) * NP + u) * NR + i) * NR + j]; R[a][t][u][i][j] = v > CAP ? CAP : v; }
    snprintf(p, sizeof p, "%s/stv.bin", dir); uint8_t *sb = rd(p, &s); memcpy(stv, sb, sizeof stv);
    snprintf(p, sizeof p, "%s/env.bin", dir); uint8_t *eb = rd(p, &s); memcpy(env, eb, sizeof env);
    snprintf(p, sizeof p, "%s/tg6.bin", dir); int32_t *tb = rd(p, &s); for (int g = 0; g < 6; g++) for (int t = 0; t < NP; t++) tg[g][t] = tb[g * NP + t];
    snprintf(p, sizeof p, "%s/omap.bin", dir); int32_t *ob = rd(p, &s); for (int g = 0; g < 6; g++) for (int t = 0; t < NP; t++) for (int i = 0; i < NR; i++) omap[g][t][i] = ob[(g * NP + t) * NR + i];
    for (int g = 0; g < 6; g++) for (int b = 0; b < 3; b++) for (int v = 0; v < 256; v++) { uint32_t m = 0; for (int q = 0; q < 8; q++) if (v >> q & 1) m |= 1u << tg[g][b * 8 + q]; ptab[g][b][v] = m; }
    // layer 1
    Layer L; build_keys(&L, 1); memset(L.vec, CAP, L.n * VS);
    for (uint64_t x = 0; x < L.n; x++) { int t = L.keys[x] & 31; uint8_t *v = L.vec + x * VS;
        for (int c = 0; c < NC; c++) for (int i = 0; i < NR; i++) v[c * RS + i] = stv[c < 3 ? c : 3][t][i]; }
    fprintf(stderr, "layer 1: %llu canonical states\n", (unsigned long long)L.n);
    if (kdump < 0) { snprintf(p, sizeof p, "%s/layers/k01_keys.bin", dir); FILE *f = fopen(p, "wb"); fwrite(L.keys, 8, L.n, f); fclose(f);
        snprintf(p, sizeof p, "%s/layers/k01_vec.bin", dir); f = fopen(p, "wb"); fwrite(L.vec, VS, L.n, f); fclose(f); }
    for (int k = 1; k < NP; k++) {
        double t0 = omp_get_wtime();
        Layer Ln; build_keys(&Ln, k + 1);
        #pragma omp parallel for schedule(dynamic, 64)
        for (uint64_t x = 0; x < Ln.n; x++) {
            uint64_t key = Ln.keys[x]; int u = key & 31; uint32_t M2 = unrank(key >> 5, k + 1); uint32_t M = M2 & ~(1u << u);
            __m256i acc[NC][2]; for (int c = 0; c < NC; c++) { acc[c][0] = _mm256_set1_epi8((char)CAP); acc[c][1] = acc[c][0]; }
            uint8_t src[VS] __attribute__((aligned(32)));
            for (uint32_t mt = M; mt; mt &= mt - 1) {
                int t = __builtin_ctz(mt); int g; uint64_t ck = canon(M, t, &g); int64_t idx = find(&L, ck);
                if (idx < 0) { fprintf(stderr, "missing state\n"); exit(5); }
                const uint8_t *cv = L.vec + idx * VS;
                for (int c = 0; c < NC; c++) for (int i = 0; i < NR; i++) src[c * RS + i] = cv[c * RS + omap[g][t][i]];
                __m256i best3[NC][2]; for (int c = 0; c < NC; c++) { best3[c][0] = _mm256_set1_epi8((char)CAP); best3[c][1] = best3[c][0]; }
                for (int i = 0; i < NR; i++) {
                    const uint8_t *r0 = R[0][t][u][i], *r1 = R[1][t][u][i], *r2 = R[2][t][u][i], *r3 = R[3][t][u][i];
                    __m256i a0l = _mm256_loadu_si256((const __m256i *)r0), a0h = _mm256_loadu_si256((const __m256i *)(r0 + 16));
                    __m256i a1l = _mm256_loadu_si256((const __m256i *)r1), a1h = _mm256_loadu_si256((const __m256i *)(r1 + 16));
                    __m256i a2l = _mm256_loadu_si256((const __m256i *)r2), a2h = _mm256_loadu_si256((const __m256i *)(r2 + 16));
                    __m256i a3l = _mm256_loadu_si256((const __m256i *)r3), a3h = _mm256_loadu_si256((const __m256i *)(r3 + 16));
                    for (int c = 0; c < NC; c++) {
                        uint8_t v = src[c * RS + i]; if (v >= CAP) continue;
                        __m256i vv = _mm256_set1_epi8((char)v);
                        acc[c][0] = _mm256_min_epu8(acc[c][0], _mm256_adds_epu8(vv, a0l)); acc[c][1] = _mm256_min_epu8(acc[c][1], _mm256_adds_epu8(vv, a0h));
                        if (c + 1 < NC) { acc[c + 1][0] = _mm256_min_epu8(acc[c + 1][0], _mm256_adds_epu8(vv, a1l)); acc[c + 1][1] = _mm256_min_epu8(acc[c + 1][1], _mm256_adds_epu8(vv, a1h)); }
                        if (c + 2 < NC) { acc[c + 2][0] = _mm256_min_epu8(acc[c + 2][0], _mm256_adds_epu8(vv, a2l)); acc[c + 2][1] = _mm256_min_epu8(acc[c + 2][1], _mm256_adds_epu8(vv, a2h)); }
                        if (c + 3 < NC) { best3[c][0] = _mm256_min_epu8(best3[c][0], _mm256_adds_epu8(vv, a3l)); best3[c][1] = _mm256_min_epu8(best3[c][1], _mm256_adds_epu8(vv, a3h)); }
                    }
                }
                // chains of >= 3 A's from count c reach any count c' >= c + 3
                __m256i run0 = _mm256_set1_epi8((char)CAP), run1 = run0;
                for (int c2 = 3; c2 < NC; c2++) { run0 = _mm256_min_epu8(run0, best3[c2 - 3][0]); run1 = _mm256_min_epu8(run1, best3[c2 - 3][1]);
                    acc[c2][0] = _mm256_min_epu8(acc[c2][0], run0); acc[c2][1] = _mm256_min_epu8(acc[c2][1], run1); }
            }
            uint8_t *dst = Ln.vec + x * VS;
            for (int c = 0; c < NC; c++) {
                uint8_t tmp[64] __attribute__((aligned(32)));
                _mm256_storeu_si256((__m256i *)tmp, acc[c][0]); _mm256_storeu_si256((__m256i *)(tmp + 16), acc[c][1]);
                for (int i = 0; i < NR; i++) dst[c * RS + i] = tmp[i] > CAP ? CAP : tmp[i];
                for (int i = NR; i < RS; i++) dst[c * RS + i] = CAP;
            }
        }
        free(L.keys); free(L.vec); L = Ln;
        // layer minimum (diagnostic)
        int mn = 255; for (uint64_t x = 0; x < L.n; x++) for (int c = 0; c < NC; c++) for (int i = 0; i < NR; i++) { int v = L.vec[x * VS + c * RS + i]; if (v < mn) mn = v; }
        fprintf(stderr, "layer %d: %llu canonical states, min %d, %.1fs\n", k + 1, (unsigned long long)L.n, mn, omp_get_wtime() - t0);
        if (kdump < 0) { snprintf(p, sizeof p, "%s/layers/k%02d_keys.bin", dir, k + 1); FILE *f = fopen(p, "wb"); fwrite(L.keys, 8, L.n, f); fclose(f);
            snprintf(p, sizeof p, "%s/layers/k%02d_vec.bin", dir, k + 1); f = fopen(p, "wb"); fwrite(L.vec, VS, L.n, f); fclose(f); }
        if (kdump == k + 1) { snprintf(p, sizeof p, "%s/dump_keys.bin", dir); FILE *f = fopen(p, "wb"); fwrite(L.keys, 8, L.n, f); fclose(f);
            snprintf(p, sizeof p, "%s/dump_vec.bin", dir); f = fopen(p, "wb"); fwrite(L.vec, VS, L.n, f); fclose(f); fprintf(stderr, "dumped layer %d\n", k + 1); return 0; }
    }
    int best = 1000, bu = -1, bc = -1, bj = -1; int hist[256] = {0};
    for (uint64_t x = 0; x < L.n; x++) { int u = L.keys[x] & 31;
        for (int c = 0; c < NC; c++) { int a = 6 - c; int ty = a < 3 ? a : 3;
            for (int j = 0; j < NR; j++) { int v = L.vec[x * VS + c * RS + j] + env[ty][u][j]; if (v < 256) hist[v]++; if (v < best) { best = v; bu = u; bc = c; bj = j; } } } }
    printf("{\"bound\": %d, \"last_trail_idx\": %d, \"A_before_end\": %d, \"orbit\": %d}\n", best, bu, bc, bj);
    fprintf(stderr, "final value histogram:"); for (int v = 0; v < 40; v++) if (hist[v]) fprintf(stderr, " %d:%d", v, hist[v]); fprintf(stderr, "\n");
    return 0;
}
