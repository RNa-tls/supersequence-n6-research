#!/usr/bin/env python3
"""Round X -- independent checker (no code shared with the C searches) for dumped model chains, and for their reversals.

A chain is a list of block entries (8-letter words over 1..8) with piece sizes.  Rules (the model of Halfar's line
search, rewritten here from the words themselves):
  exit(D)  = D[7] + D[0:7]                     (the 8 rotations of D, ending at the right rotation by one)
  door(x)  = x[2:] + x[1] + x[0]               (weight-2 step to the next block of a piece)
  seam(y)  = y[3:] + any permutation of y[0:3] (weight-3 step to the first block of the next piece)
  pieces of 1..7 blocks, all classes (rotation classes) distinct, deficit of a piece = 7 - blocks.
For a forward chain also: first entry 12345678, every non-empty prefix of value a r - b d in (0, c].
Reversal: block entries rev(exit(D)) in reverse order, the same piece sizes reversed; it must satisfy the same local
rules (start and prefix conditions are not required), and every non-empty SUFFIX of the original must have positive
value iff the reversal is a kept chain after relabeling (checked as: prefix values of the reversal in (0, c]).
usage: check_chains.py a b c DUMP.jsonl [--reverse]   -> JSON summary"""
import sys, json, itertools

def exitw(D): return D[7] + D[:7]
def door(x): return x[2:] + x[1] + x[0]
def canon(w):
    i = w.index("8"); return w[i:] + w[:i]

def check_rules(ent, pieces):
    if sum(pieces) != len(ent) or any(not 1 <= p <= 7 for p in pieces): return "piece sizes"
    if any(sorted(e) != list("12345678") for e in ent): return "not a permutation"
    cls = [canon(e) for e in ent]
    if len(set(cls)) != len(cls): return "class repeated"
    q = 0
    for k, p in enumerate(pieces):
        if k > 0:
            y = exitw(ent[q - 1]); e = ent[q]
            if not (e[:5] == y[3:] and sorted(e[5:]) == sorted(y[:3])): return "seam at piece %d" % k
        for t in range(1, p):
            if ent[q + t] != door(exitw(ent[q + t - 1])): return "door in piece %d" % k
        q += p
    return None

def main():
    a, b, c = map(int, sys.argv[1:4]); rows = [json.loads(l) for l in open(sys.argv[4]) if "summary" not in l]
    rev = "--reverse" in sys.argv
    bad = 0; kept_rev = 0; n = 0
    for x in rows:
        ent, pieces = x["entries"], x["pieces"]; n += 1
        err = check_rules(ent, pieces)
        if err is None and ent[0] != "12345678": err = "start"
        d = sum(7 - p for p in pieces)
        if err is None and (len(pieces) != x["r"] or d != x["d"] or a * x["r"] - b * d != x["v"]): err = "r/d/v"
        if err is None:
            s = 0
            for p in pieces:
                s += a - b * (7 - p)
                if not 0 < s <= c: err = "prefix value"; break
        if err is None and rev:
            rent = [exitw(D)[::-1] for D in reversed(ent)]; rp = list(reversed(pieces))
            e2 = check_rules(rent, rp)
            if e2: err = "reversal: " + e2
            else:
                s, ok = 0, True
                for p in rp:
                    s += a - b * (7 - p)
                    if not 0 < s <= c: ok = False; break
                kept_rev += ok
        if err: bad += 1; print("BAD", x["r"], x["v"], err, file=sys.stderr)
    print(json.dumps(dict(chains=n, bad=bad, reversal_checked=rev, reversals_kept=kept_rev if rev else None)))

main()
