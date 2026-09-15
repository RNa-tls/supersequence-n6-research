/* Round 153 -- INDEPENDENT enumeration of the equality witnesses.
 *
 * WHAT IS ENUMERATED.  For a cell K = (b, d, a, bb, e, h) and a target T this
 * lists EVERY walk of the round-152 transition system that starts at 123456,
 * respects all six budgets, has exactly T ports and ends with deficit <= d.
 *
 * Round 148 recorded a witness only when the deficit was EXACTLY d.  This
 * enumerator is deliberately more inclusive -- deficit <= d -- so that a
 * realisation with a smaller deficit cannot slip through unlisted.  The
 * deficit of each witness is reported, so the two conventions can be compared.
 *
 * WHY STOPPING AT DEPTH T IS COMPLETE.  Round 152 certified cap(K) = T, so no
 * walk has more than T ports at deficit <= d; a longer walk can therefore never
 * become a witness.  That certified value is the ONLY round-152 input used
 * here (Phase 9: do not recompute the capacity tables).
 *
 * PRUNING.  Two routes:
 *   --no-table   only the proved analytic reach bound (P2) and the round-150
 *                feasibility lemma.  Nothing else.
 *   --table F    additionally the (P1) monotone bound, taken from a list of
 *                ROUND-152 CERTIFIED values (same format as the checker's
 *                prune list: "<b> <d> <a> <bb> <e> <h> <cap>" per line).
 * The two routes must produce the same witness set.
 *
 * build: cc -O2 -o eqwit153.exe eqwit153.c
 * run:   ./eqwit153.exe <b> <d> <a> <bb> <e> <h> <target> <out.jsonl>
 *                       [--table <prune.txt> | --no-table] [node_cap]
 */
#define CHECKER152_NO_MAIN
#include "checker152.c"

static FILE *OUT;
static uint64_t WITCOUNT;
static int ETARGET, USE_TABLE;

static void erec(int cur, int corb, int ports, int tok, int au, int bu,
                 int eu, int hu) {
    ++NODES;
    if (NODECAP && NODES > NODECAP) { CAPPED = 1; return; }
    if (ports == ETARGET) {
        if (deficit <= CD) {
            ++WITCOUNT;
            fprintf(OUT, "{\"deficit\":%d,\"ports\":[", deficit);
            for (int i = 0; i < ports; ++i)
                fprintf(OUT, "%s%d", i ? "," : "", TRAIL[i]);
            fputs("]}\n", OUT);
            if (ferror(OUT)) { fprintf(stderr, "witness write\n"); exit(3); }
        }
        return;                       /* cap(K) = T: nothing longer can qualify */
    }
    if (!feas(tok, corb)) return;
    int reach = ports + (NH - hexcount) + (CA - au) + (CBB - bu) + (CE - eu);
    if (USE_TABLE) {
        int r2 = ports + ubound(tok, CD - deficit + 4 + 5 * tok, CA - au,
                                CBB - bu, CE - eu, CH - hu) - 1;
        if (r2 < reach) reach = r2;
    }
    if (reach < ETARGET) return;

    /* clean E */
    int t = FREE_T[cur];
    {
        int q = ORBID[t];
        if (q == corb && !(phm[q] >> PHASE[t] & 1)) {
            int newhex = !hexu[HEXID[t]];
            if (newhex || CE > eu) {
                int spend = newhex ? 0 : 1;      /* clean E is not dirty */
                unsigned char old = phm[q];
                phm[q] = (unsigned char)(old | (1u << PHASE[t]));
                deficit -= 1;
                if (newhex) { hexu[HEXID[t]] = 1; ++hexcount; }
                TRAIL[ports] = t;
                erec(t, q, ports + 1, tok, au, bu, eu + spend, hu);
                if (newhex) { hexu[HEXID[t]] = 0; --hexcount; }
                deficit += 1;
                phm[q] = old;
            }
        }
    }
    /* dirty A, dirty B, five paid, heavy */
    for (int kind = 0; kind < 4; ++kind) {
        int lo = 0, hi = 0;
        if (kind == 0) { if (au >= CA) continue; hi = 1; }
        if (kind == 1) { if (bu >= CBB) continue; hi = 1; }
        if (kind == 2) hi = 5;
        if (kind == 3) hi = NHV[cur];
        for (int i = lo; i < hi; ++i) {
            int tt, cost = 0, isdirty;
            if (kind == 0) { tt = DA_T[cur]; isdirty = 1; }
            else if (kind == 1) { tt = DB_T[cur]; isdirty = 2; }
            else if (kind == 2) { tt = PAID_T[cur][i]; isdirty = 0; }
            else { tt = HV_T[cur][i]; cost = HV_C[cur][i]; isdirty = 0;
                   if (hu + cost > CH) continue; }
            int q = ORBID[tt];
            if (phm[q] >> PHASE[tt] & 1) continue;
            int newhex = !hexu[HEXID[tt]], spend = 0;
            if (!newhex && isdirty == 0) { if (eu >= CE) continue; spend = 1; }
            int fresh = (phm[q] == 0);
            int tc = fresh ? 0 : 1;
            if (tc > tok) continue;
            unsigned char old = phm[q];
            phm[q] = (unsigned char)(old | (1u << PHASE[tt]));
            if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
            if (newhex) { hexu[HEXID[tt]] = 1; ++hexcount; }
            TRAIL[ports] = tt;
            erec(tt, q, ports + 1, tok - tc, au + (isdirty == 1),
                 bu + (isdirty == 2), eu + spend, hu + cost);
            if (newhex) { hexu[HEXID[tt]] = 0; --hexcount; }
            if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
            phm[q] = old;
        }
    }
}

