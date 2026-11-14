/* Round Y -- heuristic (NOT a proof) search for long efficient exact weight-3 chains, to see how the best attainable
   deficit grows with the number of pieces beyond the kept-chain census (kept chains end by ~400 pieces).
   Model: that of rX/csrc/dsearch_dump.c (block = rotation class of its entry, exit = last digit to the front, doors,
   the five seam words y4..y8 + pi(y1 y2 y3), all classes distinct, first entry 12345678).
   Beam search: K states; each state is extended by every (seam word, piece length) that is legal; the new states are
   ranked by the score  A r - B d  (+ a tiny random tie-break) and the best K are kept.  For every r the largest value
   17 r - 38 d (line 2) and 4 r - 9 d (line 1) seen at r pieces is reported, with the deficit d.
   usage: beam_long K A B MAXR SEED */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef unsigned int u32; typedef uint64_t u64;
#define K8 8
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static int cmap[1 << 21];
static inline u32 code(u32 c) { while ((c >> 28) != K8) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
static int cidx(u32 c) { return cmap[code(c)]; }
#define NW 79                                   /* 5040 bits */
typedef struct { u64 used[NW]; u32 y; int r, d; double sc; } st_t;
static u64 rng = 88172645463325252ull;
static inline double rnd(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (rng >> 11) * (1.0 / 9007199254740992.0); }
static int A, B;
static int cmpst(const void *a, const void *b) { double x = ((const st_t *)a)->sc, y = ((const st_t *)b)->sc; return x < y ? 1 : x > y ? -1 : 0; }
int main(int argc, char **argv) {
    int K = atoi(argv[1]); A = atoi(argv[2]); B = atoi(argv[3]); int MAXR = atoi(argv[4]); rng ^= (u64)atoll(argv[5]) * 2654435761ull;
    /* enumerate the 5040 classes: words with 8 first */
    memset(cmap, 0xff, sizeof cmap); int n = 0;
    { int p[7] = {1, 2, 3, 4, 5, 6, 7};
      for (;;) { u32 w = 8; for (int i = 0; i < 7; i++) w = w << 4 | p[i]; cmap[code(w)] = n++;
        int i = 5; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 6; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
        for (int a = i + 1, b = 6; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } } }
    if (n != 5040) return 2;
    st_t *cur = calloc(K, sizeof(st_t)), *nxt = malloc(sizeof(st_t) * (size_t)K * 35); int nc = 0;
    long best2[1024], best1[1024]; int bd2[1024]; for (int i = 0; i < 1024; i++) { best2[i] = -1000000; best1[i] = -1000000; bd2[i] = -1; }
    /* initial: first piece from entry 12345678, every length 1..7 */
    { u32 D = 0x12345678u; st_t s; memset(&s, 0, sizeof s);
      for (int len = 1; len <= 7; len++) { int ci = cidx(D); if (s.used[ci >> 6] >> (ci & 63) & 1) break; s.used[ci >> 6] |= 1ull << (ci & 63);
          u32 x = exc(D); st_t t = s; t.y = x; t.r = 1; t.d = 7 - len; t.sc = A * 1.0 - B * t.d + rnd() * 1e-3; cur[nc++] = t; D = door(x); } }
    for (int r = 1; r < MAXR && nc > 0; r++) {
        int nn = 0;
        for (int q = 0; q < nc; q++) {
            st_t *s = &cur[q]; u32 y = s->y;
            long v2 = 17L * s->r - 38L * s->d, v1 = 4L * s->r - 9L * s->d;
            if (v2 > best2[s->r]) { best2[s->r] = v2; bd2[s->r] = s->d; } if (v1 > best1[s->r]) best1[s->r] = v1;
            u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
            u32 five[5] = {base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
            for (int i = 0; i < 5; i++) {
                u32 D = five[i]; st_t t; memcpy(t.used, s->used, sizeof t.used);
                for (int len = 1; len <= 7; len++) {
                    int ci = cidx(D); if (t.used[ci >> 6] >> (ci & 63) & 1) break; t.used[ci >> 6] |= 1ull << (ci & 63);
                    u32 x = exc(D); st_t *o = &nxt[nn++]; memcpy(o->used, t.used, sizeof t.used); o->y = x; o->r = s->r + 1; o->d = s->d + 7 - len;
                    o->sc = (double)A * o->r - (double)B * o->d + rnd() * 1e-3; D = door(x);
                }
            }
        }
        if (nn == 0) break;
        if (nn > K) { qsort(nxt, nn, sizeof(st_t), cmpst); nn = K; }
        memcpy(cur, nxt, sizeof(st_t) * nn); nc = nn;
    }
    for (int q = 0; q < nc; q++) { st_t *s = &cur[q]; long v2 = 17L * s->r - 38L * s->d, v1 = 4L * s->r - 9L * s->d; if (v2 > best2[s->r]) { best2[s->r] = v2; bd2[s->r] = s->d; } if (v1 > best1[s->r]) best1[s->r] = v1; }
    printf("# beam K=%d score=%d r - %d d\n# r best_v2 deficit_at_best_v2 best_v1\n", K, A, B);
    for (int r = 1; r < 1024; r++) if (bd2[r] >= 0) printf("%d %ld %d %ld\n", r, best2[r], bd2[r], best1[r]);
    return 0;
}
