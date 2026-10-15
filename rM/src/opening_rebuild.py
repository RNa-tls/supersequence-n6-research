#!/usr/bin/env python3
"""Round M -- rebuild a word from (family JSON, opening description) and compare with a record file.
Independent of opening_extract.py and of every earlier round: uses only the two JSON files.

The description is a list [trail, version, start index, number of runs]; each piece contributes the
runs start[i], start[i+1], ... (cyclic) of that trail version, each run = the 8 left rotations of its
start.  The word is the greedy overlap concatenation of the permutation route; symbols 0..7 are
written as 1..8 followed by a newline (the record file format).
usage: opening_rebuild.py FAMILY.json DESCRIPTION.json [RECORD]"""
import sys, json, hashlib

def main():
    fam = json.load(open(sys.argv[1])); desc = json.load(open(sys.argv[2]))["description"]
    T = {}
    for tr in fam["trails"]:
        for v, s in enumerate(tr["versions"]):
            T[tr["trail"], v] = [s[8 * k:8 * k + 8] for k in range(len(s) // 8)]
    route = []
    for t, v, i, ln in desc:
        st = T[t, v]
        for k in range(ln):
            p = st[(i + k) % len(st)]
            route += [p[j:] + p[:j] for j in range(8)]
    assert len(route) == 40320 and len(set(route)) == 40320, "description does not cover every permutation once"
    word = route[0]
    for x, y in zip(route, route[1:]):
        k = next(k for k in range(1, 9) if k == 8 or x[k:] == y[:8 - k])
        word += y[8 - k:]
    data = ("".join(chr(ord(c) + 1) for c in word) + "\n").encode()
    res = dict(length=len(word), sha256=hashlib.sha256(data).hexdigest())
    if len(sys.argv) > 3:
        ref = open(sys.argv[3], "rb").read()
        res.update(record=sys.argv[3], record_sha256=hashlib.sha256(ref).hexdigest(), identical=(ref == data))
    print(json.dumps(res))

if __name__ == "__main__":
    main()
