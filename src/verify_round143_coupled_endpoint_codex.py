"""Endpoint-aware coupled-piece necessary bound; two allocation algorithms.

No literal search. Missing capacities propagate UNKNOWN. Exact A is never
treated monotonically. See RR_ROUND143_COUPLED_ENDPOINT_INDEPENDENT_CODEX.md.
"""
import argparse
from collections import Counter
import functools
import hashlib
import json
from pathlib import Path
from verify_round143_coupled_codex import validate_capacity_file

ROOT=Path(__file__).resolve().parents[1]
NEG=-100000


def optimizers(cells):
    @functools.lru_cache(None)
    def capacity(A,b,D):
        if A>D+5*b:
            return (0,0,0,0)
        options=[r['endpoints'] for r in cells if r['A']==A and r['b']>=b and r['D']>=D]
        return tuple(min(v[i] for v in options) for i in range(4)) if options else (None,)*4

    @functools.lru_cache(None)
    def back(internal,seams,other,b,D,bad,require_partial=0):
        if internal>D+5*b:
            return NEG
        best=NEG;unknown=False
        last=seams+other==0
        for aa in ([internal] if last else range(internal+1)):
            for bb in ([b] if last else range(b+1)):
                for dd in ([D] if last else range(D+1)):
                    for mask,value in enumerate(capacity(aa,bb,dd)):
                        if value==0:
                            continue
                        spent=int(require_partial and not(mask&1))
                        if spent>bad:
                            continue
                        if last:
                            if value is None:unknown=True
                            else:best=max(best,value)
                            continue
                        moves=[]
                        if seams:moves.append((seams-1,other,int(not(mask&2))))
                        if other:moves.append((seams,other-1,0))
                        for ns,no,nr in moves:
                            tail=back(internal-aa,ns,no,b-bb,D-dd,bad-spent,nr)
                            if tail==NEG:continue
                            if value is None or tail is None:unknown=True
                            else:best=max(best,value+tail)
        return None if unknown else best

    def forward(INTERNAL,SEAMS,OTHER,B,D,BAD):
        # Independently allocate a sequence left-to-right; a seam is chosen
        # on entering a new piece, not when leaving the preceding piece.
        # State: internal A, designated seams, other joins, b, D, bad, lastpartial.
        current={(0,0,0,0,0,0,False):(0,False)}
        for step in range(SEAMS+OTHER+1):
            nxt={}
            for (a,s,o,b,d,bad,last),(value,unknown) in current.items():
                for aa in range(INTERNAL-a+1):
                    for bb in range(B-b+1):
                        for dd in range(D-d+1):
                            if INTERNAL-a-aa>D-d-dd+5*(B-b-bb):continue
                            for mask,cap in enumerate(capacity(aa,bb,dd)):
                                if cap==0:continue
                                joins=[(s,o,bad)] if step==0 else []
                                if step and s<SEAMS:
                                    nb=bad+int(not(last or mask&1))
                                    if nb<=BAD:joins.append((s+1,o,nb))
                                if step and o<OTHER:joins.append((s,o+1,bad))
                                for ns,no,nb in joins:
                                    key=(a+aa,ns,no,b+bb,d+dd,nb,bool(mask&2))
                                    old,unc=nxt.get(key,(NEG,False))
                                    score=value+cap if cap is not None and value!=NEG else NEG
                                    nxt[key]=(max(old,score),unc or unknown or cap is None)
            current=nxt
        results=[v for (a,s,o,b,d,bad,last),v in current.items()
                 if (a,s,o,b,d)==(INTERNAL,SEAMS,OTHER,B,D)]
        return None if any(u for v,u in results) else max((v for v,u in results),default=NEG)
    return capacity,back,forward


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+')
    ap.add_argument('--base',default='outputs/rr_round143_t4_combined_codex.json')
    ap.add_argument('--output',default='outputs/rr_round143_t4_coupled_endpoint_codex.json')
    args=ap.parse_args();cells=[];hashes={}
    for rel in args.inputs:
        new,sha=validate_capacity_file(ROOT/rel);cells+=new;hashes[rel]=sha
    hashes[args.base]=hashlib.sha256((ROOT/args.base).read_bytes()).hexdigest()
    data=json.loads((ROOT/args.base).read_text())
    capacity,back,forward=optimizers(cells);checked={}
    closed={'STRICT','SIGMA_DEFICIT_OBSTRUCTION','EXACT_P_EXCLUDED','ALL_PREFIX_STATIC_COMPLETIONS_EXCLUDED'}
    for r in data['rows']:
        if r['status'] in closed:continue
        best=NEG;unknown=False;maximizers=[]
        for sharing in range(r['Bstar']+1):
            for m in range(1,r['Z']+r['d']+2+r['h']):
                for retained in range(max(0,r['D2']+r['Qs']-r['Z']-r['d']),r['D2']+1):
                    # Each lost A is either one of d cycle openings or a
                    # distinct linear split. Thus A-Aret <= m-1.
                    if r['D2']-retained>m-1:continue
                    seams=max(0,r['D2']-retained-r['d'])
                    if seams>m-1:continue
                    key=(retained,seams,m-1-seams,r['Bstar']-sharing,
                         5*r['k']-r['G']+5*sharing,r['Z']-r['Qs'])
                    val=back(*key)
                    if key not in checked:
                        second=forward(*key)
                        assert second==val,(key,val,second)
                        checked[key]=val
                    if val is None:unknown=True
                    elif val>best:best=val;maximizers=[key]
                    elif val==best:maximizers.append(key)
        r['coupled_endpoint_upper']=None if unknown else best
        r['coupled_endpoint_maximizers']=maximizers
        if not unknown and (r['upper'] is None or best<r['upper']):
            r['upper']=best
            r['status']='STRICT' if best<r['P_required'] else ('EQUALITY' if best==r['P_required'] else 'OPEN_CAPACITY')
    data.update(schema='round143-coupled-endpoint-ledger-v1',endpoint_input_sha256=hashes,
                endpoint_independent_cells=len(checked),
                endpoint_recurrence='Aret; a=max(0,A-Aret-d); other=m-1-a; bad<=Z-Qs; new sharing in [0,Bstar]')
    data['counts']={str(L):dict(Counter(r['status'] for r in data['rows'] if r['L']==L)) for L in (869,870,871)}
    data['threshold_closed']={str(L):all(r['status'] in closed for r in data['rows'] if r['L']==L) for L in (869,870,871)}
    (ROOT/args.output).write_text(json.dumps(data,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(counts=data['counts'],independent_cells=len(checked),cache=str(back.cache_info()))))


if __name__=='__main__':main()
