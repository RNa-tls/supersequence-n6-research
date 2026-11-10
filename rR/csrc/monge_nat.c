// Round S -- exhaustive check of the Monge four-point inequality for the run weights at every NATURAL link.
// w(x, y) = least s in 1..7 with last(x)[s..] = first(y)[..8-s]  (8 if none), last(x) = x_7 x_0 .. x_6.
// Monge (proved for arbitrary strings in rR/lean/Monge.lean):
//     w(b, u) <= min(w(a, u), w(b, y))   ==>   w(a, y) + w(b, u) <= w(a, u) + w(b, y).
// Here (b, u) runs over the 10080 natural links b = pred(u) of the 60 trail versions (c(u) = w(b, u) in {2, 3}) and
// a, y over all runs that can occur together with u in one route: the runs of the other trails (both versions) and the
// runs of u's own trail in u's version; a and y of the same trail must be of the same version.  (Runs of the two
// versions of one trail never occur together; 432 runs are common to both versions and would give weight 1.)
// Trivial cases a = b (the natural link itself), y = u, a = u, y = b and a = y are skipped.
// Output: number of triples (a, u, y) with the hypothesis, the largest excess  w(a,y) + c - w(a,u) - w(b,y)  (must be
// <= 0), the number of equalities; and for the triples where the hypothesis FAILS (c(u) = 3 and a -> u or b -> y is a
// link of weight 2, i.e. the wrap of a full chain) the largest excess.
// Detour lemma L1 of Round R is the special case "a, u, y in three different trails".
// usage: monge_nat DIR(runs.bin) OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: monge_nat DIR OUT.json\n"); return 1; }
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    int N = 0, vb[NTR][2]; for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { vb[t][v] = N; N += mrun[t][v]; }
    uint8_t (*first)[8] = malloc((size_t)8 * N), (*last)[8] = malloc((size_t)8 * N); int *pred = malloc(sizeof(int) * N), *tr = malloc(sizeof(int) * N), *ver = malloc(sizeof(int) * N);
    { int o = 0; for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int m = mrun[t][v], base = o;
        for (int k = 0; k < m; k++, o++) { memcpy(first[o], runp[t][v] + 8 * k, 8); last[o][0] = first[o][7]; for (int i = 1; i < 8; i++) last[o][i] = first[o][i - 1]; pred[o] = base + (k + m - 1) % m; tr[o] = t; ver[o] = v; } } }
    int8_t *W = malloc((size_t)N * N), *Wt = malloc((size_t)N * N);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int a = 0; a < N; a++) for (int b = 0; b < N; b++) { int8_t w = a == b ? 8 : (int8_t)wgt(last[a], first[b]); W[(size_t)a * N + b] = w; Wt[(size_t)b * N + a] = w; }
    // sanity inside consistent version pairs: no weight-1 link between distinct runs; weight-2 links = natural w2 links and wraps
    long n1 = 0, n2nat = 0, n2other = 0;
    for (int a = 0; a < N; a++) for (int b = 0; b < N; b++) { if (a == b || (tr[a] == tr[b] && ver[a] != ver[b])) continue; int w = W[(size_t)a * N + b]; if (w == 1) n1++; if (w == 2) { if (pred[b] == a) n2nat++; else n2other++; } }
    long hyp = 0, tight = 0; int worst = -100; long cuts2 = 0, cuts3 = 0;
    long fail_in = 0, fail_out = 0; int worst_in = -100, worst_out = -100;
    #pragma omp parallel for schedule(dynamic, 8) reduction(+:hyp, tight, cuts2, cuts3, fail_in, fail_out) reduction(max:worst, worst_in, worst_out)
    for (int u = 0; u < N; u++) { int b = pred[u]; int c = W[(size_t)b * N + u]; int tu = tr[u], vu = ver[u];
        if (c == 2) cuts2++; else if (c == 3) cuts3++; else { fprintf(stderr, "cut weight %d\n", c); exit(3); }
        const int8_t *col = Wt + (size_t)u * N;      // col[a] = w(a, u)
        const int8_t *row = W + (size_t)b * N;       // row[y] = w(b, y)
        // val[y] = c - w(b, y) if y is admissible and the hypothesis w(b, y) >= c holds, else -100
        int8_t *val = malloc(N), *valf = malloc(N); long ny = 0;
        int lo = vb[tu][1 - vu], hi = lo + mrun[tu][1 - vu];              // the other version of u's trail: excluded
        for (int y = 0; y < N; y++) { int ok = !(y >= lo && y < hi) && y != u && y != b; val[y] = (ok && row[y] >= c) ? (int8_t)(c - row[y]) : -100; valf[y] = (ok && row[y] < c) ? (int8_t)(c - row[y]) : -100; if (val[y] > -100) ny++; }
        for (int a = 0; a < N; a++) { if ((a >= lo && a < hi) || a == b || a == u) continue; int wau = col[a]; const int8_t *ra = W + (size_t)a * N;
            int ta = tr[a], lo2 = vb[ta][1 - ver[a]], hi2 = lo2 + mrun[ta][1 - ver[a]];   // the other version of a's trail: excluded for y
            if (wau >= c) {
                int mx = -100; long eq = 0, cntv = 0;
                // three ranges: [0, lo2), [hi2, N) ; a itself is skipped through the diagonal (W[a][a] = 8 -> excluded below)
                for (int part = 0; part < 2; part++) { int y0 = part ? hi2 : 0, y1 = part ? N : lo2; int m1 = -100; long e1 = 0, c1 = 0;
                    for (int y = y0; y < y1; y++) { int s = ra[y] + val[y]; m1 = s > m1 ? s : m1; e1 += (s == wau); c1 += (val[y] > -100); }
                    if (m1 > mx) mx = m1; eq += e1; cntv += c1; }
                // remove the diagonal term y = a (if a was counted): recompute exactly
                if (val[a] > -100) { cntv--; int s = ra[a] + val[a]; if (s == wau) eq--;
                    if (s == mx) { mx = -100; for (int part = 0; part < 2; part++) { int y0 = part ? hi2 : 0, y1 = part ? N : lo2; for (int y = y0; y < y1; y++) { if (y == a) continue; int s2 = ra[y] + val[y]; if (s2 > mx) mx = s2; } } } }
                hyp += cntv; tight += eq; if (cntv > 0 && mx - wau > worst) worst = mx - wau;
                // hypothesis fails on the out side: w(b, y) < c  (c = 3, b -> y is the wrap of b's chain)
                for (int part = 0; part < 2; part++) { int y0 = part ? hi2 : 0, y1 = part ? N : lo2;
                    for (int y = y0; y < y1; y++) { if (valf[y] <= -100 || y == a) continue; fail_out++; int d = ra[y] + valf[y] - wau; if (d > worst_out) worst_out = d; } }
            } else {      // w(a, u) < c(u): c = 3 and a -> u is the wrap into the chain start u
                for (int part = 0; part < 2; part++) { int y0 = part ? hi2 : 0, y1 = part ? N : lo2;
                    for (int y = y0; y < y1; y++) { if (y == a || y == u || y == b || (y >= lo && y < hi)) continue; fail_in++; int d = ra[y] + c - wau - row[y]; if (d > worst_in) worst_in = d; } }
            } }
        free(val); free(valf); }
    FILE *o = fopen(argv[2], "w");
    fprintf(o, "{\"runs\": %d, \"natural_links\": %d, \"cuts_c2\": %ld, \"cuts_c3\": %ld,\n \"weight1_links_between_distinct_runs_same_version_vector\": %ld, \"weight2_natural_links\": %ld, \"weight2_other_links_wraps\": %ld,\n"
               " \"triples_with_hypothesis\": %ld, \"max_excess\": %d, \"equalities\": %ld,\n"
               " \"hypothesis_fails_wrap_into_u\": %ld, \"max_excess_wrap_into_u\": %d, \"hypothesis_fails_wrap_out_of_b\": %ld, \"max_excess_wrap_out_of_b\": %d,\n"
               " \"monge_holds_at_all_natural_links\": %s}\n",
            N, N, cuts2, cuts3, n1, n2nat, n2other, hyp, worst, tight, fail_in, worst_in, fail_out, worst_out, (worst <= 0 && n1 == 0) ? "true" : "false");
    fclose(o);
    printf("hyp %ld worst %d tight %ld | fails: wrap-in %ld (max excess %d) wrap-out %ld (max excess %d) | w1 %ld w2nat %ld w2other %ld\n", hyp, worst, tight, fail_in, worst_in, fail_out, worst_out, n1, n2nat, n2other);
    return worst > 0;
}
