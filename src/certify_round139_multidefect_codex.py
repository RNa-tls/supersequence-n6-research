"""Independent literal/event checks, seam replay, and row conservation.
This certificate verifies finite inputs; the universal proof is in the report.
"""
import hashlib,itertools,json,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/'outputs'/name).read_text())
def canon_orbit(v):return min(v[j:-1]+v[:j]+v[-1:] for j in range(len(v)-1))
def canon_hex(v):return min(v[j:]+v[:j] for j in range(len(v)))
def literal(raw,n):
    w=tuple(map(int,raw));expected=set(range(n));positions=[];windows=[]
    for i in range(len(w)-n+1):
        v=w[i:i+n]
        if set(v)==expected:positions.append(i);windows.append(v)
    assert positions[0]==0 and positions[-1]+n==len(w) and len(set(windows))==len(windows)
    starts=[0]+[j for j in range(1,len(windows)) if positions[j]>positions[j-1]+1]
    ends=starts[1:]+[len(windows)];passes=[(windows[i],j-i) for i,j in zip(starts,ends)]
    joints=[positions[k]-positions[k-1] for k in starts[1:]]
    for k,weight in zip(starts[1:],joints):
        a,b=windows[k-1],windows[k];assert next((z for z in range(1,n) if a[z:]==b[:-z]),n)==weight
    entry={v:i for i,(v,l) in enumerate(passes)};nu=[]
    for v,l in passes:nu.append(entry[v[l%n:]+v[:l%n]])
    qs=[canon_orbit(v) for v,l in passes];seen={qs[0]};repeats=[]
    for i in range(1,len(qs)):
        if qs[i]!=qs[i-1] and qs[i] in seen:repeats.append(i)
        seen.add(qs[i])
    free={i for i,w in enumerate(joints) if w==2 and qs[i]!=qs[i+1]}
    ordinary={i+1 for i in free if nu[i]<i};asc={i for i,j in enumerate(nu) if i<j}
    assert ordinary<=set(repeats)
    a=len(asc-free);eta=len(set(repeats)-ordinary)
    S=sum(w>=3 for w in joints);H=sum(max(0,w-3) for w in joints)
    x=sum(w>=3 and qs[i]==qs[i+1] for i,w in enumerate(joints))
    m=dict(P=len(passes),O=len(seen),D=(n-1)*len(seen)-len(passes),e=len(repeats),x=x,S=S,H=H)
    return dict(metrics=m,F=len(asc),G=len(passes)-len({canon_hex(v) for v,l in passes}),
                delta=len(asc)+len(repeats)-len(free),a=a,eta=eta,nu=nu,
                repeats=repeats,ordinary=sorted(ordinary),exceptional=sorted(set(repeats)-ordinary),
                passes=passes,orbits=seen,windows=set(windows))

def csp_verify():
    from verify_round138_privacy_codex import equality_partitions
    hist=Counter();count=0
    for n in range(1,8):
        for word in equality_partitions(n):
            repetitions={j for j in range(n) if word[j] in word[:j]}
            for colours in range(1,min(3,n)+1):
                for cuts in itertools.combinations(range(1,n),colours-1):
                    ranges=list(zip((0,)+cuts,cuts+(n,)));charges=set();s=0
                    for q in set(word):
                        firsts=[next(j for j in range(lo,hi) if word[j]==q) for lo,hi in ranges if q in word[lo:hi]]
                        s+=len(firsts)-1;charges.update(firsts[1:])
                    assert len(charges)==s and charges<=repetitions
                    rp=sorted(repetitions)
                    for z in range(1<<len(rp)):
                        ordinary={j for k,j in enumerate(rp) if z>>k&1};exceptional=repetitions-ordinary
                        for eta_d in range(min(2,len(exceptional))+1):
                            for designated in itertools.combinations(sorted(exceptional),eta_d):
                                o=len(charges&ordinary);overlap=len(charges&set(designated))
                                assert 2-eta_d+len(exceptional)>=2+s-o-overlap
                                hist[f's{s}/ordinary{o}/overlap{overlap}']+=1;count+=1
    return dict(models=count,histogram=dict(hist))

