"""Apply complete exact-P component decisions to ALL surviving port allocations.

One exact-P NO can refute its pair, not a larger/smaller P. A positive
necessary-model path/cycle does not assert a realizable global cover.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from run_round143_general_prefix_codex import FIELDS, readpaths, sha
from verify_round143_cycle_controls_codex import replay_cycle
from verify_round143_component_convolution_codex import CLOSED

ROOT=Path(__file__).resolve().parents[1]


def load_decisions(path):
    source=json.loads(path.read_text())
    kind={'round143-paired-general-exact-P-v1':'path',
          'round143-paired-cycle-exact-P-v1':'cycle'}[source['schema']]
    answer={}
    for row in source['rows']:
        key=tuple(row[k] for k in FIELDS)
        paths=[]
        for side in ('producer','independent'):
            run=row[side];file=ROOT/run['export_file']
            assert sha(file)==run['export_sha256']
            assert run['proof_query']==('EXACT_P_NOT_CAPACITY' if kind=='path' else 'EXACT_CYCLE_P_NOT_CAPACITY')
            if kind=='path':
                items=readpaths(file,key)
            else:
                listed=[]
                for line in file.read_text().splitlines():
                    record=json.loads(line);entries=record['entries'] if isinstance(record,dict) else record
                    replay_cycle(entries,*key[:6])
                    assert len(entries)==key[-1]
                    listed.append(tuple(entries))
                assert len(listed)==len(set(listed))
                items=set(listed)
            assert len(items)==run['exported_prefixes']
            paths.append(items)
        complete=all(row[s]['completed'] and not row[s]['capped'] for s in ('producer','independent'))
        assert complete==row['complete']
        if complete:
            assert paths[0]==paths[1]
            answer[key]=dict(kind=kind,possible=bool(paths[0]),source=path.relative_to(ROOT).as_posix(),
                             exact_P=key[-1],export_count=len(paths[0]))
    return kind,answer


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True)
    ap.add_argument('--decisions',nargs='+',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();data=json.loads((ROOT/args.base).read_text());decisions={'path':{},'cycle':{}}
    hashes={args.base:sha(ROOT/args.base)}
    for rel in args.decisions:
        kind,new=load_decisions(ROOT/rel);hashes[rel]=sha(ROOT/rel)
        for k,v in new.items():
            if k in decisions[kind]:assert v['possible']==decisions[kind][k]['possible']
            decisions[kind][k]=v
    for row in data['rows']:
        if row['status'] in CLOSED:continue
        if row['d']!=1:continue
        assert 'component_exact_P_pairs' in row,'Need exhaustive allocation and residue-class export'
        survivors=[];killed=[]
        for pair in row['component_exact_P_pairs']:
            reasons=[decisions[kind][tuple(pair[kind])] for kind in ('path','cycle')
                     if tuple(pair[kind]) in decisions[kind] and not decisions[kind][tuple(pair[kind])]['possible']]
            if reasons:killed.append(dict(pair=pair,reasons=reasons))
            else:survivors.append(pair)
        row['component_pair_exclusions']=killed
        row['remaining_component_pairs']=survivors
        if not survivors:
            row['status']='ALL_COMPONENT_P_PAIRS_EXCLUDED'
    closed=CLOSED|{'ALL_COMPONENT_P_PAIRS_EXCLUDED'}
    data.update(schema='round143-exact-component-pairs-ledger-v1',component_pair_input_sha256=hashes,
                pair_verifier_sha256=sha(Path(__file__)))
    data['counts']={str(L):dict(Counter(r['status'] for r in data['rows'] if r['L']==L)) for L in (869,870,871)}
    data['threshold_closed']={str(L):all(r['status'] in closed for r in data['rows'] if r['L']==L) for L in (869,870,871)}
    dest=ROOT/args.output;assert not dest.exists()
    dest.write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(counts=data['counts'],remaining=sum(r['status'] not in closed for r in data['rows']))))


if __name__=='__main__':main()
