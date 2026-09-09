"""G3 capacity envelopes and literal finite-domain certificates; no NR6 DFS."""
import functools,hashlib,itertools,json,subprocess
from collections import Counter
from pathlib import Path
from research_round140_g3_codex import parse,splice,Q,rot,digest
ROOT=Path(__file__).resolve().parents[1]
def load(f):return json.loads((ROOT/'outputs'/f).read_text())
def cap_bounds():
    old=load('rr_f0_column_115.json')['table'];r136=load('rr_round136_capacity_codex.json')['capacity']['result']
    fresh=load('rr_round140_capacity_codex.json');assert fresh['verified'];new={}
    for r in fresh['rows']:
        z=r['result'];assert not z['capped'];key=(z['b'],z['s'])
        if key in new:assert new[key]==z['passes']
        new[key]=z['passes']
    used={}
    def C(b,d):
        if b==3:assert d<=2;value=new[3,2];source='R140 paired b3/D2';cap=2
        elif b==2:
            assert d<=7;cap=2 if d<=2 else 7;value=new[2,cap];source='R140 paired b2'
        elif b==1 and d>7:
            assert d<=13 and not r136['capped'];value=r136['passes'];source='R136 independently verified b1/D13';cap=13
        elif b==0 and d>12:
            assert d<=18;z=old['0,0,18'];assert not z['capped'];value=z['passes'];source='R115 independently verified b0/D18';cap=18
        else:
            z=old[f'{b},0,{d}'];assert not z['capped'];value=z['passes'];source='R115 preserved finite cell';cap=d
        used[str((b,d))]=dict(upper=value,deficit_cap=cap,source=source);return value
    @functools.lru_cache(None)
    def bound(m,b,d):
        if m==1:return C(b,d)
        return max(C(i,j)+bound(m-1,b-i,d-j) for i in range(b+1) for j in range(d+1))
    out=[]
    for k in range(1,5):
        for K in [2,4]:
            for c in range(K):
                for H in range(4):
                    B=1-k+c-H
                    if B<0:continue
                    for h in range(4):
                        for hh in itertools.combinations_with_replacement([4,5,6],h):
                            if sum(w-3 for w in hh)!=H:continue
                            m=4-c+h;needed=123-5*c
                            for s in range((B if m>1 else 0)+1):
                                b=B-s;D=5*k-3+5*s;upper=bound(m,b,D)
                                assert upper<=needed
                                reason='STRICT_CAPACITY'
                                if upper==needed:
                                    assert (K,c,H,hh,m,D,b)==(4,3,1,(4,),2,12,0)
                                    reason='ALL_52_EXTREMAL_W4_SEAMS_HEX_COLLIDE'
                                out.append(dict(k=k,K=K,c=c,H=H,heavy=hh,B=B,b=b,s=s,D_sum=D,
                                    m_max=m,P_required=needed,capacity_bound=upper,margin=needed-upper,closure=reason))
    return dict(rows=out,counts_by_k=dict(Counter(r['k'] for r in out)),used_capacities=used,all_closed=True)
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();base=load('rr_round140_g3_codex.json');bounds=cap_bounds()
    # Do not assign an equality closure label merely because arithmetic is
    # tight. The independent verifier additionally regenerates the domains.
    assert not base['seams']['capped'] and len(base['seams']['rows'])==52
    assert base['seams']['counts']=={'HEX_COLLISION':52}
    assert all(r['status']=='HEX_COLLISION' and r['overlapping_hexagons'] for r in base['seams']['rows'])
    nr4=load('rr_round140_nr4_codex.json');assert not nr4['summary']['capped'];hist=Counter();representatives={};Jmin={};stronger=None;privacy=None
    fnv=1469598103934665603
    for word in nr4['words']:
        for a in tuple(map(int,word))+(255,):fnv=((fnv^a)*1099511628211)&((1<<64)-1)
        d=splice(word,4);m=d['original'];key=str((m['G'],m['F'],m['delta'],m['x'],m['H'],d['K'],d['R'],d['c'],d['b'],d['s']))
        hist[key]+=1
        if key not in representatives:representatives[key]=d
        Jmin[m['J']]=min(Jmin.get(m['J'],999),m['delta'])
        if m['G']==3 and m['J']>m['delta'] and stronger is None:stronger=dict(word=word,metrics=m,refutes='delta >= J')
        if m['G']==3 and m['eta']>0 and privacy is None:
            p=parse(word,4);events=set(p['repeat_events'])-set(p['ordinary']);cut=min(events)
            qs=[Q(v) for v,l in p['passes']];s=len(set(qs[:cut])&set(qs[cut:]))
            assert s>=1;Gamma={next(i for i in range(cut,len(qs)) if qs[i]==q) for q in set(qs[:cut])&set(qs[cut:])}
            o=len(Gamma&set(p['ordinary']));z=len(Gamma&events);q=p['delta']
            assert p['delta']>=q+s-o-z and p['delta']<q+s
            privacy=dict(word=word,cut_before_pass=cut,designated_typed_defects=q,delta=p['delta'],s=s,o=o,z=z,
                charge_events=sorted(Gamma),all_exceptional_events=sorted(events),metrics=m,
                scope='fixed run-respecting two-piece cut; refutes unconditional delta>=q+s, not a qualified canonical-cut lemma')
    assert f'{fnv:016x}'==nr4['summary']['path_digest_fnv64']
    # Explicit actual-heavy-gap controls, excluded by minimum-overlap-only parsers.
    gap_controls=[]
    for n in [4,5,6]:
        v=tuple(range(n));t=rot(v);word=''.join(map(str,v+t+t[:n-2]));d=splice(word,n)
        assert d['original']['weights']==[n];gap_controls.append(d)
    coverage=[]
    for r in base['resources']['rows']:
        possibleK={z['K'] for z in base['support']['g3_supports'] if (z['type'],z['F'])==(r['type'],r['F'])}
        matches=[]
        for i,z in enumerate(bounds['rows']):
            excess=r['S']+1-r['O']+z['c']
            if (r['k']==z['k'] and r['H']==z['H'] and z['K'] in possibleK and 0<=z['s']<=excess):
                assert excess-z['s']<=z['b'];matches.append(i)
        if not matches:assert all(r['S']+1-r['O']+c<0 for K in possibleK for c in range(K))
        coverage.append(r|dict(status='CLOSED',master_envelope_indices=matches,reason='MASTER' if matches else 'NEGATIVE_FREE_BLOCK_BUDGET'))
    out=dict(schema='codex/round140-certificate/1',commit=head,bounds=bounds,resource_coverage=coverage,
        nr4=dict(count=len(nr4['words']),histogram=dict(hist),representatives=list(representatives.values()),J_delta_min=Jmin,
            stronger_bound_counterexample=stronger,unconditional_privacy_counterexample=privacy),
        actual_gap_controls=gap_controls,theorem_A='PROVED_ALL_G',G3_cells=[[k,3] for k in range(1,5)],
        inherited_R139='PROVISIONAL_PENDING_EXTERNAL_AUDIT',combined_provisional_ledger='17/55',NR6='ASSUMED',global_L6_ge_872='NOT_PROVED')
    out['inputs']={f:hashlib.sha256((ROOT/'outputs'/f).read_bytes()).hexdigest() for f in ['rr_round140_g3_codex.json','rr_round140_nr4_codex.json','rr_round140_capacity_codex.json','rr_f0_column_115.json','rr_round136_capacity_codex.json']}
    out['deterministic_digest']=digest({k:out[k] for k in ['bounds','resource_coverage','nr4','actual_gap_controls']})
    (ROOT/'outputs/rr_round140_certificate_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(bounds=bounds['counts_by_k'],controls=len(nr4['words']),representatives=len(representatives),resources=len(coverage),J_delta_min=Jmin)))
if __name__=='__main__':main()
