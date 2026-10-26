// Round R -- identity-aware forward search for the BRACKET-TREE family (every V = P multi-opening, after the reduction
// by the detour lemmas L1/L2).  A bracket tree = path P of mains + c >= 1 cycles; opening every cycle at its anchor
// and appending the cycles to P gives a sequence SIGMA of all 30 trails (each once) with c junctions:
//     G = c + [cut(first) = 2] + sum_{non-junction edges} e + sum_i beta_i,   beta_i >= hout(end of Z_i) + hin(start of Z_i).
// States (S, t, M, F): S = phi trails so far, t = last phi trail, M = A trails so far, F = 1 iff a junction occurred
// (we are inside a cycle segment).  Prefix values g[o] are lower bounds as in Round P/Q (gaps of <= 2 A trails exact,
// >= 3 identity-free).  Pruning:  F = 0: g + HP(S, t, .) <= THR;  F = 1: g + HZ(S, t, .) <= THR  (tables of ckM.c),
// pending junctions: V + PLZ[rest] <= THR.
// A junction block between consecutive phi trails t and u:  end chain D1 after t (+ hout of its last option iff F = 1),
// + 1, optionally A-only cycle segments with A set Dm (cost midc(Dm) >= 1 + least closing, each followed by a junction),
// then a free-start chain D2 into u (+ hin of its first option).  Junction after the last phi trail: end chain D1, + 1,
// then A-only last segment(s) with the rest (cost lastc >= least closing).  P may be A-only (junction inside the word's
// start chain).
// Every bracket tree with G <= THR survives; surviving patterns are written for the exact evaluation (ckM_eval.c).
// An empty result proves G >= THR + 1 for every bracket tree, hence (with L1/L2) for every V = P multi-opening.
// TRACE MODE (env CKM_TRACE = "t0,...,t29;j1,j2,..."): keep only the states of one given junction sequence.
// usage: ckM_search DIR HKEYDIR MDIR THR OUT.json
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
static inline int wpk(uint64_t x, uint64_t y) { for (int s = 1; s < 8; s++) if ((x >> (8 * s)) == (y & ((1ull << (8 * (8 - s))) - 1))) return s; return 8; }
static uint64_t pack(const uint8_t *p) { uint64_t r = 0; for (int i = 0; i < 8; i++) r |= (uint64_t)p[i] << (8 * i); return r; }
static int G, gt[12][NTR]; static int32_t *gop; static int sel[6], ptr[6][NPH], kap[MAXO], oorb[NPH][NOP], orep[NPH][NOR];
static int omq[6][NPH][NOP];
static uint64_t bn[25][26];
static inline uint64_t rk(uint32_t m) { uint64_t r = 0; int i = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) { i++; r += bn[b][i]; } return r; }
static inline uint64_t keyof(uint32_t m, int t) { return (rk(m) << 5) | (uint64_t)t; }
static inline uint32_t pmB(int g, uint32_t m) { uint32_t o = 0; for (int b = 0; b < NPH; b++) if (m >> b & 1) o |= 1u << ptr[g][b]; return o; }
static inline uint64_t canB(uint32_t m, int t, int *gg) { uint64_t best = 0; int bg = -1; for (int g = 0; g < 6; g++) { uint64_t k = keyof(pmB(g, m), ptr[g][t]); if (bg < 0 || k > best) { best = k; bg = g; } } *gg = bg; return best; }
static uint64_t *Hk[NPH + 1]; static uint8_t *HZv[NPH + 1], *HPv[NPH + 1]; static uint64_t Hn[NPH + 1]; static uint8_t *PLZ;
#define VSZ (NCN * NOR)
static void *mapf(const char *p, size_t *sz) { int fd = open(p, O_RDONLY); if (fd < 0) { fprintf(stderr, "open %s\n", p); exit(2); } struct stat st; fstat(fd, &st); *sz = st.st_size;
    void *m = mmap(NULL, st.st_size ? st.st_size : 1, PROT_READ, MAP_SHARED, fd, 0); if (m == MAP_FAILED) exit(2); close(fd); return m; }
