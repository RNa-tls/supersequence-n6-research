"""
Constructive (upper-bound) witnesses for superpermutation length.

`greedy_construct` is a simple, provably-terminating greedy algorithm. It is
NOT claimed to be optimal -- it exists so this repository has concrete,
self-verified example superpermutations for every n, built entirely from
first principles (no literature string is trusted without independent
verification; see tests/test_literature_witnesses.py for that separate
check).

Algorithm: maintain the string built so far. At each step, try appending
each symbol (by default in a fixed priority order); take the first symbol
whose length-n suffix is a permutation not seen before. If no single
character works, splice in the (by given priority) best unseen permutation,
overlapped with the current suffix as much as possible. Termination is
guaranteed because every iteration adds at least one previously-unseen
permutation to `seen`, and there are only n! of those.
"""
from .perms import all_permutation_strings, default_alphabet


def _max_overlap(s, p):
    """Largest k such that s[-k:] == p[:k]."""
    limit = min(len(s), len(p))
    for k in range(limit, -1, -1):
        if k == 0 or s[-k:] == p[:k]:
            return k
    return 0


def greedy_construct(n, alphabet=None, priority=None):
    alphabet = alphabet or default_alphabet(n)
    required = set(all_permutation_strings(n, alphabet))
    order = priority or tuple(reversed(alphabet))

    s = ''.join(alphabet)
    seen = {s}

    while len(seen) < len(required):
        suffix = s[-(n - 1):]
        extended = False
        for sym in order:
            cand = suffix + sym
            if len(set(cand)) == n and cand not in seen:
                s += sym
                seen.add(cand)
                extended = True
                break
        if extended:
            continue

        best, best_ov = None, -1
        for p in sorted(required):
            if p in seen:
                continue
            ov = _max_overlap(s, p)
            if ov > best_ov:
                best_ov, best = ov, p
        s += best[best_ov:]
        seen.add(best)

    return s


if __name__ == "__main__":
    from .verify import verify_superpermutation
    from .lower_bound import houston_lower_bound, sum_of_factorials_upper_bound

    for n in range(1, 7):
        s = greedy_construct(n)
        report = verify_superpermutation(s, n)
        print(f"n={n}: greedy length={len(s)}, valid={report['valid']}, "
              f"lower_bound={houston_lower_bound(n)}, "
              f"sum_of_factorials={sum_of_factorials_upper_bound(n)}")
