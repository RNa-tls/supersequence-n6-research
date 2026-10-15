/*
 * Round M -- standalone driver for the elkai copy of LKH-3.0.8 with the r = 0 SPECIAL distance.
 * usage: lkh_r0 PARAMS PROBLEM NODEDATA OUT_TOUR
 *   PARAMS: LKH parameter text (PROBLEM_FILE = a real file: the elkai copy reads sections such as
 *   FIXED_EDGES_SECTION only from files); PROBLEM: any text (kept for the elkai interface);
 *   NODEDATA: binary file for r0special.c;  OUT_TOUR: the best tour, one node id per line.
 */
#include "LKH.h"
#include "gb_string.h"

extern void ElkaiSolveProblem(gbString params, gbString problem, int *tourSize, int **tourPtr);
extern void R0_load(const char *path);

static gbString slurp(const char *path)
{
    FILE *f = fopen(path, "rb");
    long n; char *buf; gbString s;
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
    fseek(f, 0, SEEK_END); n = ftell(f); fseek(f, 0, SEEK_SET);
    buf = (char *) malloc(n + 1);
    if (fread(buf, 1, n, f) != (size_t) n) { fprintf(stderr, "read error %s\n", path); exit(1); }
    buf[n] = 0; fclose(f);
    s = gb_make_string(buf); free(buf);
    return s;
}

int main(int argc, char *argv[])
{
    int tourSize = 0, *tour = 0, i;
    FILE *out;
    if (argc != 5) { fprintf(stderr, "usage: lkh_r0 PARAMS PROBLEM NODEDATA OUT_TOUR\n"); return 2; }
    R0_load(argv[3]);
    ElkaiSolveProblem(slurp(argv[1]), slurp(argv[2]), &tourSize, &tour);
    out = fopen(argv[4], "w");
    for (i = 0; i < tourSize; i++) fprintf(out, "%d\n", tour[i]);
    fclose(out);
    printf("tour written: %d nodes\n", tourSize);
    return 0;
}