def seams_verify(initial):
    from research_round135_contraction_codex import geometry
    from round135_heavy_seam_codex import chains
    g=geometry(6);tables=initial['heavy_seams']['tables'];cc=Counter()
    for ds in [0,2,4]:
        d=tables[str(ds)];new=chains(g,d['best'],ds)
        assert {tuple(z['path']) for z in new['rows']}=={tuple(z) for z in d['witnesses']}
    def transform(path,start):return [g.idx[tuple(g.words[start][a] for a in g.words[v])] for v in path]
    def failure(a,b):
        if {g.q[v] for v in a}&{g.q[v] for v in b}:
            # New stronger check: these candidates fail literal hex occupancy
            # too. The final k1 theorem ALLOWS shared orbits and needs this.
            assert {g.h[v] for v in a}&{g.h[v] for v in b}
            return 'orbit'
        if {g.h[v] for v in a}&{g.h[v] for v in b}:return 'hex'
        return None
    for ds in initial['heavy_seams']['extremal_splits']:
        for aa in tables[str(ds[0])]['witnesses']:
            for t,w in g.joint[g.s(aa[-1],5)]:
                if w!=4:continue
                for rawb in tables[str(ds[1])]['witnesses']:
                    bb=transform(rawb,t);cc['pairs']+=1;why=failure(aa,bb)
                    if why:cc['pair_'+why]+=1;continue
                    for u,w2 in g.joint[g.s(bb[-1],5)]:
                        if w2!=4:continue
                        for rawc in tables[str(ds[2])]['witnesses']:
                            c=transform(rawc,u);cc['triples']+=1;why=failure(aa+bb,c)
                            assert why;cc['triple_'+why]+=1
    assert dict(cc)==dict(pairs=78,pair_orbit=30,pair_hex=40,triples=104,triple_orbit=53,triple_hex=51)
    old=read('rr_round135_heavy_seams_codex.json')['chains'];two=Counter()
    from verify_round135_structural_codex import run_enum
    regenerated={}
    for T,D in [(46,4),(66,9)]:
        nodes,paths=run_enum(g,T,D)
        archived=next(r['rows'] for r in old if r['target']==T)
        assert set(paths)=={tuple(r['path']) for r in archived}
        regenerated[str(T)]=dict(deficit=D,nodes=nodes,extreme_count=len(paths),capped=False)
    for A,B in [old,old[::-1]]:
        for row in A['rows']:
            a=row['path']
            for t,w in g.joint[g.s(a[-1],5)]:
                if w!=4:continue
                for rr in B['rows']:
                    b=transform(rr['path'],t);s=len({g.q[v] for v in a}&{g.q[v] for v in b})
                    hc=bool({g.h[v] for v in a}&{g.h[v] for v in b});assert hc
                    two[str(s)]+=1
    assert sum(two.values())==312 and two['1']==6
    return dict(three_chain=dict(cc),three_chain_orbit_rejections_also_hex_collide=True,
                all_104_second_seams_hex_collide=True,two_chain_all_hex_collision=312,two_chain_shared_orbit_histogram=dict(two),
                two_chain_extrema_regenerated=regenerated)

