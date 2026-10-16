"""splice a re-optimised window path into 46185 and verify the resulting word independently"""
import sys, json, math, itertools
sys.path.insert(0, 'rN/src')
import rl_window as RW
n = 8
win = json.load(open(sys.argv[1]))
st = RW.word_runs('rL/records/superperm8_46185.txt')
lo, hi = win['lo'], win['hi']
new_runs = st[:lo] + [tuple(p) for p in win['path']] + st[hi + 1:]
assert len(new_runs) == len(st) == 5040, len(new_runs)
perms = []
for p in new_runs:
    q = list(p)
    for _ in range(n): perms.append(tuple(q)); q = q[1:] + q[:1]
def wt(x, y):
    for k in range(1, n):
        if x[k:] == y[:n - k]: return k
    return n
word = list(perms[0])
for a, b in zip(perms, perms[1:]): word += list(b[n - wt(a, b):])
s = ''.join(str(c + 1) for c in word)
seen = set(tuple(s[i:i + n]) for i in range(len(s) - n + 1))
full = set(tuple(str(c + 1) for c in p) for p in itertools.permutations(range(n)))
print(json.dumps(dict(length=len(s), all_perms=full <= seen, missing=len(full - seen))))
if full <= seen: open(sys.argv[2], 'w').write(s + '\n')
