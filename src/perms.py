"""Core permutation utilities shared by the rest of the codebase."""
from itertools import permutations


def default_alphabet(n):
    """Single-character alphabet '0'..str(n-1). Only defined for n <= 10."""
    if n > 10:
        raise ValueError("default alphabet only defined for n <= 10; pass alphabet explicitly")
    return tuple(str(i) for i in range(n))


def all_permutation_strings(n, alphabet=None):
    """All n! permutations of `alphabet` (default: default_alphabet(n)), as strings."""
    alphabet = alphabet or default_alphabet(n)
    if len(alphabet) != n:
        raise ValueError(f"alphabet has {len(alphabet)} symbols, expected {n}")
    return [''.join(p) for p in permutations(alphabet)]


def rotate_left(s, k):
    k %= len(s)
    return s[k:] + s[:k]
