"""Two independent finite endpoint-obligation optimizers, Z=0 only."""
import functools,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NEG=-100000
def optimizers(table):
    @functools.lru_cache(None)
    def backward(a,h,b,D,previous):
        # a sigma and h heavy boundaries remain after choosing this piece.
        # previous=0: no incoming constraint; 1: incoming requires first partial.
        vals=[]
        for bj in range(b+1):
            for dj in range(D+1):
                caps=table.get((bj,dj))
                if caps is None:return None
                for mask,p in enumerate(caps):
                    if not p or previous and not(mask&1):continue
                    if a+h==0:
                        if bj==b and dj==D:vals.append(p)
                    else:
                        if a:
                            z=backward(a-1,h,b-bj,D-dj,0 if mask&2 else 1)
                            if z is None:return None
                            if z!=NEG:vals.append(p+z)
                        if h:
                            z=backward(a,h-1,b-bj,D-dj,0)
                            if z is None:return None
                            if z!=NEG:vals.append(p+z)
        return max(vals,default=NEG)
    def forward(A,H,B,D):
        # Independently build layers of prefix allocations and edge counts.
        current={(0,0,0,0,False):0}
        for step in range(A+H+1):
            nxt={}
            for (a,h,b,d,rightpartial),value in current.items():
                for bb in range(B-b+1):
                    for dd in range(D-d+1):
                        caps=table.get((bb,dd))
                        if caps is None:return None
                        for mask,p in enumerate(caps):
                            if not p:continue
                            routes=[(a,h)] if step==0 else []
                            if step and a<A and (rightpartial or mask&1):routes.append((a+1,h))
                            if step and h<H:routes.append((a,h+1))
                            for na,nh in routes:
                                key=(na,nh,b+bb,d+dd,bool(mask&2))
                                nxt[key]=max(nxt.get(key,NEG),value+p)
            current=nxt
        return max((v for (a,h,b,d,r),v in current.items() if (a,h,b,d)==(A,H,B,D)),default=NEG)
    return backward,forward
def main():
    caps=json.loads((ROOT/'outputs/rr_round143_endpoint_capacities_codex.json').read_text())
    table={}
    for r in caps['rows']:
        assert r['complete'] and r['producer']['endpoint_max_passes']==r['independent']['endpoint_max_passes']
        table[r['b'],r['D']]=r['producer']['endpoint_max_passes']
    rec,forward=optimizers(table)
    rows=json.loads((ROOT/'outputs/rr_round143_marked_envelopes_codex.json').read_text())['rows']
    for r in rows:
        if r['Z']==0 and r['L']==869:
            args=(r['D2'],r['h'],r['b_sum'],r['D_sum']);a=rec(*args,0);b=forward(*args)
            assert a==b,(r,a,b)
            r['endpoint_upper']=a
            if a is not None and a<r['P_required']:r['status']='ENDPOINT_STRICT'
    out=dict(schema='round143-endpoint-obligation-v1',rows=rows,
      counts={str(L):dict(Counter(r['status'] for r in rows if r['L']==L)) for L in (869,870,871)},
      conditional_lemma='Z=0 implies one beta path; every sigma seam must have a partial incident E block.',
      independent_optimizers_agree=True,threshold_869_closed=all(r['status'] in ('STRICT','ENDPOINT_STRICT','COMPANION_DEFICIT_OBSTRUCTION') for r in rows if r['L']==869))
    (ROOT/'outputs/rr_round143_endpoint_envelopes_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['counts']))
    for r in rows:
        if r['L']==869 and r['status'] not in ('STRICT','ENDPOINT_STRICT','COMPANION_DEFICIT_OBSTRUCTION'):print(json.dumps(r))
if __name__=='__main__':main()
