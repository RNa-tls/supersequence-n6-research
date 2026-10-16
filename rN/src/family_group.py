#!/usr/bin/env python3
"""Round N -- symmetry group of the 6A+24phi family: symbol permutations g in S_8 that map every
(trail, version) run sequence onto some (trail', version') run sequence (as a cyclic sequence of run
starts).  Such g preserve every weight w(last(s), t), hence every J, and act on trails.
usage: family_group.py FAMILY.json OUT.json"""
import sys, json, itertools

def main():
    fam = json.load(open(sys.argv[1]))
    seqs = {}
    for t, tr in enumerate(fam["trails"]):
        for v, s in enumerate(tr["versions"]):
            seqs[(t, v)] = [tuple(int(c) for c in s[8 * k:8 * k + 8]) for k in range(len(s) // 8)]
    owner = {}
    for key, ss in seqs.items():
        for k, p in enumerate(ss): owner.setdefault(p, []).append((key, k))
    probe = seqs[(1, 0)][0]
    group = []
    for g in itertools.permutations(range(8)):
        if tuple(g[x] for x in probe) not in owner: continue
        img = {}
        ok = True
        for key, ss in seqs.items():
            q0 = tuple(g[x] for x in ss[0])
            if q0 not in owner: ok = False; break
            found = False
            for (k2, off) in owner[q0]:
                s2 = seqs[k2]
                if len(s2) != len(ss): continue
                if all(tuple(g[x] for x in ss[i]) == s2[(off + i) % len(s2)] for i in range(len(ss))):
                    img[key] = (k2, off); found = True; break
            if not found: ok = False; break
        if ok: group.append((g, img))
    trail_perm = []
    for g, img in group:
        trail_perm.append({str(t): [img[(t, v)][0][0] for v in (0, 1)] for t in range(len(fam["trails"]))})
    orbits = []
    seen = set()
    for t in range(len(fam["trails"])):
        if t in seen: continue
        orb = sorted({tp[str(t)][0] for tp in trail_perm})
        seen |= set(orb); orbits.append(orb)
    res = dict(order=len(group), elements=[list(g) for g, _ in group],
               version_action=[{str(t): [img[(t, v)][0][1] for v in (0, 1)] for t in range(len(fam["trails"]))} for g, img in group],
               trail_action=trail_perm, trail_orbits=orbits)
    json.dump(res, open(sys.argv[2], "w"))
    print(json.dumps(dict(order=len(group), trail_orbits=orbits)))

if __name__ == "__main__":
    main()
