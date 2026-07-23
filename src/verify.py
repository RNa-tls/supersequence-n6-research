"""
Ground-truth verification that a candidate string is a valid superpermutation.

This is the single source of truth used to check every other claim in this
repository (constructions, literature-sourced witness strings, search
results). It does the obvious, unglamorous thing: scan every length-n window
of the candidate string and check that the set of n! required permutations
is fully covered.
"""
from .perms import all_permutation_strings, default_alphabet


def verify_superpermutation(s, n, alphabet=None):
    """
    Check whether `s` contains every permutation of `alphabet` (default:
    '0'..str(n-1)) as a contiguous window of length n.

    Returns a dict:
        valid:    bool
        length:   len(s)
        required: n! (number of permutations that must appear)
        covered:  how many distinct required permutations actually appear
        missing:  set of permutation-strings that never appear as a window
    """
    alphabet = alphabet or default_alphabet(n)
    required = set(all_permutation_strings(n, alphabet))

    covered = set()
    for i in range(len(s) - n + 1):
        w = s[i:i + n]
        if len(set(w)) == n:
            covered.add(w)
    covered &= required

    missing = required - covered
    return {
        "valid": len(missing) == 0,
        "length": len(s),
        "required": len(required),
        "covered": len(covered),
        "missing": missing,
    }
