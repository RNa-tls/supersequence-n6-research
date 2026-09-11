"""Necessary coupled-piece extraction, with independent forward convolution.

Every input capacity is checked by paired exhaustion and independent literal
replay. Exact A is never treated as monotone. Missing cells mean UNKNOWN.
"""
import argparse
import functools
import hashlib
import json
from collections import Counter
from pathlib import Path
from verify_round143_coupled_codex import validate_capacity_file

ROOT=Path(__file__).resolve().parents[1]
NEG=-100000


def optimizers(cells):
    @functools.lru_cache(None)
    def capacity(A,b,D):
        # Hand sigma-cluster deficit theorem, including old-Q entries.
        if A>D+5*b:
            return 0
        possible=[r['upper'] for r in cells if r['A']==A and r['b']>=b and r['D']>=D]
        return min(possible) if possible else None

    @functools.lru_cache(None)
    def backward(m,A,b,D):
        if A>D+5*b:
            return NEG
        if m==1:
            v=capacity(A,b,D)
            return None if v is None else (v if v else NEG)
        best=NEG
        unknown=False
        for aa in range(A+1):
            for bb in range(b+1):
                for dd in range(D+1):
                    x=capacity(aa,bb,dd)
                    if x==0:
                        continue
                    y=backward(m-1,A-aa,b-bb,D-dd)
                    if y==NEG:
                        continue
                    if x is None or y is None:
                        unknown=True
                    else:
                        best=max(best,x+y)
        return None if unknown else best

    def forward(m,A,B,D):
        # Build prefix allocations independently. Track unknown reachability
        # separately rather than propagating a fictitious numeric capacity.
        current={(0,0,0):(0,False)}
        for _ in range(m):
            nxt={}
            for (a,b,d),(value,unknown) in current.items():
                for aa in range(A-a+1):
                    for bb in range(B-b+1):
                        for dd in range(D-d+1):
                            if A-(a+aa)>D-(d+dd)+5*(B-(b+bb)):
                                continue
                            x=capacity(aa,bb,dd)
                            if x==0:
                                continue
                            key=(a+aa,b+bb,d+dd)
                            old,unc=nxt.get(key,(NEG,False))
                            nxt[key]=(max(old,value+x if x is not None and value!=NEG else NEG),
                                      unc or unknown or x is None)
            current=nxt
        value,unknown=current.get((A,B,D),(NEG,False))
        return None if unknown else value
    return capacity,backward,forward


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+')
    ap.add_argument('--through',type=int,default=870)
    ap.add_argument('--output',default='outputs/rr_round143_coupled_extraction_codex.json')
    ap.add_argument('--verbose-residual',action='store_true')
    a=ap.parse_args()
    cells=[];hashes={}
    for rel in a.inputs:
        new,sha=validate_capacity_file(ROOT/rel)
        cells+=new;hashes[rel]=sha
    cap,back,fwd=optimizers(cells)
    base=ROOT/'outputs/rr_round143_general_endpoint_corrected_codex.json'
    hashes[base.relative_to(ROOT).as_posix()]=hashlib.sha256(base.read_bytes()).hexdigest()
    out=json.loads(base.read_text())
    verified={}
    for r in out['rows']:
        delta=5*r['k']-r['G']+5*r['Bstar']
        lower=r['D2']+r['Qs']-r['Z']-r['d']
        r['run_deficit']=delta;r['run_deficit_lower']=max(0,lower)
        if delta<lower:
            r['status']='SIGMA_DEFICIT_OBSTRUCTION'
            continue
        if r['L']>a.through or r['status']=='STRICT':
            continue
        mmax=r['Z']+r['d']+1+r['h']
        values=[];unknown=False
        for s in range(r['Bstar']+1):
            for m in range(1,mmax+1):
                for retained in range(max(0,lower),r['D2']+1):
                    args=(m,retained,r['Bstar']-s,5*r['k']-r['G']+5*s)
                    v=back(*args)
                    if args not in verified:
                        second=fwd(*args)
                        assert second==v,(args,v,second)
                        verified[args]=v
                    if v is None:
                        unknown=True
                    else:
                        values.append(v)
        v=None if unknown else max(values,default=NEG)
        r['coupled_extraction_upper']=v
        r['coupled_m_max']=mmax
        r['coupled_new_sharing']='MAXIMIZED_INDEPENDENTLY_OF_OLD_s'
        if v is not None and (r['upper'] is None or v<r['upper']):
            r['upper']=v
            r['status']='STRICT' if v<r['P_required'] else ('EQUALITY' if v==r['P_required'] else 'OPEN_CAPACITY')
    out.update(schema='round143-general-coupled-extraction-v1',input_sha256=hashes,
               independently_checked_convolution_cells=len(verified),independent_through=a.through,
               recurrence_domain='1<=m<=Z+d+1+h; Aret in [max(0,A+Qs-Z-d),A]; fresh sharing s-prime in [0,Bstar]',
               cache=str(back.cache_info()))
    out['counts']={str(L):dict(Counter(r['status'] for r in out['rows'] if r['L']==L)) for L in (869,870,871)}
    out['threshold_closed']={str(L):all(r['status'] in ('STRICT','SIGMA_DEFICIT_OBSTRUCTION') for r in out['rows'] if r['L']==L) for L in (869,870,871)}
    (ROOT/a.output).write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['counts']))
    print('independent convolution cells',len(verified))
    for r in out['rows']:
        if a.verbose_residual and r['L']==a.through and r['status'] not in ('STRICT','SIGMA_DEFICIT_OBSTRUCTION'):
            print(json.dumps(r))


if __name__=='__main__':
    main()
