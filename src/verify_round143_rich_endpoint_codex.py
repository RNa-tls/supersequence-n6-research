"""Triple-overlap endpoint recurrence; exact local run geometry, relaxed joins."""
import functools,json,argparse
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NEG=-100000
def solve(table,local):
    @functools.lru_cache(None)
    def rec(a,o,b,D,bad,prev,context,incomingA):
        vals=[]
        for bb in range(b+1):
            for dd in range(D+1):
                caps=table.get((bb,dd))
                if caps is None:return None
                for first,last,single,p in caps:
                    spent=0
                    if incomingA:
                        geom=local[(context,prev,first) if context else (prev,first)]
                        if geom['entry_collision']:continue
                        spent=geom['last_run_extra_overlap']
                    if spent>bad:continue
                    nc=prev if single and incomingA else 0
                    if a+o==0:
                        if bb==b and dd==D:vals.append(p)
                    else:
                        for aa,oo,kind in ([(a-1,o,1)] if a else [])+([(a,o-1,0)] if o else []):
                            v=rec(aa,oo,b-bb,D-dd,bad-spent,last,nc,kind)
                            if v is None:return None
                            if v!=NEG:vals.append(p+v)
        return max(vals,default=NEG)
    return rec
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-length',type=int,default=870);args=ap.parse_args()
    data=json.loads((ROOT/'outputs/rr_round143_rich_capacities_codex.json').read_text());table={}
    for r in data['rows']:
        assert r['complete'];a,b=r['producer'],r['independent'];assert a['rich_endpoint_max_passes']==b['rich_endpoint_max_passes']
        table[r['b'],r['D']]=[(i%25//5+1,i%5+1,i//25,p) for i,p in enumerate(a['rich_endpoint_max_passes']) if p]
    local={tuple(r['lengths']):r for r in json.loads((ROOT/'outputs/rr_round143_sigma_local_codex.json').read_text())['rows']}
    rec=solve(table,local);out=json.loads((ROOT/'outputs/rr_round143_general_endpoint_corrected_codex.json').read_text())
    for r in out['rows']:
        if r['L']>args.max_length or r['status']=='STRICT':continue
        lost=min(r['D2'],r['d']);a=r['D2']-lost;o=r['Z']+r['h']+lost
        v=rec(a,o,r['b_sum'],r['D_sum'],r['Z']-r['Qs'],0,0,0);r['rich_upper']=v
        if v is not None:
            r['upper']=v;r['status']='STRICT' if v<r['P_required'] else ('EQUALITY' if v==r['P_required'] else 'OPEN_CAPACITY')
    out['schema']='round143-rich-endpoint-v1';out['counts']={str(L):dict(Counter(r['status'] for r in out['rows'] if r['L']==L)) for L in (869,870,871)}
    out['threshold_closed']={str(L):all(r['status']=='STRICT' for r in out['rows'] if r['L']==L) for L in (869,870,871)}
    out['rich_recurrence_independent_verification']='PENDING';out['cache']=str(rec.cache_info())
    (ROOT/'outputs/rr_round143_rich_envelopes_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['counts']));print(out['cache'])
    residual=[r for r in out['rows'] if r['L']==870 and r['status']!='STRICT']
    print(json.dumps(residual))
if __name__=='__main__':main()
