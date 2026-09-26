#!/usr/bin/env python3
"""Round 181 -- Delta(n) bound table, separated by status.
  R178 (unconditional, paper proof):  ceil(2(n-2)((n-3)!-1)/(n^2-4n+1))
  CS restricted (Theorem CS, nu_s = 0, given omega): ceil((ORB-(n-2))/((n-2)+(n-1)omega))
  NF(theta) conditional:                ceil((ORB-(n-2))/((n-2)+(n-1)theta))
  m = 0 restricted:                     (n-3)! - 1
  Egan upper bound on Delta:            (n-3)!"""
from math import factorial as f
cd = lambda a, b: -(-a // b)
print(f"{'n':>3} {'R178':>10} {'CS w=2':>10} {'CS w=3':>10} {'NF th=1':>10} {'m=0':>10} {'Egan':>10}")
for n in range(6, 15):
    ORB = f(n - 2)
    r178 = cd(2 * (n - 2) * (f(n - 3) - 1), n * n - 4 * n + 1)
    cs = lambda w: cd(ORB - (n - 2), (n - 2) + (n - 1) * w)
    print(f"{n:>3} {r178:>10} {cs(2):>10} {cs(3):>10} {cs(1):>10} {f(n-3)-1:>10} {f(n-3):>10}")
