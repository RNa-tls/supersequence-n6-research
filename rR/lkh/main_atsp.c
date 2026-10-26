/*
 * Round R -- standalone driver for the elkai copy of LKH-3.0.8 (explicit-matrix problems).
 * usage: lkh_atsp PARAMS OUT_TOUR
 *   PARAMS: LKH parameter text; PROBLEM_FILE (and INITIAL_TOUR_FILE if any) must be real files.
 *   OUT_TOUR: the best tour, one node id (1-based) per line.
 * The LKH sources are not part of this repository (build.sh compiles them from the elkai 2.0.1 sdist).
 */
#include "LKH.h"
#include "gb_string.h"

extern void ElkaiSolveProblem(gbString params, gbString problem, int *tourSize, int **tourPtr);

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
    if (argc != 3) { fprintf(stderr, "usage: lkh_atsp PARAMS OUT_TOUR\n"); return 2; }
    ElkaiSolveProblem(slurp(argv[1]), gb_make_string(""), &tourSize, &tour);
    out = fopen(argv[2], "w");
    for (i = 0; i < tourSize; i++) fprintf(out, "%d\n", tour[i]);
    fclose(out);
    printf("tour written: %d nodes\n", tourSize);
    return 0;
}
