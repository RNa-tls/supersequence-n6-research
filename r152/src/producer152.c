/* Round 152 -- a fast, UNTRUSTED witness producer.
 *
 * It emits an L6-CAPCERT-2 file: for each cell, the claimed value and a walk
 * that attains it.  Nothing it writes is taken on faith -- r152/src/checker152.c
 * and r152/src/checker152.py each re-establish both directions from scratch.
 * It therefore prunes with whatever values it likes, including the claims it is
 * trying to witness; a bad prune can only make it fail to find a witness.
 *
 * build: cc -O2 -o producer152.exe producer152.c
 * run:   ./producer152.exe <claims.txt> <out.txt> [node_cap]
 *        claims.txt: one "<b> <d> <a> <bb> <e> <h> <cap>" per line, in the
 *        order the cells should be certified.
 */
#define CHECKER152_NO_MAIN
#include "checker152.c"

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s <claims.txt> <out.txt> [node_cap]\n", argv[0]); return 3; }
    NODECAP = argc > 3 ? strtoull(argv[3], NULL, 10) : 0;
    common_setup();

    int arg[8192][6], claim[8192], n = 0;
    FILE *f = fopen(argv[1], "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[1]); return 3; }
    while (fscanf(f, "%d %d %d %d %d %d %d", &arg[n][0], &arg[n][1], &arg[n][2],
                  &arg[n][3], &arg[n][4], &arg[n][5], &claim[n]) == 7) {
        if (++n >= 8192) { fprintf(stderr, "too many claims\n"); return 3; }
    }
    fclose(f);
    for (int i = 0; i < n; ++i) ub_add(arg[i], claim[i]);   /* heuristic only */

    FILE *o = fopen(argv[2], "w");
    if (!o) { fprintf(stderr, "cannot write %s\n", argv[2]); return 3; }
    fputs("L6-CAPCERT-2\n", o);
    fputs("# produced by r152/src/producer152.c -- UNTRUSTED, see the checkers\n", o);
    fputs("# cell <b> <d> <a> <bb> <e> <h> <cap> <nports>, then the ports\n", o);
    fputs("# port index = rank in the lexicographic list of the 720\n", o);
    fputs("# permutations of \"123456\"\n", o);

    Cell c;
    int missing = 0;
    for (int i = 0; i < n; ++i) {
        memcpy(c.arg, arg[i], sizeof c.arg);
        /* One attempt only, at the claimed value.  Walking DOWN would cost a
         * fresh exhaustive search per step and tell us nothing the checker
         * cannot work out for itself, so a miss just leaves the cell without a
         * witness and the checker proves the upper bound alone. */
        int target = claim[i], got = -1;
        static int w[900];
        c.cap = target;
        const char *r = search_cell(&c, target);
        if (!strcmp(r, "FOUND")) {
            got = target;
            for (int j = 0; j < target; ++j) w[j] = TRAIL[j];
        } else if (!strcmp(r, "EXHAUSTED")) {
            fprintf(stderr, "CLAIM NOT ATTAINED %d|%d|%d|%d|%d|%d claim=%d "
                    "(no walk that long exists)\n", arg[i][0], arg[i][1],
                    arg[i][2], arg[i][3], arg[i][4], arg[i][5], claim[i]);
        }
        /* No witness found inside the node cap: still emit the cell with an
         * EMPTY witness.  The checker then proves only the UPPER bound, which
         * is the direction the row census actually consumes. */
        int np = (got == claim[i]) ? got : 0;
        if (np == 0) { ++missing;
            fprintf(stderr, "no witness at the claim for %d|%d|%d|%d|%d|%d "
                    "(claim %d, best found %d) -- upper only\n",
                    arg[i][0], arg[i][1], arg[i][2], arg[i][3], arg[i][4],
                    arg[i][5], claim[i], got); }
        (void)r;
        fprintf(o, "cell %d %d %d %d %d %d %d %d\n", arg[i][0], arg[i][1],
                arg[i][2], arg[i][3], arg[i][4], arg[i][5], claim[i], np);
        for (int j = 0; j < np; ++j) fprintf(o, "%s%d", j ? " " : "", w[j]);
        fputc('\n', o);
        fflush(o);
        fprintf(stderr, "%4d/%4d %d|%d|%d|%d|%d|%d cap=%d\n", i + 1, n,
                arg[i][0], arg[i][1], arg[i][2], arg[i][3], arg[i][4],
                arg[i][5], got);
    }
    fclose(o);
    fprintf(stderr, "cells=%d witnessed=%d upper_only=%d\n", n, n - missing, missing);
    return 0;
}
