"""Build a hashed scalar-capacity input and verify the suffix hand identities."""
import argparse
import hashlib
import json
from pathlib import Path
from verify_round143_coupled_codex import validate_capacity_file, replay, WORDS, orbit

ROOT=Path(__file__).resolve().parents[1]
INDEX={p:i for i,p in enumerate(WORDS)}


def normalize(entries):
    first=WORDS[entries[0]]
    inverse={v:i for i,v in enumerate(first)}
    return [INDEX[tuple(inverse[v] for v in WORDS[i])] for i in entries]


def upper(cells,A,b,delta):
    if delta<0 or b<0 or A<0 or A>delta:
        return 0
    maxima=[]
    for bb in range(min(b,delta//5)+1):
        D=delta-5*bb
        terms=[c['upper'] for c in cells if c['A']==A and c['b']>=bb and c['D']>=D]
        if not terms:
            return None
        maxima.append(min(terms))
    return max(maxima,default=0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+')
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    destination=ROOT/a.output
    assert not destination.exists(),'Bound tables are frozen inputs; use a new path'
    hashes={};cells=[];witnesses=[]
    for name in a.inputs:
        new,digest=validate_capacity_file(ROOT/name)
        cells+=new;hashes[name]=digest
        data=json.loads((ROOT/name).read_text())
        for row in data['rows']:
            if not row['complete']:
                continue
            for r in (row['producer'],row['independent']):
                path=r['witness']
                entries=path['entries'] if isinstance(path,dict) else path
                if entries:
                    witnesses.append(entries)
    dedup={}
    for c in cells:
        key=c['A'],c['b'],c['D']
        if key in dedup:
            assert dedup[key]==c['upper']
        dedup[key]=c['upper']
    checks=bounded=old_boundary=0
    for entries in witnesses:
        whole=replay(entries)
        for n,kind in enumerate(whole['kinds'],1):
            if kind=='E':
                continue
            before=replay(entries[:n])
            after=replay(normalize(entries[n:]))
            old=int(orbit(WORDS[entries[n]]) in {orbit(WORDS[i]) for i in entries[:n]})
            remaining_b=whole['b']-before['b']-old
            remaining_A=whole['A']-before['A']-int(kind=='A')
            delta=whole['D']+5*whole['b']-before['D']-5*before['b']
            assert after['A']==remaining_A
            assert after['b']<=remaining_b
            assert after['D']+5*after['b']==delta
            bound=upper(cells,remaining_A,remaining_b,delta)
            if bound is not None:
                assert after['P']<=bound,(entries,n,after,bound)
                bounded+=1
            checks+=1;old_boundary+=old
    records=[(*key,value) for key,value in sorted(dedup.items())]
    text=''.join('%d %d %d %d\n'%r for r in records)
    destination.write_text(text,newline='\n')
    out=dict(schema='round143-certified-suffix-table-v1',input_sha256=hashes,
             table=destination.relative_to(ROOT).as_posix(),table_sha256=hashlib.sha256(text.encode()).hexdigest(),
             cell_count=len(records),witnesses_checked=len(witnesses),nonE_splits=checks,
             splits_with_finite_upper=bounded,old_orbit_boundary_splits=old_boundary,
             all_suffix_identities_verified=True,all_available_upper_bounds_verified=True,
             missing_cells='INFINITY: NO PRUNE',scope='Finite positive controls plus separate hand inclusion theorem')
    destination.with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out))


if __name__=='__main__':
    main()
