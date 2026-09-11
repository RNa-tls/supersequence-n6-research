"""Apply exact-P paired decisions only to their proved one-path domain."""
import hashlib
import json
from pathlib import Path
from collections import Counter
from verify_round143_coupled_codex import replay

ROOT=Path(__file__).resolve().parents[1]
BASE='outputs/rr_round143_t4_refined_envelopes_codex.json'
SOURCES=['outputs/rr_round143_t4_exact_prefix_pilot_codex.json',
         'outputs/rr_round143_t4_b0_exact_prefix_codex.json',
         'outputs/rr_round143_t4_reentry_exact_prefix_codex.json']


def main():
    out=json.loads((ROOT/BASE).read_text());hashes={};queries={}
    for name in [BASE]+SOURCES:
        hashes[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name in SOURCES:
        data=json.loads((ROOT/name).read_text())
        assert data['schema']=='round143-paired-exact-P-v1'
        for row in data['rows']:
            key=tuple(row[x] for x in ('A','b','D','P'))
            assert key not in queries,'Duplicate proof query'
            queries[key]=dict(source=name,status=row['status'],complete=row['complete'])
            sides=[]
            for side in ('producer','independent'):
                result=row[side]
                assert result['proof_query']=='EXACT_P_NOT_CAPACITY'
                assert result['suffix_bound_enabled']
                path=ROOT/result['exported_file']
                assert hashlib.sha256(path.read_bytes()).hexdigest()==result['export_sha256']
                entries=[]
                for line in path.read_text().splitlines():
                    x=json.loads(line);p=x['entries'] if isinstance(x,dict) else x
                    r=replay(p)
                    assert r['A']==row['A'] and r['P']==row['P'] and r['b']<=row['b'] and r['D']<=row['D']
                    entries.append(tuple(p))
                assert len(entries)==len(set(entries))==result['independently_replayed_exports']
                sides.append(sorted(entries))
            if row['complete']:
                assert all(row[s]['completed'] and not row[s]['capped'] for s in ('producer','independent'))
                assert sides[0]==sides[1]
                assert hashlib.sha256(json.dumps(sides[0],separators=(',',':')).encode()).hexdigest()==row['canonical_exports_sha256']
                assert (not sides[0])==(row['status']=='NO_EXACT_P_PREFIX')
            else:
                assert row['status']=='UNKNOWN_CAP'
    static_file=ROOT/'outputs/rr_round143_marked96_completion_codex.json'
    static=json.loads(static_file.read_text())
    assert static['all_static_completions_impossible'] and static['exact_marked_prefixes']==2
    hashes[static_file.relative_to(ROOT).as_posix()]=hashlib.sha256(static_file.read_bytes()).hexdigest()
    closed={'STRICT','SIGMA_DEFICIT_OBSTRUCTION'}
    for r in out['rows']:
        if r['L']!=871 or r['Z'] or r['H'] or r['status'] in closed:
            continue
        key=(r['D2'],r['Bstar'],5*r['k']-r['G'],r['P_required'])
        cert=queries.get(key)
        if cert is None or not cert['complete']:
            continue
        r['exact_P_certificate']=cert
        if cert['status']=='NO_EXACT_P_PREFIX':
            r['status']='EXACT_P_EXCLUDED'
        elif key==(0,0,14,96):
            assert r['k']==4 and r['G']==r['c']==6
            r['status']='ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED'
    closed|={'EXACT_P_EXCLUDED','ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED'}
    out.update(schema='round143-exact-query-threshold-ledger-v1',exact_query_input_sha256=hashes,
               unique_queries=len(queries),query_status_counts=dict(Counter(r['status'] for r in queries.values())))
    out['counts']={str(L):dict(Counter(r['status'] for r in out['rows'] if r['L']==L)) for L in (869,870,871)}
    out['threshold_closed']={str(L):all(r['status'] in closed for r in out['rows'] if r['L']==L) for L in (869,870,871)}
    out['Z0_H0_871_closed']=all(r['status'] in closed for r in out['rows'] if r['L']==871 and r['Z']==r['H']==0)
    (ROOT/'outputs/rr_round143_t4_exact_query_ledger_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(counts=out['counts'],queries=out['unique_queries'],query_counts=out['query_status_counts'],Z0_H0_871_closed=out['Z0_H0_871_closed'])))


if __name__=='__main__':
    main()
