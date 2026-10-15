#!/usr/bin/env python3
"""Round M -- export the closed-trail FAMILY of an r = 0 word as explicit data.

The family of the 46187 word: its chain set decomposes into 30 closed trails (6 A-bundles, 24
phi-cycles); every closed trail has exactly two relabelled versions with the same class set
(Round L, hybrid_relink.all_versions).  Exported: for every trail and version the cyclic list of
RUN STARTS (a run = the 8 left rotations of its start).  This file is the only input (besides an
opening description) needed by opening_rebuild.py.
usage: family_export.py WORD OUT.json"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "rL", "src"))
import hybrid_relink as H

def main():
    word, out = sys.argv[1], sys.argv[2]
    seqs, L0, K, alt = H.closed_trails(word)
    cache = os.path.join(os.environ.get("RL_CACHE", "."), "versions_" + os.path.basename(word) + ".pkl")
    V = H.all_versions(seqs, cache)
    fam = []
    for ti, vers in enumerate(V):
        vv = []
        for s in vers:
            starts = [s[i] for i in range(0, len(s), 8)]
            # sanity: the cyclic sequence is the concatenation of the 8 rotations of each start
            for k, p in enumerate(starts):
                assert s[8 * k:8 * k + 8] == [p[j:] + p[:j] for j in range(8)]
            vv.append("".join("".join(str(c) for c in p) for p in starts))
        fam.append(dict(trail=ti, classes=len(vers[0]) // 8, versions=vv))
    json.dump(dict(source=os.path.basename(word), trails=fam), open(out, "w"))
    print(json.dumps(dict(trails=len(fam), versions=[len(f["versions"]) for f in fam], sizes=sorted(f["classes"] for f in fam))))

if __name__ == "__main__":
    main()
