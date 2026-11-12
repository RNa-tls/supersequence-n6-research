/* Round V -- paths of the public 16-trail selection that use gap arcs (the host of a detached chain C written as one
   piece N0 .. Q_end, the chain itself left out):  lower bounds for routes with one or two wraps.
     beta1(g)       = least J-part of a path through all 16 trails in which the host of g uses the gap arc g
     beta2(g1 > g2) = the same with both hosts on gap arcs, g1 before g2 in the path  (hosts different)
   A route that uses the wraps of C1, C2 with both detached chains unsplit and both gaps cut as the hosts' only cut has
       J = J(route without the two chains) + ins1 + ins2 >= beta2 + ins1 + ins2,   ins >= 0  (Monge).
   Method: base forward table (prefix values A_g[S]), base backward table (suffix values D_g[S]), and for every
   representative chain g1 a forward programme started at g1 (middle values into every g2); three-segment minimum over
   the partitions of the 14 other trails.
   Input: ARCS.txt (base run-level arcs), GAPS.txt ("chain host head7 tail7 cost" per line), REPS.txt (chain ids)
   usage: gap_pairs ARCS.txt GAPS.txt REPS.txt OUT_beta1.txt OUT_beta2.bin   (beta2: int8 [nrep][ngap], 100 = same host) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define T 16
#define MAXO 6000
#define MAXG 1000
#define INF 100
static int no, otr[MAXO], oco[MAXO], first[T + 1]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9], G;        /* keys = head prefixes */
static int tk2[8][MAXO], hk2[8][MAXO], nk2[8], koff2[9], G2;     /* keys = tail suffixes (for the backward table) */
static int ng, ghost[MAXG], gcost[MAXG], ghid[8][MAXG], gtid2[8][MAXG], gtidF[8][MAXG]; static char ghd[MAXG][8], gtl[MAXG][8];
static int *mapH[8], *mapT[8];
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
static int ovs(const char *tail, const char *head) { int k = 7; while (k > 0 && memcmp(tail + 7 - k, head, k)) k--; return k; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) { otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; }
    fclose(f); { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    f = fopen(argv[2], "r"); int ci; while (fscanf(f, "%d %d %15s %15s %d", &ci, &t, h, tl, &c) == 5) { ghost[ng] = t; gcost[ng] = c; memcpy(ghd[ng], h, 8); memcpy(gtl[ng], tl, 8); ng++; } fclose(f);
    int nrep = 0, rep[MAXG]; f = fopen(argv[3], "r"); while (fscanf(f, "%d", &rep[nrep]) == 1) nrep++; fclose(f);
    for (int k = 1; k <= 7; k++) {
        mapH[k] = malloc(sizeof(int) << (3 * k)); mapT[k] = malloc(sizeof(int) << (3 * k)); for (int i = 0; i < 1 << (3 * k); i++) mapH[k][i] = mapT[k][i] = -1; nk[k] = nk2[k] = 0;
        for (int o = 0; o < no; o++) { int cd = code(ohd[o], k); if (mapH[k][cd] < 0) mapH[k][cd] = nk[k]++; hid[k][o] = mapH[k][cd]; }
        for (int o = 0; o < no; o++) tid[k][o] = mapH[k][code(otl[o] + 7 - k, k)];
        for (int o = 0; o < no; o++) { int cd = code(otl[o] + 7 - k, k); if (mapT[k][cd] < 0) mapT[k][cd] = nk2[k]++; tk2[k][o] = mapT[k][cd]; }
        for (int o = 0; o < no; o++) hk2[k][o] = mapT[k][code(ohd[o], k)];
        for (int g = 0; g < ng; g++) { ghid[k][g] = mapT[k][code(ghd[g], k)];            /* head of g looked up among tail keys (prefix values) */
                                       gtid2[k][g] = mapH[k][code(gtl[g] + 7 - k, k)];   /* tail of g looked up among head keys (suffix values) */
                                       gtidF[k][g] = mapH[k][code(gtl[g] + 7 - k, k)]; }
    }
    koff[1] = 1; koff2[1] = 1; for (int k = 1; k <= 7; k++) { koff[k + 1] = koff[k] + nk[k]; koff2[k + 1] = koff2[k] + nk2[k]; } G = koff[8]; G2 = koff2[8];
    int NS = 1 << T; double t0 = omp_get_wtime();
    signed char *A = malloc((size_t)ng * NS), *D = malloc((size_t)ng * NS); memset(A, INF, (size_t)ng * NS); memset(D, INF, (size_t)ng * NS);
    /* ---- forward base table: F[S][o]; A_g[S] = least cost of a path through S followed by the join into g */
    { signed char *F = malloc((size_t)NS * no); memset(F, INF, (size_t)NS * no); signed char *gt = malloc(G), *g2 = malloc(G2);
      for (int o = 0; o < no; o++) F[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
      for (int g = 0; g < ng; g++) A[(size_t)g * NS] = 0;
      for (int S = 1; S < NS; S++) { const signed char *fs = F + (size_t)S * no; memset(gt, INF, G); memset(g2, INF, G2); int m = INF;
        for (int o = 0; o < no; o++) { int v = fs[o]; if (v >= INF) continue; if (v < m) m = v;
            for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0 && v < gt[koff[k] + id]) gt[koff[k] + id] = v; int id2 = tk2[k][o]; if (v < g2[koff2[k] + id2]) g2[koff2[k] + id2] = v; } }
        gt[0] = (signed char)m;
        for (int g = 0; g < ng; g++) { if (S >> ghost[g] & 1) continue; int best = m + 5; for (int k = 1; k <= 7; k++) { int id = ghid[k][g]; if (id >= 0) { int v = g2[koff2[k] + id] + 5 - k; if (v < best) best = v; } } A[(size_t)g * NS + S] = (signed char)best; }
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *fn = F + (size_t)(S | 1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int best = gt[0] + 5; for (int k = 1; k <= 7; k++) { int v = gt[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; } best += oco[o]; if (best < fn[o]) fn[o] = (signed char)best; } } }
      free(F); free(gt); free(g2); }
    /* ---- backward base table: B[S][o] = least cost of a path that starts with o and uses S; D_g[S] = join out of g + path through S */
    { signed char *B = malloc((size_t)NS * no); memset(B, INF, (size_t)NS * no); signed char *mh = malloc(G), *mt = malloc(G2);
      for (int o = 0; o < no; o++) B[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
      for (int g = 0; g < ng; g++) D[(size_t)g * NS] = 0;
      for (int S = 1; S < NS; S++) { const signed char *bs = B + (size_t)S * no; memset(mh, INF, G); int m = INF;
        for (int o = 0; o < no; o++) { int v = bs[o]; if (v >= INF) continue; if (v < m) m = v; for (int k = 1; k <= 7; k++) { int id = koff[k] + hid[k][o]; if (v < mh[id]) mh[id] = v; } }
        mh[0] = (signed char)m;
        for (int g = 0; g < ng; g++) { if (S >> ghost[g] & 1) continue; int best = m + 5; for (int k = 1; k <= 7; k++) { int id = gtid2[k][g]; if (id >= 0) { int v = mh[koff[k] + id] + 5 - k; if (v < best) best = v; } } D[(size_t)g * NS + S] = (signed char)best; }
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *bn = B + (size_t)(S | 1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int best = mh[0] + 5; for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0) { int v = mh[koff[k] + id] + 5 - k; if (v < best) best = v; } } best += oco[o]; if (best < bn[o]) bn[o] = (signed char)best; } } }
      free(B); free(mh); (void)mt; }
    fprintf(stderr, "base tables %.0fs\n", omp_get_wtime() - t0);
    /* ---- beta1 */
    FILE *fo = fopen(argv[4], "w"); int *beta1 = malloc(sizeof(int) * ng);
    for (int g = 0; g < ng; g++) { int rest = (NS - 1) & ~(1 << ghost[g]), best = INF; for (int S1 = rest;; S1 = (S1 - 1) & rest) { int v = A[(size_t)g * NS + S1] + gcost[g] + D[(size_t)g * NS + (rest ^ S1)]; if (v < best) best = v; if (!S1) break; }
        beta1[g] = best; fprintf(fo, "%d %d %d\n", g, ghost[g], best); }
    fclose(fo);
    /* ---- beta2: forward programme from each representative g1 */
    signed char *beta2 = malloc((size_t)nrep * ng); memset(beta2, INF, (size_t)nrep * ng);
    #pragma omp parallel
    {
        signed char *P = malloc((size_t)NS * no), *gt = malloc(G), *g2 = malloc(G2), *Cl = malloc((size_t)ng * NS), *X = malloc(NS);
        #pragma omp for schedule(dynamic, 1)
        for (int ri = 0; ri < nrep; ri++) { int g1 = rep[ri], t1 = ghost[g1], rest1 = (NS - 1) & ~(1 << t1);
            memset(P, INF, (size_t)NS * no); memset(Cl, INF, (size_t)ng * NS);
            for (int o = 0; o < no; o++) { if (otr[o] == t1) continue; P[(size_t)(1 << otr[o]) * no + o] = (signed char)(gcost[g1] + 5 - ovs(gtl[g1], ohd[o]) + oco[o]); }
            for (int g = 0; g < ng; g++) if (ghost[g] != t1) Cl[(size_t)g * NS] = (signed char)(gcost[g1] + 5 - ovs(gtl[g1], ghd[g]));
            for (int S = 1; S < NS; S++) { if (S >> t1 & 1) continue; const signed char *ps = P + (size_t)S * no; memset(gt, INF, G); memset(g2, INF, G2); int m = INF;
                for (int o = 0; o < no; o++) { int v = ps[o]; if (v >= INF) continue; if (v < m) m = v;
                    for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0 && v < gt[koff[k] + id]) gt[koff[k] + id] = v; int id2 = tk2[k][o]; if (v < g2[koff2[k] + id2]) g2[koff2[k] + id2] = v; } }
                gt[0] = (signed char)m;
                for (int g = 0; g < ng; g++) { if (ghost[g] == t1 || (S >> ghost[g] & 1)) continue; int best = m + 5; for (int k = 1; k <= 7; k++) { int id = ghid[k][g]; if (id >= 0) { int v = g2[koff2[k] + id] + 5 - k; if (v < best) best = v; } } Cl[(size_t)g * NS + S] = (signed char)best; }
                for (int tt = 0; tt < T; tt++) { if (tt == t1 || (S >> tt & 1)) continue; signed char *pn = P + (size_t)(S | 1 << tt) * no;
                    for (int o = first[tt]; o < first[tt + 1]; o++) { int best = gt[0] + 5; for (int k = 1; k <= 7; k++) { int v = gt[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; } best += oco[o]; if (best < pn[o]) pn[o] = (signed char)best; } } }
            for (int g = 0; g < ng; g++) { int t2 = ghost[g]; if (t2 == t1) continue; int O = rest1 & ~(1 << t2), best = INF; const signed char *Ag = A + (size_t)g1 * NS, *Cg = Cl + (size_t)g * NS, *Dg = D + (size_t)g * NS;
                /* X[Tm] = min over S1 subset of Tm of A_g1[S1] + Cl[g][Tm - S1] */
                for (int Tm = O;; Tm = (Tm - 1) & O) { int bx = INF; for (int S1 = Tm;; S1 = (S1 - 1) & Tm) { int v = Ag[S1] + Cg[Tm ^ S1]; if (v < bx) bx = v; if (!S1) break; }
                    int v = bx + gcost[g] + Dg[O ^ Tm]; if (v < best) best = v; if (!Tm) break; }
                beta2[(size_t)ri * ng + g] = (signed char)best; }
            fprintf(stderr, "rep %d/%d (chain %d) done %.0fs\n", ri + 1, nrep, g1, omp_get_wtime() - t0);
        }
        free(P); free(gt); free(g2); free(Cl); free(X);
    }
    fo = fopen(argv[5], "wb"); fwrite(beta2, 1, (size_t)nrep * ng, fo); fclose(fo);
    int h1[INF + 1] = {0}; for (int g = 0; g < ng; g++) h1[beta1[g]]++; printf("beta1 histogram:"); for (int v = 0; v <= INF; v++) if (h1[v]) printf(" %d:%d", v, h1[v]); printf("\n");
    long h2[INF + 1] = {0}; for (size_t i = 0; i < (size_t)nrep * ng; i++) h2[(int)beta2[i]]++; printf("beta2 (ordered, rep first) histogram:"); for (int v = 0; v <= INF; v++) if (h2[v]) printf(" %d:%ld", v, h2[v]); printf("\n");
    return 0;
}
