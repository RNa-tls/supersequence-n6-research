import sys, json
sys.path.insert(0, '/home/user/supersequence-n6-research/rN/src')
import options as OP
fam, opts = OP.load('/home/user/supersequence-n6-research/rM/certs/family_46187.json')
d = json.load(open('/home/user/supersequence-n6-research/rN/certs/audit_superperm8_46185.json'))
rows = d['table']
oid = {(o['t'], o['v'], o['k']): i for i, o in enumerate(opts)}
cnf_in, mp_in, cnf_out = sys.argv[1], sys.argv[2], sys.argv[3]
mp = json.load(open(mp_in))['varmap']
units = []
seq = [r['trail'] for r in rows]
for r in rows:
    units.append(mp['x'][str(oid[(r['trail'], r['version'], r['start'])])])
for a, b in zip(seq, seq[1:]): units.append(mp['s']['%d_%d' % (a, b)])
units.append(mp['b'][str(seq[0])])
lines = open(cnf_in).read().splitlines()
hdr = [l for l in lines if l.startswith('p ')][0].split()
nv, nc = int(hdr[2]), int(hdr[3])
with open(cnf_out, 'w') as f:
    f.write('p cnf %d %d\n' % (nv, nc + len(units)))
    for l in lines:
        if not l.startswith('p ') and not l.startswith('c'): f.write(l + '\n')
    for u in units: f.write('%d 0\n' % u)
print('units', len(units))
