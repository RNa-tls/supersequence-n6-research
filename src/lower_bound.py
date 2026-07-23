"""
The published lower bound on minimal superpermutation length.

    L(n) >= n! + (n-1)! + (n-2)! + n - 3      for n >= 2
    L(1) = 1                                  (trivial)

History: first proved by an anonymous poster on the 4chan /sci/ board in
September 2011. Independently verified and written up formally by Robin
Houston, together with Jay Pantone and Vince Vatter:

    R. Houston, "Tackling the Minimal Superpermutation Problem",
    arXiv:1408.5108 (2014).

For n <= 5 this bound is known to be TIGHT (it equals the proven minimal
length sum_{k=1}^{n} k!): L(1..5) = 1, 3, 9, 33, 153, with n=4 established
by Ashlock & Tillotson and n=5 by Ben Chaffin et al. via exhaustive
computer search (see njohnston.ca, "All Minimal Superpermutations on Five
Symbols Have Been Found", 2014).

For n = 6 the bound gives 867, but the best known valid superpermutation
has length 872 (found by Greg Egan / Robin Houston using a TSP-solver-based
search, improving on the naive sum-of-factorials upper bound of 873).
Whether L(6) = 872, or something strictly between 867 and 872, is an OPEN
problem: no published proof closes this gap as of the sources available to
this repository. This repository's research goal is to try to close (or
narrow) that gap; see STATUS.md for the current state of that effort.
"""
from math import factorial


def houston_lower_bound(n):
    """The proven lower bound on the minimal superpermutation length for n symbols."""
    if n < 1:
        raise ValueError("n must be >= 1")
    if n == 1:
        return 1
    return factorial(n) + factorial(n - 1) + factorial(n - 2) + n - 3


def sum_of_factorials_upper_bound(n):
    """
    The classical ("naive recursive") upper bound: sum_{k=1}^{n} k!.
    Achieved by the standard recursive insertion construction, and known to
    be the exact minimal length for n <= 5.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    return sum(factorial(k) for k in range(1, n + 1))


if __name__ == "__main__":
    print(f"{'n':>2} {'lower bound':>12} {'sum-of-factorials':>18}")
    for n in range(1, 8):
        print(f"{n:>2} {houston_lower_bound(n):>12} {sum_of_factorials_upper_bound(n):>18}")
