/* Round 152 -- producer of EXPLICIT EXHAUSTION TREES (format L6-EXTREE-1).
 *
 * The upper-bound direction cap(K) <= C is a complete case analysis, and this
 * writes that case analysis down instead of asking a reader to rerun a search.
 * The file is a preorder token stream, one token per node of the tree:
 *
 *     N<k>   an internal node whose children are EXACTLY the k legal moves
 *            from its state, in the catalogue's canonical order
 *     L      a leaf, justified by one of three PROVED facts (the checker works
 *            out which, it is not told):
 *              (b) ports + (120 - |hexagons used|) + (a+bb+e left) < C+1
 *              (f) the feasibility lemma already excludes the continuation
 *              (p) the (P1) monotone bound from a cell certified EARLIER in
 *                  this same file
 *
 * A reader verifies it with r152/src/extree152.py, which performs NO search:
 * it recomputes the legal moves at each node, insists the file lists all of
 * them, and checks each leaf's justification.
 *
 * build: cc -O2 -o extree152.exe extree152.c
 * run:   ./extree152.exe <cap_cert.txt> <out.extree> [node_cap]
 */
#define CHECKER152_NO_MAIN
#include "checker152.c"

static FILE *OUT;
static uint64_t TNODES;
static int ECAP;                     /* the claimed cap of the current cell */

/* the same legality filter the checker will apply, in the same order */
static int legal_moves(int cur, int corb, int tok, int au, int bu, int eu,
                       int hu, int *tgt, int *knd, int *cst) {
    int n = 0;
    static int cand[NP + 16], kind[NP + 16], cost[NP + 16];
    cand[0] = FREE_T[cur]; kind[0] = 4; cost[0] = 0;
    cand[1] = DA_T[cur];   kind[1] = 1; cost[1] = 0;
    cand[2] = DB_T[cur];   kind[2] = 2; cost[2] = 0;
    int m = 3;
    for (int i = 0; i < 5; ++i) { cand[m] = PAID_T[cur][i]; kind[m] = 0; cost[m] = 0; ++m; }
    for (int i = 0; i < NHV[cur]; ++i) {
        cand[m] = HV_T[cur][i]; kind[m] = 3; cost[m] = HV_C[cur][i]; ++m;
        if (m >= NP + 16) { fprintf(stderr, "move overflow\n"); exit(3); }
    }
    for (int i = 0; i < m; ++i) {
        int t = cand[i], k = kind[i], c = cost[i];
        if (k == 1 && au >= CA) continue;
        if (k == 2 && bu >= CBB) continue;
        if (k == 3 && hu + c > CH) continue;
        int q = ORBID[t];
        if (phm[q] >> PHASE[t] & 1) continue;
        if (k == 4 && q != corb) continue;
        int newhex = !hexu[HEXID[t]];
        if (!newhex && k != 1 && k != 2 && eu >= CE) continue;
        int fresh = (phm[q] == 0);
        int tc = (k == 4 || fresh) ? 0 : 1;
        if (tc > tok) continue;
        tgt[n] = t; knd[n] = k; cst[n] = c; ++n;
    }
    return n;
}

static int leaf_reason(int corb, int ports, int tok, int au, int bu, int eu, int hu) {
    if (ports + (NH - hexcount) + (CA - au) + (CBB - bu) + (CE - eu) < ECAP + 1)
        return 'b';
    if (!feas(tok, corb)) return 'f';
    if (ports + ubound(tok, CD - deficit + 4 + 5 * tok, CA - au, CBB - bu,
                       CE - eu, CH - hu) - 1 < ECAP + 1)
        return 'p';
    return 0;
}

