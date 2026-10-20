// Round Q, section 3 -- exhaustive RELAXED lower bound for routes in which exactly one trail T is cut into two
// fragments (all other trails single pieces).  Virtual cover = path (phi set U, contains T(a)) + cycle (T(b) + the phi
// set B = complement of U [+ T itself if T is phi]).  With the relaxed (A-identity-free) backward table H of ckB.c:
//   path over U with c1 A uses  >=  PL(U, c1) = min_{t in U, a <= c1} S_a(t, o) + H((all \ U) + t, t, c1 - a)[o]
//   phi anchor T in U, cycle over B with c2 A uses  >=  min_o H(U, T, c2)[o]            (closing edge >= 0)
//       (B empty: cycle = T(b) + c2 >= 1 A trails, cost >= min_b K_{c2}(b-1 -> b))
//   A anchor alpha, cycle over B (nonempty) with c2 further A uses, i.e. c2 + 1 A copies in the cycle (alpha(b) included):
//       drop the closing edge into a phi q of B -> path from q's exit covering B - q with c2 + 1 A copies
//       >= CA(U, c2 + 1) = min_{q notin U} min_o H(U + q, q, c2 + 1)[o]
//       (B empty: cycle of A trails only, bounded by the exact A-only closed-walk minimum ACYC(k);
//        U empty: the path is A-only, cost >= 0)
//   G >= 1 + PL + cycle bound;  J = 77 + G.   c1 + c2 = 6 (phi anchor), c1 + c2 = 6 with c1 >= 1 (A anchor, alpha in both).
// usage: split_bound CKBDIR(runs.bin) HDIR OUT.json
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
static int NOPT, otr[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA, phl[NPH], nph; static uint8_t oen[16384][8], oex[16384][8];
static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static uint64_t bn[25][26];
static uint32_t urk(uint64_t r, int k) { uint32_t m = 0; for (int i = k; i >= 1; i--) { int b = i - 1; while (b + 1 < NPH && bn[b + 1][i] <= r) b++; r -= bn[b][i]; m |= 1u << b; } return m; }
static int ptr[6][NPH], orep[NPH][NOR], oorb[NPH][NOP];
static void *mapf(const char *p, size_t *sz) { int fd = open(p, O_RDONLY); if (fd < 0) { fprintf(stderr, "open %s\n", p); exit(2); } struct stat st; fstat(fd, &st); *sz = st.st_size; void *m = mmap(NULL, st.st_size ? st.st_size : 1, PROT_READ, MAP_SHARED, fd, 0); close(fd); return m; }
static inline void amin8(uint8_t *p, uint8_t v) { uint8_t old = __atomic_load_n(p, __ATOMIC_RELAXED); while (v < old && !__atomic_compare_exchange_n(p, &old, v, 0, __ATOMIC_RELAXED, __ATOMIC_RELAXED)) {} }
static inline uint32_t pm(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *hdir = argv[2], *outp = argv[3]; char p[2048]; double T0 = omp_get_wtime();
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
    // meta (orbit numbering and trail actions of the H layers)
    { snprintf(p, sizeof p, "%s/meta.bin", hdir); size_t sz; int32_t *mt = mapf(p, &sz); const int32_t *q = mt;
      for (int i = 0; i < NPH; i++) if (q[i] != phl[i]) return 13; q += NPH;
      for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ptr[s][i] = q[s * NPH + i]; q += 6 * NPH;
      for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) orep[i][j] = q[i * NOR + j]; q += NPH * NOR;
      for (int i = 0; i < NPH; i++) for (int j = 0; j < NOP; j++) oorb[i][j] = q[i * NOP + j]; }
    // chain tables (relaxed, consecutive A trails distinct): Kc[len][y][x], start Sc[len][x]
    int NPO = NPH * NOP, NAO = tcnt[Alist[0]];
    uint8_t *Kc = malloc((size_t)NCN * NPO * NPO); memset(Kc, BIG, (size_t)NCN * NPO * NPO); uint8_t *Sc = malloc(NCN * NPO); memset(Sc, BIG, NCN * NPO);
    for (int y = 0; y < NPO; y++) for (int x = 0; x < NPO; x++) { int oy = tofs[phl[y / NOP]] + y % NOP, ox = tofs[phl[x / NOP]] + x % NOP; if (otr[oy] != otr[ox]) Kc[(size_t)y * NPO + x] = e[(size_t)oy * NOPT + ox]; }
    for (int x = 0; x < NPO; x++) Sc[x] = ocut[tofs[phl[x / NOP]] + x % NOP] == 2;
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y <= NPO; y++) {
        uint8_t *cur = malloc(6 * NAO), *nx = malloc(6 * NAO); uint8_t *row = malloc(NPO);
        for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int oa = tofs[Alist[a]] + q; cur[a * NAO + q] = (y < NPO) ? e[(size_t)(tofs[phl[y / NOP]] + y % NOP) * NOPT + oa] : (ocut[oa] == 2); }
        for (int len = 1; len <= 6; len++) {
            memset(row, BIG, NPO);
            for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT;
                for (int x = 0; x < NPO; x++) { int w = v + er[tofs[phl[x / NOP]] + x % NOP]; if (w < row[x]) row[x] = w; } }
            if (y < NPO) memcpy(Kc + ((size_t)len * NPO + y) * NPO, row, NPO); else memcpy(Sc + len * NPO, row, NPO);
            if (len == 6) break;
            memset(nx, BIG, 6 * NAO);
            for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT;
                for (int b = 0; b < 6; b++) { if (b == a) continue; const int8_t *eb = er + tofs[Alist[b]]; uint8_t *nb = nx + b * NAO; for (int r = 0; r < NAO; r++) { int w = v + eb[r]; if (w < nb[r]) nb[r] = w; } } }
            uint8_t *tt = cur; cur = nx; nx = tt; }
        free(cur); free(nx); free(row); }
    fprintf(stderr, "chain tables %.1fs\n", omp_get_wtime() - T0);
    // Sred[a][t][i] (orbit rep), and phi self-cycles through A trails only: SelfA[c][t] = min_b Kc[c][b][b] (exit b-1 -> entry b)
    static uint8_t Sred[NCN][NPH][NOR]; static int SelfA[NCN][NPH];
    for (int a = 0; a < NCN; a++) for (int t = 0; t < NPH; t++) { for (int i = 0; i < NOR; i++) Sred[a][t][i] = Sc[a * NPO + t * NOP + orep[t][i]];
        int m = BIG; for (int q = 0; q < NOP; q++) { int y = t * NOP + q; int v = Kc[((size_t)a * NPO + y) * NPO + y]; if (a >= 1 && v < m) m = v; } SelfA[a][t] = m; }
    // A-only closed walks: ACYC[k] = min cost of a cycle of k >= 2 A copies (consecutive trails distinct), via DP from every A option
    int NAA = 6 * NAO; int ACYC[8]; for (int k = 0; k < 8; k++) ACYC[k] = BIG;
    { int *acyc_t = malloc(sizeof(int) * 8 * omp_get_max_threads()); for (int i = 0; i < 8 * omp_get_max_threads(); i++) acyc_t[i] = BIG;
      // cheap-edge lists (e <= 6) between A options of different trails
      int *off = malloc(4 * (NAA + 1)), *to = malloc(4 * (size_t)NAA * 2000); int8_t *wt = malloc((size_t)NAA * 2000); size_t ne = 0;
      for (int z = 0; z < NAA; z++) { off[z] = ne; int oz = tofs[Alist[z / NAO]] + z % NAO;
          for (int z2 = 0; z2 < NAA; z2++) { if (z2 / NAO == z / NAO) continue; int v = e[(size_t)oz * NOPT + tofs[Alist[z2 / NAO]] + z2 % NAO]; if (v <= 2 && ne < (size_t)NAA * 2000) { to[ne] = z2; wt[ne] = v; ne++; } } }
      off[NAA] = ne; fprintf(stderr, "A-A edges with e <= 2: %zu\n", ne);
      #pragma omp parallel
      { int tid = omp_get_thread_num(); int *d = malloc(4 * NAA), *d2 = malloc(4 * NAA);
        #pragma omp for schedule(dynamic, 64)
        for (int z = 0; z < NAA; z++) { for (int i = 0; i < NAA; i++) d[i] = BIG; d[z] = 0;
            for (int k = 1; k <= 7; k++) { for (int i = 0; i < NAA; i++) d2[i] = BIG;
                for (int u = 0; u < NAA; u++) { if (d[u] >= BIG) continue; for (size_t j = off[u]; j < (size_t)off[u + 1]; j++) { int v = d[u] + wt[j]; if (v < d2[to[j]]) d2[to[j]] = v; } }
                int *tt = d; d = d2; d2 = tt; if (k >= 2 && d[z] < acyc_t[tid * 8 + k]) acyc_t[tid * 8 + k] = d[z]; } }
        free(d); free(d2); }
      for (int i = 0; i < omp_get_max_threads(); i++) for (int k = 0; k < 8; k++) if (acyc_t[i * 8 + k] < ACYC[k]) ACYC[k] = acyc_t[i * 8 + k];
      // walks using an edge with e >= 3 cost >= 3: cap
      for (int k = 2; k < 8; k++) if (ACYC[k] > 3) ACYC[k] = 3;
      free(off); free(to); free(wt); free(acyc_t); }
    fprintf(stderr, "A-only cycle minima (k=2..7, capped at 3): %d %d %d %d %d %d\n", ACYC[2], ACYC[3], ACYC[4], ACYC[5], ACYC[6], ACYC[7]);
    free(Kc);
    // H layers
    uint64_t *Hk[NPH + 1]; uint8_t *Hv[NPH + 1]; uint64_t Hn[NPH + 1];
    for (int k = 1; k <= NPH; k++) { size_t s1, s2; snprintf(p, sizeof p, "%s/H%02d.key", hdir, k); Hk[k] = mapf(p, &s1); snprintf(p, sizeof p, "%s/H%02d.val", hdir, k); Hv[k] = mapf(p, &s2); Hn[k] = s1 / 8; }
    // pass 1: PL[U][c], CA[U][c] over all subsets U (all images of each canonical state)
    uint32_t FULL = (1u << NPH) - 1; size_t NU = (size_t)1 << NPH;
    uint8_t *PL = malloc(NU * NCN), *CA = malloc(NU * NCN); memset(PL, BIG, NU * NCN); memset(CA, BIG, NU * NCN);
    int bestPhi = BIG, bpU = -1, bpT = -1, bpc = -1; long nphi_le[40] = {0};
    for (int k = 1; k <= NPH; k++) {
        #pragma omp parallel for schedule(dynamic, 4096)
        for (uint64_t x = 0; x < Hn[k]; x++) {
            uint64_t key = Hk[k][x]; int t = key & 31; uint32_t S = urk(key >> 5, k); const uint8_t *hv = Hv[k] + x * VSZ;
            int vp[NCN], vc[NCN];
            for (int c = 0; c < NCN; c++) { int m = BIG; for (int a = 0; a <= c; a++) for (int i = 0; i < NOR; i++) { int v = Sred[a][t][i] + hv[(c - a) * NOR + i]; if (v < m) m = v; } vp[c] = m;
                int mc = BIG; for (int i = 0; i < NOR; i++) if (hv[c * NOR + i] < mc) mc = hv[c * NOR + i]; vc[c] = mc; }
            uint32_t Up = (FULL & ~S) | (1u << t), Uc = S & ~(1u << t);
            for (int g = 0; g < 6; g++) { uint32_t a1 = pm(g, Up), a2 = pm(g, Uc);
                for (int c = 0; c < NCN; c++) { if (vp[c] < BIG) amin8(PL + (size_t)a1 * NCN + c, (uint8_t)vp[c]); if (vc[c] < BIG) amin8(CA + (size_t)a2 * NCN + c, (uint8_t)vc[c]); } }
        }
        fprintf(stderr, "pass1 layer %d, %.1fs\n", k, omp_get_wtime() - T0);
    }
    // relaxed single-path values by A count (sanity: c = 6 gives the relaxed optimum 20)
    int PLfull[NCN]; for (int c = 0; c < NCN; c++) PLfull[c] = PL[(size_t)FULL * NCN + c];
    fprintf(stderr, "relaxed full path by A count: %d %d %d %d %d %d %d\n", PLfull[0], PLfull[1], PLfull[2], PLfull[3], PLfull[4], PLfull[5], PLfull[6]);
    // pass 2: phi anchors.  canonical state (U, T): G >= 1 + PL(U, c1) + min_o H(U, T, 6 - c1)[o]; B empty (U = FULL): + SelfA
    for (int k = 1; k <= NPH; k++) {
        int lb = BIG, lu = -1, lt = -1, lc = -1; long hl[40] = {0};
        #pragma omp parallel
        { int mb = BIG, mu = -1, mt = -1, mcc = -1; long h2[40] = {0};
          #pragma omp for schedule(dynamic, 4096)
          for (uint64_t x = 0; x < Hn[k]; x++) { uint64_t key = Hk[k][x]; int t = key & 31; uint32_t U = urk(key >> 5, k); const uint8_t *hv = Hv[k] + x * VSZ; int best = BIG, bc = -1;
              for (int c1 = 0; c1 < NCN; c1++) { int c2 = 6 - c1; int pl = PL[(size_t)U * NCN + c1]; if (pl >= BIG) continue; int cy;
                  if (U == FULL) { if (c2 < 1) continue; cy = SelfA[c2][t]; }
                  else { cy = BIG; for (int i = 0; i < NOR; i++) if (hv[c2 * NOR + i] < cy) cy = hv[c2 * NOR + i]; }
                  int G = 1 + pl + cy; if (G < best) { best = G; bc = c1; } }
              if (best < 40) h2[best]++; if (best < mb) { mb = best; mu = U; mt = t; mcc = bc; } }
          #pragma omp critical
          { if (mb < lb) { lb = mb; lu = mu; lt = mt; lc = mcc; } for (int g = 0; g < 40; g++) hl[g] += h2[g]; } }
        for (int g = 0; g < 40; g++) nphi_le[g] += hl[g];
        if (lb < bestPhi) { bestPhi = lb; bpU = lu; bpT = lt; bpc = lc; }
    }
    // pass 3: A anchors.  for every U: G >= 1 + min_{c1 >= 1} PL(U, c1) + (U != FULL ? CA(U, 7 - c1) : ACYC(7 - c1)), PL(empty, c1) := 0
    int bestA = BIG; uint32_t baU = 0; int bac = -1; long nA_le[40] = {0};
    #pragma omp parallel
    { int mb = BIG; uint32_t mu = 0; int mc = -1; long h2[40] = {0};
      #pragma omp for schedule(dynamic, 65536)
      for (size_t U = 0; U < NU; U++) { int best = BIG, bc = -1;
          for (int c1 = 1; c1 < NCN; c1++) { int pl = U ? PL[U * NCN + c1] : 0; if (pl >= BIG) continue; int c2 = 6 - c1; int cy;
              if (U == FULL) { if (c2 < 1) continue; cy = ACYC[c2 + 1]; } else cy = CA[U * NCN + c2 + 1];
              if (cy >= BIG) continue; int G = 1 + pl + cy; if (G < best) { best = G; bc = c1; } }
          if (best < 40) h2[best]++; if (best < mb) { mb = best; mu = (uint32_t)U; mc = bc; } }
      #pragma omp critical
      { if (mb < bestA) { bestA = mb; baU = mu; bac = mc; } for (int g = 0; g < 40; g++) nA_le[g] += h2[g]; } }
    FILE *fo = fopen(outp, "w");
    fprintf(fo, "{\"relaxed_full_path_by_A_count\": [%d, %d, %d, %d, %d, %d, %d], \"A_only_cycle_min_k2_7_capped3\": [%d, %d, %d, %d, %d, %d],\n", PLfull[0], PLfull[1], PLfull[2], PLfull[3], PLfull[4], PLfull[5], PLfull[6], ACYC[2], ACYC[3], ACYC[4], ACYC[5], ACYC[6], ACYC[7]);
    fprintf(fo, " \"phi_anchor\": {\"min_G\": %d, \"argmin_U_size\": %d, \"argmin_U\": %u, \"argmin_T_phi_index\": %d, \"argmin_c1\": %d, \"hist\": {", bestPhi, __builtin_popcount(bpU), bpU, bpT, bpc);
    int fz = 1; for (int g = 0; g < 40; g++) if (nphi_le[g]) { fprintf(fo, "%s\"%d\": %ld", fz ? "" : ", ", g, nphi_le[g]); fz = 0; } fprintf(fo, "}},\n");
    fprintf(fo, " \"A_anchor\": {\"min_G\": %d, \"argmin_U_size\": %d, \"argmin_U\": %u, \"argmin_c1\": %d, \"hist\": {", bestA, __builtin_popcount(baU), baU, bac);
    fz = 1; for (int g = 0; g < 40; g++) if (nA_le[g]) { fprintf(fo, "%s\"%d\": %ld", fz ? "" : ", ", g, nA_le[g]); fz = 0; } fprintf(fo, "}},\n \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    printf("{\"phi_anchor_min_G\": %d, \"A_anchor_min_G\": %d, \"relaxed_full_path_by_A_count\": [%d, %d, %d, %d, %d, %d, %d]}\n", bestPhi, bestA, PLfull[0], PLfull[1], PLfull[2], PLfull[3], PLfull[4], PLfull[5], PLfull[6]);
    return 0;
}
