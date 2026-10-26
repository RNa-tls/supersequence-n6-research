// Round R -- copy of rQ/csrc/dominance.c that also writes the effective slack table (env SLACK_OUT).
// Round Q -- dominance of extended single visits by single pieces, in every neighbour context.
// Trail-version T with runs r_0..r_{m-1}; D(x, y) = w(x, y) - 4 for an exit permutation x and an entry permutation y.
// A visit (y, x, kappa) inserted between the exit p of the previous trail and the entry q of the next one costs
//     D(p, first(r_y)) + kappa + D(last(r_x), q).
// Single pieces are (k, k-1, 3 - c_k).  The extended visit (y, x) is DOMINATED if for every p (exit of a run of any
// other trail, either version) and every q (entry of a run of any other trail) some single piece costs <= it; also in
// the start context (no p) and end context (no q).  With In_p[k] = D(p, first r_k), Out_q[k] = D(last r_k, q):
//     slack(y, x) = max_{p, q} [ min_k (In_p[k] + kap_k + Out_q[k-1]) - In_p[y] - Out_q[x] ],  dominated <=> kappa >= slack.
// Profiles are grouped (distinct In / Out vectors).  Input kappa table: m x m int8 (99 = > KMAX, -1 diagonal).
// usage: dominance DIR(runs.bin) TRAIL VERSION KAPPA.bin OFFSET(bytes) OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
typedef struct { int8_t *v; int n, m, cap; } Prof;
static uint64_t hv(const int8_t *a, int m) { uint64_t h = 1469598103934665603ull; for (int i = 0; i < m; i++) { h ^= (uint8_t)a[i]; h *= 1099511628211ull; } return h; }
static void addprof(Prof *P, uint64_t **ht, int *hcap, const int8_t *a) {
    uint64_t h = hv(a, P->m); int64_t c = *hcap; uint64_t *H = *ht; uint64_t i = h & (c - 1);
    while (H[i]) { int idx = (int)(H[i] >> 32) - 1; if ((uint32_t)H[i] == (uint32_t)h && !memcmp(P->v + (size_t)idx * P->m, a, P->m)) return; i = (i + 1) & (c - 1); }
    if (P->n == P->cap) { P->cap *= 2; P->v = realloc(P->v, (size_t)P->cap * P->m); }
    memcpy(P->v + (size_t)P->n * P->m, a, P->m); P->n++; H[i] = ((uint64_t)P->n << 32) | (uint32_t)h;
    if (2 * P->n > c) { int64_t nc = c * 4; uint64_t *NH = calloc(nc, 8);
        for (int64_t j = 0; j < c; j++) if (H[j]) { uint64_t k = (H[j] & 0xffffffffull) & (nc - 1); while (NH[k]) k = (k + 1) & (nc - 1); NH[k] = H[j]; }
        free(H); *ht = NH; *hcap = (int)nc; }
}
int main(int argc, char **argv) {
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); const char *kap_p = argv[4]; long off = atol(argv[5]); const char *outp = argv[6]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    int m = mrun[T0][V0]; int both = getenv("DOM_BOTH") && atoi(getenv("DOM_BOTH")); int m2 = both ? m + mrun[T0][1 - V0] : m;
    uint8_t (*first)[8] = malloc(8 * m2), (*last)[8] = malloc(8 * m2); int *cpred = malloc(4 * m2);
    for (int k = 0; k < m2; k++) { int vv = k < m ? V0 : 1 - V0, kk = k < m ? k : k - m, mm = mrun[T0][vv];
        memcpy(first[k], runp[T0][vv] + 8 * kk, 8); last[k][0] = first[k][7]; for (int i = 1; i < 8; i++) last[k][i] = first[k][i - 1];
        cpred[k] = (k < m ? 0 : m) + (kk + mm - 1) % mm; }   // index of the version predecessor run (exit of the single piece entering at k)
    int8_t *K = malloc((size_t)m * m);
    if (strcmp(kap_p, "-")) { f = fopen(kap_p, "rb"); fseek(f, off, SEEK_SET); if (fread(K, 1, (size_t)m * m, f) != (size_t)m * m) return 2; fclose(f); }
    else { memset(K, 99, (size_t)m * m); for (int k = 0; k < m; k++) { K[(size_t)k * m + k] = -1; K[(size_t)k * m + (k + m - 1) % m] = (int8_t)(3 - wgt(last[(k + m - 1) % m], first[k])); } }
    int *kap1 = malloc(4 * m2);   // single piece k: kappa(k, pred k) = 3 - c_k
    for (int k = 0; k < m2; k++) { int c = wgt(last[cpred[k]], first[k]); kap1[k] = 3 - c; if (k < m && K[(size_t)k * m + (k + m - 1) % m] != kap1[k]) { fprintf(stderr, "single piece kappa mismatch at %d: %d vs %d\n", k, K[(size_t)k * m + (k + m - 1) % m], kap1[k]); return 3; } }
    // neighbour profiles
    Prof In = {malloc(1024 * m2), 0, m2, 1024}, Out = {malloc(1024 * m2), 0, m2, 1024}; int hci = 4096, hco = 4096; uint64_t *hti = calloc(hci, 8), *hto = calloc(hco, 8);
    int8_t *a = malloc(m2); long nex = 0;
    for (int t = 0; t < NTR; t++) { if (t == T0) continue; for (int v = 0; v < 2; v++) for (int k = 0; k < mrun[t][v]; k++) {
        const uint8_t *fp = runp[t][v] + 8 * k; uint8_t lp[8]; lp[0] = fp[7]; for (int i = 1; i < 8; i++) lp[i] = fp[i - 1];
        for (int r = 0; r < m2; r++) a[r] = (int8_t)(wgt(lp, first[r]) - 4); addprof(&In, &hti, &hci, a);
        for (int r = 0; r < m2; r++) a[r] = (int8_t)(wgt(last[r], fp) - 4); addprof(&Out, &hto, &hco, a); nex++; } }
    fprintf(stderr, "trail %d v%d: m %d, neighbour runs %ld, distinct in-profiles %d, out-profiles %d\n", T0, V0, m, nex, In.n, Out.n);
    // A_P[x] = max_Q (min_k (P_k + kap_k + Q_{k-1}) - Q_x);  slack(y,x) = max_P (A_P[x] - P_y)
    int *slack = malloc(4 * (size_t)m * m); for (size_t i = 0; i < (size_t)m * m; i++) slack[i] = -1000;
    int *sstart = malloc(4 * m), *send = malloc(4 * m); for (int i = 0; i < m; i++) sstart[i] = send[i] = -1000;
    #pragma omp parallel
    { int *AP = malloc(4 * m); int *ls = malloc(4 * (size_t)m * m); for (size_t i = 0; i < (size_t)m * m; i++) ls[i] = -1000; int *v = malloc(4 * Out.n);
      #pragma omp for schedule(dynamic, 16)
      for (int pi = 0; pi < In.n; pi++) { const int8_t *P = In.v + (size_t)pi * m2;
          for (int qi = 0; qi < Out.n; qi++) { const int8_t *Q = Out.v + (size_t)qi * m2; int mn = 1000;
              for (int k = 0; k < m2; k++) { int c = P[k] + kap1[k] + Q[cpred[k]]; if (c < mn) mn = c; } v[qi] = mn; }
          for (int x = 0; x < m; x++) { int best = -1000; for (int qi = 0; qi < Out.n; qi++) { int c = v[qi] - Out.v[(size_t)qi * m2 + x]; if (c > best) best = c; } AP[x] = best; }
          for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int c = AP[x] - P[y]; if (c > ls[y * m + x]) ls[y * m + x] = c; } }
      #pragma omp critical
      for (size_t i = 0; i < (size_t)m * m; i++) if (ls[i] > slack[i]) slack[i] = ls[i];
      free(AP); free(ls); free(v); }
    // start context: cost kappa(y,x) + Q_x vs min_k kap_k + Q_{k-1};  end context: P_y + kappa vs min_k P_k + kap_k
    for (int qi = 0; qi < Out.n; qi++) { const int8_t *Q = Out.v + (size_t)qi * m2; int mn = 1000; for (int k = 0; k < m2; k++) { int c = kap1[k] + Q[cpred[k]]; if (c < mn) mn = c; }
        for (int x = 0; x < m; x++) if (mn - Q[x] > sstart[x]) sstart[x] = mn - Q[x]; }
    for (int pi = 0; pi < In.n; pi++) { const int8_t *P = In.v + (size_t)pi * m2; int mn = 1000; for (int k = 0; k < m2; k++) { int c = P[k] + kap1[k]; if (c < mn) mn = c; }
        for (int y = 0; y < m; y++) if (mn - P[y] > send[y]) send[y] = mn - P[y]; }
    // effective slack per (y, x): max(slack, start context, end context); a visit (y, x, kappa) is undominated iff kappa < it.
    // m x m int8, -100 on the diagonal and on single pieces (x = y - 1)
    if (getenv("SLACK_OUT")) { int8_t *E = malloc((size_t)m * m);
        for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int sl = slack[y * m + x]; if (sstart[x] > sl) sl = sstart[x]; if (send[y] > sl) sl = send[y];
            if (x == y || x == (y + m - 1) % m) sl = -100; if (sl > 120) sl = 120; if (sl < -100) sl = -100; E[(size_t)y * m + x] = (int8_t)sl; }
        FILE *fs = fopen(getenv("SLACK_OUT"), "wb"); fwrite(E, 1, (size_t)m * m, fs); fclose(fs); free(E); }
    // kappa-free report: slack over ALL (y, x) pairs that are not single pieces (dominated for any kappa >= slack)
    long shist[16] = {0}; int smax = -1000; int sbest_y = -1, sbest_x = -1;
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { if (x == y || x == (y + m - 1) % m) continue;
        int sl = slack[y * m + x]; if (sstart[x] > sl) sl = sstart[x]; if (send[y] > sl) sl = send[y];
        int b = sl < -5 ? 0 : (sl > 9 ? 15 : sl + 6); shist[b]++; if (sl > smax) { smax = sl; sbest_y = y; sbest_x = x; } }
    FILE *fo = fopen(outp, "w"); int next = 0, nund = 0, maxgain = -100; fprintf(fo, "{\"trail\": %d, \"version\": %d, \"runs\": %d, \"in_profiles\": %d, \"out_profiles\": %d, \"undominated\": [", T0, V0, m, In.n, Out.n);
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { if (x == y || x == (y + m - 1) % m) continue; int k = K[(size_t)y * m + x]; if (k < 0 || k == 99) continue; next++;
        int g = slack[y * m + x] - k; int gs = sstart[x] - k, ge = send[y] - k; int gm = g > gs ? g : gs; if (ge > gm) gm = ge;
        if (gm > maxgain) maxgain = gm;
        if (gm > 0) { fprintf(fo, "%s{\"y\": %d, \"x\": %d, \"kappa\": %d, \"gain_mid\": %d, \"gain_start\": %d, \"gain_end\": %d}", nund ? ", " : "", y, x, k, g, gs, ge); nund++; } }
    fprintf(fo, "], \"extended_checked\": %d, \"n_undominated\": %d, \"max_gain\": %d, \"max_slack_any_pair\": %d, \"argmax\": [%d, %d], \"slack_hist_from_minus6\": [", next, nund, maxgain, smax, sbest_y, sbest_x);
    for (int b = 0; b < 16; b++) fprintf(fo, "%s%ld", b ? ", " : "", shist[b]); fprintf(fo, "]}\n"); fclose(fo);
    printf("{\"trail\": %d, \"version\": %d, \"extended_checked\": %d, \"n_undominated\": %d, \"max_gain\": %d, \"max_slack_any_pair\": %d}\n", T0, V0, next, nund, maxgain, smax);
    return 0;
}
