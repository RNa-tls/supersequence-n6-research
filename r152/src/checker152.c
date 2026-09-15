/* Round 152 -- an INDEPENDENT C checker for the capacity certificates.
 *
 * This is the SECOND checker.  It reads the same plain-text certificate bytes
 * as r152/src/checker152.py and establishes the same two facts for every cell:
 *
 *     lower   the stored witness replays legally to `cap` ports    cap(K) >= C
 *     upper   an exhaustive search for C+1 ports finds nothing     cap(K) <= C
 *
 * It shares NO code and NO data file with the production searcher
 * r147/src/l6_chain_capacity_147.c: the joint catalogue is rebuilt here from
 * string algebra, no UB table is read, and the only pruning values it ever
 * uses are the ones it has itself certified earlier in the same run, which is
 * sound by (P1) monotonicity (research/RR_L6_R147_SOUND_UB.md).
 *
 * FAIL-CLOSED.  Hitting the node cap prints UNKNOWN_CAP, never a pass.  Finding
 * a walk with C+1 ports prints DISAGREE.  A non-zero exit means "not certified".
 *
 * build: cc -O2 -o checker152.exe checker152.c
 * run:   ./checker152.exe <cert.txt> <node_cap>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define NP 720
#define NH 120
#define NQ 144

static char PERM[NP][7];
static int  HEXID[NP], ORBID[NP], PHASE[NP];
static int  FREE_T[NP], DA_T[NP], DB_T[NP], PAID_T[NP][5], NPAID[NP];
static int  HV_T[NP][NP], HV_C[NP][NP], NHV[NP];

static int permindex(const char *s) {          /* lexicographic rank */
    int lo = 0, hi = NP - 1;
    while (lo <= hi) { int m = (lo + hi) / 2, c = strcmp(PERM[m], s);
        if (!c) return m; if (c < 0) lo = m + 1; else hi = m - 1; }
    return -1;
}
static void build_perms(void) {
    char a[7] = "123456"; int n = 0;
    for (;;) {
        memcpy(PERM[n++], a, 7);
        int i = 4; while (i >= 0 && a[i] >= a[i + 1]) --i;
        if (i < 0) break;
        int j = 5; while (a[j] <= a[i]) --j;
        char t = a[i]; a[i] = a[j]; a[j] = t;
        for (int l = i + 1, r = 5; l < r; ++l, --r) { t = a[l]; a[l] = a[r]; a[r] = t; }
    }
    if (n != NP) { fprintf(stderr, "perm build\n"); exit(3); }
}
static void sigma(const char *s, char *o) { memcpy(o, s + 1, 5); o[5] = s[0]; o[6] = 0; }
static void tau(const char *s, char *o)   { memcpy(o, s + 1, 4); o[4] = s[0]; o[5] = s[5]; o[6] = 0; }
static void endw(const char *v, char *o)  { o[0] = v[5]; memcpy(o + 1, v, 5); o[6] = 0; }

static void classify(void (*f)(const char *, char *), int *out, int *ncls) {
    for (int i = 0; i < NP; ++i) out[i] = -1;
    int c = 0;
    for (int i = 0; i < NP; ++i) {
        if (out[i] >= 0) continue;
        int q = i; char b[7];
        while (out[q] < 0) { out[q] = c; f(PERM[q], b); q = permindex(b); }
        ++c;
    }
    *ncls = c;
}
static int gapof(const char *e, const char *t) {
    for (int k = 1; k <= 5; ++k) if (!strncmp(t, e + k, (size_t)(6 - k))) return k;
    return 6;
}
static int idx6(const char *w) {           /* w need not be NUL-terminated */
    char b[7]; memcpy(b, w, 6); b[6] = 0; return permindex(b);
}
static int isperm6(const char *w) {
    int m = 0; for (int i = 0; i < 6; ++i) m |= 1 << (w[i] - '1');
    return m == 0x3f;
}

