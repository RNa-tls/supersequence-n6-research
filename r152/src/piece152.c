/* Round 152 -- producer and checker for the MARKED PIECE capacities C(b,d,mask).
 *
 * The chain capacities are not the only capacity table the L = 870/871 census
 * leans on.  Dropping the piece model leaves 52 rows at L = 871 and one at
 * L = 870 unclosed (r152/certs/piece_needed_152.json), so the piece table is
 * load-bearing too and needs the same treatment.
 *
 * DEFINITION.  A PIECE for (b, d) is a walk v_0 = 123456, v_1, ... over the
 * 720 words in which
 *   * every step is a clean E (= tau) or one of the five paid joints,
 *   * every word lands on a hexagon not used before (the piece is hex-simple),
 *   * no phase of an orbit is used twice,
 *   * a step that re-enters an already opened orbit costs one token, and a
 *     clean E never costs one; at most b tokens in all,
 *   * the deficit 5*(orbits opened) - (ports) is at most d.
 * A BLOCK is a maximal run of clean E steps.  With fp, lp in {0,1},
 *
 *     C(b, d, fp, lp) = max ports over such pieces whose FIRST block is
 *                       partial (< 5 ports) if fp = 1, and whose LAST block is
 *                       partial if lp = 1; a mask bit 0 constrains nothing.
 *                       -1 when no piece meets the constraint.
 *
 * Certificate format L6-PIECECERT-1, plain text:
 *     pcell <b> <d> <fp> <lp> <cap> <nports>
 *     <nports port indices>
 * cap = -1 carries no witness and claims the mask is unreachable, which the
 * checker establishes by exhausting the whole space for that mask.
 *
 * build: cc -O2 -o piece152.exe piece152.c
 * run:   ./piece152.exe check   <cert.txt> [node_cap]
 *        ./piece152.exe produce <claims.txt> <out.txt> [node_cap]
 *        claims.txt: one "<b> <d> <fp> <lp> <cap>" per line, in certification
 *        order.
 */
#define CHECKER152_NO_MAIN
#include "checker152.c"

/* ---------------------------------------------------------------- the bound */
#define PT 8
#define PD 64
static int PUB[PT][PD];
static void pub_init(void) {
    for (int t = 0; t < PT; ++t) for (int d = 0; d < PD; ++d) PUB[t][d] = 120;
}
static void pub_add(int b, int d, int val) {     /* a certified (b,d,0,0) */
    for (int t = 0; t <= b && t < PT; ++t)
        for (int dd = 0; dd <= d && dd < PD; ++dd)
            if (val < PUB[t][dd]) PUB[t][dd] = val;
}
static int pub(int tok, int d) {
    if (tok < 0) tok = 0;
    if (d < 0) d = 0;
    if (tok >= PT || d >= PD) {
        fprintf(stderr, "pub index out of range: %d %d\n", tok, d);
        exit(3);                                            /* fail closed */
    }
    return PUB[tok][d];
}

/* --------------------------------------------------------------- the search */
static int PB, PDMAX, PFP, PLP, PTARGET;
static int PTRAIL[900];
static int PWIT[900], PWITN;

