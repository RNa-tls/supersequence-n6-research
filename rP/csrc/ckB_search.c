// Round P, checker B (part 2) -- identity-aware forward search, pruned by checker B's own backward table H.
// Independent of exact_relevant.py, prep_t12.c, prep_chain.c, symprep.py and phidp_sym7.c: it rebuilds the
// options and the excesses e from runs.bin, verifies the symmetry group again, computes its own chain tables,
// and reads only the layers H written by ckB.c (a lower bound for every completion, see ckB.c).
//   State (S, t, M): S = phi trails used, t = last phi trail, M = A trails used.  g[o] (o = option of t) =
//   least cost of a prefix consistent with (S, t, M) in which gaps of 0, 1, 2 A trails and start chains of
//   <= 2 A trails are priced EXACTLY for their trails (minimum over the options of the A trails), while gaps
//   and start chains of a >= 3 A trails are priced by the identity-free chain minimum K_a / S_a, for every
//   a-subset of the unused A trails.  Hence g[o] <= the true prefix cost of every single-opening word whose
//   prefix has this (S, t, M) and option o.
//   Option o survives iff g[o] + H(S, t, 6 - |M|)[o] <= THR.  Final layer: + end chain (exact for <= 2
//   remaining A trails, Q_a otherwise).  Every word with F <= THR survives at every layer, so an empty
//   final result proves that no single-opening word has F <= THR.
// Surviving complete paths are re-evaluated EXACTLY by a fixed-order DP (all orders of their unordered
// chains of >= 3 A trails are tried), so every reported "word" is a genuine single-opening word.
// usage: ckB_search DIR HDIR THR OUT.json        (env CKB_MUT=file with lines "a b v": e(a, b) := v)
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
#define VSZ (NCN * NOR)
static void *mapf(const char *p, size_t *sz) { int fd = open(p, O_RDONLY); if (fd < 0) { fprintf(stderr, "open %s\n", p); exit(2); } struct stat st; fstat(fd, &st); *sz = st.st_size;
    void *m = mmap(NULL, st.st_size ? st.st_size : 1, PROT_READ, MAP_SHARED, fd, 0); if (m == MAP_FAILED) exit(2); close(fd); return m; }