static void build_catalogue(void) {
    char e[7], b[7], spell[13];
    for (int vi = 0; vi < NP; ++vi) {
        FREE_T[vi] = DA_T[vi] = DB_T[vi] = -1; NPAID[vi] = 0; NHV[vi] = 0;
        endw(PERM[vi], e);
        int ei = permindex(e);
        for (int ti = 0; ti < NP; ++ti) {
            const char *t = PERM[ti];
            int g = gapof(e, t);
            if (g >= 4) {
                if (ti != vi && ti != ei) { HV_T[vi][NHV[vi]] = ti; HV_C[vi][NHV[vi]++] = g - 3; }
                continue;
            }
            if (g < 2) continue;
            memcpy(spell, e, 6); memcpy(spell + 6, t + 6 - g, (size_t)g); spell[6 + g] = 0;
            int hid[4], nh = 0;
            for (int o = 1; o < g; ++o) if (isperm6(spell + o)) hid[nh++] = idx6(spell + o);
            if (g == 2) {
                if (nh == 0) FREE_T[vi] = ti;
                else if (nh == 1 && hid[0] == vi) DA_T[vi] = ti;
                continue;
            }
            if (nh == 2 && hid[0] == vi && HEXID[ti] == HEXID[vi]) { DB_T[vi] = ti; continue; }
            int k = -1;
            if (nh == 0) {
                int d0[3];
                for (int j = 0; j < 3; ++j) {
                    d0[j] = -1;
                    for (int q = 0; q < 3; ++q) if (e[q] == t[3 + j]) { d0[j] = q; break; }
                }
                int code = 100 * d0[0] + 10 * d0[1] + d0[2];
                if (code == 120 || code == 201 || code == 210) k = 0;
            } else if (nh == 1 && hid[0] == vi) {
                k = 3;
            } else if (nh == 1) {
                sigma(PERM[hid[0]], b);
                if (!strcmp(b, t)) k = 4;
            }
            if (k >= 0) { if (NPAID[vi] >= 5) { fprintf(stderr, "paid overflow\n"); exit(3); }
                          PAID_T[vi][NPAID[vi]++] = ti; }
        }
        if (FREE_T[vi] < 0 || DA_T[vi] < 0 || DB_T[vi] < 0 || NPAID[vi] != 5) {
            fprintf(stderr, "catalogue incomplete at %s\n", PERM[vi]); exit(3);
        }
    }
}

/* ------------------------------------------------------------- certificate */
#define MAXCELL 4096
typedef struct { int arg[6], cap, n, *w; } Cell;
static Cell CELLS[MAXCELL];
static int NCELL;

static void read_cert(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(3); }
    char line[64];
    if (!fgets(line, sizeof line, f) || strncmp(line, "L6-CAPCERT-2", 12)) {
        fprintf(stderr, "not an L6-CAPCERT-2 file\n"); exit(3);
    }
    rewind(f);
    char tok[64];
    int have = 0;
    while (fscanf(f, "%63s", tok) == 1) {
        if (tok[0] == '#') { int c; while ((c = fgetc(f)) != EOF && c != '\n') ; continue; }
        if (!strncmp(tok, "L6-CAPCERT", 10)) { have = 1; continue; }
        if (strcmp(tok, "cell")) { fprintf(stderr, "expected 'cell', saw %s\n", tok); exit(3); }
        if (NCELL >= MAXCELL) { fprintf(stderr, "too many cells\n"); exit(3); }
        Cell *c = &CELLS[NCELL++];
        for (int i = 0; i < 6; ++i) if (fscanf(f, "%d", &c->arg[i]) != 1) { fprintf(stderr, "bad cell\n"); exit(3); }
        if (fscanf(f, "%d %d", &c->cap, &c->n) != 2) { fprintf(stderr, "bad cap\n"); exit(3); }
        c->w = malloc(sizeof(int) * (size_t)(c->n > 0 ? c->n : 1));
        for (int i = 0; i < c->n; ++i) if (fscanf(f, "%d", &c->w[i]) != 1) { fprintf(stderr, "witness truncated\n"); exit(3); }
    }
    fclose(f);
    if (!have) { fprintf(stderr, "missing magic\n"); exit(3); }
}

/* ------------------------------------------------------------ the searcher */
static int CB, CD, CA, CBB, CE, CH;                 /* the cell being checked */
static int TARGET;
static uint64_t NODES, NODECAP; static int CAPPED, FOUND;
static unsigned char phm[NQ]; static int opened[NQ], nopened, deficit;
static unsigned char hexu[NH]; static int hexcount;

/* cells already certified IN THIS RUN, the only pruning values allowed */
static int CERT_ARG[MAXCELL][6], CERT_VAL[MAXCELL], NCERT;