static long hmiss = 0;
static int hvec(int which, uint32_t S, int t, uint8_t out[NCN][NOP]) {   // which = 0: HP, 1: HZ
    int k = __builtin_popcount(S), g; uint64_t key = canB(S, t, &g);
    int64_t lo = 0, hi = (int64_t)Hn[k] - 1, id = -1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (Hk[k][mid] < key) lo = mid + 1; else if (Hk[k][mid] > key) hi = mid - 1; else { id = mid; break; } }
    if (id < 0) { hmiss++; return 0; }
    const uint8_t *v = (which ? HZv[k] : HPv[k]) + id * VSZ; for (int c = 0; c < NCN; c++) for (int q = 0; q < NOP; q++) out[c][q] = v[c * NOR + omq[g][t][q]];
    return 1;
}
static inline int plz(uint32_t S, int crem) { return PLZ[(size_t)(((1u << NPH) - 1) & ~S) * NCN + crem]; }
// e blocks
static uint8_t *EPP, *EPA, *EAA, *EAP, S0[NPO];
static uint8_t *T1, *T2, *KL, *S1, *S2, *SL, *Q1, *Q2, *QL, *H1, *H2, *HL, *F1, *F2, *FL;   // Q*: end chain; H*: end chain + hout(last); F*: hin(first) + chain
static uint8_t *hinO, *houtO;
static int azseg[64], apseg[64], midc[64], lastc[64];   // A-only segments (cycle: hin + internal + hout; P: [cut=2] + internal)
static inline uint8_t eget(int a, int b) { if (otr[a] == otr[b]) return BIG; int v = e[(size_t)a * NOPT + b]; return v < 0 ? 0 : v >= BIG ? BIG : (uint8_t)v; }
static inline int gpo(int y) { return tofs[phl[y / NOP]] + y % NOP; }
static inline int gao(int z) { return tofs[Alist[z / NAO]] + z % NAO; }
static inline void relax_row(uint8_t *row, const uint8_t *r, int v, int n) { for (int x = 0; x < n; x++) { uint8_t s = (uint8_t)(v + r[x]); if (s < row[x]) row[x] = s; } }
static void chain_tables(void) {
    size_t P2 = (size_t)NPO * NPO;
    T1 = malloc(6 * P2); T2 = malloc(36 * P2); KL = malloc(4 * P2); memset(T2, BIG, 36 * P2);
    S1 = malloc(6 * NPO); S2 = malloc(36 * NPO); SL = malloc(4 * NPO); Q1 = malloc(6 * NPO); Q2 = malloc(36 * NPO); QL = malloc(4 * NPO);
    H1 = malloc(6 * NPO); H2 = malloc(36 * NPO); HL = malloc(4 * NPO); F1 = malloc(6 * NPO); F2 = malloc(36 * NPO); FL = malloc(4 * NPO);
    memset(S2, BIG, 36 * NPO); memset(Q2, BIG, 36 * NPO); memset(H2, BIG, 36 * NPO); memset(F2, BIG, 36 * NPO);
    #pragma omp parallel for schedule(dynamic, 2)
    for (int y = 0; y <= NPO + 1; y++) {            // y = NPO: word start; y = NPO + 1: free start (hin)
        uint8_t *src = malloc(NAA), *cur = malloc(NAA), *nx = malloc(NAA), *row = malloc(NPO), *R2 = malloc(NAO);
        for (int z = 0; z < NAA; z++) src[z] = y < NPO ? EPA[(size_t)y * NAA + z] : (y == NPO ? (uint8_t)(ocut[gao(z)] == 2) : hinO[gao(z)]);
        int ty = y < NPO ? y / NOP : -1;
        for (int a = 0; a < 6; a++) {
            memset(row, BIG, NPO); int qm = BIG, qh = BIG;
            for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; if (v < qm) qm = v; int vh = v + houtO[gao(a * NAO + q)]; if (vh < qh) qh = vh; relax_row(row, EAP + (size_t)(a * NAO + q) * NPO, v, NPO); }
            if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T1 + ((size_t)a * NPO + y) * NPO, row, NPO); Q1[a * NPO + y] = qm; H1[a * NPO + y] = qh; } else memcpy((y == NPO ? S1 : F1) + a * NPO, row, NPO);
            for (int b = 0; b < 6; b++) { if (b == a) continue;
                memset(R2, BIG, NAO);
                for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; relax_row(R2, EAA + (size_t)(a * NAO + q) * NAA + b * NAO, v, NAO); }
                memset(row, BIG, NPO); int qm2 = BIG, qh2 = BIG;
                for (int q = 0; q < NAO; q++) { int v = R2[q]; if (v > CAPV) continue; if (v < qm2) qm2 = v; int vh = v + houtO[gao(b * NAO + q)]; if (vh < qh2) qh2 = vh; relax_row(row, EAP + (size_t)(b * NAO + q) * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T2 + ((size_t)(a * 6 + b) * NPO + y) * NPO, row, NPO); Q2[(a * 6 + b) * NPO + y] = qm2; H2[(a * 6 + b) * NPO + y] = qh2; } else memcpy((y == NPO ? S2 : F2) + (a * 6 + b) * NPO, row, NPO);
            } }
        memcpy(cur, src, NAA);
        for (int len = 1; len <= 6; len++) {
            if (len >= 3) { memset(row, BIG, NPO); int qm = BIG, qh = BIG;
                for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; if (v < qm) qm = v; int vh = v + houtO[gao(z)]; if (vh < qh) qh = vh; relax_row(row, EAP + (size_t)z * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(KL + ((size_t)(len - 3) * NPO + y) * NPO, row, NPO); QL[(len - 3) * NPO + y] = qm; HL[(len - 3) * NPO + y] = qh; } else memcpy((y == NPO ? SL : FL) + (len - 3) * NPO, row, NPO); }
            if (len == 6) break;
            memset(nx, BIG, NAA);
            for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; relax_row(nx, EAA + (size_t)z * NAA, v, NAA); }
            uint8_t *tt = cur; cur = nx; nx = tt;
        }
        free(src); free(cur); free(nx); free(row); free(R2);
    }
    for (int x = 0; x < NPO; x++) S0[x] = ocut[gpo(x)] == 2;
    // A-only segments: exact for 1 and 2 A trails (both orders), identity-free (consecutive distinct) for >= 3
    for (int D = 1; D < 64; D++) {
        int a = __builtin_popcount(D), bz = BIG, bp = BIG;
        if (a == 1) { int i = __builtin_ctz(D); for (int q = 0; q < NAO; q++) { int o = tofs[Alist[i]] + q; int v = hinO[o] + houtO[o]; if (v < bz) bz = v; int w = ocut[o] == 2; if (w < bp) bp = w; } }
        else if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D);
            for (int r = 0; r < 2; r++) { int x = r ? j : i, y2 = r ? i : j;
                for (int q = 0; q < NAO; q++) { int o = tofs[Alist[x]] + q; for (int q2 = 0; q2 < NAO; q2++) { int o2 = tofs[Alist[y2]] + q2; int ee = eget(o, o2);
                    int v = hinO[o] + ee + houtO[o2]; if (v < bz) bz = v; int w = (ocut[o] == 2) + ee; if (w < bp) bp = w; } } } }
        else { uint8_t *cz = malloc(NAA), *cp = malloc(NAA), *nz = malloc(NAA), *np = malloc(NAA);
            for (int z = 0; z < NAA; z++) { cz[z] = hinO[gao(z)]; cp[z] = ocut[gao(z)] == 2; }
            for (int len = 1; len < a; len++) { memset(nz, BIG, NAA); memset(np, BIG, NAA);
                for (int z = 0; z < NAA; z++) { if (cz[z] <= CAPV) relax_row(nz, EAA + (size_t)z * NAA, cz[z], NAA); if (cp[z] <= CAPV) relax_row(np, EAA + (size_t)z * NAA, cp[z], NAA); }
                uint8_t *t1 = cz; cz = nz; nz = t1; t1 = cp; cp = np; np = t1; }
            for (int z = 0; z < NAA; z++) { int v = cz[z] + houtO[gao(z)]; if (v < bz) bz = v; if (cp[z] < bp) bp = cp[z]; }
            free(cz); free(cp); free(nz); free(np); }
        azseg[D] = bz; apseg[D] = bp; }
    // midc(D): one or more A-only cycle segments covering D, each followed by a junction; lastc(D): the same at the end of SIGMA
    for (int D = 1; D < 64; D++) { int m = 1 + azseg[D], l = azseg[D];
        for (int D1 = (D - 1) & D; D1; D1 = (D1 - 1) & D) { int v = 1 + azseg[D1] + midc[D & ~D1]; if (v < m) m = v; int w = azseg[D1] + 1 + lastc[D & ~D1]; if (w < l) l = w; }
        midc[D] = m; lastc[D] = l; }
    midc[0] = 0; lastc[0] = BIG;
}
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
static void lfree(Layer *L) { free(L->r); free(L->ht); }
static inline uint64_t skey(uint32_t S, int t, int M, int F) { return (uint64_t)S | ((uint64_t)t << 24) | ((uint64_t)M << 29) | ((uint64_t)F << 35); }
static void put(Layer *L, uint64_t key, const uint8_t *w) { Rec *r = lget(L, key); for (int q = 0; q < NOP; q++) if (w[q] < r->g[q]) r->g[q] = w[q]; }
static const uint8_t *gaptab(int D, int alt) { int a = __builtin_popcount(D);
    if (a == 0) return EPP; if (a == 1) return T1 + (size_t)__builtin_ctz(D) * NPO * NPO;
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? T2 + (size_t)(j * 6 + i) * NPO * NPO : T2 + (size_t)(i * 6 + j) * NPO * NPO; }
    return KL + (size_t)(a - 3) * NPO * NPO; }
