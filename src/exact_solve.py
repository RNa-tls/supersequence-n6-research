"""
Exhaustive (exact) minimal-superpermutation length solver, by naive IDA*.

This is only tractable for very small n (n <= 3 comfortably; n = 4 is
already expensive without much smarter pruning than used here). It exists
to give this repository at least one genuinely from-scratch, independently
computed confirmation of a published minimal length, rather than trusting
every number by citation alone.

It is NOT intended to be, and cannot be, pushed to n = 5 or n = 6: the
published exhaustive proofs for those cases (Chaffin et al. 2014 for n=5)
required substantially smarter methods (symmetry reduction, recursive
structure, meet-in-the-middle, serious compute) than the textbook IDA*
implemented here. Anyone extending this file toward n=6 should read that as
a warning, not a challenge to brute force away.
"""
from .perms import all_permutation_strings, default_alphabet


def minimal_superpermutation_length(n, alphabet=None, node_budget=2_000_000):
    """
    Returns (length, node_count, exhausted) via IDA*.

    exhausted=True means the search completed and `length` is proven
    minimal. exhausted=False means node_budget ran out first and `length`
    (if not None) is only a bound found so far, not a proof of minimality.
    """
    alphabet = alphabet or default_alphabet(n)
    required = set(all_permutation_strings(n, alphabet))
    start = ''.join(alphabet)

    nodes = [0]

    def h(covered_count):
        # admissible: every uncovered permutation needs >= 1 more character
        return len(required) - covered_count

    def dfs(s, covered, bound):
        nodes[0] += 1
        if nodes[0] > node_budget:
            return None  # signal budget exhaustion
        g = len(s)
        f = g + h(len(covered))
        if f > bound:
            return f
        if len(covered) == len(required):
            return s
        suffix = s[-(n - 1):] if len(s) >= n - 1 else s
        min_next = None
        for sym in alphabet:
            cand_suffix = (suffix + sym)[-n:]
            new_s = s + sym
            new_covered = covered
            if len(cand_suffix) == n and len(set(cand_suffix)) == n and cand_suffix in required:
                new_covered = covered | {cand_suffix}
            result = dfs(new_s, new_covered, bound)
            if result is None:
                return None
            if isinstance(result, str):
                return result
            if min_next is None or result < min_next:
                min_next = result
        return min_next

    covered0 = {start} if start in required else set()
    bound = len(start) + h(len(covered0))
    while True:
        result = dfs(start, covered0, bound)
        if result is None:
            return (None, nodes[0], False)
        if isinstance(result, str):
            return (len(result), nodes[0], True)
        bound = result


if __name__ == "__main__":
    for n in (2, 3):
        length, nodes, exhausted = minimal_superpermutation_length(n)
        print(f"n={n}: minimal_length={length} (nodes={nodes}, proven={exhausted})")
