import sys, json
cnf, mp, a, b, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
M = json.load(open(mp))['varmap']['runcount']
units = []
for oy, r in zip(M, (a, b)):
    # oy[j] <-> (#runs >= j+1): r runs  <=>  oy[r-1] true and oy[r] false
    units.append(oy[r - 1])
    if r < len(oy): units.append(-oy[r])
lines = open(cnf).read().splitlines()
hdr = [l for l in lines if l.startswith('p ')][0].split()
with open(out, 'w') as f:
    f.write('p cnf %s %d\n' % (hdr[2], int(hdr[3]) + len(units)))
    for l in lines:
        if not l.startswith('p ') and not l.startswith('c'): f.write(l + '\n')
    for u in units: f.write('%d 0\n' % u)
print(out, units)
