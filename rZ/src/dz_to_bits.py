#!/usr/bin/env python3
"""Round Z -- convert the LIST output of rZ/csrc/disjoint_z.c (nameX nameY same same_rev cross cross_rev | o:s:rank ..)
into the pair format of rX/csrc/disjoint_bits.c (nameX nameY zeros zeros_rev | o:rank ..) for rX/csrc/triple_test.c.
usage: dz_to_bits.py IN OUT"""
import sys
with open(sys.argv[2], 'w') as out:
    for line in open(sys.argv[1]):
        if line.startswith('#') or not line.strip(): continue
        head, _, tail = line.partition('|'); h = head.split()
        z0 = int(h[2]) + int(h[4]); z1 = int(h[3]) + int(h[5])
        pl = ['%s:%s' % (p.split(':')[0], p.split(':')[2]) for p in tail.split()]
        out.write('%s %s %d %d%s%s\n' % (h[0], h[1], z0, z1, ' |' if pl else '', (' ' + ' '.join(pl)) if pl else ''))
