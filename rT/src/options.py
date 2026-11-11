#!/usr/bin/env python3
"""Round T -- all single-opening arcs of the 16 closed trails (letter level).
An arc of trail t = the cyclic windows s .. e (first and last are permutations); the dropped windows e+1 .. s-1 must
each be a non-permutation or a permutation that occurs once more among the retained windows of the same trail.
cost = 2 - (number of dropped windows)  (a cut at a weight-3 step costs 0, at a weight-2 step 1, inside a class 2).
piece length = R + 5 + cost.  Output: text lines  trail start dropped cost head7 tail7  and a summary json.
usage: options.py SEL TSV BASE OUT.txt OUT.json"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model
N = 8
def options(c):
    R = len(c); d = c + c + c; win = [d[i:i + N] for i in range(R)]; ok = [model.isperm(x) for x in win]
    occ = collections.Counter(x for x, o in zip(win, ok) if o); out = []
    for s in range(R):
        if not ok[s]: continue
        # grow the dropped interval backwards from s - 1
        dropped = collections.Counter(); k = 0
        while k < R - 1:
            if ok[(s - k - 1) % R]: out.append((s, k))            # arc s .. s-k-1 is trimmed: record it
            x = win[(s - k - 1) % R]
            if ok[(s - k - 1) % R]:
                if occ[x] - dropped[x] < 2: break                 # last retained copy: cannot drop
                dropped[x] += 1
            k += 1
    return out
if __name__ == "__main__":
    selp, tsvp, basep, outp, jsonp = sys.argv[1:6]; cyc = model.load(selp, tsvp, basep)
    hist = collections.Counter(); n = 0; fo = open(outp, "w"); per = []
    dupx = 0
    for t, c in enumerate(cyc):
        R = len(c); d = c + c + c; ops = options(c); h = collections.Counter()
        win = [d[i:i + N] for i in range(R)]; cnt = collections.Counter(x for x in win if model.isperm(x)); dupx += sum(v - 1 for v in cnt.values())
        for s, k in ops:
            piece = d[s:s + R + 7 - k]; assert model.isperm(piece[:N]) and model.isperm(piece[-N:])
            fo.write("%d %d %d %d %s %s\n" % (t, s, k, 2 - k, piece[:7], piece[-7:])); h[2 - k] += 1; n += 1
        hist.update(h); per.append(dict(trail=t, R=R, options=len(ops), by_cost={str(k): v for k, v in sorted(h.items())}))
    fo.close()
    # duplicates across trails?
    allp = collections.Counter()
    for t, c in enumerate(cyc):
        d = c + c[:N]
        for x in {d[i:i + N] for i in range(len(c)) if model.isperm(d[i:i + N])}: allp[x] += 1
    res = dict(options=n, by_cost={str(k): v for k, v in sorted(hist.items())}, per_trail=per, repeated_windows_within_trails=dupx, permutations_in_two_trails=sum(1 for v in allp.values() if v > 1), distinct_permutations=len(allp))
    json.dump(res, open(jsonp, "w"), indent=1); print({k: v for k, v in res.items() if k != "per_trail"}); print(per[0], per[12])