int main(int argc, char **argv) {
    if (argc < 9) {
        fprintf(stderr, "usage: %s <b> <d> <a> <bb> <e> <h> <target> <out.jsonl>"
                        " [--table <prune.txt>|--no-table] [node_cap]\n", argv[0]);
        return 3;
    }
    CB = atoi(argv[1]); CD = atoi(argv[2]); CA = atoi(argv[3]);
    CBB = atoi(argv[4]); CE = atoi(argv[5]); CH = atoi(argv[6]);
    ETARGET = atoi(argv[7]);
    common_setup();
    int ai = 9;
    const char *prune = NULL;
    if (argc > ai && !strcmp(argv[ai], "--table")) { prune = argv[ai + 1]; ai += 2; }
    else if (argc > ai && !strcmp(argv[ai], "--no-table")) { ++ai; }
    NODECAP = argc > ai ? strtoull(argv[ai], NULL, 10) : 0;
    if (prune) {
        read_prune(prune);
        int self[6] = {CB, CD, CA, CBB, CE, CH};
        (void)self;
        ub_rebuild_excluding((int[6]){-1, -1, -1, -1, -1, -1});  /* keep all */
        USE_TABLE = 1;
    }
    OUT = fopen(argv[8], "w");
    if (!OUT) { fprintf(stderr, "cannot write %s\n", argv[8]); return 3; }
    NODES = 0; CAPPED = 0; WITCOUNT = 0;
    memset(phm, 0, sizeof phm); memset(hexu, 0, sizeof hexu);
    nopened = 0; hexcount = 1; hexu[HEXID[0]] = 1;
    phm[ORBID[0]] = (unsigned char)(1u << PHASE[0]);
    opened[nopened++] = ORBID[0]; deficit = 4;
    TRAIL[0] = 0;
    clock_t t0 = clock();
    erec(0, ORBID[0], 1, CB, 0, 0, 0, 0);
    fclose(OUT);
    printf("{\"enumerator\":\"EQ153\",\"cell\":\"%d|%d|%d|%d|%d|%d\","
           "\"target\":%d,\"route\":\"%s\",\"witnesses\":%llu,\"nodes\":%llu,"
           "\"capped\":%s,\"seconds\":%.2f,\"file\":\"%s\"}\n",
           CB, CD, CA, CBB, CE, CH, ETARGET, prune ? "table" : "no-table",
           (unsigned long long)WITCOUNT, (unsigned long long)NODES,
           CAPPED ? "true" : "false",
           (double)(clock() - t0) / CLOCKS_PER_SEC, argv[8]);
    return CAPPED ? 1 : 0;
}
