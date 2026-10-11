"""Shared helper: classes of the closed trail of a syllable word started at the identity."""
def comp(p, q): return tuple(p[q[i]] for i in range(len(p)))
def syllables(n):
    BAC, CBA = (1, 0, n - 1), (n - 1, 1, 0)
    syl = {}
    for r in range(0, n - 2):
        syl[f"S{r}"] = [(n - 3, BAC)] + [(n - 1, BAC)] * r
        if n - 4 >= 1: syl[f"X{r}"] = [(n - 3, CBA), (n - 2, BAC), (n - 1, CBA), (n - 4, BAC)] + [(n - 1, BAC)] * r
    return syl
def closed_letters(n, word):
    I = tuple(range(n)); F = tuple(list(range(1, n - 1)) + [0, n - 1])
    Fp = [I]
    for _ in range(n - 1): Fp.append(comp(Fp[-1], F))
    T = lambda s: tuple(list(range(2, n - 1)) + list(s))
    syl = syllables(n)
    letters = [x for s in word.split() for x in syl[s]]
    Pi = I
    for l, s in letters: Pi = comp(Pi, comp(Fp[l - 1], T(s)))
    m = 1; X = Pi
    while X != I: X = comp(X, Pi); m += 1
    return letters * m, Fp, T
def closed_classes(n, word):
    letters, Fp, T = closed_letters(n, word)
    def canon(p):
        k = p.index(0); return p[k:] + p[:k]
    P = tuple(range(n)); out = []
    for l, s in letters:
        for j in range(l): out.append(canon(comp(P, Fp[j])))
        P = comp(P, comp(Fp[l - 1], T(s)))
    assert len(set(out)) == len(out)
    return out
