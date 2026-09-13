"""One path plus d nonpure cycles: independently checked resource convolution.

No literal search is performed. Missing cycle cells use proved opened-path
relaxations, never capped empirical maxima. Exact-P decisions are not maxima.
"""
import argparse
import functools
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from prepare_round143_general_bounds_codex import build
from verify_round143_coupled_codex import validate_capacity_file
from verify_round143_coupled_extraction_codex import optimizers, NEG
from verify_round143_cycle_controls_codex import replay_cycle

ROOT = Path(__file__).resolve().parents[1]
BASE = 'outputs/rr_round143_generic_query_ledger_codex.json'
CLOSED = {'STRICT', 'SIGMA_DEFICIT_OBSTRUCTION', 'EXACT_P_EXCLUDED',
          'ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED', 'GENERAL_EXACT_P_EXCLUDED',
          'GENERAL_ALL_STATIC_COMPLETIONS_EXCLUDED', 'COMPONENT_CAPACITY_EXCLUDED'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_cycles(path):
    raw = json.loads(path.read_text())
    assert raw['schema'] == 'round143-paired-cycle-capacity-v1'
    cells = []
    for row in raw['rows']:
        A,Q,R,H,b,D = (row[k] for k in ('A','Qs','R','H','b','D'))
        grids = []
        for side in ('producer','independent'):
            run = row[side]
            assert run['proof_query'] == 'CYCLE_CAPACITY'
            assert not run['suffix_bound_enabled']
            file = ROOT/run['export_file']
            assert sha(file) == run['export_sha256']
            grid = {}
            for line in file.read_text().splitlines():
                record = json.loads(line)
                checked = replay_cycle(record['entries'], A,Q,R,H,b,D)
                key = checked['b'], checked['D']
                assert key not in grid
                assert record['b'] == key[0] and record['D'] == key[1]
                assert record['P'] == checked['P']
                grid[key] = checked['P']
            assert len(grid) == run['exported_prefixes']
            assert max(grid.values(), default=0) == run['max_passes']
            grids.append(grid)
        complete = all(row[s]['completed'] and not row[s]['capped'] for s in ('producer','independent'))
        assert complete == row['complete']
        if not complete:
            assert row['status'] == 'UNKNOWN_CAP'
            continue
        assert grids[0] == grids[1]
        assert row['producer']['accepted_cycles'] == row['independent']['accepted_cycles']
        assert grids[0] == {(c['b'],c['D']):c['maximum'] for c in row['exact_resource_grid']}
        cells.append(dict(A=A,Q=Q,R=R,H=H,b=b,D=D,grid=grids[0],source=path.relative_to(ROOT).as_posix()))
    return cells


def allocators(path_capacity, cycle_capacity):
    """Budgets (A,Q,extra_R,H,b,D); first four exact allocated upper resources.

    A,Q are actual exact counts. extra_R/H may be padded so their upper
    budgets can be allocated with equality. Actual b,D allocations are exact.
    """
    @functools.lru_cache(None)
    def back(d, key):
        if d == 0:
            p = path_capacity(*key)
            return p if p else NEG
        best = NEG
        for chosen in itertools.product(*(range(x+1) for x in key)):
            c = cycle_capacity(*chosen)
            if not c:
                continue
            rest = tuple(x-y for x,y in zip(key,chosen))
            value = back(d-1, rest)
            if value != NEG:
                best = max(best, c+value)
        return best

    def forward(d, budget):
        # Independent bottom-up product of cycle resource polynomials.
        zero = (0,)*6
        table = {zero:0}
        options = [(key, cycle_capacity(*key))
                   for key in itertools.product(*(range(v+1) for v in budget))]
        options = [(key,value) for key,value in options if value]
        for _ in range(d):
            nxt = {}
            for used,value in table.items():
                for cost,cap in options:
                    key = tuple(x+y for x,y in zip(used,cost))
                    if any(x>y for x,y in zip(key,budget)):
                        continue
                    nxt[key] = max(nxt.get(key,NEG),value+cap)
            table = nxt
        best = NEG
        for used,value in table.items():
            rest = tuple(x-y for x,y in zip(budget,used))
            p = path_capacity(*rest)
            if p:
                best = max(best,value+p)
        return best
    return back,forward


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cycles', nargs='*')
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    data = json.loads((ROOT/BASE).read_text())
    hashes = {BASE:sha(ROOT/BASE)}
    cells = []
    for rel in data['input_sha256']:
        if 'general_endpoint_corrected' in rel:
            continue
        new,digest = validate_capacity_file(ROOT/rel)
        assert digest == data['input_sha256'][rel]
        cells += new
        hashes[rel] = digest
    cyclecells = []
    for rel in args.cycles:
        cyclecells += read_cycles(ROOT/rel)
        hashes[rel] = sha(ROOT/rel)
    residual = [r for r in data['rows'] if r['L']==871 and r['status'] not in CLOSED]
    assert all(r['d']>0 for r in residual)
    queries = [(r['D2'],r['Qs'],r['D2']+r['Z']-r['d'],r['H'],r['Bstar'],
                5*r['k']-r['G']+5*r['Bstar'],r['P_required']) for r in residual]
    rows,nchecked = build(cells,queries)
    general = {tuple(r[:-1]):r[-1] for r in rows}
    direct,_,_ = optimizers(cells)
    evidence = {}

    @functools.lru_cache(None)
    def path(a,q,e,h,b,D):
        R = a+q+e
        value = min(120+R,general[(a,q,R,h,b,D+5*b)])
        if q==e==h==0:
            c = direct(a,b,D)
            if c is not None:
                value = min(value,c)
        return value

    @functools.lru_cache(None)
    def cycle(a,q,e,h,b,D):
        R = a+q+e
        # Open preferred closing A, else B, else a clean w3/heavy edge.
        # The opening preserves b,D,R and removes exactly its A/B/H cost.
        if a:
            fallback = path(a-1,q,e+1,h,b,D)
        elif q:
            fallback = path(a,q-1,e+1,h,b,D)
        else:
            fallback = path(a,q,e,h,b,D) # includes clean-w3 closure reservation
        possible = [c for c in cyclecells if c['A']==a and c['Q']==q and
                    c['R']>=R and c['H']>=h and c['b']>=b and c['D']>=D]
        # b,D are actual component resources; a complete grid can use the
        # exact cell, NOT the global maximum of the bounding rectangle.
        value = min([fallback]+[c['grid'].get((b,D),0) for c in possible])
        key = (a,q,e,h,b,D)
        evidence[key] = dict(A=a,Qs=q,R=R,H=h,b=b,D=D,upper=value,
                             opened_path_upper=fallback,
                             paired_cycle_sources=sorted({c['source'] for c in possible}))
        return value

    back,forward = allocators(path,cycle)
    checked = {}
    for row in residual:
        extra = row['Z']-row['d']-row['Qs']
        assert extra>=0
        options = []
        for sharing in range(row['Bstar']+1):
            key = (row['D2'],row['Qs'],extra,row['H'],row['Bstar']-sharing,
                   5*row['k']-row['G']+5*sharing)
            query = row['d'],key
            if query not in checked:
                v = back(*query)
                w = forward(*query)
                assert v==w,(query,v,w)
                checked[query] = v
            options.append(dict(sharing=sharing,resources=key,upper=checked[query]))
        upper = max(x['upper'] for x in options)
        row['component_convolution'] = dict(upper=upper,allocations=options,independent_dp_match=True)
        if upper < row['P_required']:
            row['status']='COMPONENT_CAPACITY_EXCLUDED'
        else:
            row['upper']=min(row['upper'],upper) if row['upper'] is not None else upper
            row['status']='EQUALITY' if row['upper']==row['P_required'] else 'OPEN_CAPACITY'
    data.update(schema='round143-path-cycle-convolution-v1',component_input_sha256=hashes,
                component_verifier_sha256=sha(Path(__file__)),
                component_suffix_cells=nchecked,component_allocation_cells=len(checked),
                component_cycle_capacity_evidence=[evidence[k] for k in sorted(evidence)],
                component_missing_cell_policy='proved opened-path relaxation; no capped maximum used')
    data['counts']={str(L):dict(Counter(r['status'] for r in data['rows'] if r['L']==L)) for L in (869,870,871)}
    data['threshold_closed']={str(L):all(r['status'] in CLOSED for r in data['rows'] if r['L']==L) for L in (869,870,871)}
    dest=ROOT/args.output
    assert not dest.exists(),'Preserve earlier ledgers'
    dest.write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(counts=data['counts'],allocation_cells=len(checked),suffix_cells=nchecked,
                         remaining=sum(r['status'] not in CLOSED for r in data['rows']))))


if __name__=='__main__':
    main()
