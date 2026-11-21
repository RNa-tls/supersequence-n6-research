#!/usr/bin/env python3
"""Round Omega -- markdown table of the surviving frontier cells of a frontier_compat.py result (for the report).
usage: report_cells.py RESULT.json"""
import sys, json
T = json.load(open(sys.argv[1]))
surv = [c for c in T['rows'] if not c['excluded']]
print('| cell (R, p, F) | chains n | Delta | min deficit | margin | junctions (loops, pairs, shared) | one optimal decomposition (rows: v1/v2, kinds line 1/line 2) |')
print('|---|---|---|---|---|---|---|')
for c in surv:
    j = c['junction_argmin']
    dec = ' + '.join('%d: %d/%d %s/%s' % (x['r'], x['v1'], x['v2'], x['line1_kind'], x['line2_kind']) for x in c['decomposition'])
    print('| (%d, %d, %d) | %d | %d | %d | %d | %d, %d, %d | %s |' % (c['R'], c['p'], c['F'], c['chains'], c['Delta'], c['min_deficit'], c['margin'],
                                                                 j['F_loops'], j['F_pairs'], j['shared_rows'], dec))
print()
from collections import Counter
print('survivors:', len(surv), ' margins:', dict(sorted(Counter(c['margin'] for c in surv).items())))
print('removed relative to the input list:', [(c['R'], c['p'], c['F']) for c in T['rows'] if c['excluded']])
