"""Certified suffix upper bounds for generic one-path exact-P queries.

No path search: resource allocation only, checked backward and forward.
"""
import argparse
import functools
import hashlib
import json
from pathlib import Path
from verify_round143_coupled_codex import validate_capacity_file
from verify_round143_coupled_extraction_codex import optimizers,NEG

ROOT=Path(__file__).resolve().parents[1]


def build(cells,queries):
    cap,back,forward=optimizers(cells);checked={}
    @functools.lru_cache(None)
    def upper(a,q,r,h,B,delta):
        if r<a+q:return 0
        best=NEG;unknown=False
        for old in range(min(B,delta//5)+1):
            for m in range(1,2+h+r-a):
                for retained in range(max(0,2*a+q-r),a+1):
                    if a-retained>m-1:continue
                    args=(m,retained,old,delta-5*old)
                    if args not in checked:
                        v=back(*args);w=forward(*args)
                        assert v==w,(args,v,w);checked[args]=v
                    value=checked[args]
                    if value is None:unknown=True
                    else:best=max(best,value)
        return 100000 if unknown else max(0,best)
    keys=set()
    for A,Q,R,H,B,D,P in queries:
        for a in range(A+1):
            for q in range(Q+1):
                for r in range(R+1):
                    for h in range(H+1):
                        for b in range(B+1):
                            for delta in range(D+5*B+1):keys.add((a,q,r,h,b,delta))
    rows=[(*key,upper(*key)) for key in sorted(keys)]
    return rows,len(checked)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('inputs',nargs='+')
    ap.add_argument('--base',default='outputs/rr_round143_t4_combined_codex.json')
    ap.add_argument('--output',default='outputs/rr_round143_general_suffix_v1.json')
    args=ap.parse_args();cells=[];hashes={}
    for rel in args.inputs:
        new,sha=validate_capacity_file(ROOT/rel);cells+=new;hashes[rel]=sha
    hashes[args.base]=hashlib.sha256((ROOT/args.base).read_bytes()).hexdigest()
    base=json.loads((ROOT/args.base).read_text())
    residual=[r for r in base['rows'] if r['L']==871 and r['d']==0
              and r['status'] in ('EQUALITY','OPEN_CAPACITY','UNKNOWN_CAPACITY')]
    queries=sorted({(r['D2'],r['Qs'],r['D2']+r['Z'],r['H'],r['Bstar'],5*r['k']-r['G'],r['P_required']) for r in residual})
    rows,n=build(cells,queries)
    outpath=ROOT/args.output;table=outpath.with_suffix('.txt')
    table.write_text(''.join(' '.join(map(str,r))+'\n' for r in rows),newline='\n')
    data=dict(schema='round143-general-suffix-bounds-v1',query_fields=['A','Qs','R','H','b','D','P'],
              queries=queries,domain='d=0 ONLY; one beta path',input_sha256=hashes,
              table_file=table.relative_to(ROOT).as_posix(),table_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
              table_fields=['A_remaining','Qs_remaining','R_upper','H_upper','b_upper','delta_upper','upper_passes'],
              independent_convolution_cells=n,table_rows=len(rows),missing_or_unknown_upper=100000,
              strict_unknown_note='100000 is conservative sentinel, not a computed finite maximum')
    outpath.write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(queries=len(queries),table_rows=len(rows),independent_cells=n)))


if __name__=='__main__':main()