static long hmiss = 0; static uint8_t hb[NCN][NOP];
static int hvec(uint32_t S, int t, uint8_t out[NCN][NOP]) {
    int k = __builtin_popcount(S), g; uint64_t key = canB(S, t, &g);
    int64_t lo = 0, hi = (int64_t)Hn[k] - 1, id = -1; while (lo <= hi) { int64_t mid = (lo + hi) / 2; if (Hk[k][mid] < key) lo = mid + 1; else if (Hk[k][mid] > key) hi = mid - 1; else { id = mid; break; } }
    if (id < 0) { hmiss++; return 0; }
    const uint8_t *v = Hv[k] + id * VSZ; for (int c = 0; c < NCN; c++) for (int q = 0; q < NOP; q++) out[c][q] = v[c * NOR + omq[g][t][q]];
    return 1;
}
// e blocks: phi local index y = i*84 + q; A local index z = a*NAO + q
static uint8_t *EPP, *EPA, *EAA, *EAP, S0[NPO];
static uint8_t *T1, *T2, *KL, *S1, *S2, *SL, *Q1, *Q2, *QL;   // KL/SL/QL: chain lengths 3..6 (index a-3)
static inline uint8_t eget(int a, int b) { if (otr[a] == otr[b]) return BIG; int v = e[(size_t)a * NOPT + b]; return v < 0 ? 0 : v >= BIG ? BIG : (uint8_t)v; }
static inline int gpo(int y) { return tofs[phl[y / NOP]] + y % NOP; }
static inline int gao(int z) { return tofs[Alist[z / NAO]] + z % NAO; }
static inline void relax_row(uint8_t *row, const uint8_t *r, int v, int n) { for (int x = 0; x < n; x++) { uint8_t s = (uint8_t)(v + r[x]); if (s < row[x]) row[x] = s; } }
static void chain_tables(void) {
    size_t P2 = (size_t)NPO * NPO;
    T1 = malloc(6 * P2); T2 = malloc(36 * P2); KL = malloc(4 * P2); memset(T2, BIG, 36 * P2);
    S1 = malloc(6 * NPO); S2 = malloc(36 * NPO); SL = malloc(4 * NPO); Q1 = malloc(6 * NPO); Q2 = malloc(36 * NPO); QL = malloc(4 * NPO);
    memset(S2, BIG, 36 * NPO); memset(Q2, BIG, 36 * NPO);
    // source y in 0..NPO-1 (phi option) or y == NPO (word start: cost [cut = 2] of the first A option)
    #pragma omp parallel for schedule(dynamic, 2)
    for (int y = 0; y <= NPO; y++) {
        uint8_t *src = malloc(NAA), *cur = malloc(NAA), *nx = malloc(NAA), *row = malloc(NPO), *R2 = malloc(NAO);
        for (int z = 0; z < NAA; z++) src[z] = y < NPO ? EPA[(size_t)y * NAA + z] : (uint8_t)(ocut[gao(z)] == 2);
        int ty = y < NPO ? y / NOP : -1;
        for (int a = 0; a < 6; a++) {                                   // exact single A trail
            memset(row, BIG, NPO); int qm = BIG;
            for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; if (v < qm) qm = v; relax_row(row, EAP + (size_t)(a * NAO + q) * NPO, v, NPO); }
            if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T1 + ((size_t)a * NPO + y) * NPO, row, NPO); Q1[a * NPO + y] = qm; } else memcpy(S1 + a * NPO, row, NPO);
            for (int b = 0; b < 6; b++) { if (b == a) continue;            // exact ordered pair (a, b)
                memset(R2, BIG, NAO);
                for (int q = 0; q < NAO; q++) { int v = src[a * NAO + q]; if (v > CAPV) continue; relax_row(R2, EAA + (size_t)(a * NAO + q) * NAA + b * NAO, v, NAO); }
                memset(row, BIG, NPO); int qm2 = BIG;
                for (int q = 0; q < NAO; q++) { int v = R2[q]; if (v > CAPV) continue; if (v < qm2) qm2 = v; relax_row(row, EAP + (size_t)(b * NAO + q) * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(T2 + ((size_t)(a * 6 + b) * NPO + y) * NPO, row, NPO); Q2[(a * 6 + b) * NPO + y] = qm2; } else memcpy(S2 + (a * 6 + b) * NPO, row, NPO);
            } }
        memcpy(cur, src, NAA);                                          // identity-free chains (consecutive A trails distinct)
        for (int len = 1; len <= 6; len++) {
            if (len >= 3) { memset(row, BIG, NPO); int qm = BIG;
                for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; if (v < qm) qm = v; relax_row(row, EAP + (size_t)z * NPO, v, NPO); }
                if (ty >= 0) { memset(row + ty * NOP, BIG, NOP); memcpy(KL + ((size_t)(len - 3) * NPO + y) * NPO, row, NPO); QL[(len - 3) * NPO + y] = qm; } else memcpy(SL + (len - 3) * NPO, row, NPO); }
            if (len == 6) break;
            memset(nx, BIG, NAA);
            for (int z = 0; z < NAA; z++) { int v = cur[z]; if (v > CAPV) continue; relax_row(nx, EAA + (size_t)z * NAA, v, NAA); }   // same-trail block of EAA is BIG
            uint8_t *tt = cur; cur = nx; nx = tt;
        }
        free(src); free(cur); free(nx); free(row); free(R2);
    }
    for (int x = 0; x < NPO; x++) S0[x] = ocut[gpo(x)] == 2;
}
// ---------------------------------------------------------------- search
typedef struct { uint64_t key; uint8_t g[NOP]; int32_t bp[NOP]; uint8_t bo[NOP], bk[NOP], bd[NOP]; } Rec;
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
    Rec *r = &L->r[L->n]; L->ht[h] = L->n++; r->key = key; memset(r->g, BIG, NOP); for (int q = 0; q < NOP; q++) r->bp[q] = -2; return r;
}
static Rec *lfind(const Layer *L, uint64_t key) {
    uint64_t h = hsh(key) & (L->hcap - 1);
    while (L->ht[h] >= 0) { if (L->r[L->ht[h]].key == key) return &L->r[L->ht[h]]; h = (h + 1) & (L->hcap - 1); }
    return NULL;
}
static inline uint64_t skey(uint32_t S, int t, int M) { return (uint64_t)S | ((uint64_t)t << 24) | ((uint64_t)M << 29); }
static void put(Layer *L, uint32_t S, int t, int M, const uint8_t *w, int32_t pred, const uint8_t *po, int kind, int dat) {
    Rec *r = lget(L, skey(S, t, M));
    for (int q = 0; q < NOP; q++) if (w[q] < r->g[q]) { r->g[q] = w[q]; r->bp[q] = pred; r->bo[q] = po ? po[q] : 0; r->bk[q] = kind; r->bd[q] = dat; }
}
// w[x] = min_y g[y] + Tab[t*84 + y][u*84 + x] over live y; po = argmin; then prune with h
static int relax_state(const uint8_t *g, const int *live, int nl, const uint8_t *Tab, int t, int u, const uint8_t *h, uint8_t *w, uint8_t *po) {
    int any = 0;
    for (int x = 0; x < NOP; x++) { int m = BIG, am = 0;
        for (int i = 0; i < nl; i++) { int y = live[i]; int v = g[y] + Tab[(size_t)(t * NOP + y) * NPO + u * NOP + x]; if (v < m) { m = v; am = y; } }
        if (m + h[x] <= THR) { w[x] = (uint8_t)m; po[x] = (uint8_t)am; any = 1; } else { w[x] = BIG; po[x] = 0; } }
    return any;
}
// exact fixed-order value of a full trail order (min over all options)
static int fixed_order(const int *ord, int n) {
    static int cur[MAXO], nx[MAXO]; int t0 = ord[0];
    for (int q = 0; q < tcnt[t0]; q++) cur[q] = ocut[tofs[t0] + q] == 2;
    for (int i = 1; i < n; i++) { int a = ord[i - 1], b = ord[i];
        for (int q2 = 0; q2 < tcnt[b]; q2++) nx[q2] = 1 << 20;
        for (int q = 0; q < tcnt[a]; q++) { int v = cur[q]; const int8_t *er = e + (size_t)(tofs[a] + q) * NOPT + tofs[b];
            for (int q2 = 0; q2 < tcnt[b]; q2++) { int s = v + er[q2]; if (s < nx[q2]) nx[q2] = s; } }
        memcpy(cur, nx, sizeof(int) * tcnt[b]); }
    int m = 1 << 20; for (int q = 0; q < tcnt[ord[n - 1]]; q++) if (cur[q] < m) m = cur[q]; return m;
}
// segments: list of trails with flags; unordered segments (sets of A trails) are permuted exhaustively
typedef struct { int tr[6]; int n; int unordered; } Seg;
static int bestF, bestOrd[NTR];
static int collect = 0; static int (*good)[NTR] = NULL; static int *goodF = NULL; static long ngood = 0, goodcap = 0;
static void perm_eval(Seg *sg, int ns, int si, int *ord, int len) {
    if (si == ns) { int F = fixed_order(ord, len); if (F < bestF) { bestF = F; memcpy(bestOrd, ord, sizeof(int) * len); }
        if (collect && F <= THR) { if (ngood == goodcap) { goodcap = goodcap ? 2 * goodcap : 1024; good = realloc(good, sizeof(int[NTR]) * goodcap); goodF = realloc(goodF, sizeof(int) * goodcap); }
            memcpy(good[ngood], ord, sizeof(int) * NTR); goodF[ngood++] = F; }
        return; }
    Seg *s = &sg[si];
    if (!s->unordered || s->n <= 1) { for (int i = 0; i < s->n; i++) ord[len + i] = s->tr[i]; perm_eval(sg, ns, si + 1, ord, len + s->n); return; }
    int p[6]; for (int i = 0; i < s->n; i++) p[i] = i;
    // iterate all permutations (Heap's algorithm, iterative)
    int c[6] = {0}; int k = 0;
    for (int i = 0; i < s->n; i++) ord[len + i] = s->tr[p[i]];
    perm_eval(sg, ns, si + 1, ord, len + s->n);
    while (k < s->n) { if (c[k] < k) { int j = (k % 2 == 0) ? 0 : c[k]; int tmp = p[j]; p[j] = p[k]; p[k] = tmp;
            for (int i = 0; i < s->n; i++) ord[len + i] = s->tr[p[i]];
            perm_eval(sg, ns, si + 1, ord, len + s->n); c[k]++; k = 0; } else { c[k] = 0; k++; } }
}
// ---------------------------------------------------------------- complete enumeration (env CKB_ENUM)
// backward DFS over the kept records: a record-level path (phi trails, gap A sets / orders) is followed iff some
// option assignment has search cost <= THR (min prefix value g of the predecessor + exact suffix vector).
static Layer *ALL; static long en_pat = 0; static int en_best = 1 << 20;
static void en_emit(Seg *rev, int nrev) {
    Seg sg[64]; int nsg = 0; for (int i = nrev - 1; i >= 0; i--) sg[nsg++] = rev[i];
    int ord[NTR], tl = 0; for (int i = 0; i < nsg; i++) tl += sg[i].n; if (tl != NTR) { fprintf(stderr, "enum: bad length %d\n", tl); exit(17); }
    bestF = 1 << 20; perm_eval(sg, nsg, 0, ord, 0); en_pat++; if (bestF < en_best) en_best = bestF;
}
static void en_dfs(int k, const Rec *r, const int *s, Seg *rev, int nrev) {
    uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63;
    rev[nrev++] = (Seg){{phl[t]}, 1, 0};
    if (k == 1) { int a = __builtin_popcount(M); const uint8_t *tabs[2]; Seg segs[2]; int nt = 0;
        if (a == 0) { tabs[nt] = S0; segs[nt++] = (Seg){{0}, 0, 0}; }
        else if (a == 1) { tabs[nt] = S1 + __builtin_ctz(M) * NPO; segs[nt++] = (Seg){{Alist[__builtin_ctz(M)]}, 1, 0}; }
        else if (a == 2) { int i = __builtin_ctz(M), j = 31 - __builtin_clz(M);
            tabs[nt] = S2 + (i * 6 + j) * NPO; segs[nt++] = (Seg){{Alist[i], Alist[j]}, 2, 0}; tabs[nt] = S2 + (j * 6 + i) * NPO; segs[nt++] = (Seg){{Alist[j], Alist[i]}, 2, 0}; }
        else { tabs[nt] = SL + (a - 3) * NPO; Seg sgm = {{0}, 0, 1}; for (int i = 0; i < 6; i++) if (M >> i & 1) sgm.tr[sgm.n++] = Alist[i]; segs[nt++] = sgm; }
        for (int z = 0; z < nt; z++) { int ok = 0; for (int y = 0; y < NOP; y++) if (s[y] < BIG && tabs[z][t * NOP + y] + s[y] <= THR) ok = 1;
            if (!ok) continue; int nr = nrev; if (segs[z].n) rev[nr++] = segs[z]; en_emit(rev, nr); }
        return; }
    uint32_t Sp = S & ~(1u << t);
    for (int tp = 0; tp < NPH; tp++) { if (!(Sp >> tp & 1)) continue;
        for (int D = 0; D < 64; D++) { if (D & ~M) continue; const Rec *rp = lfind(&ALL[k - 1], skey(Sp, tp, M & ~D)); if (!rp) continue;
            int a = __builtin_popcount(D); const uint8_t *tabs[2]; Seg segs[2]; int nt = 0;
            if (a == 0) { tabs[nt] = EPP; segs[nt++] = (Seg){{0}, 0, 0}; }
            else if (a == 1) { tabs[nt] = T1 + (size_t)__builtin_ctz(D) * NPO * NPO; segs[nt++] = (Seg){{Alist[__builtin_ctz(D)]}, 1, 0}; }
            else if (a == 2) { int i = __builtin_ctz(D), j = 31 - __builtin_clz(D);
                tabs[nt] = T2 + (size_t)(i * 6 + j) * NPO * NPO; segs[nt++] = (Seg){{Alist[i], Alist[j]}, 2, 0}; tabs[nt] = T2 + (size_t)(j * 6 + i) * NPO * NPO; segs[nt++] = (Seg){{Alist[j], Alist[i]}, 2, 0}; }
            else { tabs[nt] = KL + (size_t)(a - 3) * NPO * NPO; Seg sgm = {{0}, 0, 1}; for (int i = 0; i < 6; i++) if (D >> i & 1) sgm.tr[sgm.n++] = Alist[i]; segs[nt++] = sgm; }
            for (int z = 0; z < nt; z++) { int sp[NOP]; int ok = 0;
                for (int y = 0; y < NOP; y++) { sp[y] = BIG; if (rp->g[y] >= BIG) continue; const uint8_t *row = tabs[z] + (size_t)(tp * NOP + y) * NPO + t * NOP;
                    for (int x = 0; x < NOP; x++) if (s[x] < BIG) { int v = row[x] + s[x]; if (v < sp[y]) sp[y] = v; }
                    if (sp[y] > BIG) sp[y] = BIG; if (rp->g[y] + sp[y] <= THR) ok = 1; }
                if (!ok) continue; int nr = nrev; if (segs[z].n) rev[nr++] = segs[z]; en_dfs(k - 1, rp, sp, rev, nr); } } }
}
// ---------------------------------------------------------------- trace of a given word (env CKB_TRACE: 30 lines "trail local_option")
static int tr_on = 0, tr_ord[NTR], tr_opt[NTR], tr_ppos[NPH + 1]; static int tr_G[NPH + 1], tr_g[NPH + 1], tr_found[NPH + 1]; static uint64_t tr_key[NPH + 1];
static void trace_check(int k, const Layer *L) {
    const Rec *r = lfind(L, tr_key[k]); tr_found[k] = r != NULL; tr_g[k] = r ? r->g[tr_opt[tr_ppos[k]] - tofs[tr_ord[tr_ppos[k]]]] : -1;
}
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage\n"); return 1; }
    const char *dir = argv[1], *hdir = argv[2]; THR = atoi(argv[3]); const char *outp = argv[4]; char p[2048];
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
    // query mode (cross-check with checker A): CKB_QUERY = file of (uint32 S, uint32 t) pairs -> CKB_QOUT = 7 x 84 bytes each
    const char *qf = getenv("CKB_QUERY");
    if (qf && *qf) { size_t sz; uint32_t *qq = mapf(qf, &sz); size_t nq = sz / 8; FILE *qo = fopen(getenv("CKB_QOUT"), "wb");
        for (size_t i = 0; i < nq; i++) { if (!hvec(qq[2 * i], (int)qq[2 * i + 1], hb)) { fprintf(stderr, "query miss\n"); return 15; } fwrite(hb, 1, sizeof hb, qo); }
        fclose(qo); fprintf(stderr, "answered %zu queries\n", nq); return 0; }
    // e blocks
    EPP = malloc((size_t)NPO * NPO); EPA = malloc((size_t)NPO * NAA); EAA = malloc((size_t)NAA * NAA); EAP = malloc((size_t)NAA * NPO);
    #pragma omp parallel for
    for (int y = 0; y < NPO; y++) { for (int x = 0; x < NPO; x++) EPP[(size_t)y * NPO + x] = eget(gpo(y), gpo(x)); for (int z = 0; z < NAA; z++) EPA[(size_t)y * NAA + z] = eget(gpo(y), gao(z)); }
    #pragma omp parallel for
    for (int z = 0; z < NAA; z++) { for (int z2 = 0; z2 < NAA; z2++) EAA[(size_t)z * NAA + z2] = eget(gao(z), gao(z2)); for (int x = 0; x < NPO; x++) EAP[(size_t)z * NPO + x] = eget(gao(z), gpo(x)); }
    chain_tables();
    fprintf(stderr, "chain tables %.1fs\n", omp_get_wtime() - T0);
    const char *trf = getenv("CKB_TRACE"); int tr_total = -1;
    if (trf && *trf) { FILE *tf = fopen(trf, "r"); for (int i = 0; i < NTR; i++) { int a, b; if (fscanf(tf, "%d %d", &a, &b) != 2) return 18; tr_ord[i] = a; tr_opt[i] = tofs[a] + b; } fclose(tf); tr_on = 1;
        int G = ocut[tr_opt[0]] == 2, k = 0; uint32_t S = 0; int M = 0;
        for (int i = 0; i < NTR; i++) { int tt = tr_ord[i];
            if (isA[tt]) M |= 1 << aidx[tt]; else { k++; S |= 1u << phidx[tt]; tr_ppos[k] = i; tr_G[k] = G; tr_key[k] = skey(S, phidx[tt], M); }   // M = A trails before this phi trail
            if (i + 1 < NTR) G += e[(size_t)tr_opt[i] * NOPT + tr_opt[i + 1]]; }
        tr_total = G;
        fprintf(stderr, "trace word: true F with given options %d\n", tr_total); }
    // ---------------------------------------------------------------- layer 1
    Layer cur; linit(&cur); uint8_t w[NOP];
    int nsub = 0; int subs[64]; for (int m = 0; m < 64; m++) subs[nsub++] = m;
    for (int t = 0; t < NPH; t++) {
        if (!hvec(1u << t, t, hb)) return 15;
        for (int m = 0; m < 64; m++) { int a = __builtin_popcount(m); const uint8_t *h = hb[6 - a];
            // candidate start chains with A set m
            for (int x = 0; x < NOP; x++) { int y = t * NOP + x, v = BIG;
                if (a == 0) v = S0[y];
                else if (a == 1) v = S1[__builtin_ctz(m) * NPO + y];
                else if (a == 2) { int i = __builtin_ctz(m), j = 31 - __builtin_clz(m); int v1 = S2[(i * 6 + j) * NPO + y], v2 = S2[(j * 6 + i) * NPO + y]; v = v1 < v2 ? v1 : v2; }
                else v = SL[(a - 3) * NPO + y];
                w[x] = v + h[x] <= THR ? v : BIG; }
            int any = 0; for (int x = 0; x < NOP; x++) any |= w[x] < BIG;
            if (!any) continue;
            int kind = a == 0 ? 4 : a == 1 ? 5 : a == 2 ? 6 : 7; int dat = m;
            if (a == 2) { int i = __builtin_ctz(m), j = 31 - __builtin_clz(m); dat = 0;
                // record which order realises the minimum per option: bd = 6*i+j or 6*j+i
                Rec *r = lget(&cur, skey(1u << t, t, m));
                for (int x = 0; x < NOP; x++) { int y = t * NOP + x; if (w[x] >= BIG || w[x] >= r->g[x]) continue;
                    int v1 = S2[(i * 6 + j) * NPO + y]; r->g[x] = w[x]; r->bp[x] = -1; r->bo[x] = 0; r->bk[x] = 6; r->bd[x] = v1 == w[x] ? i * 6 + j : j * 6 + i; }
                continue; }
            put(&cur, 1u << t, t, m, w, -1, NULL, kind, dat);
        } }
    (void)subs; (void)nsub;
    fprintf(stderr, "layer 1: %lld states\n", (long long)cur.n);
    if (tr_on) trace_check(1, &cur);
    Layer *all = malloc(sizeof(Layer) * (NPH + 1)); all[1] = cur;
    FILE *jo = fopen(outp, "w"); fprintf(jo, "{\n \"checker\": \"B-search\",\n \"THR\": %d,\n \"mutations\": %d,\n \"layers\": [{\"layer\": 1, \"states\": %lld}", THR, nmut, (long long)cur.n);
    long long ntr_total = 0;
    for (int k = 1; k < NPH; k++) {
        Layer nxt; linit(&nxt); Layer *L = &all[k]; long long ntr = 0;
        for (int64_t ri = 0; ri < L->n; ri++) {
            Rec *r = &L->r[ri]; uint32_t S = r->key & 0xFFFFFF; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63, c = __builtin_popcount(M);
            int live[NOP], nl = 0; uint8_t g[NOP]; memcpy(g, r->g, NOP); for (int q = 0; q < NOP; q++) if (g[q] < BIG) live[nl++] = q;
            if (!nl) continue;
            for (int u = 0; u < NPH; u++) { if (S >> u & 1) continue; uint32_t S2_ = S | 1u << u;
                if (!hvec(S2_, u, hb)) return 15;
                uint8_t po[NOP];
                for (int a = 0; a <= 6 - c; a++) { const uint8_t *h = hb[6 - c - a];
                    if (a == 0) { ntr++; if (relax_state(g, live, nl, EPP, t, u, h, w, po)) put(&nxt, S2_, u, M, w, (int32_t)ri, po, 0, 0); }
                    else if (a == 1) { for (int i = 0; i < 6; i++) { if (M >> i & 1) continue; ntr++;
                        if (relax_state(g, live, nl, T1 + (size_t)i * NPO * NPO, t, u, h, w, po)) put(&nxt, S2_, u, M | 1 << i, w, (int32_t)ri, po, 1, i); } }
                    else if (a == 2) { for (int i = 0; i < 6; i++) for (int j = 0; j < 6; j++) { if (i == j || (M >> i & 1) || (M >> j & 1)) continue; ntr++;
                        if (relax_state(g, live, nl, T2 + (size_t)(i * 6 + j) * NPO * NPO, t, u, h, w, po)) put(&nxt, S2_, u, M | 1 << i | 1 << j, w, (int32_t)ri, po, 2, i * 6 + j); } }
                    else { ntr++;
                        if (relax_state(g, live, nl, KL + (size_t)(a - 3) * NPO * NPO, t, u, h, w, po))
                            for (int U = 0; U < 64; U++) if (!(U & M) && __builtin_popcount(U) == a) put(&nxt, S2_, u, M | U, w, (int32_t)ri, po, 3, U); }
                } } }
        // drop states without any surviving option
        int64_t keep = 0; for (int64_t i = 0; i < nxt.n; i++) { int any = 0; for (int q = 0; q < NOP; q++) any |= nxt.r[i].g[q] < BIG; keep += any; }
        all[k + 1] = nxt; ntr_total += ntr; if (tr_on) trace_check(k + 1, &all[k + 1]);
        fprintf(stderr, "layer %d: %lld states (%lld nonempty), %lld transitions, %.1fs\n", k + 1, (long long)nxt.n, (long long)keep, ntr, omp_get_wtime() - T0);
        fprintf(jo, ", {\"layer\": %d, \"states\": %lld, \"transitions\": %lld}", k + 1, (long long)keep, ntr);
    }
    fprintf(jo, "],\n");
    // ---------------------------------------------------------------- final layer: end chains
    Layer *F = &all[NPH]; int best = 1 << 20; long nfin = 0, nsol = 0;
    typedef struct { int64_t ri; int q; int endkind; int enddat; int val; } Sol; int scap = 1 << 16; Sol *sols = malloc(sizeof(Sol) * scap);
    for (int64_t ri = 0; ri < F->n; ri++) { Rec *r = &F->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63; int R = 63 & ~M, rc = __builtin_popcount(R); int fin = 0;
        for (int q = 0; q < NOP; q++) { if (r->g[q] >= BIG) continue; int y = t * NOP + q, ev, ek, ed = 0;
            if (rc == 0) { ev = 0; ek = 0; }
            else if (rc == 1) { ev = Q1[__builtin_ctz(R) * NPO + y]; ek = 1; ed = __builtin_ctz(R); }
            else if (rc == 2) { int i = __builtin_ctz(R), j = 31 - __builtin_clz(R); int v1 = Q2[(i * 6 + j) * NPO + y], v2 = Q2[(j * 6 + i) * NPO + y]; ek = 2; if (v1 <= v2) { ev = v1; ed = i * 6 + j; } else { ev = v2; ed = j * 6 + i; } }
            else { ev = QL[(rc - 3) * NPO + y]; ek = 3; ed = R; }
            int tot = r->g[q] + ev; if (tot < best) best = tot;
            if (tot <= THR) { fin = 1; if (nsol < scap) sols[nsol] = (Sol){ri, q, ek, ed, tot}; nsol++; } }
        nfin += fin; }
    fprintf(stderr, "final: minimum %d, final states <= THR %ld, (state, option) solutions %ld\n", best, nfin, nsol);
    // ---------------------------------------------------------------- reconstruct and evaluate exactly
    int npat = 0, pcap = 4096; int (*pats)[64] = malloc(sizeof(int[64]) * pcap); int *patF = malloc(sizeof(int) * pcap); int (*patOrd)[NTR] = malloc(sizeof(int[NTR]) * pcap);
    long nexact = 0; int bestExact = 1 << 20;
    for (long s = 0; s < nsol && s < scap; s++) {
        Seg sg[64]; int nsg = 0; int phis[NPH]; int nphis = 0;
        // end chain
        Seg endseg = {{0}, 0, 0};
        if (sols[s].endkind == 1) { endseg.tr[0] = Alist[sols[s].enddat]; endseg.n = 1; }
        else if (sols[s].endkind == 2) { endseg.tr[0] = Alist[sols[s].enddat / 6]; endseg.tr[1] = Alist[sols[s].enddat % 6]; endseg.n = 2; }
        else if (sols[s].endkind == 3) { for (int i = 0; i < 6; i++) if (sols[s].enddat >> i & 1) endseg.tr[endseg.n++] = Alist[i]; endseg.unordered = 1; }
        Seg rev[64]; int nrev = 0; if (endseg.n) rev[nrev++] = endseg;
        int64_t ri = sols[s].ri; int q = sols[s].q, k = NPH;
        while (1) { Rec *r = &all[k].r[ri]; int t = (r->key >> 24) & 31; Seg ph = {{phl[t]}, 1, 0}; rev[nrev++] = ph; phis[nphis++] = t;
            int kind = r->bk[q], dat = r->bd[q]; Seg gp = {{0}, 0, 0};
            if (kind == 1 || kind == 5) { gp.tr[0] = Alist[kind == 1 ? dat : __builtin_ctz(dat)]; gp.n = 1; }
            else if (kind == 2 || kind == 6) { gp.tr[0] = Alist[dat / 6]; gp.tr[1] = Alist[dat % 6]; gp.n = 2; }
            else if (kind == 3 || kind == 7) { for (int i = 0; i < 6; i++) if (dat >> i & 1) gp.tr[gp.n++] = Alist[i]; gp.unordered = 1; }
            if (gp.n) rev[nrev++] = gp;
            if (r->bp[q] < 0) break;
            int64_t pr = r->bp[q]; q = r->bo[q]; ri = pr; k--; }
        for (int i = nrev - 1; i >= 0; i--) sg[nsg++] = rev[i];
        // pattern signature (for de-duplication): sequence of trails, unordered segments sorted
        int sig[64]; int ns2 = 0; for (int i = 0; i < nsg; i++) { sig[ns2++] = sg[i].unordered ? 100 + sg[i].n : sg[i].n; for (int j = 0; j < sg[i].n; j++) sig[ns2++] = sg[i].tr[j]; }
        while (ns2 < 64) sig[ns2++] = -1;
        int dupl = 0; for (int i = 0; i < npat; i++) if (!memcmp(pats[i], sig, sizeof sig)) { dupl = 1; break; }
        if (dupl || npat >= pcap) continue;
        int ord[NTR]; bestF = 1 << 20; perm_eval(sg, nsg, 0, ord, 0);
        int tl = 0; for (int i = 0; i < nsg; i++) tl += sg[i].n; if (tl != NTR) { fprintf(stderr, "bad length %d\n", tl); return 16; }
        memcpy(pats[npat], sig, sizeof sig); patF[npat] = bestF; memcpy(patOrd[npat], bestOrd, sizeof bestOrd); npat++;
        if (bestF <= THR) nexact++; if (bestF < bestExact) bestExact = bestF; (void)phis; (void)nphis;
    }
    if (tr_on) { int surv = 0; for (int k = 1; k <= NPH; k++) { if (!tr_found[k] || tr_g[k] > tr_G[k]) break; surv = k; }
        fprintf(jo, " \"trace\": {\"true_F\": %d, \"layers_survived\": %d, \"per_layer\": [", tr_total, surv);
        for (int k = 1; k <= NPH; k++) fprintf(jo, "%s[%d, %d, %d, %d]", k > 1 ? ", " : "", k, tr_found[k], tr_g[k], tr_G[k]);
        fprintf(jo, "]},\n"); fprintf(stderr, "trace: survived %d of %d layers\n", surv, NPH); }
    const char *enf = getenv("CKB_ENUM");
    if (enf && *enf) { ALL = all; collect = 1; Seg rev[64]; double te = omp_get_wtime();
        for (int64_t ri = 0; ri < F->n; ri++) { const Rec *r = &F->r[ri]; int t = (r->key >> 24) & 31, M = (r->key >> 29) & 63; int R = 63 & ~M, rc = __builtin_popcount(R);
            const uint8_t *tabs[2]; Seg segs[2]; int nt = 0; static const uint8_t zero[NPO];
            if (rc == 0) { tabs[nt] = zero; segs[nt++] = (Seg){{0}, 0, 0}; }
            else if (rc == 1) { tabs[nt] = Q1 + __builtin_ctz(R) * NPO; segs[nt++] = (Seg){{Alist[__builtin_ctz(R)]}, 1, 0}; }
            else if (rc == 2) { int i = __builtin_ctz(R), j = 31 - __builtin_clz(R);
                tabs[nt] = Q2 + (i * 6 + j) * NPO; segs[nt++] = (Seg){{Alist[i], Alist[j]}, 2, 0}; tabs[nt] = Q2 + (j * 6 + i) * NPO; segs[nt++] = (Seg){{Alist[j], Alist[i]}, 2, 0}; }
            else { tabs[nt] = QL + (rc - 3) * NPO; Seg sgm = {{0}, 0, 1}; for (int i = 0; i < 6; i++) if (R >> i & 1) sgm.tr[sgm.n++] = Alist[i]; segs[nt++] = sgm; }
            for (int z = 0; z < nt; z++) { int sv[NOP]; int ok = 0;
                for (int x = 0; x < NOP; x++) { sv[x] = BIG; if (r->g[x] >= BIG) continue; sv[x] = tabs[z][t * NOP + x]; if (r->g[x] + sv[x] <= THR) ok = 1; }
                if (!ok) continue; int nr = 0; if (segs[z].n) rev[nr++] = segs[z]; en_dfs(NPH, r, sv, rev, nr); } }
        // distinct orders with exact F <= THR
        long nd = 0; for (long i = 0; i < ngood; i++) { int dup = 0; for (long j = 0; j < i; j++) if (!memcmp(good[i], good[j], sizeof(int) * NTR)) { dup = 1; break; } if (!dup) { if (nd != i) { memcpy(good[nd], good[i], sizeof(int) * NTR); goodF[nd] = goodF[i]; } nd++; } }
        fprintf(jo, " \"enumeration\": {\"record_level_patterns\": %ld, \"min_exact_F_over_patterns\": %d, \"orders_with_exact_F_le_thr\": %ld, \"sec\": %.1f, \"orders\": [", en_pat, en_best < (1 << 20) ? en_best : -1, nd, omp_get_wtime() - te);
        for (long i = 0; i < nd; i++) { fprintf(jo, "%s\n  {\"F\": %d, \"order\": [", i ? "," : "", goodF[i]); for (int j = 0; j < NTR; j++) fprintf(jo, "%s%d", j ? ", " : "", good[i][j]); fprintf(jo, "]}"); }
        fprintf(jo, "]},\n"); collect = 0;
        fprintf(stderr, "enumeration: %ld record-level patterns, %ld distinct orders with exact F <= %d, min exact F %d\n", en_pat, nd, THR, en_best); }
    char bb[32], be[32]; if (best < (1 << 20)) snprintf(bb, sizeof bb, "%d", best); else strcpy(bb, "null"); if (bestExact < (1 << 20)) snprintf(be, sizeof be, "%d", bestExact); else strcpy(be, "null");
    fprintf(jo, " \"minimum_bound\": %s,\n \"final_states_le_thr\": %ld,\n \"solutions_le_thr\": %ld,\n \"distinct_patterns\": %d,\n \"patterns_with_exact_F_le_thr\": %ld,\n \"best_exact_F\": %s,\n \"H_lookup_misses\": %ld,\n \"transitions\": %lld,\n \"patterns\": [",
            bb, nfin, nsol, npat, nexact, be, hmiss, ntr_total);
    for (int i = 0; i < npat; i++) { fprintf(jo, "%s\n  {\"exact_F\": %d, \"order\": [", i ? "," : "", patF[i]); for (int j = 0; j < NTR; j++) fprintf(jo, "%s%d", j ? ", " : "", patOrd[i][j]); fprintf(jo, "]}"); }
    fprintf(jo, "\n ],\n \"sec\": %.1f\n}\n", omp_get_wtime() - T0); fclose(jo);
    printf("{\"checker\": \"B-search\", \"THR\": %d, \"minimum_bound\": %d, \"final_states_le_thr\": %ld, \"distinct_patterns\": %d, \"patterns_with_exact_F_le_thr\": %ld, \"best_exact_F\": %d, \"H_lookup_misses\": %ld}\n",
           THR, best < (1 << 20) ? best : -1, nfin, npat, nexact, bestExact < (1 << 20) ? bestExact : -1, hmiss);
    return 0;
}