static void prec(int cur, int corb, int ports, int tok, int firstlen,
                 int curlen, int nblk) {
    ++NODES;
    if (NODECAP && NODES > NODECAP) { CAPPED = 1; return; }
    if (deficit <= PDMAX && ports >= PTARGET) {
        int fl = (nblk > 1) ? firstlen : curlen;
        if ((!PFP || fl < 5) && (!PLP || curlen < 5)) {
            FOUND = 1; PWITN = ports;
            for (int i = 0; i < ports; ++i) PWIT[i] = PTRAIL[i];
            return;
        }
    }
    if (!feas(tok, corb)) return;                 /* DMAX is read by feas */
    int reach = ports + pub(tok, PDMAX - deficit + 4 + 5 * tok) - 1;
    int reach2 = ports + (NH - hexcount);          /* a piece is hex-simple */
    if (reach2 < reach) reach = reach2;
    if (reach < PTARGET) return;

    int t = FREE_T[cur];
    if (!hexu[HEXID[t]] && !(phm[corb] >> PHASE[t] & 1)) {
        phm[corb] |= (unsigned char)(1u << PHASE[t]);
        hexu[HEXID[t]] = 1; ++hexcount; --deficit;
        PTRAIL[ports] = t;
        prec(t, corb, ports + 1, tok, firstlen, curlen + 1, nblk);
        ++deficit; --hexcount; hexu[HEXID[t]] = 0;
        phm[corb] &= (unsigned char)~(1u << PHASE[t]);
    }
    for (int i = 0; i < 5 && !FOUND && !CAPPED; ++i) {
        t = PAID_T[cur][i];
        if (hexu[HEXID[t]]) continue;
        int q = ORBID[t];
        int fresh = (phm[q] == 0);
        if (!fresh) { if (phm[q] >> PHASE[t] & 1) continue; if (tok < 1) continue; }
        unsigned char old = phm[q];
        phm[q] = (unsigned char)(old | (1u << PHASE[t]));
        if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
        hexu[HEXID[t]] = 1; ++hexcount;
        PTRAIL[ports] = t;
        prec(t, q, ports + 1, tok - (fresh ? 0 : 1),
             (nblk > 1) ? firstlen : curlen, 1, nblk + 1);
        --hexcount; hexu[HEXID[t]] = 0;
        if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
        phm[q] = old;
    }
}

static const char *psearch(int b, int d, int fp, int lp, int target) {
    PB = b; PDMAX = d; CD = d; PFP = fp; PLP = lp; PTARGET = target;
    NODES = 0; CAPPED = 0; FOUND = 0; PWITN = 0;
    memset(phm, 0, sizeof phm); memset(hexu, 0, sizeof hexu);
    nopened = 0; hexcount = 1; hexu[HEXID[0]] = 1;
    phm[ORBID[0]] = (unsigned char)(1u << PHASE[0]);
    opened[nopened++] = ORBID[0]; deficit = 4;
    PTRAIL[0] = 0;
    prec(0, ORBID[0], 1, b, 0, 1, 1);
    if (FOUND) return "FOUND";
    if (CAPPED) return "CAP";
    return "EXHAUSTED";
}

/* --------------------------------------------------------------- the replay */
static const char *preplay(int b, int d, int fp, int lp, int cap,
                           const int *w, int n) {
    static unsigned char ph[NQ], hx[NH];
    memset(ph, 0, sizeof ph); memset(hx, 0, sizeof hx);
    if (n != cap) return "witness length != cap";
    if (n < 1 || w[0] != 0) return "the piece must start at 123456";
    ph[ORBID[0]] = (unsigned char)(1u << PHASE[0]);
    hx[HEXID[0]] = 1;
    int norb = 1, def = 4, tok = 0, corb = ORBID[0];
    int firstlen = 0, curlen = 1, nblk = 1;
    for (int i = 0; i + 1 < n; ++i) {
        int u = w[i], t = w[i + 1];
        if (t < 0 || t >= NP) return "port out of range";
        if (hx[HEXID[t]]) return "a piece may not revisit a hexagon";
        int q = ORBID[t];
        if (ph[q] >> PHASE[t] & 1) return "phase reused";
        if (t == FREE_T[u]) {
            if (q != corb) return "clean E left its orbit";
            ph[q] |= (unsigned char)(1u << PHASE[t]);
            def -= 1; ++curlen;
        } else {
            int ok = 0;
            for (int j = 0; j < 5; ++j) if (PAID_T[u][j] == t) ok = 1;
            if (!ok) return "step is neither a clean E nor a paid joint";
            int fresh = (ph[q] == 0);
            if (!fresh) ++tok;
            ph[q] |= (unsigned char)(1u << PHASE[t]);
            if (fresh) { ++norb; def += 4; } else def -= 1;
            firstlen = (nblk > 1) ? firstlen : curlen;
            curlen = 1; ++nblk;
            corb = q;
        }
        hx[HEXID[t]] = 1;
    }
    if (tok > b) return "token budget exceeded";
    if (def > d) return "deficit budget exceeded";
    if (def != 5 * norb - n) return "deficit identity violated";
    int fl = (nblk > 1) ? firstlen : curlen;
    if (fp && fl >= 5) return "the mask requires a partial FIRST block";
    if (lp && curlen >= 5) return "the mask requires a partial LAST block";
    return NULL;
}

