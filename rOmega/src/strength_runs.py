#!/usr/bin/env python3
"""Round Omega -- HYPOTHETICAL strength measurements on top of a PROVED knapsack configuration.
For each (r0, c): add the unproved statement "every chain of >= r0 rows has line-2 value <= c" and report which
cells survive.  These runs are NOT proofs and remove no cell; they measure what a long-chain density theorem would
have to say.  usage: strength_runs.py PROVED_CONFIG.json OUTDIR r0:c [r0:c ...]"""
import sys, json, subprocess, os
cfg_path, outdir = sys.argv[1], sys.argv[2]; os.makedirs(outdir, exist_ok=True)
base = json.load(open(cfg_path)); rows = []
here = os.path.dirname(os.path.abspath(__file__))
for spec in sys.argv[3:]:
    r0, c = map(int, spec.split(':'))
    cfg = dict(base); cfg['HYPOTHESIS_cap'] = [r0, c]
    cp = os.path.join(outdir, 'HYPOTHETICAL_cap_%d_%d_config.json' % (r0, c)); json.dump(cfg, open(cp, 'w'), indent=1)
    op = os.path.join(outdir, 'HYPOTHETICAL_cap_%d_%d.json' % (r0, c))
    subprocess.run([sys.executable, '-I', os.path.join(here, 'frontier_compat.py'), cp, op], check=True, stdout=subprocess.DEVNULL)
    T = json.load(open(op)); surv = [(x['R'], x['p'], x['F']) for x in T['rows'] if not x['excluded']]
    rows.append(dict(r0=r0, c=c, survivors=len(surv), cells=surv)); print(r0, c, len(surv), surv, flush=True)
json.dump(rows, open(os.path.join(outdir, 'HYPOTHETICAL_strength_summary.json'), 'w'), indent=1)