static void emit(int cur, int corb, int ports, int tok, int au, int bu, int eu, int hu) {
    ++TNODES;
    if (NODECAP && TNODES > NODECAP) { CAPPED = 1; return; }
    if (ports >= ECAP + 1 && deficit <= CD) { FOUND = 1; return; }
    if (leaf_reason(corb, ports, tok, au, bu, eu, hu)) { fputs("L ", OUT); return; }
    int *tgt = malloc(sizeof(int) * 3 * (NP + 16));
    int *knd = tgt + (NP + 16), *cst = knd + (NP + 16);
    if (!tgt) { fprintf(stderr, "alloc\n"); exit(3); }
    int n = legal_moves(cur, corb, tok, au, bu, eu, hu, tgt, knd, cst);
    fprintf(OUT, "N%d ", n);
    for (int i = 0; i < n && !FOUND && !CAPPED; ++i) {
        int t = tgt[i], k = knd[i], c = cst[i], q = ORBID[t];
        int fresh = (phm[q] == 0), newhex = !hexu[HEXID[t]];
        int spend_e = (!newhex && k != 1 && k != 2) ? 1 : 0;
        int tc = (k == 4 || fresh) ? 0 : 1;
        unsigned char old = phm[q];
        phm[q] = (unsigned char)(old | (1u << PHASE[t]));
        if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
        if (newhex) { hexu[HEXID[t]] = 1; ++hexcount; }
        emit(t, q, ports + 1, tok - tc, au + (k == 1), bu + (k == 2),
             eu + spend_e, hu + (k == 3 ? c : 0));
        if (newhex) { hexu[HEXID[t]] = 0; --hexcount; }
        if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
        phm[q] = old;
    }
    free(tgt);
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s <cap_cert.txt> <out.extree> [node_cap]\n", argv[0]); return 3; }
    NODECAP = argc > 3 ? strtoull(argv[3], NULL, 10) : 0;
    common_setup();
    read_cert(argv[1]);
    OUT = fopen(argv[2], "w");
    if (!OUT) { fprintf(stderr, "cannot write %s\n", argv[2]); return 3; }
    fputs("L6-EXTREE-1\n", OUT);
    fputs("# preorder: N<k> = internal with exactly k legal children,\n", OUT);
    fputs("# L = leaf justified by (b), (f) or (p); see extree152.py\n", OUT);
    const int bad = 0;
    for (int i = 0; i < NCELL; ++i) {
        Cell *c = &CELLS[i];
        CB = c->arg[0]; CD = c->arg[1]; CA = c->arg[2];
        CBB = c->arg[3]; CE = c->arg[4]; CH = c->arg[5];
        ECAP = c->cap;
        TNODES = 0; CAPPED = 0; FOUND = 0;
        memset(phm, 0, sizeof phm); memset(hexu, 0, sizeof hexu);
        nopened = 0; hexcount = 1; hexu[HEXID[0]] = 1;
        phm[ORBID[0]] = (unsigned char)(1u << PHASE[0]);
        opened[nopened++] = ORBID[0]; deficit = 4;
        fprintf(OUT, "\ntree %d %d %d %d %d %d %d\n", c->arg[0], c->arg[1],
                c->arg[2], c->arg[3], c->arg[4], c->arg[5], c->cap);
        emit(0, ORBID[0], 1, CB, 0, 0, 0, 0);
        fputc('\n', OUT);
        if (FOUND || CAPPED) {
            /* The stream for this cell is truncated, so the whole file is
             * unusable.  Say so and stop rather than leave a file that looks
             * complete. */
            fprintf(stderr, "cell %d|%d|%d|%d|%d|%d: %s -- aborting, %s is "
                    "incomplete\n", c->arg[0], c->arg[1], c->arg[2], c->arg[3],
                    c->arg[4], c->arg[5], FOUND ? "DISAGREE" : "node cap",
                    argv[2]);
            fclose(OUT);
            return 1;
        }
        ub_add(c->arg, c->cap);
        fprintf(stderr, "%4d/%4d %d|%d|%d|%d|%d|%d cap=%d nodes=%llu\n", i + 1,
                NCELL, c->arg[0], c->arg[1], c->arg[2], c->arg[3], c->arg[4],
                c->arg[5], c->cap, (unsigned long long)TNODES);
    }
    fclose(OUT);
    fprintf(stderr, "cells=%d trees_written=%d skipped=%d\n", NCELL, NCELL - bad, bad);
    return bad ? 1 : 0;
}
