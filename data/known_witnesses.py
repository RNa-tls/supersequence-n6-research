"""
Literature-sourced example superpermutations, kept separate from this
repo's own (independently derived) `src.construct` output so the two can
never be silently confused.

Every string here is treated as an *unverified claim* until the test suite
(tests/test_literature_witnesses.py) checks it against src.verify -- do not
add a string here without a citation and a passing test.
"""

# n = 4, length 33, over alphabet "1234". Matches the proven minimal length
# for n = 4 (Ashlock & Tillotson). Sourced via web search summarizing
# standard references on the minimal superpermutation problem.
N4_LENGTH_33 = "123412314231243121342132413214321"
