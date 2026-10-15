#!/usr/bin/env python3
"""Round M -- per-option in/out excess profile of the single-opening model.

For every opening option o: in_min(o) = min excess of a boundary INTO o from another trail,
out_min(o) = min excess of a boundary OUT of o.  For a trail T in the middle of a single-opening
word the two boundaries at T use the same option, so they cost at least
q(T) = min_o (in_min(o) + out_min(o)); summing over trails counts every boundary twice:
        sum_k e_k  >=  (1/2) * ( sum_{T not first, not last} q(T) + in-part of last + out-part of first ).
Also reported: per trail the number of options with (in_min, out_min) = (0,0), (0,1), (1,0), ...
usage: option_profile.py FAMILY.json"""
import sys, os, json, itertools
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trail_order_exact as TOE

def main():
    fam = json.load(open(sys.argv[1]))
    layers, const = TOE.load_layers(fam)
    T = len(layers)
    opts = []; by_entry = defaultdict(list)
    for t, L in enumerate(layers):
        for o in L:
            by_entry[o[0]].append(len(opts)); opts.append((t,) + o)
    INF = 99
    inm = [INF] * len(opts); outm = [INF] * len(opts)
    for a, (t, entry, ex, cut, v, k) in enumerate(opts):
        for w in range(2, 8):
            for perm in itertools.permutations(ex[:w]):
                y = ex[w:] + perm
                if TOE.wt(ex, y) != w: continue
                for b in by_entry.get(y, []):
                    if opts[b][0] == t: continue
                    e = w - opts[b][3] - 1
                    if e < outm[a]: outm[a] = e
                    if e < inm[b]: inm[b] = e
            if outm[a] == 0: break
    # w = 8 is always available: excess 8 - cut - 1
    for b in range(len(opts)):
        inm[b] = min(inm[b], 8 - opts[b][3] - 1)
    for a in range(len(opts)):
        outm[a] = min(outm[a], min(8 - c - 1 for c in (2, 3)))
    per = []
    for t in range(T):
        os_ = [i for i in range(len(opts)) if opts[i][0] == t]
        q = min(inm[i] + outm[i] for i in os_)
        hist = Counter((inm[i], outm[i]) for i in os_)
        per.append(dict(trail=t, size=len(layers[t]) // 2, q=q, in0out0=hist.get((0, 0), 0),
                        profile={"%d,%d" % k: v for k, v in sorted(hist.items())}))
    qs = sorted(p["q"] for p in per)
    lb = (sum(qs) - qs[-1] - qs[-2]) / 2.0 if len(qs) > 2 else 0
    print(json.dumps(dict(q_hist=dict(Counter(qs)), half_sum_lower_bound=lb, per_trail=per)))

if __name__ == "__main__":
    main()
