// Round Q, section 3 -- identity-aware forward search for the EXACT single-split reformulation (built on
// Round P checker B's search).  Every single split (one trail S cut into two pieces, all other trails single
// pieces) is a sequence SIGMA of all 30 trails, each exactly once with one option, plus a JUNCTION between two
// consecutive elements (the end of the virtual path P and the start of Z - S(b)):
//     G = 1 + F_J + beta,  F_J = [cut(first) = 2] + sum_{edges of SIGMA except the junction} e,  beta >= 0
// (beta = e(last -> S(b)) + e(S(b) -> element after the junction), S a trail before the junction).
// States (S, t, M, J): J = 1 iff the junction has occurred.  Prefix values g[o] are lower bounds exactly as in
// ckB_search (gaps of <= 2 A trails exact for their trails, >= 3 by the identity-free minimum).  Pruning:
//     J = 0: g + HT(S, t, 6 - |M|) <= THR       (HT from ckT.c: completions containing the junction)
//     J = 1: g + H (S, t, 6 - |M|) <= THR       (H from ckB.c)
// Junction transitions: end chain of the A set D1 after t (Q tables), then a FREE-START chain of the A set D2
// into the next phi trail (F tables: no [cut = 2] term), D1, D2 disjoint and unused.  Junction inside the word's
// start chain: A-only first part D1 (cost bounded below by 0), then F_{D2} into the first phi trail.  Junction
// after the last phi trail: end chain D1, then an A-only nonempty second part (cost bounded below by 0).
// Every single split with G <= THR + 1 (beta = 0 bound) survives; the surviving patterns are written for the exact
// evaluation (split_eval.c).  An empty result proves G >= THR + 2 for every single split.
// usage: ckT_search DIR HDIR HTDIR THR OUT.json
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
#define CAPV 50
#define NPO (NPH * NOP)
#define MAXO 16384
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, NAO, NAA; static int otr[MAXO], ocut[MAXO]; static uint64_t pen[MAXO], pex[MAXO];
static int isA[NTR], Alist[6], nA, phl[NPH], nph, tofs[NTR], tcnt[NTR], phidx[NTR], aidx[NTR];
static int8_t *e;
static int THR;
// overlap weight on packed permutations: least s >= 1 with x[s:] == y[:8-s]
static inline int wpk(uint64_t x, uint64_t y) { for (int s = 1; s < 8; s++) if ((x >> (8 * s)) == (y & ((1ull << (8 * (8 - s))) - 1))) return s; return 8; }
static uint64_t pack(const uint8_t *p) { uint64_t r = 0; for (int i = 0; i < 8; i++) r |= (uint64_t)p[i] << (8 * i); return r; }
// symmetry
static int G, gt[12][NTR]; static int32_t *gop; static int sel[6], ptr[6][NPH], kap[MAXO], oorb[NPH][NOP], orep[NPH][NOR];
static int omq[6][NPH][NOP];
static uint64_t bn[25][26];
static inline uint64_t rk(uint32_t m) { uint64_t r = 0; int i = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) { i++; r += bn[b][i]; } return r; }
static inline uint64_t keyof(uint32_t m, int t) { return (rk(m) << 5) | (uint64_t)t; }
static inline uint32_t pmB(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
static inline uint64_t canB(uint32_t m, int t, int *gg) { uint64_t best = 0; int bg = -1; for (int g = 0; g < 6; g++) { uint64_t k = keyof(pmB(g, m), ptr[g][t]); if (bg < 0 || k > best) { best = k; bg = g; } } *gg = bg; return best; }
// H layers (mmap)
static uint64_t *Hk[NPH + 1]; static uint8_t *Hv[NPH + 1]; static uint64_t Hn[NPH + 1];
static uint64_t *HTk[NPH + 1]; static uint8_t *HTv[NPH + 1]; static uint64_t HTn[NPH + 1];
#define VSZ (NCN * NOR)
static void *mapf(const char *p, size_t *sz) { int fd = open(p, O_RDONLY); if (fd < 0) { fprintf(stderr, "open %s\n", p); exit(2); } struct stat st; fstat(fd, &st); *sz = st.st_size;
    void *m = mmap(NULL, st.st_size ? st.st_size : 1, PROT_READ, MAP_SHARED, fd, 0); if (m == MAP_FAILED) exit(2); close(fd); return m; }
static long hmiss = 0; static uint8_t hb[NCN][NOP];
static int hvec2(int which, uint32_t S, int t, uint8_t out[NCN][NOP]) {   // which = 0: H, 1: HT
    int k = __builtin_popcount(S), g; uint64_t key = canB(S, t, &g);
    int64_t lo = 0, hi = (int64_t)Hn[k] - 1, id = -1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (Hk[k][mid] < key) lo = mid + 1; else if (Hk[k][mid] > key) hi = mid - 1; else { id = mid; break; } }
    if (id < 0) { hmiss++; return 0; }
    const uint8_t *v = (which ? HTv[k] : Hv[k]) + id * VSZ; for (int c = 0; c < NCN; c++) for (int q = 0; q < NOP; q++) out[c][q] = v[c * NOR + omq[g][t][q]];
    return 1;
}
// e blocks: phi local index y = i*84 + q; A local index z = a*NAO + q
static uint8_t *EPP, *EPA, *EAA, *EAP, S0[NPO];
static uint8_t *T1, *T2, *KL, *S1, *S2, *SL, *Q1, *Q2, *QL;   // KL/SL/QL: chain lengths 3..6 (index a-3)
static uint8_t *F1, *F2, *FL;                                  // free-start chains (after the junction)
static inline uint8_t eget(int a, int b) { if (otr[a] == otr[b]) return BIG; int v = e[(size_t)a * NOPT + b]; return v < 0 ? 0 : v >= BIG ? BIG : (uint8_t)v; }
static inline int gpo(int y) { return tofs[phl[y / NOP]] + y % NOP; }
static inline int gao(int z) { return tofs[Alist[z / NAO]] + z % NAO; }
static inline void relax_row(uint8_t *row, const uint8_t *r, int v, int n) { for (int x = 0; x < n; x++) { uint8_t s = (uint8_t)(v + r[x]); if (s < row[x]) row[x] = s; } }
static void chain_tables(void) {
    size_t P2 = (size_t)NPO * NPO;
    T1 = malloc(6 * P2); T2 = malloc(36 * P2); KL = malloc(4 * P2); memset(T2, BIG, 36 * P2);
    S1 = malloc(6 * NPO); S2 = malloc(36 * NPO); SL = malloc(4 * NPO); Q1 = malloc(6 * NPO); Q2 = malloc(36 * NPO); QL = malloc(4 * NPO);
    F1 = malloc(6 * NPO); F2 = malloc(36 * NPO); FL = malloc(4 * NPO);
    memset(S2, BIG, 36 * NPO); memset(Q2, BIG, 36 * NPO); memset(F2, BIG, 36 * NPO);
    // source y in 0..NPO-1 (phi option) or y == NPO (word start: cost [cut = 2] of the first A option)
    #pragma omp parallel for schedule(dynamic, 2)
    for (int y = 0; y <= NPO + 1; y++) {            // y = NPO: word start; y = NPO + 1: free start (junction)
        uint8_t *src = malloc(NAA), *cur = malloc(NAA), *nx = malloc(NAA), *row = malloc(NPO), *R2 = malloc(NAO);
        for (int z = 0; z < NAA; z++) src[z] = y < NPO ? EPA[(size_t)y * NAA + z] : (y == NPO ? (uint8_t)(ocut[gao(z)] == 2) : 0);
        int ty = y < NPO ? y / NOP : -1;
        for (int a = 0; a < 6; a++) {                                   // exact single A trail
            memset(row, BIG, NPO); int qm = BIG;
            for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; if (v < qm) qm = v; relax_row(row, EAP + (size_t)(a * NAO + q) * NPO, v, NPO); }
            if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T1 + ((size_t)a * NPO + y) * NPO, row, NPO); Q1[a * NPO + y] = qm; } else memcpy((y == NPO ? S1 : F1) + a * NPO, row, NPO);
            for (int b = 0; b < 6; b++) { if (b == a) continue;            // exact ordered pair (a, b)
                memset(R2, BIG, NAO);
                for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; relax_row(R2, EAA + (size_t)(a * NAO + q) * NAA + b * NAO, v, NAO); }
                memset(row, BIG, NPO); int qm2 = BIG;
                for (int q = 0; q < NAO; q++) { int v = R2[q]; if (v > CAPV) continue; if (v < qm2) qm2 = v; relax_row(row, EAP + (size_t)(b * NAO + q) * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T2 + ((size_t)(a * 6 + b) * NPO + y) * NPO, row, NPO); Q2[(a * 6 + b) * NPO + y] = qm2; } else memcpy((y == NPO ? S2 : F2) + (a * 6 + b) * NPO, row, NPO);
            } }
        memcpy(cur, src, NAA);                                          // identity-free chains (consecutive A trails distinct)
        for (int len = 1; len <= 6; len++) {
            if (len >= 3) { memset(row, BIG, NPO); int qm = BIG;
                for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; if (v < qm) qm = v; relax_row(row, EAP + (size_t)z * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(KL + ((size_t)(len - 3) * NPO + y) * NPO, row, NPO); QL[(len - 3) * NPO + y] = qm; } else memcpy((y == NPO ? SL : FL) + (len - 3) * NPO, row, NPO); }
            if (len == 6) break;
            memset(nx, BIG, NAA);
            for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; relax_row(nx, EAA + (size_t)z * NAA, v, NAA); }   // same-trail block of EAA is BIG
            uint8_t *tt = cur; cur = nx; nx = tt;
        }
        free(src); free(cur); free(nx); free(row); free(R2);
    }
    for (int x = 0; x < NPO; x++) S0[x] = ocut[gpo(x)] == 2;
}
// ---------------------------------------------------------------- search (records keep only g; patterns by backward DFS)
typedef struct { uint64_t key; uint8_t g[NOP]; } Rec;
typedef struct { Rec *r; int64_t n, cap; int64_t *ht; int64_t hcap; } Layer;
static void linit(Layer *L) { L->n = 0; L->cap = 1024; L->r = malloc(L->cap * sizeof(Rec)); L->hcap = 1 << 12; L->ht = malloc(L->hcap * 8); memset(L->ht, -1, L->hcap * 8); }
static inline uint64_t hsh(uint64_t k) { k ^= k >> 31; k *= 0x9E3779B97F4A7C15ull; k ^= k >> 29; return k; }
static Rec *lget(Layer *L, uint64_t key) {
    if (2 * (L->n + 1) > L->hcap) { int64_t nc = L->hcap * 4; int64_t *nt = malloc(nc * 8); memset(nt, -1, nc * 8);
        for (int64_t i = 0; i < L->n; i++) { uint64_t h = hsh(L->r[i].key) & (nc - 1); while (nt[h] >= 0) h = (h + 1) & (nc - 1); nt[h] = i; }
        free(L->ht); L->ht = nt; L->hcap = nc; }
    uint64_t h = hsh(key) & (L->hcap - 1);
    while (L->ht[h] >= 0) { if (L->r[L->ht[h]].key == key) return &L->r[L->ht[h]]; h = (h + 1) & (L->hcap - 1); }
    if (L->n == L->cap) { L->cap *= 2; L->r = realloc(L->r, L->cap * sizeof(Rec)); }
    Rec *r = &L->r[L->n]; L->ht[h] = L->n++; r->key = key; memset(r->g, BIG, NOP); return r;
}
static const Rec *lfind(const Layer *L, uint64_t key) {
    uint64_t h = hsh(key) & (L->hcap - 1);
    while (L->ht[h] >= 0) { if (L->r[L->ht[h]].key == key) return &L->r[L->ht[h]]; h = (h + 1) & (L->hcap - 1); }
    return NULL;
}
static inline uint64_t skey(uint32_t S, int t, int M, int J) { return (uint64_t)S | ((uint64_t)t << 24) | ((uint64_t)M << 29) | ((uint64_t)J << 35); }
static void put(Layer *L, uint64_t key, const uint8_t *w) { Rec *r = lget(L, key); for (int q = 0; q < NOP; q++) if (w[q] < r->g[q]) r->g[q] = w[q]; }
// gap table pointer for an ordered/unordered A set: returns the table and sets *ord (0 single/none, 1 = order (i,j), 2 = order (j,i))
static const uint8_t *gaptab(int D, int alt) { int a = __builtin_popcount(D);
    if (a == 0) return EPP; if (a == 1) return T1 + (size_t)__builtin_ctz(D) * NPO * NPO;
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? T2 + (size_t)(j * 6 + i) * NPO * NPO : T2 + (size_t)(i * 6 + j) * NPO * NPO; }
    return KL + (size_t)(a - 3) * NPO * NPO; }
