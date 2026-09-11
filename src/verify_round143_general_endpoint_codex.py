"""Endpoint loss recurrence with bad-full/full A seams charged to topology.
Every selected capacity is an independently exhausted necessary model.
Unknown table cells propagate UNKNOWN, not an upper bound.
"""
import functools,json,hashlib,argparse
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NEG=-100000
def solver(table):
    @functools.lru_cache(None)
    def rec(a,other,b,D,bad,requires):
        vals=[]
        for bb in range(b+1):
            for dd in range(D+1):
                caps=table.get((bb,dd))
                if caps is None:return None
                for mask,p in enumerate(caps):
                    if p==0:continue
                    spent=int(requires and not(mask&1))
                    if spent>bad:continue
                    if a+other==0:
                        if bb==b and dd==D:vals.append(p)
                    else:
                        for na,no,nr in ([(a-1,other,int(not(mask&2)))] if a else [])+([(a,other-1,0)] if other else []):
                            sub=rec(na,no,b-bb,D-dd,bad-spent,nr)
                            if sub is None:return None
                            if sub!=NEG:vals.append(p+sub)
        return max(vals,default=NEG)
    return rec
def forward(table,A,OTH,B,D,BAD):
    cur={(0,0,0,0,0,False):0}
    for step in range(A+OTH+1):
        nxt={}
        for (a,o,b,d,spent,last),v in cur.items():
            for bb in range(B-b+1):
                for dd in range(D-d+1):
                    caps=table.get((bb,dd))
                    if caps is None:return None
                    for mask,p in enumerate(caps):
                        if not p:continue
                        ways=[(a,o,spent)] if step==0 else []
                        if step and a<A:
                            ns=spent+int(not(last or mask&1))
                            if ns<=BAD:ways.append((a+1,o,ns))
                        if step and o<OTH:ways.append((a,o+1,spent))
                        for aa,oo,ss in ways:
                            key=(aa,oo,b+bb,d+dd,ss,bool(mask&2));nxt[key]=max(nxt.get(key,NEG),v+p)
        cur=nxt
    return max((v for (a,o,b,d,s,l),v in cur.items() if (a,o,b,d)==(A,OTH,B,D)),default=NEG)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',nargs='+',default=['outputs/rr_round143_endpoint_capacities_codex.json','outputs/rr_round143_t3_capacities_codex.json']);ap.add_argument('--independent-through',type=int,default=869);ap.add_argument('--output',default='outputs/rr_round143_general_endpoint_codex.json');a=ap.parse_args()
    table={};hashes={}
    for rel in a.inputs:
        raw=(ROOT/rel).read_bytes();data=json.loads(raw);hashes[rel]=hashlib.sha256(raw).hexdigest()
        for row in data['rows']:
            if not row['complete']:continue
            x,y=row['producer'],row['independent'];assert x['endpoint_max_passes']==y['endpoint_max_passes']
            table[row['b'],row['D']]=x['endpoint_max_passes']
    rec=solver(table);rows=json.loads((ROOT/'outputs/rr_round143_threshold_budgets_codex.json').read_text())['rows']
    for r in rows:
        # A/B acyclicity does NOT ensure a nonpure cycle has a paid opening.
        # Up to d A seams may be lost at cycle openings. Demote extras;
        # charge interior bad seams by R_int >= A-x+Qs-y+bad, x+y<=d.
        lost=min(r['D2'],r['d'])
        args=(r['D2']-lost,r['Z']+r['h']+lost,r['b_sum'],r['D_sum'],r['Z']-r['Qs']);assert args[-1]>=0
        value=rec(*args,0);r['upper']=value
        r['status']='UNKNOWN_CAPACITY' if value is None else ('STRICT' if value<r['P_required'] else ('EQUALITY' if value==r['P_required'] else 'OPEN_CAPACITY'))
        if r['L']<=a.independent_through:
            second=forward(table,*args);assert second==value,(r,second);r['independent_dp_match']=True
    out=dict(schema='round143-general-endpoint-v1',input_sha256=hashes,rows=rows,
      counts={str(L):dict(Counter(r['status'] for r in rows if r['L']==L)) for L in (869,870,871)},
      bad_seam_lemma='interior full/full A seams <= Z-Qs; retain at least max(0,D2-d) designated A seams',
      correction_note='Initial uncommitted draft incorrectly required every nonpure cycle to open at a non-A/non-B paid edge. This version permits d lost A/B openings. Z=0/869 results unaffected.',
      independent_through=a.independent_through,threshold_closed={str(L):all(r['status']=='STRICT' for r in rows if r['L']==L) for L in (869,870,871)})
    (ROOT/a.output).write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['counts']))
    for L in (869,870,871):
        residual=[r for r in rows if r['L']==L and r['status'] in ('EQUALITY','OPEN_CAPACITY')]
        print('L',L,'residual',len(residual))
        if L<871:
            for r in residual:print(json.dumps(r))
if __name__=='__main__':main()