/* ---------------------------------------------------------------- the cells */
#define MAXP 4096
typedef struct { int b, d, fp, lp, cap, n, *w; } PCell;
static PCell PC[MAXP];
static int NPC;

static void read_pcert(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(3); }
    char tok[64];
    int have = 0;
    while (fscanf(f, "%63s", tok) == 1) {
        if (tok[0] == '#') { int c; while ((c = fgetc(f)) != EOF && c != '\n') ; continue; }
        if (!strncmp(tok, "L6-PIECECERT", 12)) { have = 1; continue; }
        if (strcmp(tok, "pcell")) { fprintf(stderr, "expected 'pcell', saw %s\n", tok); exit(3); }
        if (NPC >= MAXP) { fprintf(stderr, "too many cells\n"); exit(3); }
        PCell *c = &PC[NPC++];
        if (fscanf(f, "%d %d %d %d %d %d", &c->b, &c->d, &c->fp, &c->lp,
                   &c->cap, &c->n) != 6) { fprintf(stderr, "bad pcell\n"); exit(3); }
        c->w = malloc(sizeof(int) * (size_t)(c->n > 0 ? c->n : 1));
        for (int i = 0; i < c->n; ++i)
            if (fscanf(f, "%d", &c->w[i]) != 1) { fprintf(stderr, "witness truncated\n"); exit(3); }
    }
    fclose(f);
    if (!have) { fprintf(stderr, "missing magic\n"); exit(3); }
}

/* Second-pass pruning, exactly as in r152/src/checker152.c: a cell that could
 * not be exhausted with the bounds available in the ascending pass is retried
 * with the bounds that pass PROVED, the cell itself excluded from its own
 * table.  The list is plain text, one "<b> <d> <cap00>" per line. */
static int EXT_B[MAXP], EXT_D[MAXP], EXT_V[MAXP], NEXT_;

static void read_pprune(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(3); }
    while (NEXT_ < MAXP &&
           fscanf(f, "%d %d %d", &EXT_B[NEXT_], &EXT_D[NEXT_], &EXT_V[NEXT_]) == 3)
        ++NEXT_;
    fclose(f);
    fprintf(stderr, "prune list: %d (b,d) cells from %s\n", NEXT_, path);
}

static void pub_rebuild_excluding(int sb, int sd) {
    pub_init();
    for (int i = 0; i < NEXT_; ++i) {
        if (EXT_B[i] == sb && EXT_D[i] == sd) continue;
        pub_add(EXT_B[i], EXT_D[i], EXT_V[i]);
    }
}

static int do_check(const char *path, const char *prune) {
    read_pcert(path);
    if (prune) read_pprune(prune);
    uint64_t total = 0;
    int ok = 1, ncert = 0;
    printf("{\"checker\":\"P152\",\"cells\":%d,\"rows\":[\n", NPC);
    for (int i = 0; i < NPC; ++i) {
        PCell *c = &PC[i];
        if (prune) pub_rebuild_excluding(c->b, c->d);
        clock_t t0 = clock();
        const char *status, *detail = "";
        uint64_t nodes = 0;
        if (c->cap < 0) {
            /* the claim is that the mask is unreachable: exhaust everything */
            const char *r = psearch(c->b, c->d, c->fp, c->lp, 1);
            nodes = NODES; total += nodes;
            if (!strcmp(r, "FOUND")) { status = "DISAGREE"; detail = "a piece with this mask exists"; }
            else if (!strcmp(r, "CAP")) status = "UNKNOWN_CAP";
            else status = "EXACT_CERTIFIED";
        } else {
            const char *bad = c->n ? preplay(c->b, c->d, c->fp, c->lp, c->cap,
                                             c->w, c->n) : NULL;
            if (bad) { status = "WITNESS_BAD"; detail = bad; }
            else {
                const char *r = psearch(c->b, c->d, c->fp, c->lp, c->cap + 1);
                nodes = NODES; total += nodes;
                if (!strcmp(r, "FOUND")) status = "DISAGREE";
                else if (!strcmp(r, "CAP")) status = "UNKNOWN_CAP";
                else status = c->n ? "EXACT_CERTIFIED" : "UPPER_CERTIFIED";
            }
        }
        if (!strcmp(status, "EXACT_CERTIFIED") || !strcmp(status, "UPPER_CERTIFIED")) {
            ++ncert;
            if (c->fp == 0 && c->lp == 0 && c->cap >= 0) pub_add(c->b, c->d, c->cap);
        } else ok = 0;
        printf("%s{\"cell\":\"%d|%d|%d%d\",\"b\":%d,\"d\":%d,\"fp\":%d,\"lp\":%d,"
               "\"cap\":%d,\"status\":\"%s\",\"detail\":\"%s\",\"nodes\":%llu,"
               "\"seconds\":%.2f}", i ? ",\n" : "", c->b, c->d, c->fp, c->lp,
               c->b, c->d, c->fp, c->lp, c->cap, status, detail,
               (unsigned long long)nodes, (double)(clock() - t0) / CLOCKS_PER_SEC);
        fflush(stdout);
    }
    printf("\n],\"certified\":%d,\"total_nodes\":%llu,\"all_certified\":%s}\n",
           ncert, (unsigned long long)total, ok ? "true" : "false");
    return ok ? 0 : 1;
}