def main():
    initial=read('rr_round139_initial_codex.json');controls=read('rr_round139_controls_codex.json')
    capacities=read('rr_round139_capacities_codex.json');ind=read('rr_round139_independent_codex.json')
    assert ind['input_sha256']['initial']==sha(ROOT/'outputs/rr_round139_initial_codex.json')
    checked=closed_controls=0;hist=Counter();counterexamples=[]
    for row in controls['n4']['rows']+controls['local']:
        z=literal(row['word'],row['n']);old=row['classification'];checked+=1
        for k in ['F','G','a','eta','delta','nu']:assert z[k]==old[k]
        for k,v in z['metrics'].items():assert v==old['metrics'][k]
        assert z['delta']==z['a']+z['eta']
        if row in controls['n4']['rows'] and z['F']==2 and z['delta']<=1:
            dec=row['decomposition'];assert dec is not None;closed_controls+=1
            p=[literal(r['word'],row['n']) for r in dec['pieces']]
            for r in p:assert all(l==row['n'] for v,l in r['passes']) and r['windows']<=z['windows']
            if len(p)==2:assert p[0]['orbits'].isdisjoint(p[1]['orbits'])
            hist[dec['kind']]+=1
        if row.get('fused_events') and z['G']==2:counterexamples.append(row['word'])
    assert checked==1573 and closed_controls==1063 and len(counterexamples)==4
    csp=csp_verify();assert csp['models']==controls['csp']['models'] and csp['histogram']==controls['csp']['histogram']
    for mode in range(3):
        A=capacities['rows'][2*mode]['result'];B=capacities['rows'][2*mode+1]['result']
        assert not A['capped'] and not B['capped']
        assert [{k:v for k,v in r.items() if k!='witness'} for r in A['rows']]==B['rows']
        from research_round135_contraction_codex import geometry
        g=geometry(6)
        for r in A['rows']:
            if r['passes']<0:continue
            ps=[(v,6) for v in r['witness']];rep=g.replay(ps);assert rep
            z=literal(rep['word'],6);m=z['metrics']
            assert m['D']==r['deficit'] and m['P']==r['passes'] and m['e']==1
            assert m['x']==(r['token'] if mode==1 else 0) and m['H']==(r['token'] if mode==2 else 0)
    assert [r['result']['passes'] for r in ind['independent_b2']]==[62,77,92]
    assert capacities['rows'][-1]['result']['passes']==92 and not capacities['rows'][-1]['result']['capped']
    C=[20,20,33,33,46,46,49,58,62]
    two=max(C[a]+C[8-a] for a in range(9));three=max(C[a]+C[b]+C[8-a-b] for a in range(9) for b in range(9-a))
    bounds=dict(two_ordinary=two,one_b_two_ordinary=two+15,three_ordinary=three)
    for mode,key in [(0,'R'),(1,'RX'),(2,'RH')]:
        tok=mode!=0;rs=[r for r in capacities['rows'][2*mode]['result']['rows'] if r['token']==tok]
        bounds[key+'_plus_C0']=max(r['passes']+C[8-r['deficit']] for r in rs if r['passes']>=0)
    rows=[]
    for r in initial['resources']['rows']:
        closed=(r['delta']==0 or r['F']==2 and r['delta']==1)
        reason=('TYPE_A_REVERSED_ORDER' if r['F']==1 and r['delta']==0 else
                'DECORATED_LOCKS' if r['delta']==0 else 'ONE_DEFECT_DECORATED_NORMALIZATION' if closed else
                'REVERSED_TRIPLE_ONE_DEFECT' if r['F']==1 else 'TWO_DEFECT_SHARED_OR_CROSSING')
        rows.append(r|dict(status='CLOSED' if closed else 'OPEN',proof_dependency=reason))
    assert len(rows)==73 and sum(r['status']=='CLOSED' for r in rows)==60
    output=dict(schema='codex/round139-intermediate-ledger/1',phase='HISTORICAL_INTERMEDIATE_NOT_CURRENT',
        superseded_by='rr_round139_master_verified_codex.json',rows=rows,closed_rows=60,open_rows=13,raw_tuples=78,
        closed_raw_tuples=sum(len(r['heavy_multisets']) for r in rows if r['status']=='CLOSED'),
        capacities_verified=True,literal_controls_verified=checked,normalized_F2_controls=closed_controls,
        symbolic_event_models=csp['models'],seams=seams_verify(initial),bounds=bounds,
        conditional_outer_ledger='11/55 UNCHANGED',NR6='ASSUMED',L6_ge_872='NOT_PROVED',
        universal_proof='research/RR_ROUND139_G2_K2_MULTIDEFECT_CODEX.md sections 2-5; not inferred from finite controls',
        inputs={f:sha(ROOT/'outputs'/f) for f in ['rr_round139_initial_codex.json','rr_round139_controls_codex.json','rr_round139_capacities_codex.json','rr_round139_independent_codex.json']},
        report_sha256=sha(ROOT/'research/RR_ROUND139_G2_K2_MULTIDEFECT_CODEX.md'),
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        verifier_sha256=sha(__file__),verified=True)
    (ROOT/'outputs/rr_round139_intermediate_ledger_codex.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ['closed_rows','open_rows','closed_raw_tuples','literal_controls_verified','bounds','verified']}))
if __name__=='__main__':main()
