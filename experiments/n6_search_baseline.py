"""
Baseline attempt: try to determine the minimal n=6 superpermutation length
via the naive exhaustive IDA* solver in src/exact_solve.py.

This is expected to be INCONCLUSIVE, and that is the point of running it:
it establishes, honestly and empirically, that naive brute force is nowhere
near sufficient for n=6, which is exactly why the published literature
(Houston/Pantone/Vatter for the 867 lower bound, Egan/Houston for the 872
upper-bound construction) needed much smarter combinatorial arguments
rather than search. Closing the 867-872 gap requires either reproducing and
extending that combinatorial machinery, or a search with domain-specific
pruning far beyond what is implemented here (symmetry reduction, the
recursive/rotation-pass structure, etc. -- see STATUS.md).

Run with: python -m experiments.n6_search_baseline
"""
import time

from src.exact_solve import minimal_superpermutation_length
from src.lower_bound import houston_lower_bound
from src.construct import greedy_construct
from src.verify import verify_superpermutation


def main(node_budget=8_000_000):
    print("n=6 baseline exhaustive-search attempt")
    print(f"  proven lower bound (Houston et al.): {houston_lower_bound(6)}")
    print(f"  best known upper bound (literature, not reproduced here): 872")

    g = greedy_construct(6)
    report = verify_superpermutation(g, 6)
    print(f"  this repo's own greedy construction: length={len(g)}, valid={report['valid']}")

    t0 = time.time()
    length, nodes, exhausted = minimal_superpermutation_length(6, node_budget=node_budget)
    elapsed = time.time() - t0

    print(f"  naive IDA* search: nodes_expanded={nodes}, seconds={elapsed:.2f}, "
          f"exhausted={exhausted}, result={length}")
    if not exhausted:
        print("  => INCONCLUSIVE. Budget exhausted with no proof either way. "
              "This is expected; see module docstring and STATUS.md.")


if __name__ == "__main__":
    main()
