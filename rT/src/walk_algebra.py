#!/usr/bin/env python3
"""Round T -- algebra of the closed walks of rows: the public 27-loop walk W27 and the old 16-loop walk A.
State x = an ordering of the 6 loop letters; a row of length v sends x to step(x, v) = x o pi_v (a permutation of
places).  usage: walk_algebra.py SELECTION OLD_WALKS.json OUT.json"""
import sys, json, itertools, math
K = 6
def step(x, v):
    if v == K: return x[1:K - 1] + x[0:1] + x[K - 1:K]
    return x[v + 1:] + x[:v - 1] + x[v:v + 1] + x[v - 1:v]
def port_perm(v, j):
    if v == K: return (j - 1) % (K - 1)
    if j < v: return j + K - v - 1
    if j == v: return K - v - 2
    return j - v - 1
def pi(v): return tuple(int(ch) for ch in step("012345", v))            # x' [i] = x[pi[i]]
def compose(p, q): return tuple(p[i] for i in q)                        # first p then q:  x'' [i] = x[p[q[i]]]
def cycle_type(p):
    seen = set(); out = []
    for i in range(len(p)):
        if i in seen: continue
        n = 0; j = i
        while j not in seen: seen.add(j); j = p[j]; n += 1
        out.append(n)
    return sorted(out, reverse=True)
def order(p): return math.lcm(*cycle_type(p))
def closure(gens):
    idn = tuple(range(K)); seen = {idn}; fr = [idn]
    while fr:
        nx = []
        for g in fr:
            for h in gens:
                q = compose(g, h)
                if q not in seen: seen.add(q); nx.append(q)
        fr = nx
    return seen
def canon_loop(x):
    i = x.index(min(x)); return x[i:] + x[:i]
def analyse(word, x0, letters):
    """word: row lengths along the walk from state x0"""
    states = [x0]
    for v in word: states.append(step(states[-1], int(v)))
    closed = states[-1] == x0; states = states[:-1]
    prod = tuple(range(K))
    for v in word: prod = compose(prod, pi(int(v)))
    ports = list(range(K - 1))
    for v in word: ports = [port_perm(int(v), j) for j in ports]
    # ports[j] = port reached after one pass when entering at j
    m = len(word); rot_sym = [r for r in range(m) if word[r:] + word[:r] == word]
    rev = word[::-1]; rev_sym = any(rev[r:] + rev[:r] == word for r in range(m))
    # stabiliser among relabelings of the letters: sigma maps the set of row states to itself
    stset = set(states); stab = []
    for perm in itertools.permutations(letters):
        mp = dict(zip(letters, perm))
        if "".join(mp[ch] for ch in x0) in stset and all("".join(mp[ch] for ch in s) in stset for s in states): stab.append("".join(perm))
    partial = []
    pr = tuple(range(K))
    for v in word: pr = compose(pr, pi(int(v))); partial.append(order(pr))
    return dict(row_word=word, rows=m, Q=sum(K - int(v) for v in word), closed=closed, distinct_states=len(stset), distinct_loops=len({canon_loop(s) for s in states}),
                product_place_permutation=list(prod), product_is_identity=prod == tuple(range(K)), port_permutation_per_pass=ports, port_cycle_type=cycle_type(tuple(ports)),
                trails_of_the_walk=len(cycle_type(tuple(ports))), row_word_rotation_symmetries=rot_sym, row_word_equals_a_rotation_of_its_reverse=rev_sym,
                letter_stabiliser_order=len(stab), letter_stabiliser=stab[:8], letters_per_loop_Q=round(sum(K - int(v) for v in word) / m, 4)), states
if __name__ == "__main__":
    selp, oldp, outp = sys.argv[1:4]
    res = dict(generators={str(v): dict(place_permutation=list(pi(v)), cycle_type=cycle_type(pi(v)), order=order(pi(v))) for v in (1, 2, 3, 4, 6)})
    res["group_generated_by_pi2_pi4_pi6"] = len(closure([pi(2), pi(4), pi(6)])); res["group_generated_by_pi4_pi6"] = len(closure([pi(4), pi(6)])); res["group_generated_by_pi6"] = len(closure([pi(6)]))
    # ---- public selection
    sel = [(l.split()[0], int(l.split()[1])) for l in open(selp) if l.strip() and not l.startswith("#")]
    vof = {x: v for x, v in sel}; seen = set(); walks = []
    for x, v in sel:
        if v == 0 or x in seen: continue
        wk = []; y = x
        while y not in seen: seen.add(y); wk.append(y); y = step(y, vof[y])
        assert y == x; walks.append(wk)
    pub = []
    for wk in walks:
        word = "".join(str(vof[x]) for x in wk); r = min(range(len(wk)), key=lambda q: word[q:] + word[:q]); wk = wk[r:] + wk[:r]; word = word[r:] + word[:r]
        a, st = analyse(word, wk[0], "012345"); a["start_state"] = wk[0]; pub.append((a, st))
    res["public_walks"] = [a for a, _ in pub]
    # relabelings carrying walk 0 to walk i (state to state, start to start)
    rel = []
    for a, st in pub:
        mp = dict(zip(pub[0][1][0], st[0])); ok = all("".join(mp[ch] for ch in s) == s2 for s, s2 in zip(pub[0][1], st)); rel.append(dict(to_start=st[0], relabeling="".join(mp[ch] for ch in "012345"), maps_walk0_onto_it=ok))
    res["relabelings_from_walk0"] = rel
    rowless = {canon_loop(x) for x, v in sel if v == 0}; allst = {x for x, v in sel if v > 0}
    stab = []
    for perm in itertools.permutations("012345"):
        mp = dict(zip("012345", perm))
        if all("".join(mp[ch] for ch in x) in allst for x in allst): stab.append("".join(perm))
    res["public_selection_letter_stabiliser"] = dict(order=len(stab), elements=stab)
    # ---- old A walk: states recovered from the loop sequence
    old = json.load(open(oldp)); A = next(a for a in old if a["loops"] == 16 and a["version"] == 0)
    letters = "".join(sorted(set(A["walk"][0]))); word = A["row_word"]; found = None
    for r in range(K):
        x0 = A["walk"][0][r:] + A["walk"][0][:r]; y = x0; ok = True
        for i, v in enumerate(word):
            if canon_loop(y) != A["walk"][i]: ok = False; break
            y = step(y, int(v))
        if ok and y == x0: found = x0; break
    assert found, "old walk states not recovered"
    r = min(range(len(word)), key=lambda q: word[q:] + word[:q])
    y = found
    for v in word[:r]: y = step(y, int(v))
    a, st = analyse(word[r:] + word[:r], y, letters); a["start_state"] = y; res["old_A_walk"] = a
    # the period-4 block of A
    blk = tuple(range(K))
    for v in "4666": blk = compose(blk, pi(int(v)))
    res["old_A_block_4666"] = dict(place_permutation=list(blk), cycle_type=cycle_type(blk), order=order(blk))
    json.dump(res, open(outp, "w"), indent=1)
    for k in ("generators", "group_generated_by_pi2_pi4_pi6", "group_generated_by_pi4_pi6", "old_A_block_4666", "relabelings_from_walk0", "public_selection_letter_stabiliser"): print(k, json.dumps(res[k]))
    print("W27", json.dumps(res["public_walks"][0])); print("A", json.dumps(res["old_A_walk"]))