static int ubound(int tok, int d, int a, int bb, int e, int h) {
    int best = 120 + a + bb + e;                    /* (P2), analytic */
    for (int i = 0; i < NCERT; ++i) {
        const int *k = CERT_ARG[i];
        if (k[0] >= tok && k[1] >= d && k[2] >= a && k[3] >= bb
            && k[4] >= e && k[5] >= h && CERT_VAL[i] < best) best = CERT_VAL[i];
    }
    return best;
}
static int pc5(unsigned x) { int c = 0; while (x) { x &= x - 1; ++c; } return c; }
static int feas(int tok, int skip) {
    int hist[6] = {0, 0, 0, 0, 0, 0};
    for (int i = 0; i < nopened; ++i) {
        int q = opened[i]; if (q == skip) continue;
        hist[5 - pc5(phm[q])]++;
    }
    int tot = 0, left = tok;
    for (int d = 4; d >= 1; --d) {
        int take = hist[d] < left ? hist[d] : left;
        left -= take; tot += (hist[d] - take) * d;
    }
    return tot <= CD;
}
static void rec(int cur, int corb, int ports, int tok, int au, int bu, int eu, int hu);

static void step(int t, int corb, int ports, int tok, int au, int bu, int eu,
                 int hu, int isdirty) {
    if (CAPPED || FOUND) return;
    int newhex = !hexu[HEXID[t]], spend_e = 0;
    if (!newhex && isdirty <= 0) { if (eu >= CE) return; spend_e = 1; }
    int q = ORBID[t];
    if (phm[q] >> PHASE[t] & 1) return;
    int fresh = (phm[q] == 0);
    if (isdirty == -1 && q != corb) return;
    int cost = (isdirty == -1 || fresh) ? 0 : 1;
    if (cost > tok) return;
    unsigned char old = phm[q];
    phm[q] = (unsigned char)(old | (1u << PHASE[t]));
    if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
    if (newhex) { hexu[HEXID[t]] = 1; ++hexcount; }
    rec(t, q, ports + 1, tok - cost, au + (isdirty == 1), bu + (isdirty == 2),
        eu + spend_e, hu);
    if (newhex) { hexu[HEXID[t]] = 0; --hexcount; }
    if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
    phm[q] = old;
}

static void rec(int cur, int corb, int ports, int tok, int au, int bu, int eu, int hu) {
    ++NODES;
    if (NODECAP && NODES > NODECAP) { CAPPED = 1; return; }
    if (ports >= TARGET && deficit <= CD) { FOUND = 1; return; }
    if (!feas(tok, corb)) return;
    int left = (CA - au) + (CBB - bu) + (CE - eu);
    int reach = ports + ubound(tok, CD - deficit + 4 + 5 * tok,
                               CA - au, CBB - bu, CE - eu, CH - hu) - 1;
    int reach2 = ports + (NH - hexcount) + left;
    if (reach2 < reach) reach = reach2;
    if (reach < TARGET) return;
    step(FREE_T[cur], corb, ports, tok, au, bu, eu, hu, -1);
    if (au < CA) step(DA_T[cur], corb, ports, tok, au, bu, eu, hu, 1);
    if (bu < CBB) step(DB_T[cur], corb, ports, tok, au, bu, eu, hu, 2);
    for (int i = 0; i < 5; ++i) step(PAID_T[cur][i], corb, ports, tok, au, bu, eu, hu, 0);
    for (int i = 0; i < NHV[cur]; ++i)
        if (hu + HV_C[cur][i] <= CH)
            step(HV_T[cur][i], corb, ports, tok, au, bu, eu, hu + HV_C[cur][i], 0);
}

static const char *search_cell(const Cell *c, int target) {
    CB = c->arg[0]; CD = c->arg[1]; CA = c->arg[2];
    CBB = c->arg[3]; CE = c->arg[4]; CH = c->arg[5];
    TARGET = target; NODES = 0; CAPPED = 0; FOUND = 0;
    memset(phm, 0, sizeof phm); memset(hexu, 0, sizeof hexu);
    nopened = 0; hexcount = 1; hexu[HEXID[0]] = 1;
    phm[ORBID[0]] = (unsigned char)(1u << PHASE[0]);
    opened[nopened++] = ORBID[0]; deficit = 4;
    rec(0, ORBID[0], 1, CB, 0, 0, 0, 0);
    if (FOUND) return "FOUND";
    if (CAPPED) return "CAP";
    return "EXHAUSTED";
}

