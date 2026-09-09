"""All-G slack envelopes, no broad NR6 DFS. Exact S/F/G convention of R140."""
import collections,functools,hashlib,itertools,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(f):return json.loads((ROOT/'outputs'/f).read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def alloc(v,m):
    if m==1:yield (v,);return
    for a in range(v+1):
        for z in alloc(v-a,m-1):yield (a,)+z
def envelopes():
    old=load('rr_f0_column_115.json')['table'];fresh=load('rr_round140_capacity_codex.json');used={}
    assert fresh['verified'];new={}
    for r in fresh['rows']:
        z=r['result'];assert not z['capped'];new[z['b'],z['s']]=z['passes']
    @functools.lru_cache(None)
    def C(b,d):
        if (f'{b},0,{d}') in old:
            r=old[f'{b},0,{d}'];assert not r['capped'];v=r['passes'];source='R115 independently accepted'
        elif b==3 and d<=2:v=new[3,2];source='R140 paired b3/D2 monotone relaxation'
        elif b==2 and d<=7:v=new[2,2 if d<=2 else 7];source='R140 paired b2 monotone relaxation'
        elif b==1 and d<=13:
            r=load('rr_round136_capacity_codex.json')['capacity']['result'];assert not r['capped'];v=r['passes'];source='R136 independently accepted b1/D13'
        else:raise AssertionError((b,d))
        used[str((b,d))]=dict(upper=v,source=source);return v
    @functools.lru_cache(None)
    def bound(m,b,d):
        return max(sum(C(x,y) for x,y in zip(bs,ds)) for bs in alloc(b,m) for ds in alloc(d,m))
    rows=[]
    for k in range(1,5):
        for G in range(4,5*k+1):
            for z in range(4-k+1):
                for H in range(4-k-z+1):
                    B=4-k-z-H
                    for h in range(H+1):
                        for heavy in itertools.combinations_with_replacement([4,5,6],h):
                            if sum(w-3 for w in heavy)!=H:continue
                            m=z+1+h
                            for s in range(B+1):
                                if m==1 and s:continue
                                b=B-s;D=5*k-G+5*s;P=120-4*G+5*z;upper=bound(m,b,D)
                                rows.append(dict(k=k,G=G,z=z,c=G-z,H=H,heavy=heavy,b=b,s=s,D=D,m_max=m,
                                    P_required=P,upper=upper,margin=P-upper,
                                    status='CLOSED_STRICT' if upper<P else 'RESIDUAL_EQUALITY' if upper==P else 'RESIDUAL_CORE'))
    return dict(rows=rows,used_capacities=used)
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();env=envelopes()
    slack=[dict(k=k,J=J,delta=a,x=x,H=H) for k in range(1,5) for J in range(5-k)
        for a in range(5-k-J) for x in range(5-k-J-a) for H in range(5-k-J-a-x)]
    # k0 forcesG0,J0; ordinary G0 column is independently closed.
    k0=[dict(k=0,G=0,J=0,delta=a,x=x,H=H) for a in range(5) for x in range(5-a) for H in range(5-a-x)]
    cells=[]
    for k in range(5):
        for G in range(5*k+1):
            rr=[i for i,r in enumerate(env['rows']) if (r['k'],r['G'])==(k,G)]
            status='CLOSED_ACCEPTED_BASELINE' if G<=3 else 'CLOSED_STRICT' if all(env['rows'][i]['status']=='CLOSED_STRICT' for i in rr) else 'RESIDUAL_CORE'
            assert G<=3 or rr
            cells.append(dict(k=k,G=G,status=status,envelopes=rr,scope='NR6_CONDITIONAL'))
    assert sum(c['status']=='CLOSED_ACCEPTED_BASELINE' for c in cells)==17 and len(cells)==55
    out=dict(schema='codex/round141-outer/1',source_commit=head,accepted_baseline=17,total_cells=55,
        slack_types=slack,k0_slack=k0,envelopes=env,cells=cells,
        status_counts=dict(collections.Counter(c['status'] for c in cells)),NR6='ASSUMED',global_L6_ge872='NOT_PROVED')
    out['deterministic_digest']=digest({k:out[k] for k in ['slack_types','k0_slack','envelopes','cells']})
    out['input_sha256']={f:hashlib.sha256((ROOT/'outputs'/f).read_bytes()).hexdigest() for f in ['rr_f0_column_115.json','rr_round140_capacity_codex.json','rr_round136_capacity_codex.json']}
    (ROOT/'outputs/rr_round141_outer_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(slack_types=len(slack),k0_slack=len(k0),envelopes=len(env['rows']),cells=out['status_counts'],residual=[r for r in env['rows'] if r['status']!='CLOSED_STRICT'])))
if __name__=='__main__':main()
