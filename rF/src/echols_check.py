#!/usr/bin/env python3
"""Final round -- verify external Egan-1 words (Echols n = 9, 10; archive n = 8) as superpermutations
with an independent sliding-window check, and compute Bridge parameters + conservation terms (n <= 9)."""
import math, sys, os, random, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
for d in ("r178/src", "r176/src", "r182/src", "rF/src"): sys.path.insert(0, os.path.join(ROOT, d))
SP = "/tmp/claude-0/-home-user-supersequence-n6-research/0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad/echols/superpermutations"

def check_word(w, n):
    alph = sorted(set(w)); assert len(alph) == n
    seen = set()
    for i in range(len(w) - n + 1):
        t = w[i:i + n]
        if len(set(t)) == n: seen.add(t)
    return len(seen) == math.factorial(n)

if __name__ == "__main__":
    from bridge178 import normalize, route_of_word
    from conservation import terms
    for n, fn in ((9, "9/408965.txt"), (10, "10/4037046.txt")):
        w = "".join(ch for ch in open(os.path.join(SP, fn)).read() if ch.isdigit())
        f = sum(math.factorial(n - i) for i in range(4)) + n - 4
        print(f"n={n}: length {len(w)}, f(n) = {f}, Egan = {f + 1}, superpermutation: {check_word(w, n)}", flush=True)
        if n == 9:
            t0 = time.time()
            mp = {c: i for i, c in enumerate(sorted(set(w)))}
            route = [tuple(mp[c] for c in t) for t in route_of_word(w, n)]
            route = normalize(route, n)
            d = terms(route, n, random.Random(0), "echols9")
            print(d, f"({time.time() - t0:.0f}s)", flush=True)