/* --------------------------------------------------------------- the replay */
static int move_kind(int u, int t, int *cost) {   /* -1 none, 0 paid, 1 A, 2 B, 3 heavy, 4 free E */
    *cost = 0;
    if (FREE_T[u] == t) return 4;
    if (DA_T[u] == t) return 1;
    if (DB_T[u] == t) return 2;
    for (int i = 0; i < 5; ++i) if (PAID_T[u][i] == t) return 0;
    for (int i = 0; i < NHV[u]; ++i) if (HV_T[u][i] == t) { *cost = HV_C[u][i]; return 3; }
    return -1;
}
static const char *replay(const Cell *c) {
    static unsigned char ph[NQ]; static unsigned char hx[NH];
    memset(ph, 0, sizeof ph); memset(hx, 0, sizeof hx);
    if (c->n != c->cap) return "witness length != cap";
    int norb = 0, def = 4, tok = 0, au = 0, bu = 0, eu = 0, hu = 0;
    int v0 = c->w[0];
    if (v0 < 0 || v0 >= NP) return "port out of range";
    ph[ORBID[v0]] = (unsigned char)(1u << PHASE[v0]); ++norb;
    hx[HEXID[v0]] = 1;
    int corb = ORBID[v0];
    for (int i = 0; i + 1 < c->n; ++i) {
        int u = c->w[i], t = c->w[i + 1], cost;
        if (t < 0 || t >= NP) return "port out of range";
        int kind = move_kind(u, t, &cost);
        if (kind < 0) return "illegal move";
        int q = ORBID[t];
        if (ph[q] >> PHASE[t] & 1) return "phase reused";
        if (kind == 4 && q != corb) return "clean E left its orbit";
        int fresh = (ph[q] == 0), newhex = !hx[HEXID[t]];
        if (!newhex && kind != 1 && kind != 2) ++eu;
        if (kind == 1) ++au;
        if (kind == 2) ++bu;
        if (kind == 3) hu += cost;
        if (!(kind == 4 || fresh)) ++tok;
        ph[q] |= (unsigned char)(1u << PHASE[t]);
        if (fresh) ++norb;
        hx[HEXID[t]] = 1;
        def += fresh ? 4 : -1;
        corb = q;
    }
    if (tok > c->arg[0] || def > c->arg[1] || au > c->arg[2] || bu > c->arg[3]
        || eu > c->arg[4] || hu > c->arg[5]) return "budget exceeded";
    if (def != 5 * norb - c->n) return "deficit identity violated";
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s <cert.txt> [node_cap]\n", argv[0]); return 3; }
    NODECAP = argc > 2 ? strtoull(argv[2], NULL, 10) : 0;
    build_perms();
    int nhex, norb;
    classify(sigma, HEXID, &nhex);
    classify(tau, ORBID, &norb);
    if (nhex != NH || norb != NQ) { fprintf(stderr, "class counts %d %d\n", nhex, norb); return 3; }
    for (int q = 0; q < NQ; ++q) {
        int rep = -1;
        for (int i = 0; i < NP && rep < 0; ++i) if (ORBID[i] == q) rep = i;
        char b[7]; int x = rep;
        for (int k = 0; k < 5; ++k) { PHASE[x] = k; tau(PERM[x], b); x = permindex(b); }
    }
    build_catalogue();
    read_cert(argv[1]);

    uint64_t total = 0; int ok = 1, ncert = 0;
    printf("{\"checker\":\"C152\",\"cells\":%d,\"rows\":[\n", NCELL);
    for (int i = 0; i < NCELL; ++i) {
        Cell *c = &CELLS[i];
        clock_t t0 = clock();
        const char *status, *detail = "";
        const char *bad = replay(c);
        uint64_t nodes = 0;
        if (bad) { status = "WITNESS_BAD"; detail = bad; }
        else {
            const char *r = search_cell(c, c->cap + 1);
            nodes = NODES; total += nodes;
            if (!strcmp(r, "FOUND")) status = "DISAGREE";
            else if (!strcmp(r, "CAP")) status = "UNKNOWN_CAP";
            else {
                status = "EXACT_CERTIFIED";
                memcpy(CERT_ARG[NCERT], c->arg, sizeof c->arg);
                CERT_VAL[NCERT++] = c->cap; ++ncert;
            }
        }
        if (strcmp(status, "EXACT_CERTIFIED")) ok = 0;
        printf("%s{\"cell\":\"%d|%d|%d|%d|%d|%d\",\"cap\":%d,\"status\":\"%s\","
               "\"detail\":\"%s\",\"nodes\":%llu,\"seconds\":%.2f}",
               i ? ",\n" : "", c->arg[0], c->arg[1], c->arg[2], c->arg[3],
               c->arg[4], c->arg[5], c->cap, status, detail,
               (unsigned long long)nodes, (double)(clock() - t0) / CLOCKS_PER_SEC);
        fflush(stdout);
    }
    printf("\n],\"certified\":%d,\"total_nodes\":%llu,\"all_certified\":%s}\n",
           ncert, (unsigned long long)total, ok ? "true" : "false");
    return ok ? 0 : 1;
}