static int qval(int D, int t, int y, int alt) { int a = __builtin_popcount(D), yy = t * NOP + y;    // end chain of the A set D after phi option yy
    if (a == 0) return 0; if (a == 1) return Q1[__builtin_ctz(D) * NPO + yy];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? Q2[(j * 6 + i) * NPO + yy] : Q2[(i * 6 + j) * NPO + yy]; }
    return QL[(a - 3) * NPO + yy]; }
static int fval(int D, int u, int x, int alt) { int a = __builtin_popcount(D), xx = u * NOP + x;    // free-start chain of D into phi option xx
    if (a == 0) return 0; if (a == 1) return F1[__builtin_ctz(D) * NPO + xx];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? F2[(j * 6 + i) * NPO + xx] : F2[(i * 6 + j) * NPO + xx]; }
    return FL[(a - 3) * NPO + xx]; }
static int sval(int D, int u, int x, int alt) { int a = __builtin_popcount(D), xx = u * NOP + x;    // word-start chain of D into phi option xx
    if (a == 0) return S0[xx]; if (a == 1) return S1[__builtin_ctz(D) * NPO + xx];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? S2[(j * 6 + i) * NPO + xx] : S2[(i * 6 + j) * NPO + xx]; }
    return SL[(a - 3) * NPO + xx]; }