// end chain of the A set D after phi option (t, y): hz = 0 plain (end of P), hz = 1 with hout of the last option (end of a cycle)
static int qv(int D, int t, int y, int alt, int hz) { int a = __builtin_popcount(D), yy = t * NOP + y;
    const uint8_t *q1 = hz ? H1 : Q1, *q2 = hz ? H2 : Q2, *ql = hz ? HL : QL;
    if (a == 0) return hz ? houtO[gpo(yy)] : 0; if (a == 1) return q1[__builtin_ctz(D) * NPO + yy];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? q2[(j * 6 + i) * NPO + yy] : q2[(i * 6 + j) * NPO + yy]; }
    return ql[(a - 3) * NPO + yy]; }
static int fval(int D, int u, int x, int alt) { int a = __builtin_popcount(D), xx = u * NOP + x;
    if (a == 0) return hinO[gpo(xx)]; if (a == 1) return F1[__builtin_ctz(D) * NPO + xx];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? F2[(j * 6 + i) * NPO + xx] : F2[(i * 6 + j) * NPO + xx]; }
    return FL[(a - 3) * NPO + xx]; }
static int sval(int D, int u, int x, int alt) { int a = __builtin_popcount(D), xx = u * NOP + x;
    if (a == 0) return S0[xx]; if (a == 1) return S1[__builtin_ctz(D) * NPO + xx];
    if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return alt ? S2[(j * 6 + i) * NPO + xx] : S2[(i * 6 + j) * NPO + xx]; }
    return SL[(a - 3) * NPO + xx]; }
