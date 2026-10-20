// Round Q, section 13 -- consistency check of the junction table HT (ckT.c) by a different computation path.
// Because the junction decouples the two parts, the relaxed root of HT must equal
//     min over U (phi set of the part before the junction), c1:  PL[U][c1] + PLf[ALL \ U][6 - c1]
// (PL = relaxed path over exactly U with word start and end chain, computed here from the layers H of ckB.c;
//  PLf = free-start table written by ckT.c), and for the junction inside the start chain (U empty) the second
//  term alone (first part A-only, cost >= 0).  Also checks PLf against an own recomputation from H.
// usage: ht_consistency CKBDIR(runs.bin, group.bin) HDIR HTDIR(PLf.bin, HT layers) OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <omp.h>
#define NTR 30
#define NPH 24
#define NOP 84
#define NOR 42
#define NCN 7
#define BIG 200
#define VSZ (NCN * NOR)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA, phl[NPH], nph; static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static uint64_t bn[25][26];
static uint32_t urk(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 < NPH && bn[b + 1][i] <= r) b++; r -= bn[b][i]; m |= 1u << b; } return m; }
static int ptr[6][NPH], orep[NPH][NOR];
static void *mapf(const char *p, size_t *sz) { int fd = open(p, O_RDONLY); if (fd < 0) { fprintf(stderr, "open %s\n", p); exit(2); } struct stat st; fstat(fd, &st); *sz = st.st_size; void *m = mmap(NULL, st.st_size ? st.st_size : 1, PROT_READ, MAP_SHARED, fd, 0); close(fd); return m; }
static inline void amin8(uint8_t *p, uint8_t v) { uint8_t old = __atomic_load_n(p, __ATOMIC_RELAXED); while (v < old && !__atomic_compare_exchange_n(p, &old, v, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {} }
static inline uint32_t pm(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *hdir = argv[2], *tdir = argv[3], *outp = argv[4]; char p[2048]; double T0 = omp_get_wtime();
    for (int n = 0; n <= 24; n++) for (int k = 0; k <= 25; k++) bn[n][k] = k == 0 ? 1 : (n == 0 ? 0 : bn[n - 1][k - 1] + bn[n - 1][k]);
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v]; for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t;
        memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m); oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = nph = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; else phl[nph++] = t; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = otr[a] == otr[b] ? 99 : (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    { snprintf(p, sizeof p, "%s/meta.bin", hdir); size_t sz; int32_t *mt = mapf(p, &sz); const int32_t *q = mt;
      for (int i = 0; i < NPH; i++) if (q[i] != phl[i]) return 13; q += NPH;
      for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ptr[s][i] = q[s * NPH + i]; q += 6 * NPH;
      for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) orep[i][j] = q[i * NOR + j]; }
    // start chains into phi options (orbit reps): with [cut = 2] (Sw) and free (Fw); own A-chain DP, consecutive A trails distinct
    int NPO = NPH * NOP, NAO = tcnt[Alist[0]];
    static uint8_t Sw[NCN][NPH][NOR], Fw[NCN][NPH][NOR];
    for (int kind = 0; kind < 2; kind++) {
        uint8_t *cur = malloc(6 * NAO), *nx = malloc(6 * NAO); uint8_t *row = malloc(NPO);
        for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int oa = tofs[Alist[a]] + q; cur[a * NAO + q] = kind == 0 ? (ocut[oa] == 2) : 0; }
        for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { int ox = tofs[phl[t]] + orep[t][i]; Sw[0][t][i] = ocut[ox] == 2; Fw[0][t][i] = 0; }
        for (int len = 1; len <= 6; len++) {
            memset(row, BIG, NPO);
            #pragma omp parallel for schedule(dynamic, 64)
            for (int x = 0; x < NPO; x++) { int ox = tofs[phl[x / NOP]] + x % NOP, m = BIG;
                for (int z = 0; z < 6 * NAO; z++) { int v = cur[z]; if (v >= BIG) continue; int w = v + e[(size_t)(tofs[Alist[z / NAO]] + z % NAO) * NOPT + ox]; if (w < m) m = w; } row[x] = m; }
            for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { int v = row[t * NOP + orep[t][i]]; if (kind == 0) Sw[len][t][i] = v; else Fw[len][t][i] = v; }
            if (len == 6) break;
            memset(nx, BIG, 6 * NAO);
            #pragma omp parallel for schedule(dynamic, 1)
            for (int b = 0; b < 6; b++) for (int r = 0; r < NAO; r++) { int ob = tofs[Alist[b]] + r, m = BIG;
                for (int z = 0; z < 6 * NAO; z++) { if (z / NAO == b) continue; int v = cur[z]; if (v >= BIG) continue; int w = v + e[(size_t)(tofs[Alist[z / NAO]] + z % NAO) * NOPT + ob]; if (w < m) m = w; } nx[b * NAO + r] = m; }
            uint8_t *tt = cur; cur = nx; nx = tt; }
        free(cur); free(nx); free(row); }
    fprintf(stderr, "start chains %.1fs\n", omp_get_wtime() - T0);
    uint32_t FULL = (1u << NPH) - 1; size_t NU = (size_t)1 << NPH;
    uint8_t *PL = malloc(NU * NCN), *PF = malloc(NU * NCN); memset(PL, BIG, NU * NCN); memset(PF, BIG, NU * NCN);
    for (int k = 1; k <= NPH; k++) { size_t s1, s2; snprintf(p, sizeof p, "%s/H%02d.key", hdir, k); uint64_t *hk = mapf(p, &s1); snprintf(p, sizeof p, "%s/H%02d.val", hdir, k); uint8_t *hv0 = mapf(p, &s2); uint64_t hn = s1 / 8;
        #pragma omp parallel for schedule(dynamic, 4096)
        for (uint64_t x = 0; x < hn; x++) { uint64_t key = hk[x]; int t = key & 31; uint32_t S = urk(key >> 5, k); const uint8_t *hv = hv0 + x * VSZ; int vs[NCN], vf[NCN];
            for (int c = 0; c < NCN; c++) { int ms = BIG, mf = BIG; for (int a = 0; a <= c; a++) for (int i = 0; i < NOR; i++) { int h = hv[(c - a) * NOR + i]; int v1 = Sw[a][t][i] + h, v2 = Fw[a][t][i] + h; if (v1 < ms) ms = v1; if (v2 < mf) mf = v2; } vs[c] = ms; vf[c] = mf; }
            uint32_t R = (FULL & ~S) | (1u << t);
            for (int g = 0; g < 6; g++) { uint32_t Rg = pm(g, R); for (int c = 0; c < NCN; c++) { if (vs[c] < BIG) amin8(PL + (size_t)Rg * NCN + c, (uint8_t)vs[c]); if (vf[c] < BIG) amin8(PF + (size_t)Rg * NCN + c, (uint8_t)vf[c]); } } }
        munmap(hk, s1); munmap(hv0, s2); fprintf(stderr, "layer %d %.1fs\n", k, omp_get_wtime() - T0); }
    PF[0] = BIG; for (int c = 1; c < NCN; c++) PF[c] = 0;
    // compare PF with ckT's PLf
    size_t szp; uint8_t *PLf; snprintf(p, sizeof p, "%s/PLf.bin", tdir); PLf = mapf(p, &szp); long diff = 0; if (szp != NU * NCN) return 9;
    for (size_t i = 0; i < NU * NCN; i++) if (PF[i] != PLf[i]) diff++;
    // decomposition minimum
    int best_after = BIG, best_start = BIG;
    #pragma omp parallel for reduction(min:best_after) schedule(dynamic, 65536)
    for (size_t U = 1; U < NU; U++) for (int c1 = 0; c1 < NCN; c1++) { int a = PL[U * NCN + c1], b = PLf[(size_t)(FULL & ~(uint32_t)U) * NCN + 6 - c1]; if (a < BIG && b < BIG && a + b < best_after) best_after = a + b; }
    for (int a1 = 1; a1 <= 6; a1++) { int b = PLf[(size_t)FULL * NCN + 6 - a1]; if (b < best_start) best_start = b; }
    FILE *fo = fopen(outp, "w");
    fprintf(fo, "{\"PLf_recomputed_mismatches\": %ld, \"decomposition_min_F_junction_after_phi\": %d, \"decomposition_min_F_junction_in_start_chain\": %d, \"PL_full_by_A_count\": [%d, %d, %d, %d, %d, %d, %d], \"sec\": %.1f}\n",
            diff, best_after, best_start, PL[(size_t)FULL * NCN + 0], PL[(size_t)FULL * NCN + 1], PL[(size_t)FULL * NCN + 2], PL[(size_t)FULL * NCN + 3], PL[(size_t)FULL * NCN + 4], PL[(size_t)FULL * NCN + 5], PL[(size_t)FULL * NCN + 6], omp_get_wtime() - T0);
    fclose(fo); printf("PLf mismatches %ld, decomposition min after phi %d, in start chain %d\n", diff, best_after, best_start);
    return 0;
}