static int do_produce(const char *claims, const char *out) {
    int b[MAXP], d[MAXP], fp[MAXP], lp[MAXP], cl[MAXP], n = 0;
    FILE *f = fopen(claims, "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", claims); return 3; }
    while (fscanf(f, "%d %d %d %d %d", &b[n], &d[n], &fp[n], &lp[n], &cl[n]) == 5)
        if (++n >= MAXP) { fprintf(stderr, "too many claims\n"); return 3; }
    fclose(f);
    for (int i = 0; i < n; ++i)                      /* heuristic prune only */
        if (fp[i] == 0 && lp[i] == 0 && cl[i] >= 0) pub_add(b[i], d[i], cl[i]);
    FILE *o = fopen(out, "w");
    if (!o) { fprintf(stderr, "cannot write %s\n", out); return 3; }
    fputs("L6-PIECECERT-1\n", o);
    fputs("# pcell <b> <d> <fp> <lp> <cap> <nports>, then the ports\n", o);
    fputs("# cap = -1 claims the mask is unreachable and carries no witness\n", o);
    int missing = 0;
    for (int i = 0; i < n; ++i) {
        int np = 0;
        if (cl[i] >= 0) {
            const char *r = psearch(b[i], d[i], fp[i], lp[i], cl[i]);
            if (!strcmp(r, "FOUND") && PWITN == cl[i]) np = PWITN;
            else { ++missing;
                fprintf(stderr, "no witness at the claim for %d|%d|%d%d "
                        "(claim %d, %s)\n", b[i], d[i], fp[i], lp[i], cl[i], r); }
        }
        fprintf(o, "pcell %d %d %d %d %d %d\n", b[i], d[i], fp[i], lp[i], cl[i], np);
        for (int j = 0; j < np; ++j) fprintf(o, "%s%d", j ? " " : "", PWIT[j]);
        fputc('\n', o);
        fflush(o);
        fprintf(stderr, "%4d/%4d %d|%d|%d%d cap=%d ports=%d\n", i + 1, n,
                b[i], d[i], fp[i], lp[i], cl[i], np);
    }
    fclose(o);
    fprintf(stderr, "cells=%d witnessed=%d upper_or_infeasible=%d\n",
            n, n - missing, missing);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s check <cert.txt> [node_cap] [prune.txt]\n"
                        "       %s produce <claims.txt> <out.txt> [node_cap]\n",
                argv[0], argv[0]);
        return 3;
    }
    common_setup();
    pub_init();
    if (!strcmp(argv[1], "check")) {
        NODECAP = argc > 3 ? strtoull(argv[3], NULL, 10) : 0;
        return do_check(argv[2], argc > 4 ? argv[4] : NULL);
    }
    if (!strcmp(argv[1], "produce")) {
        if (argc < 4) { fprintf(stderr, "produce needs an output path\n"); return 3; }
        NODECAP = argc > 4 ? strtoull(argv[4], NULL, 10) : 0;
        return do_produce(argv[2], argv[3]);
    }
    fprintf(stderr, "unknown mode %s\n", argv[1]);
    return 3;
}
