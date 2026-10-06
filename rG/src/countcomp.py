#!/usr/bin/env python3
"""Count all completions (distinct block sets) of a kernel by exhaustive Algorithm X + forest check.
Cross-check against Egan's PermutationChains README: n=5 -> 6 solutions, n=6 -> 42,288 solutions
(standard 3-cycle kernel)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matroidtest import all_completions
from candcore import kernel_rows
from complete import World
n = int(sys.argv[1]); t0 = time.time()
W = World(n); s = all_completions(W, kernel_rows(n, sys.argv[2]))
print(f"n={n} kernel {sys.argv[2]}: {len(s)} distinct completions ({time.time()-t0:.0f}s)", flush=True)