static inline int nalt(int D) { return __builtin_popcount(D) == 2 ? 2 : 1; }
// ---------------------------------------------------------------- pattern output (backward DFS)
// token stream per pattern: phi trail ids (>= 0), A groups encoded as 1000 + 100 * kind + data:
//   kind 1: ordered group, data = 6-bit mask (size 1) or 64 + i*6+j (ordered pair i, j);  kind 2: unordered set (mask);
//   -1 = junction marker.  Patterns are written one per line.
static Layer *ALL; static FILE *patf; static long npat = 0, patcap = 0; static int THRP;
static void emit(const int *rev, int nrev) { if (patcap && npat >= patcap) { npat++; return; } for (int i = nrev - 1; i >= 0; i--) fprintf(patf, "%d%c", rev[i], i ? ' ' : '\n'); npat++; }
static int gcode(int D, int alt) { int a = __builtin_popcount(D); if (a <= 1) return 1000 + 100 + D; if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return 1000 + 100 + 64 + (alt ? j * 6 + i : i * 6 + j); } return 1000 + 200 + D; }
static void dfs(int k, const Rec *r, const int *s, int *rev, int nrev) {
    uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, J = (r->key >> 35) & 1;
    rev[nrev++] = phl[t];
    if (k == 1) {
        if (!J) { for (int alt = 0; alt < nalt(M); alt++) { int ok = 0; for (int x = 0; x < NOP; x++) if (s[x] < BIG && sval(M, t, x, alt) + s[x] <= THRP) ok = 1;
                if (!ok) continue; int nr = nrev; if (M) rev[nr++] = gcode(M, alt); emit(rev, nr); } }
        else { for (int D1 = M; D1; D1 = (D1 - 1) & M) { int D2 = M & ~D1;
                for (int alt = 0; alt < nalt(D2); alt++) { int ok = 0; for (int x = 0; x < NOP; x++) if (s[x] < BIG && fval(D2, t, x, alt) + s[x] <= THRP) ok = 1;
                    if (!ok) continue; int nr = nrev; if (D2) rev[nr++] = gcode(D2, alt); rev[nr++] = -1; rev[nr++] = 1000 + 200 + D1; emit(rev, nr); } } }
        return; }
    uint32_t Sp = S & ~(1u << t);
    for (int tp = 0; tp < NPH; tp++) { if (!(Sp >> tp & 1)) continue;
        // normal predecessor (same J)
        for (int D = M; ; D = (D - 1) & M) {
            const Rec *rp = lfind(&ALL[k - 1], skey(Sp, tp, M & ~D, J));
            if (rp) for (int alt = 0; alt < nalt(D); alt++) { const uint8_t *tab = gaptab(D, alt); int sp[NOP]; int ok = 0;
                for (int y = 0; y < NOP; y++) { sp[y] = BIG; if (rp->g[y] >= BIG) continue; const uint8_t *row = tab + (size_t)(tp * NOP + y) * NPO + t * NOP;
                    for (int x = 0; x < NOP; x++) if (s[x] < BIG) { int v = row[x] + s[x]; if (v < sp[y]) sp[y] = v; }
                    if (rp->g[y] + sp[y] <= THRP) ok = 1; }
                if (ok) { int nr = nrev; if (D) rev[nr++] = gcode(D, __builtin_popcount(D) >= 3 ? 0 : alt); dfs(k - 1, rp, sp, rev, nr); } }
            if (!D) break; }
        // junction predecessor (J = 1 from J = 0): end chain D1 after tp, free-start chain D2 into t
        if (J) for (int DD = M; ; DD = (DD - 1) & M) { const Rec *rp = lfind(&ALL[k - 1], skey(Sp, tp, M & ~DD, 0));
            if (rp) for (int D1 = DD; ; D1 = (D1 - 1) & DD) { int D2 = DD & ~D1;
                for (int a2 = 0; a2 < nalt(D2); a2++) { int m2 = BIG; for (int x = 0; x < NOP; x++) if (s[x] < BIG) { int v = fval(D2, t, x, a2) + s[x]; if (v < m2) m2 = v; }
                    if (m2 >= BIG) continue;
                    for (int a1 = 0; a1 < nalt(D1); a1++) { int sp[NOP]; int ok = 0;
                        for (int y = 0; y < NOP; y++) { sp[y] = BIG; if (rp->g[y] >= BIG) continue; int v = qval(D1, tp, y, a1) + m2; sp[y] = v > BIG ? BIG : v; if (rp->g[y] + sp[y] <= THRP) ok = 1; }
                        if (!ok) continue;
                        // tokens (reverse order): [t] [D2] JUNCTION [D1] [tp] ...   (the suffix after t is already in rev)
                        int nr = nrev; if (D2) rev[nr++] = gcode(D2, a2); rev[nr++] = -1; if (D1) rev[nr++] = gcode(D1, a1);
                        dfs(k - 1, rp, sp, rev, nr); } }
                if (!D1) break; }
            if (!DD) break; }
    }
}
int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: ckT_search DIR HDIR HTDIR THR OUT.json\n"); return 1; }
    const char *dir = argv[1], *hdir = argv[2], *htdir = argv[3]; THR = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
    double T0 = omp_get_wtime();
    for (int n = 0; n <= 24; n++) for (int k = 0; k <= 25; k++) bn[n][k] = k == 0 ? 1 : (n == 0 ? 0 : bn[n - 1][k - 1] + bn[n - 1][k]);
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; const uint8_t *en = runp[t][v] + 8 * k, *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            uint8_t ex[8]; ex[0] = pr[7]; for (int i = 1; i < 8; i++) ex[i] = pr[i - 1];
            pen[o] = pack(en); pex[o] = pack(ex); ocut[o] = wpk(pex[o], pen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = nph = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) { aidx[t] = nA; Alist[nA++] = t; } else { phidx[t] = nph; phl[nph++] = t; } }
    if (nA != 6 || nph != NPH) return 4;
    NAO = tcnt[Alist[0]]; for (int a = 0; a < 6; a++) if (tcnt[Alist[a]] != NAO) return 4; for (int i = 0; i < NPH; i++) if (tcnt[phl[i]] != NOP) return 4;
    NAA = 6 * NAO;
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for reduction(+:neg) schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) {
        if (otr[a] == otr[b]) { e[(size_t)a * NOPT + b] = 99; continue; }
        int v = wpk(pex[a], pen[b]) - ocut[b] - 1; if (v < 0) neg++; e[(size_t)a * NOPT + b] = (int8_t)v; }
    if (neg) { fprintf(stderr, "negative excess %ld\n", neg); return 5; }
    const char *mut = getenv("CKB_MUT"); int nmut = 0;
    if (mut && *mut) { FILE *mf = fopen(mut, "r"); int a, b, v; while (mf && fscanf(mf, "%d %d %d", &a, &b, &v) == 3) { e[(size_t)a * NOPT + b] = (int8_t)v; nmut++; } if (mf) fclose(mf); }
    // group: verify that every element is an automorphism (trail bijection, option bijection, cut, e)
    snprintf(p, sizeof p, "%s/group.bin", dir); f = fopen(p, "rb"); if (fread(&G, 4, 1, f) != 1 || G > 12) return 2;
    int32_t *tpb = malloc(4 * G * NTR); if (fread(tpb, 4, G * NTR, f) != (size_t)(G * NTR)) return 2;
    gop = malloc(4 * (size_t)G * NOPT); if (fread(gop, 4, (size_t)G * NOPT, f) != (size_t)G * NOPT) return 2; fclose(f);
    for (int g = 0; g < G; g++) for (int t = 0; t < NTR; t++) gt[g][t] = tpb[g * NTR + t];
    long bad = 0;
    for (int g = 0; g < G; g++) { int seen[NTR] = {0}; for (int t = 0; t < NTR; t++) { int u = gt[g][t]; if (u < 0 || u >= NTR || seen[u]++ || isA[u] != isA[t]) bad++; }
        char *so = calloc(NOPT, 1); for (int o = 0; o < NOPT; o++) { int o2 = gop[(size_t)g * NOPT + o]; if (o2 < 0 || o2 >= NOPT || so[o2]++) bad++; } free(so); }
    if (bad) { fprintf(stderr, "group: not bijective %ld\n", bad); return 6; }
    #pragma omp parallel for reduction(+:bad)
    for (int g = 0; g < G; g++) { const int32_t *P = gop + (size_t)g * NOPT;
        for (int a = 0; a < NOPT; a++) { if (otr[P[a]] != gt[g][otr[a]] || ocut[P[a]] != ocut[a]) bad++;
            const int8_t *r1 = e + (size_t)a * NOPT, *r2 = e + (size_t)P[a] * NOPT; for (int b = 0; b < NOPT; b++) if (r2[P[b]] != r1[b]) bad++; } }
    fprintf(stderr, "options %d (A %d x %d), mutations %d, group %d elements, violations %ld\n", NOPT, nA, NAO, nmut, G, bad);
    if (bad) { printf("{\"checker\": \"B-search\", \"error\": \"group invariance violated\", \"violations\": %ld}\n", bad); return 6; }
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
        for (int q = 0; q < NOP; q++) { int q2 = kap[tofs[t] + q] - tofs[t]; if (q2 < 0 || q2 >= NOP || q2 == q) return 8;
            if (oorb[i][q] >= 0) continue; orep[i][c] = q > q2 ? q : q2; oorb[i][q] = c; oorb[i][q2] = c; c++; }
        if (c != NOR) return 9; }
    for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) for (int q = 0; q < NOP; q++) {
        int o2 = gop[(size_t)sel[s] * NOPT + tofs[phl[i]] + q]; int i2 = ptr[s][i]; omq[s][i][q] = oorb[i2][o2 - tofs[phl[i2]]]; }
    // the orbit numbering and trail actions must be those under which ckB.c stored H
    { snprintf(p, sizeof p, "%s/meta.bin", hdir); size_t sz; int32_t *mt = mapf(p, &sz); int ok = sz == 4 * (size_t)(NPH + 6 * NPH + NPH * NOR + NPH * NOP + 6 * NPH * NOR);
      if (ok) { const int32_t *q = mt; for (int i = 0; i < NPH; i++) ok &= q[i] == phl[i]; q += NPH;
          for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ok &= q[s * NPH + i] == ptr[s][i]; q += 6 * NPH;
          for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) ok &= q[i * NOR + j] == orep[i][j]; q += NPH * NOR;
          for (int i = 0; i < NPH; i++) for (int j = 0; j < NOP; j++) ok &= q[i * NOP + j] == oorb[i][j]; }
      if (!ok) { fprintf(stderr, "meta mismatch\n"); return 13; } }
    for (int k = 1; k <= NPH; k++) { size_t s1, s2; snprintf(p, sizeof p, "%s/H%02d.key", hdir, k); Hk[k] = mapf(p, &s1); snprintf(p, sizeof p, "%s/H%02d.val", hdir, k); Hv[k] = mapf(p, &s2);
        Hn[k] = s1 / 8; if (s2 != Hn[k] * VSZ) { fprintf(stderr, "H layer %d size\n", k); return 14; } }
    for (int k = 1; k <= NPH; k++) { size_t s1, s2; snprintf(p, sizeof p, "%s/HT%02d.key", htdir, k); HTk[k] = mapf(p, &s1); snprintf(p, sizeof p, "%s/HT%02d.val", htdir, k); HTv[k] = mapf(p, &s2);
        HTn[k] = s1 / 8; if (s2 != HTn[k] * VSZ || HTn[k] != Hn[k]) { fprintf(stderr, "HT layer %d size\n", k); return 14; }
        if (memcmp(HTk[k], Hk[k], s1)) { fprintf(stderr, "HT layer %d keys differ from H\n", k); return 14; } }
    // e blocks
    EPP = malloc((size_t)NPO * NPO); EPA = malloc((size_t)NPO * NAA); EAA = malloc((size_t)NAA * NAA); EAP = malloc((size_t)NAA * NPO);
    #pragma omp parallel for
    for (int y = 0; y < NPO; y++) { for (int x = 0; x < NPO; x++) EPP[(size_t)y * NPO + x] = eget(gpo(y), gpo(x)); for (int z = 0; z < NAA; z++) EPA[(size_t)y * NAA + z] = eget(gpo(y), gao(z)); }
    #pragma omp parallel for
    for (int z = 0; z < NAA; z++) { for (int z2 = 0; z2 < NAA; z2++) EAA[(size_t)z * NAA + z2] = eget(gao(z), gao(z2)); for (int x = 0; x < NPO; x++) EAP[(size_t)z * NPO + x] = eget(gao(z), gpo(x)); }
    chain_tables();
    fprintf(stderr, "chain tables %.1fs\n", omp_get_wtime() - T0);
    // ---------------------------------------------------------------- layer 1
    THRP = THR;
    Layer *all = malloc(sizeof(Layer) * (NPH + 1)); linit(&all[1]);
    { uint8_t hT[NCN][NOP], hH[NCN][NOP], w[NOP];
      for (int t = 0; t < NPH; t++) {
        if (!hvec2(1, 1u << t, t, hT) || !hvec2(0, 1u << t, t, hH)) return 15;
        for (int m = 0; m < 64; m++) { int a = __builtin_popcount(m);
            // J = 0: word-start chain with the A set m
            for (int x = 0; x < NOP; x++) { int v = BIG; for (int alt = 0; alt < nalt(m); alt++) { int s = sval(m, t, x, alt); if (s < v) v = s; } w[x] = v + hT[6 - a][x] <= THR ? v : BIG; }
            int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(&all[1], skey(1u << t, t, m, 0), w);
            // J = 1: junction inside the start chain: A-only first part D1 != 0 (cost >= 0), free-start chain D2 into t
            if (!m) continue;
            for (int x = 0; x < NOP; x++) w[x] = BIG;
            for (int D1 = m; D1; D1 = (D1 - 1) & m) { int D2 = m & ~D1;
                for (int x = 0; x < NOP; x++) for (int alt = 0; alt < nalt(D2); alt++) { int v = fval(D2, t, x, alt); if (v + hH[6 - a][x] <= THR && v < w[x]) w[x] = v; } }
            any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(&all[1], skey(1u << t, t, m, 1), w); } } }
    fprintf(stderr, "layer 1: %lld states\n", (long long)all[1].n);
    FILE *jo = fopen(outp, "w"); fprintf(jo, "{\n \"checker\": \"T-search\",\n \"THR\": %d,\n \"mutations\": %d,\n \"layers\": [{\"layer\": 1, \"states\": %lld}", THR, nmut, (long long)all[1].n);
    long long ntr_total = 0;
    for (int k = 1; k < NPH; k++) {
        Layer *L = &all[k]; long long ntr = 0; int nthr = omp_get_max_threads(); Layer *part = malloc(sizeof(Layer) * nthr); for (int i = 0; i < nthr; i++) linit(&part[i]);
        // pending junction states P(S, M') -> scalar value (min over t, M, D1 of g + end chain); stored as Rec with g[0]
        Layer *pend = malloc(sizeof(Layer) * nthr); for (int i = 0; i < nthr; i++) linit(&pend[i]);
        #pragma omp parallel for schedule(dynamic, 16) reduction(+:ntr)
        for (int64_t ri = 0; ri < L->n; ri++) {
            Layer *out = &part[omp_get_thread_num()], *pd = &pend[omp_get_thread_num()];
            const Rec *r = &L->r[ri]; uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, J = (r->key >> 35) & 1, c = __builtin_popcount(M);
            int live[NOP], nl = 0; for (int q = 0; q < NOP; q++) if (r->g[q] < BIG) live[nl++] = q; if (!nl) continue;
            uint8_t hX[NCN][NOP], w[NOP], wk[NCN][NOP]; int R = 63 & ~M;
            if (!J) for (int D1 = R; ; D1 = (D1 - 1) & R) { int m1 = BIG;
                    for (int alt = 0; alt < nalt(D1); alt++) for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + qval(D1, t, y, alt); if (v < m1) m1 = v; }
                    if (m1 <= THR) { uint8_t one[NOP]; memset(one, BIG, NOP); one[0] = (uint8_t)m1; put(pd, skey(S, 0, M | D1, 0), one); }
                    if (!D1) break; }
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue; uint32_t S2_ = S | 1u << u;
                if (!hvec2(J ? 0 : 1, S2_, u, hX)) { fprintf(stderr, "H/HT miss\n"); exit(15); }
                // relaxed chains of >= 3 A trails: one min-plus per size
                for (int a = 3; a <= 6 - c; a++) { const uint8_t *tab = KL + (size_t)(a - 3) * NPO * NPO; ntr++;
                    for (int x = 0; x < NOP; x++) { int m = BIG; for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + tab[(size_t)(t * NOP + y) * NPO + u * NOP + x]; if (v < m) m = v; }
                        wk[a][x] = m + hX[6 - c - a][x] <= THR ? (uint8_t)m : BIG; } }
                for (int D = R; ; D = (D - 1) & R) { int a = __builtin_popcount(D);
                    if (a >= 3) memcpy(w, wk[a], NOP);
                    else { for (int x = 0; x < NOP; x++) w[x] = BIG;
                        for (int alt = 0; alt < nalt(D); alt++) { const uint8_t *tab = gaptab(D, alt); ntr++;
                            for (int x = 0; x < NOP; x++) { int m = BIG; for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + tab[(size_t)(t * NOP + y) * NPO + u * NOP + x]; if (v < m) m = v; }
                                if (m + hX[6 - c - a][x] <= THR && m < w[x]) w[x] = (uint8_t)m; } } }
                    int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(out, skey(S2_, u, M | D, J), w);
                    if (!D) break; } } }
        // merge pending junction states and expand them: free-start chain D2 into a new phi trail u
        Layer pj; linit(&pj); for (int i = 0; i < nthr; i++) { for (int64_t j = 0; j < pend[i].n; j++) put(&pj, pend[i].r[j].key, pend[i].r[j].g); free(pend[i].r); free(pend[i].ht); } free(pend);
        #pragma omp parallel for schedule(dynamic, 16) reduction(+:ntr)
        for (int64_t pi = 0; pi < pj.n; pi++) {
            Layer *out = &part[omp_get_thread_num()];
            uint32_t S = pj.r[pi].key & 0xFFFFFF; int Mp = (pj.r[pi].key >> 29) & 63, V = pj.r[pi].g[0], cp = __builtin_popcount(Mp), R = 63 & ~Mp;
            uint8_t hH[NCN][NOP], w[NOP];
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue; uint32_t S2_ = S | 1u << u;
                if (!hvec2(0, S2_, u, hH)) { fprintf(stderr, "H miss\n"); exit(15); }
                for (int D2 = R; ; D2 = (D2 - 1) & R) { int a = __builtin_popcount(D2); ntr++;
                    for (int x = 0; x < NOP; x++) { int m = BIG; for (int alt = 0; alt < nalt(D2); alt++) { int v = V + fval(D2, u, x, alt); if (v < m) m = v; }
                        w[x] = m + hH[6 - cp - a][x] <= THR ? (uint8_t)m : BIG; }
                    int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(out, skey(S2_, u, Mp | D2, 1), w);
                    if (!D2) break; } } }
        long long npend = pj.n; free(pj.r); free(pj.ht);
        Layer nxt; linit(&nxt); for (int i = 0; i < nthr; i++) { for (int64_t j = 0; j < part[i].n; j++) put(&nxt, part[i].r[j].key, part[i].r[j].g); free(part[i].r); free(part[i].ht); } free(part);
        all[k + 1] = nxt; ntr_total += ntr;
        long long nj = 0; for (int64_t i = 0; i < nxt.n; i++) nj += (nxt.r[i].key >> 35) & 1;
        fprintf(stderr, "layer %d: %lld states (%lld after the junction), %lld pending junctions, %lld transitions, %.1fs\n", k + 1, (long long)nxt.n, nj, npend, ntr, omp_get_wtime() - T0);
        fprintf(jo, ", {\"layer\": %d, \"states\": %lld, \"after_junction\": %lld, \"pending_junctions\": %lld, \"transitions\": %lld}", k + 1, (long long)nxt.n, nj, npend, ntr);
    }
    fprintf(jo, "],\n");
    // ---------------------------------------------------------------- final layer
    Layer *F = &all[NPH]; int best = 1 << 20; long nfin = 0, nsol = 0; long bestJ0 = 1 << 20, bestJ1 = 1 << 20;
    for (int64_t ri = 0; ri < F->n; ri++) { const Rec *r = &F->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, J = (r->key >> 35) & 1; int R = 63 & ~M; int fin = 0;
        for (int q = 0; q < NOP; q++) { if (r->g[q] >= BIG) continue; int ev = BIG;
            if (J) { for (int alt = 0; alt < nalt(R); alt++) { int v = qval(R, t, q, alt); if (v < ev) ev = v; } }
            else { if (!R) continue; for (int D1 = R; ; D1 = (D1 - 1) & R) { if (D1 != R) for (int alt = 0; alt < nalt(D1); alt++) { int v = qval(D1, t, q, alt); if (v < ev) ev = v; } if (!D1) break; } }
            int tot = r->g[q] + ev; if (tot < best) best = tot; if (J && tot < bestJ1) bestJ1 = tot; if (!J && tot < bestJ0) bestJ0 = tot;
            if (tot <= THR) { fin = 1; nsol++; } }
        nfin += fin; }
    fprintf(stderr, "final: minimum %d (junction before last phi %ld, after last phi %ld), final states <= THR %ld, solutions %ld\n", best, bestJ1, bestJ0, nfin, nsol);
    // ---------------------------------------------------------------- patterns
    char pp[2100]; snprintf(pp, sizeof pp, "%s.patterns", outp); patf = fopen(pp, "w"); ALL = all; patcap = 50000000;
    { int rev[256];
      for (int64_t ri = 0; ri < F->n; ri++) { const Rec *r = &F->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, J = (r->key >> 35) & 1; int R = 63 & ~M;
        if (J) { for (int alt = 0; alt < nalt(R); alt++) { int sv[NOP]; int ok = 0; for (int x = 0; x < NOP; x++) { sv[x] = r->g[x] < BIG ? qval(R, t, x, alt) : BIG; if (sv[x] < BIG && r->g[x] + sv[x] <= THR) ok = 1; }
                if (!ok) continue; int nr = 0; if (R) rev[nr++] = gcode(R, alt); dfs(NPH, r, sv, rev, nr); } }
        else { if (!R) continue; for (int D1 = R; ; D1 = (D1 - 1) & R) { if (D1 != R) for (int alt = 0; alt < nalt(D1); alt++) { int sv[NOP]; int ok = 0;
                    for (int x = 0; x < NOP; x++) { sv[x] = r->g[x] < BIG ? qval(D1, t, x, alt) : BIG; if (sv[x] < BIG && r->g[x] + sv[x] <= THR) ok = 1; }
                    if (!ok) continue; int nr = 0; rev[nr++] = 1000 + 200 + (R & ~D1); rev[nr++] = -1; if (D1) rev[nr++] = gcode(D1, alt); dfs(NPH, r, sv, rev, nr); }
                if (!D1) break; } } } }
    fclose(patf);
    fprintf(stderr, "patterns: %ld\n", npat);
    char bb[32]; if (best < (1 << 20)) snprintf(bb, sizeof bb, "%d", best); else strcpy(bb, "null");
    fprintf(jo, " \"minimum_bound_F_junction\": %s,\n \"final_states_le_thr\": %ld,\n \"solutions_le_thr\": %ld,\n \"patterns\": %ld,\n \"H_lookup_misses\": %ld,\n \"transitions\": %lld,\n \"sec\": %.1f\n}\n",
            bb, nfin, nsol, npat, hmiss, ntr_total, omp_get_wtime() - T0); fclose(jo);
    printf("{\"checker\": \"T-search\", \"THR\": %d, \"minimum_bound_F_junction\": %d, \"final_states_le_thr\": %ld, \"patterns\": %ld, \"H_lookup_misses\": %ld}\n", THR, best < (1 << 20) ? best : -1, nfin, npat, hmiss);
    return 0;
}
