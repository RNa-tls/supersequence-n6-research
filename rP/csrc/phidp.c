// Round P -- exact DP over subsets of the 24 phi trails (options exact); A trails enter only as
// priced connectors between consecutive phi trails (A identity and A count relaxed; each A use costs p).
// Lower bound:  F(pi) >= min_DP(p) - 6 p   for every single-opening word pi and every p >= 0.
// Values are scaled by 4 (p = P4/4) and stored as uint8 (saturating).
// usage: phidp DIR P4 [order_file]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#include <immintrin.h>
#define NP 24
#define NO 84
#define RW 96
static uint8_t *Kp;   // [NP*NO rows][NP*RW]: Kp[(t*NO+ot)*NP*RW + u*RW + ou]
static uint64_t binom[NP + 1][NP + 1];
static void *rd(const char *p, size_t *n) { FILE *f = fopen(p, "rb"); if (!f) { perror(p); exit(1); } fseek(f, 0, SEEK_END); size_t s = ftell(f); fseek(f, 0, SEEK_SET); void *b = malloc(s); if (fread(b, 1, s, f) != s) exit(2); fclose(f); *n = s; return b; }
static inline uint64_t rank_mask(uint32_t m) { uint64_t r = 0; int i = 0; while (m) { int b = __builtin_ctz(m); r += binom[b][i + 1]; i++; m &= m - 1; } return r; }
static inline int idx_in(uint32_t m, int t) { return __builtin_popcount(m & ((1u << t) - 1)); }
static uint32_t unrank(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 <= NP - 1 && binom[b + 1][i] <= r) b++; r -= binom[b][i]; m |= 1u << b; } return m; }
int main(int argc, char **argv) {
    const char *dir = argv[1]; int P4 = atoi(argv[2]); char p[1024]; size_t s;
    for (int n = 0; n <= NP; n++) { binom[n][0] = 1; for (int k = 1; k <= n; k++) binom[n][k] = binom[n - 1][k - 1] + (k <= n - 1 ? binom[n - 1][k] : 0); }
    int P = NP * NO;
    #define LOAD(nm, var) snprintf(p, sizeof p, "%s/" nm, dir); uint8_t *var = rd(p, &s);
    LOAD("Ed.bin", Ed) LOAD("K1.bin", K1) LOAD("K2.bin", K2) LOAD("PRE.bin", PRE) LOAD("SUF.bin", SUF)
    LOAD("S1.bin", S1) LOAD("S2.bin", S2) LOAD("S3.bin", S3) LOAD("Q1.bin", Q1)
    snprintf(p, sizeof p, "%s/cut.bin", dir); int32_t *cut = rd(p, &s);
    snprintf(p, sizeof p, "%s/trail.bin", dir); int32_t *trail = rd(p, &s);
    int N = s / 4; int *phi = malloc(sizeof(int) * P); int q = 0;
    for (int o = 0; o < N; o++) { int t = trail[o]; if (t == 1 || t == 8 || t == 15 || t == 22 || t == 28 || t == 29) continue; phi[q++] = o; }
    if (q != P) { fprintf(stderr, "phi count %d\n", q); return 1; }
    const int CAP = 250;
    Kp = aligned_alloc(64, (size_t)P * NP * RW);
    memset(Kp, CAP, (size_t)P * NP * RW);
    for (int y = 0; y < P; y++) for (int x = 0; x < P; x++) {
        int ty = y / NO, tx = x / NO; if (ty == tx) continue;
        int v = 4 * Ed[(size_t)y * P + x];
        int w = 4 * K1[(size_t)y * P + x] + P4; if (w < v) v = w;
        w = 4 * K2[(size_t)y * P + x] + 2 * P4; if (w < v) v = w;
        w = 4 * (PRE[y] + SUF[x]) + 3 * P4; if (w < v) v = w;
        if (v > CAP) v = CAP;
        Kp[(size_t)y * NP * RW + tx * RW + (x % NO)] = v; }
    // start / end vectors
    uint8_t st[NP * NO], en[NP * NO];
    for (int x = 0; x < P; x++) {
        int v = 4 * (cut[phi[x]] == 2), w;
        w = 4 * S1[x] + P4; if (w < v) v = w; w = 4 * S2[x] + 2 * P4; if (w < v) v = w; w = 4 * S3[x] + 3 * P4; if (w < v) v = w;
        st[x] = v > CAP ? CAP : v;
        v = 0; w = 4 * Q1[x] + P4; if (w < v) v = w; w = 4 * PRE[x] + 2 * P4; if (w < v) v = w;
        en[x] = v; }
    // optional fixed phi order (validation): evaluate the relaxation along it
    if (argc > 3) {
        FILE *f = fopen(argv[3], "r"); int ord[NP]; for (int i = 0; i < NP; i++) if (fscanf(f, "%d", &ord[i]) != 1) return 3; fclose(f);
        int D[NO], D2[NO]; for (int o = 0; o < NO; o++) D[o] = st[ord[0] * NO + o];
        for (int i = 1; i < NP; i++) { int a = ord[i - 1], b = ord[i];
            for (int o2 = 0; o2 < NO; o2++) { int m = 100000; for (int o = 0; o < NO; o++) { int v = D[o] + Kp[(size_t)(a * NO + o) * NP * RW + b * RW + o2]; if (v < m) m = v; } D2[o2] = m; }
            memcpy(D, D2, sizeof D); }
        int m = 100000; for (int o = 0; o < NO; o++) { int v = D[o] + en[ord[NP - 1] * NO + o]; if (v < m) m = v; }
        printf("{\"fixed_order_value4\": %d, \"bound_for_order\": %.4f}\n", m, m / 4.0 - 6.0 * P4 / 4.0); return 0; }
    uint8_t *L = NULL, *Ln = NULL;
    // layer 1
    uint64_t c1 = binom[NP][1];
    L = aligned_alloc(64, (size_t)c1 * 1 * RW); memset(L, CAP, (size_t)c1 * RW);
    for (int t = 0; t < NP; t++) { uint64_t r = rank_mask(1u << t); memcpy(L + r * RW, st + t * NO, NO); }
    for (int k = 1; k < NP; k++) {
        uint64_t cn = binom[NP][k + 1];
        Ln = aligned_alloc(64, (size_t)cn * (k + 1) * RW + 64);
        double t0 = omp_get_wtime();
        #pragma omp parallel for schedule(dynamic, 256)
        for (uint64_t r2 = 0; r2 < cn; r2++) {
            uint32_t M2 = unrank(r2, k + 1);
            int ju = 0;
            for (uint32_t mu = M2; mu; mu &= mu - 1, ju++) {
                int u = __builtin_ctz(mu); uint32_t M = M2 & ~(1u << u); uint64_t r = rank_mask(M);
                __m256i a0 = _mm256_set1_epi8((char)CAP), a1 = a0, a2 = a0;
                int jt = 0;
                for (uint32_t mt = M; mt; mt &= mt - 1, jt++) {
                    int t = __builtin_ctz(mt);
                    const uint8_t *src = L + (r * k + jt) * RW;
                    const uint8_t *kb = Kp + (size_t)(t * NO) * NP * RW + u * RW;
                    for (int ot = 0; ot < NO; ot++) {
                        uint8_t v = src[ot]; if (v >= CAP) continue;
                        __m256i vv = _mm256_set1_epi8((char)v);
                        const uint8_t *row = kb + (size_t)ot * NP * RW;
                        a0 = _mm256_min_epu8(a0, _mm256_adds_epu8(vv, _mm256_loadu_si256((const __m256i *)row)));
                        a1 = _mm256_min_epu8(a1, _mm256_adds_epu8(vv, _mm256_loadu_si256((const __m256i *)(row + 32))));
                        a2 = _mm256_min_epu8(a2, _mm256_adds_epu8(vv, _mm256_loadu_si256((const __m256i *)(row + 64))));
                    }
                }
                uint8_t *dst = Ln + (r2 * (k + 1) + ju) * RW;
                _mm256_storeu_si256((__m256i *)dst, a0); _mm256_storeu_si256((__m256i *)(dst + 32), a1); _mm256_storeu_si256((__m256i *)(dst + 64), a2);
                for (int o = NO; o < RW; o++) dst[o] = CAP;
                for (int o = 0; o < NO; o++) if (dst[o] > CAP) dst[o] = CAP;
            }
        }
        free(L); L = Ln;
        fprintf(stderr, "layer %d -> %d: %llu masks, %.1fs\n", k, k + 1, (unsigned long long)cn, omp_get_wtime() - t0);
    }
    // final
    uint32_t full = (1u << NP) - 1; uint64_t rf = rank_mask(full);
    int best = 100000, bt = -1, bo = -1;
    for (int j = 0; j < NP; j++) { int t = j; for (int o = 0; o < NO; o++) { int v = L[(rf * NP + j) * RW + o] + en[t * NO + o]; if (v < best) { best = v; bt = t; bo = o; } } }
    printf("{\"P4\": %d, \"p\": %.4f, \"dp_min4\": %d, \"bound\": %.4f, \"last_trail_idx\": %d, \"last_opt\": %d}\n", P4, P4 / 4.0, best, best / 4.0 - 6.0 * P4 / 4.0, bt, bo);
    return 0;
}