static inline int nalt(int D) { return __builtin_popcount(D) == 2 ? 2 : 1; }
// ---------------------------------------------------------------- patterns
// tokens: phi trail ids (>= 0); A groups 1000 + 100 * kind + data (kind 1: ordered, data = mask (size 1) or 64 + i*6+j;
// kind 2: unordered set mask); -1 = junction; 1300 + mask = A-only cycle segment(s) covering mask (between junctions,
// or after the last junction); 1400 + mask = A-only path P at the word start.
static Layer *ALL; static FILE *patf; static long npat = 0, patcap = 0;
static void emit(const int *rev, int nrev) { if (patcap && npat >= patcap) { npat++; return; } for (int i = nrev - 1; i >= 0; i--) fprintf(patf, "%d%c", rev[i], i ? ' ' : '\n'); npat++; }
static int gcode(int D, int alt) { int a = __builtin_popcount(D); if (a <= 1) return 1000 + 100 + D; if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D); return 1000 + 100 + 64 + (alt ? j * 6 + i : i * 6 + j); } return 1000 + 200 + D; }
// s[x] = least cost of the suffix after (state, option x).  Reconstruct all prefixes with g + s <= THR.
static void dfs(int k, const Rec *r, const int *s, int *rev, int nrev) {
    uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, F = (r->key >> 35) & 1;
    rev[nrev++] = phl[t];
    if (k == 1) {
        if (!F) { for (int alt = 0; alt < nalt(M); alt++) { int ok = 0; for (int x = 0; x < NOP; x++) if (s[x] < BIG && sval(M, t, x, alt) + s[x] <= THR) ok = 1;
                if (!ok) continue; int nr = nrev; if (M) rev[nr++] = gcode(M, alt); emit(rev, nr); } }
        else { // A-only P (DP != 0), junction, optional A-only cycle segments Dm, free-start chain D2 into t
            for (int DP = M; DP; DP = (DP - 1) & M) { int Rm = M & ~DP;
                for (int Dm = Rm; ; Dm = (Dm - 1) & Rm) { int D2 = Rm & ~Dm; int base = apseg[DP] + 1 + midc[Dm];
                    for (int alt = 0; alt < nalt(D2); alt++) { int ok = 0; for (int x = 0; x < NOP; x++) if (s[x] < BIG && base + fval(D2, t, x, alt) + s[x] <= THR) ok = 1;
                        if (!ok) continue; int nr = nrev; if (D2) rev[nr++] = gcode(D2, alt); if (Dm) { rev[nr++] = -1; rev[nr++] = 1300 + Dm; } rev[nr++] = -1; rev[nr++] = 1400 + DP; emit(rev, nr); }
                    if (!Dm) break; } } }
        return; }
    uint32_t Sp = S & ~(1u << t);
    for (int tp = 0; tp < NPH; tp++) { if (!(Sp >> tp & 1)) continue;
        for (int D = M; ; D = (D - 1) & M) {
            const Rec *rp = lfind(&ALL[k - 1], skey(Sp, tp, M & ~D, F));
            if (rp) for (int alt = 0; alt < nalt(D); alt++) { const uint8_t *tab = gaptab(D, alt); int sp[NOP]; int ok = 0;
                for (int y = 0; y < NOP; y++) { sp[y] = BIG; if (rp->g[y] >= BIG) continue; const uint8_t *row = tab + (size_t)(tp * NOP + y) * NPO + t * NOP;
                    for (int x = 0; x < NOP; x++) if (s[x] < BIG) { int v = row[x] + s[x]; if (v < sp[y]) sp[y] = v; }
                    if (rp->g[y] + sp[y] <= THR) ok = 1; }
                if (ok) { int nr = nrev; if (D) rev[nr++] = gcode(D, __builtin_popcount(D) >= 3 ? 0 : alt); dfs(k - 1, rp, sp, rev, nr); } }
            if (!D) break; }
        if (F) for (int DD = M; ; DD = (DD - 1) & M) {          // junction block DD = D1 | Dm | D2 between tp and t
            for (int Fp = 0; Fp < 2; Fp++) { const Rec *rp = lfind(&ALL[k - 1], skey(Sp, tp, M & ~DD, Fp)); if (!rp) continue;
                for (int D1 = DD; ; D1 = (D1 - 1) & DD) { int R1 = DD & ~D1;
                    for (int Dm = R1; ; Dm = (Dm - 1) & R1) { int D2 = R1 & ~Dm;
                        for (int a2 = 0; a2 < nalt(D2); a2++) { int m2 = BIG; for (int x = 0; x < NOP; x++) if (s[x] < BIG) { int v = fval(D2, t, x, a2) + s[x]; if (v < m2) m2 = v; }
                            if (m2 >= BIG) continue; m2 += 1 + midc[Dm];
                            for (int a1 = 0; a1 < nalt(D1); a1++) { int sp[NOP]; int ok = 0;
                                for (int y = 0; y < NOP; y++) { sp[y] = BIG; if (rp->g[y] >= BIG) continue; int v = qv(D1, tp, y, a1, Fp) + m2; sp[y] = v > BIG ? BIG : v; if (rp->g[y] + sp[y] <= THR) ok = 1; }
                                if (!ok) continue;
                                int nr = nrev; if (D2) rev[nr++] = gcode(D2, a2); if (Dm) { rev[nr++] = -1; rev[nr++] = 1300 + Dm; } rev[nr++] = -1; if (D1) rev[nr++] = gcode(D1, a1);
                                dfs(k - 1, rp, sp, rev, nr); } }
                        if (!Dm) break; }
                    if (!D1) break; } }
            if (!DD) break; }
    }
}
int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: ckM_search DIR HKEYDIR MDIR THR OUT.json\n"); return 1; }
    const char *dir = argv[1], *hkdir = argv[2], *mdir = argv[3]; THR = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
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
    NAO = tcnt[Alist[0]]; NAA = 6 * NAO;
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for reduction(+:neg) schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) {
        if (otr[a] == otr[b]) { e[(size_t)a * NOPT + b] = 99; continue; }
        int v = wpk(pex[a], pen[b]) - ocut[b] - 1; if (v < 0) neg++; e[(size_t)a * NOPT + b] = (int8_t)v; }
    if (neg) return 5;
    const char *mut = getenv("CKB_MUT"); int nmut = 0;
    if (mut && *mut) { FILE *mf = fopen(mut, "r"); int a, b, v; while (mf && fscanf(mf, "%d %d %d", &a, &b, &v) == 3) { e[(size_t)a * NOPT + b] = (int8_t)v; nmut++; } if (mf) fclose(mf); }
    snprintf(p, sizeof p, "%s/group.bin", dir); f = fopen(p, "rb"); if (fread(&G, 4, 1, f) != 1 || G > 12) return 2;
    int32_t *tpb = malloc(4 * G * NTR); if (fread(tpb, 4, G * NTR, f) != (size_t)(G * NTR)) return 2;
    gop = malloc(4 * (size_t)G * NOPT); if (fread(gop, 4, (size_t)G * NOPT, f) != (size_t)G * NOPT) return 2; fclose(f);
    for (int g = 0; g < G; g++) for (int t = 0; t < NTR; t++) gt[g][t] = tpb[g * NTR + t];
    long bad = 0;
    #pragma omp parallel for reduction(+:bad)
    for (int g = 0; g < G; g++) { const int32_t *P = gop + (size_t)g * NOPT;
        for (int a = 0; a < NOPT; a++) { if (otr[P[a]] != gt[g][otr[a]] || ocut[P[a]] != ocut[a]) bad++;
            const int8_t *r1 = e + (size_t)a * NOPT, *r2 = e + (size_t)P[a] * NOPT; for (int b = 0; b < NOPT; b++) if (r2[P[b]] != r1[b]) bad++; } }
    if (bad) { fprintf(stderr, "group invariance violated %ld\n", bad); return 6; }
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
    { snprintf(p, sizeof p, "%s/meta.bin", mdir); size_t sz; int32_t *mt = mapf(p, &sz); int ok = sz == 4 * (size_t)(NPH + 6 * NPH + NPH * NOR + NPH * NOP + 6 * NPH * NOR);
      if (ok) { const int32_t *q = mt; for (int i = 0; i < NPH; i++) ok &= q[i] == phl[i]; q += NPH;
          for (int s = 0; s < 6; s++) for (int i = 0; i < NPH; i++) ok &= q[s * NPH + i] == ptr[s][i]; q += 6 * NPH;
          for (int i = 0; i < NPH; i++) for (int j = 0; j < NOR; j++) ok &= q[i * NOR + j] == orep[i][j]; q += NPH * NOR;
          for (int i = 0; i < NPH; i++) for (int j = 0; j < NOP; j++) ok &= q[i * NOP + j] == oorb[i][j]; }
      if (!ok) { fprintf(stderr, "meta mismatch\n"); return 13; } }
    for (int k = 1; k <= NPH; k++) { size_t s1, s2, s3; snprintf(p, sizeof p, "%s/H%02d.key", hkdir, k); Hk[k] = mapf(p, &s1);
        snprintf(p, sizeof p, "%s/HZ%02d.val", mdir, k); HZv[k] = mapf(p, &s2); snprintf(p, sizeof p, "%s/HP%02d.val", mdir, k); HPv[k] = mapf(p, &s3);
        Hn[k] = s1 / 8; if (s2 != Hn[k] * VSZ || s3 != Hn[k] * VSZ) { fprintf(stderr, "layer %d size\n", k); return 14; } }
    { size_t sz; snprintf(p, sizeof p, "%s/PLZ.bin", mdir); PLZ = mapf(p, &sz); if (sz != ((size_t)1 << NPH) * NCN) { fprintf(stderr, "PLZ size\n"); return 14; } }
    EPP = malloc((size_t)NPO * NPO); EPA = malloc((size_t)NPO * NAA); EAA = malloc((size_t)NAA * NAA); EAP = malloc((size_t)NAA * NPO);
    #pragma omp parallel for
    for (int y = 0; y < NPO; y++) { for (int x = 0; x < NPO; x++) EPP[(size_t)y * NPO + x] = eget(gpo(y), gpo(x)); for (int z = 0; z < NAA; z++) EPA[(size_t)y * NAA + z] = eget(gpo(y), gao(z)); }
    #pragma omp parallel for
    for (int z = 0; z < NAA; z++) { for (int z2 = 0; z2 < NAA; z2++) EAA[(size_t)z * NAA + z2] = eget(gao(z), gao(z2)); for (int x = 0; x < NPO; x++) EAP[(size_t)z * NPO + x] = eget(gao(z), gpo(x)); }
    hinO = malloc(NOPT); houtO = malloc(NOPT);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int o = 0; o < NOPT; o++) { int mi = BIG, mo = BIG; for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[o]) continue; int a = eget(u, o), b = eget(o, u); if (a < mi) mi = a; if (b < mo) mo = b; } hinO[o] = mi; houtO[o] = mo; }
    chain_tables();
    fprintf(stderr, "tables %.1fs; A-only: azseg(single) %d %d %d %d %d %d, midc(single) %d, lastc(all) %d\n", omp_get_wtime() - T0,
            azseg[1], azseg[2], azseg[4], azseg[8], azseg[16], azseg[32], midc[1], lastc[63]);
    // trace mode
    uint64_t trk[NPH + 1]; int tron = 0;
    { const char *tv = getenv("CKM_TRACE"); if (tv && *tv) { int sq[NTR], jm[NTR + 1]; memset(jm, 0, sizeof jm); const char *q = tv; for (int i = 0; i < NTR; i++) { sq[i] = atoi(q); while (*q && *q != ',' && *q != ';') q++; if (*q) q++; }
        while (*q) { int j = atoi(q); if (j >= 0 && j <= NTR) jm[j] = 1; while (*q && *q != ',') q++; if (*q) q++; }
        uint32_t S = 0; int M = 0, k = 0, F = 0; for (int i = 0; i < NTR; i++) { if (jm[i]) F = 1; int t = sq[i]; if (isA[t]) { M |= 1 << aidx[t]; continue; } k++; S |= 1u << phidx[t]; trk[k] = skey(S, phidx[t], M, F); }
        tron = 1; fprintf(stderr, "trace on\n"); } }
    Layer *all = malloc(sizeof(Layer) * (NPH + 1)); linit(&all[1]);
    { uint8_t hP[NCN][NOP], hZ[NCN][NOP], w[NOP];
      for (int t = 0; t < NPH; t++) {
        if (!hvec(0, 1u << t, t, hP) || !hvec(1, 1u << t, t, hZ)) return 15;
        for (int m = 0; m < 64; m++) { int a = __builtin_popcount(m);
            for (int x = 0; x < NOP; x++) { int v = BIG; for (int alt = 0; alt < nalt(m); alt++) { int s = sval(m, t, x, alt); if (s < v) v = s; } w[x] = v + hP[6 - a][x] <= THR ? v : BIG; }
            int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(&all[1], skey(1u << t, t, m, 0), w);
            if (!m) continue;
            for (int x = 0; x < NOP; x++) w[x] = BIG;
            for (int DP = m; DP; DP = (DP - 1) & m) { int Rm = m & ~DP;
                for (int Dm = Rm; ; Dm = (Dm - 1) & Rm) { int D2 = Rm & ~Dm; int base = apseg[DP] + 1 + midc[Dm];
                    for (int x = 0; x < NOP; x++) for (int alt = 0; alt < nalt(D2); alt++) { int v = base + fval(D2, t, x, alt); if (v + hZ[6 - a][x] <= THR && v < w[x]) w[x] = v; }
                    if (!Dm) break; } }
            any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(&all[1], skey(1u << t, t, m, 1), w); } } }
    if (tron) { const Rec *r = lfind(&all[1], trk[1]); Layer f1; linit(&f1); if (r) put(&f1, r->key, r->g); fprintf(stderr, "trace layer 1: %s\n", r ? "kept" : "LOST"); lfree(&all[1]); all[1] = f1; }
    fprintf(stderr, "layer 1: %lld states\n", (long long)all[1].n);
    FILE *jo = fopen(outp, "w"); fprintf(jo, "{\n \"checker\": \"M-search\",\n \"THR\": %d,\n \"mutations\": %d,\n \"layers\": [{\"layer\": 1, \"states\": %lld}", THR, nmut, (long long)all[1].n);
    long long ntr_total = 0;
    for (int k = 1; k < NPH; k++) {
        Layer *L = &all[k]; long long ntr = 0; int nthr = omp_get_max_threads(); Layer *part = malloc(sizeof(Layer) * nthr); for (int i = 0; i < nthr; i++) linit(&part[i]);
        Layer *pend = malloc(sizeof(Layer) * nthr); for (int i = 0; i < nthr; i++) linit(&pend[i]);
        #pragma omp parallel for schedule(dynamic, 16) reduction(+:ntr)
        for (int64_t ri = 0; ri < L->n; ri++) {
            Layer *out = &part[omp_get_thread_num()], *pd = &pend[omp_get_thread_num()];
            const Rec *r = &L->r[ri]; uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, F = (r->key >> 35) & 1, c = __builtin_popcount(M);
            int live[NOP], nl = 0; for (int q = 0; q < NOP; q++) if (r->g[q] < BIG) live[nl++] = q; if (!nl) continue;
            uint8_t hX[NCN][NOP], w[NOP], wk[NCN][NOP]; int R = 63 & ~M;
            // junction after t: end chain D1 (+ hout iff F), + 1
            for (int D1 = R; ; D1 = (D1 - 1) & R) { int m1 = BIG;
                for (int alt = 0; alt < nalt(D1); alt++) for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + qv(D1, t, y, alt, F); if (v < m1) m1 = v; }
                m1 += 1;
                if (m1 + plz(S, 6 - c - __builtin_popcount(D1)) <= THR) { uint8_t one[NOP]; memset(one, BIG, NOP); one[0] = (uint8_t)(m1 > BIG ? BIG : m1); put(pd, skey(S, 0, M | D1, 0), one); }
                if (!D1) break; }
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue; uint32_t S2_ = S | 1u << u;
                if (!hvec(F, S2_, u, hX)) { fprintf(stderr, "table miss\n"); exit(15); }
                for (int a = 3; a <= 6 - c; a++) { const uint8_t *tab = KL + (size_t)(a - 3) * NPO * NPO; ntr++;
                    for (int x = 0; x < NOP; x++) { int m = BIG; for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + tab[(size_t)(t * NOP + y) * NPO + u * NOP + x]; if (v < m) m = v; }
                        wk[a][x] = m + hX[6 - c - a][x] <= THR ? (uint8_t)m : BIG; } }
                for (int D = R; ; D = (D - 1) & R) { int a = __builtin_popcount(D);
                    if (a >= 3) memcpy(w, wk[a], NOP);
                    else { for (int x = 0; x < NOP; x++) w[x] = BIG;
                        for (int alt = 0; alt < nalt(D); alt++) { const uint8_t *tab = gaptab(D, alt); ntr++;
                            for (int x = 0; x < NOP; x++) { int m = BIG; for (int i = 0; i < nl; i++) { int y = live[i]; int v = r->g[y] + tab[(size_t)(t * NOP + y) * NPO + u * NOP + x]; if (v < m) m = v; }
                                if (m + hX[6 - c - a][x] <= THR && m < w[x]) w[x] = (uint8_t)m; } } }
                    int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(out, skey(S2_, u, M | D, F), w);
                    if (!D) break; } } }
        // merge pending junction states (S, M') -> V; close under A-only cycle segments (midc), then expand: free start D2 into u
        Layer pj; linit(&pj); for (int i = 0; i < nthr; i++) { for (int64_t j = 0; j < pend[i].n; j++) put(&pj, pend[i].r[j].key, pend[i].r[j].g); lfree(&pend[i]); } free(pend);
        { int64_t n0 = pj.n; for (int64_t i = 0; i < n0; i++) { uint32_t S = pj.r[i].key & 0xFFFFFF; int Mp = (pj.r[i].key >> 29) & 63, V = pj.r[i].g[0], R = 63 & ~Mp;
              for (int Dm = R; Dm; Dm = (Dm - 1) & R) { int v = V + midc[Dm]; if (v + plz(S, 6 - __builtin_popcount(Mp | Dm)) > THR) continue; uint8_t one[NOP]; memset(one, BIG, NOP); one[0] = (uint8_t)v; put(&pj, skey(S, 0, Mp | Dm, 0), one); } } }
        #pragma omp parallel for schedule(dynamic, 16) reduction(+:ntr)
        for (int64_t pi = 0; pi < pj.n; pi++) {
            Layer *out = &part[omp_get_thread_num()];
            uint32_t S = pj.r[pi].key & 0xFFFFFF; int Mp = (pj.r[pi].key >> 29) & 63, V = pj.r[pi].g[0], cp = __builtin_popcount(Mp), R = 63 & ~Mp;
            uint8_t hZ[NCN][NOP], w[NOP];
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue; uint32_t S2_ = S | 1u << u;
                if (!hvec(1, S2_, u, hZ)) { fprintf(stderr, "HZ miss\n"); exit(15); }
                for (int D2 = R; ; D2 = (D2 - 1) & R) { int a = __builtin_popcount(D2); ntr++;
                    for (int x = 0; x < NOP; x++) { int m = BIG; for (int alt = 0; alt < nalt(D2); alt++) { int v = V + fval(D2, u, x, alt); if (v < m) m = v; }
                        w[x] = m + hZ[6 - cp - a][x] <= THR ? (uint8_t)m : BIG; }
                    int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG; if (any) put(out, skey(S2_, u, Mp | D2, 1), w);
                    if (!D2) break; } } }
        long long npend = pj.n; lfree(&pj);
        Layer nxt; linit(&nxt); for (int i = 0; i < nthr; i++) { for (int64_t j = 0; j < part[i].n; j++) put(&nxt, part[i].r[j].key, part[i].r[j].g); lfree(&part[i]); } free(part);
        if (tron) { const Rec *r = lfind(&nxt, trk[k + 1]); Layer f1; linit(&f1); if (r) put(&f1, r->key, r->g); int mg = BIG; if (r) for (int q = 0; q < NOP; q++) if (r->g[q] < mg) mg = r->g[q];
            fprintf(stderr, "trace layer %d: %s (min g %d)\n", k + 1, r ? "kept" : "LOST", mg); lfree(&nxt); nxt = f1; }
        all[k + 1] = nxt; ntr_total += ntr;
        long long nj = 0; for (int64_t i = 0; i < nxt.n; i++) nj += (nxt.r[i].key >> 35) & 1;
        fprintf(stderr, "layer %d: %lld states (%lld inside cycles), %lld pending junction states, %lld transitions, %.1fs\n", k + 1, (long long)nxt.n, nj, npend, ntr, omp_get_wtime() - T0);
        fprintf(jo, ", {\"layer\": %d, \"states\": %lld, \"inside_cycles\": %lld, \"pending_junctions\": %lld, \"transitions\": %lld}", k + 1, (long long)nxt.n, nj, npend, ntr);
    }
    fprintf(jo, "],\n");
    // final layer: F = 1: end chain of the rest with hout;  any F: junction after the last phi, A-only last segment(s)
    Layer *Fl = &all[NPH]; int best = 1 << 20; long nfin = 0, nsol = 0;
    for (int64_t ri = 0; ri < Fl->n; ri++) { const Rec *r = &Fl->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, F = (r->key >> 35) & 1; int R = 63 & ~M; int fin = 0;
        for (int q = 0; q < NOP; q++) { if (r->g[q] >= BIG) continue; int ev = BIG;
            if (F) for (int alt = 0; alt < nalt(R); alt++) { int v = qv(R, t, q, alt, 1); if (v < ev) ev = v; }
            if (R) for (int D1 = (R - 1) & R; ; D1 = (D1 - 1) & R) { for (int alt = 0; alt < nalt(D1); alt++) { int v = qv(D1, t, q, alt, F) + 1 + lastc[R & ~D1]; if (v < ev) ev = v; } if (!D1) break; }
            int tot = r->g[q] + ev; if (tot < best) best = tot; if (tot <= THR) { fin = 1; nsol++; } }
        nfin += fin; }
    fprintf(stderr, "final: minimum %d, final states <= THR %ld, (state, option) solutions %ld\n", best, nfin, nsol);
    char pp[2100]; snprintf(pp, sizeof pp, "%s.patterns", outp); patf = fopen(pp, "w"); ALL = all; patcap = 20000000;
    { int rev[512];
      for (int64_t ri = 0; ri < Fl->n; ri++) { const Rec *r = &Fl->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, F = (r->key >> 35) & 1; int R = 63 & ~M;
        if (F) for (int alt = 0; alt < nalt(R); alt++) { int sv[NOP]; int ok = 0; for (int x = 0; x < NOP; x++) { sv[x] = r->g[x] < BIG ? qv(R, t, x, alt, 1) : BIG; if (sv[x] < BIG && r->g[x] + sv[x] <= THR) ok = 1; }
                if (!ok) continue; int nr = 0; if (R) rev[nr++] = gcode(R, alt); dfs(NPH, r, sv, rev, nr); }
        if (R) for (int D1 = (R - 1) & R; ; D1 = (D1 - 1) & R) { for (int alt = 0; alt < nalt(D1); alt++) { int sv[NOP]; int ok = 0;
                    for (int x = 0; x < NOP; x++) { sv[x] = r->g[x] < BIG ? qv(D1, t, x, alt, F) + 1 + lastc[R & ~D1] : BIG; if (sv[x] < BIG && r->g[x] + sv[x] <= THR) ok = 1; }
                    if (!ok) continue; int nr = 0; rev[nr++] = 1300 + (R & ~D1); rev[nr++] = -1; if (D1) rev[nr++] = gcode(D1, alt); dfs(NPH, r, sv, rev, nr); }
                if (!D1) break; } } }
    fclose(patf);
    fprintf(stderr, "patterns: %ld\n", npat);
    char bb[32]; if (best < (1 << 20)) snprintf(bb, sizeof bb, "%d", best); else strcpy(bb, "null");
    fprintf(jo, " \"minimum_bound_G\": %s,\n \"final_states_le_thr\": %ld,\n \"solutions_le_thr\": %ld,\n \"patterns\": %ld,\n \"table_misses\": %ld,\n \"transitions\": %lld,\n \"sec\": %.1f\n}\n",
            bb, nfin, nsol, npat, hmiss, ntr_total, omp_get_wtime() - T0); fclose(jo);
    printf("{\"checker\": \"M-search\", \"THR\": %d, \"minimum_bound_G\": %d, \"final_states_le_thr\": %ld, \"patterns\": %ld, \"table_misses\": %ld}\n", THR, best < (1 << 20) ? best : -1, nfin, npat, hmiss);
    return 0;
}
