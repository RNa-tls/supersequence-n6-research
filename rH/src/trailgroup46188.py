#!/usr/bin/env python3
"""Do the symbol relabellings trail0 -> trail j (j=0..5) of the six long trails of the n=8 46188 word
(from longtrail46188.txt) form a group?  Maps are taken at the trails' recorded start rows, so a
negative answer only says the six trails are not an orbit of a fixed subgroup *with these phases*."""
maps = [(0, 1, 2, 3, 4, 5, 6, 7), (0, 6, 2, 5, 4, 3, 1, 7), (0, 3, 5, 1, 4, 2, 6, 7),
        (0, 1, 3, 2, 6, 5, 4, 7), (0, 4, 6, 3, 1, 5, 2, 7), (0, 2, 6, 5, 1, 3, 4, 7)]
e = maps[0]; S = set(maps)
comp = lambda a, b: tuple(a[b[i]] for i in range(8))
print("closed_under_composition", all(comp(a, b) in S for a in S for b in S))
G = {e}; fr = [e]
while fr:
    x = fr.pop()
    for g in maps:
        y = comp(g, x)
        if y not in G: G.add(y); fr.append(y)
def order(p):
    q, k = p, 1
    while q != e: q, k = comp(p, q), k + 1
    return k
print("generated_group_order", len(G))
print("element_orders", [order(p) for p in maps])
