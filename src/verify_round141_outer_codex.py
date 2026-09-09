"""Independent finite extrema, binary-inclusion cover and 55-cell checker."""
import collections,functools,hashlib,itertools,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=tuple(itertools.permutations(range(6)));IX={p:i for i,p in enumerate(P)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load(f):return json.loads((ROOT/'outputs'/f).read_text())
def cyc(v):return [v[i:]+v[:i] for i in range(len(v))]
def h(v):return min(cyc(v))
def q(v):return min(t+v[-1:] for t in cyc(v[:-1]))
HEX=sorted({h(v) for v in P});HI={v:i for i,v in enumerate(HEX)}
QS=sorted({q(v) for v in P});QI={v:i for i,v in enumerate(QS)}
BLOCKS=[sum(1<<HI[h(v)] for v in [r[i:-1]+r[:i]+r[-1:] for i in range(5)]) for r in QS]
def full_word(entries):
    word=list(P[entries[0]]);weights=[]
    for i,v in enumerate(entries):
        if i:
            target=P[v];w=next((a for a in range(1,6) if tuple(word[-6:])[a:]==target[:-a]),6)
            word.extend(target[-w:]);weights.append(w)
        word.extend(P[v][:5])
    actual=[tuple(word[i:i+6]) for i in range(len(word)-5) if len(set(word[i:i+6]))==6]
    expected=[z for i in entries for z in cyc(P[i])]
    assert actual==expected and len(set(actual))==len(actual)
    return ''.join(map(str,word)),weights
def binary_cover(U,candidates,k):
    # Independent include/exclude by fixed row order, not uncovered-column
    # branching. Dynamic programming retains suffix index, unlike producer.
    all_candidates=tuple(candidates);assert len(set(all_candidates))==len(all_candidates)>=k>=0
    candidates=[i for i in all_candidates if BLOCKS[i]&U]
    freq={i:sum(bool(BLOCKS[v]>>i&1) for v in candidates) for i in range(120) if U>>i&1}
    candidates.sort(key=lambda v:(-sum(1/freq[i] for i in freq if BLOCKS[v]>>i&1),v))
    masks=[BLOCKS[v]&U for v in candidates];suffix=[0]*(len(masks)+1)
    for i in range(len(masks)-1,-1,-1):suffix[i]=suffix[i+1]|masks[i]
    nodes=0;prunes=collections.Counter();trace=hashlib.sha256()
    @functools.lru_cache(None)
    def rec(i,rem,slots):
        nonlocal nodes;nodes+=1;trace.update(f'{i},{rem:x},{slots};'.encode())
        if not rem:return ()
        if not slots or i==len(masks):prunes['empty_budget_or_suffix']+=1;return None
        if rem&~suffix[i]:prunes['suffix_union']+=1;return None
        gains=sorted(((m&rem).bit_count() for m in masks[i:]),reverse=True)
        if sum(gains[:slots])<rem.bit_count():prunes['optimistic_top_gains']+=1;return None
        if masks[i]&rem:
            tail=rec(i+1,rem&~masks[i],slots-1)
            if tail is not None:return (candidates[i],)+tail
        return rec(i+1,rem,slots)
    answer=rec(0,U,k)
    if answer is not None:
        answer=tuple((list(answer)+[i for i in all_candidates if i not in answer])[:k])
        assert len(answer)==len(set(answer))==k and all(i in all_candidates for i in answer)
        assert U&~functools.reduce(int.__or__,(BLOCKS[i] for i in answer),0)==0
    return dict(status='UNSAT' if answer is None else 'SAT',nodes=nodes,witness=answer,
        capped=False,prunes=dict(prunes),transcript_sha256=trace.hexdigest())
def cover_instance(entries,k):
    covered={h(P[v]) for v in entries};opened={q(P[v]) for v in entries}
    U=sum(1<<HI[v] for v in HEX if v not in covered);candidate=[i for i,v in enumerate(QS) if v not in opened]
    return binary_cover(U,candidate,k)|dict(uncovered=len(HEX)-len(covered),opened=len(opened),blocks=k,entries=entries)
def arithmetic(seam_status,cover_status):
    old=load('rr_f0_column_115.json')['table'];new=load('rr_round140_capacity_codex.json')
    fresh={}
    for r in new['rows']:
        z=r['result'];assert not z['capped'] and r['exit_code']==0
        fresh.setdefault((z['b'],z['s']),[]).append(z['passes'])
    assert all(len(v)==2 and len(set(v))==1 for v in fresh.values())
    def cap(b,d):
        if f'{b},0,{d}' in old:
            a=old[f'{b},0,{d}'];assert not a['capped'];return a['passes']
        if b==2 and d<=7:return fresh[b,2 if d<=2 else 7][0]
        if b==3 and d<=2:return fresh[b,2][0]
        if b==1 and d<=13:
            a=load('rr_round136_capacity_codex.json')['capacity']['result'];assert not a['capped'];return a['passes']
        raise AssertionError((b,d))
    @functools.lru_cache(None)
    def conv(m,b,d):
        if m==1:return cap(b,d)
        return max(conv(m-1,b-i,d-j)+cap(i,j) for i in range(b+1) for j in range(d+1))
    producer=load('rr_round141_outer_codex.json');keyrows={};summary=[]
    for k,G in itertools.product(range(1,5),range(4,21)):
        if G>5*k:continue
        for z,H in itertools.product(range(4),repeat=2):
            B=4-k-z-H
            if B<0:continue
            for heavy in [(),(4,),(5,),(4,4),(6,),(4,5),(4,4,4)]:
                if sum(w-3 for w in heavy)!=H:continue
                m=z+1+len(heavy)
                for s in range(B+1):
                    if m==1 and s:continue
                    D=5*k-G+5*s;b=B-s;target=120-4*G+5*z;bound=conv(m,b,D)
                    key=(k,G,z,H,heavy,s);assert key not in keyrows
                    assert bound<=target
                    status='CLOSED_STRICT'
                    if bound==target:
                        if G in (4,7):
                            assert z==0 and H==1 and heavy==(4,) and b==0 and D==15-G and m==2
                            assert seam_status[G];status='CLOSED_EQUALITY_COLLISION_OR_COVER'
                        else:
                            assert (k,G,z,H,heavy,s,b,D,m)==(4,6,0,0,(),0,0,14,1)
                            assert cover_status;status='CLOSED_EQUALITY_COVER'
                    keyrows[key]=dict(k=k,G=G,z=z,H=H,heavy=heavy,s=s,b=b,D=D,m=m,required=target,upper=bound,status=status)
    assert len(keyrows)==160
    assert set(keyrows)=={tuple(r[f] if f!='heavy' else tuple(r[f]) for f in ['k','G','z','H','heavy','s']) for r in producer['envelopes']['rows']}
    for r in producer['envelopes']['rows']:
        t=keyrows[r['k'],r['G'],r['z'],r['H'],tuple(r['heavy']),r['s']]
        assert (t['upper'],t['required'],t['b'],t['D'],t['m'])==(r['upper'],r['P_required'],r['b'],r['D'],r['m_max'])
    for k in range(5):
        for G in range(5*k+1):
            rr=[v for key,v in keyrows.items() if key[:2]==(k,G)]
            summary.append(dict(k=k,G=G,status='CLOSED',provenance='ACCEPTED_R115_R125_R139_R140' if G<=3 else 'ROUND141_INDEPENDENT',envelope_count=len(rr)))
    return dict(rows=list(keyrows.values()),cells=summary,closed=55,total=55,new_cells=[[r['k'],r['G']] for r in summary if r['G']>=4])
def main():
    start=time.perf_counter();head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0]==head
    sources=['src/verify_round141_outer_codex.py','src/round141_verify_extrema_codex.c','src/verify_round139_marked_return_codex.c']
    committed={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in sources}
    runtime={p:sha(ROOT/p) for p in sources}
    for p in sources:assert (ROOT/p).read_bytes().replace(b'\r\n',b'\n')==subprocess.check_output(['git','show',head+':'+p]).replace(b'\r\n',b'\n')
    zig=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe');exe=ROOT/'outputs/round141_verify_extrema_codex.exe'
    build=[str(zig),'cc','-O3','src/round141_verify_extrema_codex.c','-o',str(exe)]
    subprocess.run(build,cwd=ROOT,check=True,capture_output=True)
    producer=load('rr_round141_extrema_codex.json');ext={};jobs=[]
    for r in producer['rows']:
        assert not r['capped'];T,D=r['target'],r['deficit'];argv=[str(exe),str(T),str(D),'20000000000'];ts=time.perf_counter()
        p=subprocess.run(argv,capture_output=True,text=True,check=True);z=json.loads(p.stdout);assert not z['capped']
        assert {tuple(v) for v in z['paths']}=={tuple(v) for v in r['paths']} and len(z['paths'])==z['count']==r['count']
        for entries in z['paths']:
            full_word(entries);assert 5*len({q(P[v]) for v in entries})-T==D
        ext[D]=z['paths'];jobs.append(dict(argv=argv,seconds=time.perf_counter()-ts,exit_code=p.returncode,result=z,result_digest=digest(z)))
        print('verified extrema',T,D,z['nodes'],z['count'],flush=True)
    seams=[];seam_status={}
    old=load('rr_f0_column_115.json')['table']
    for G,splits,target in [(4,[(4,7),(7,4)],104),(7,[(4,4)],92)]:
        totalD=15-G
        assert [(d,totalD-d) for d in range(totalD+1) if old[f'0,0,{d}']['passes']+old[f'0,0,{totalD-d}']['passes']==target]==splits
        for da,db in splits:
            for A in ext[da]:
                endpoint=P[A[-1]][-1:]+P[A[-1]][:-1];Ah={h(P[v]) for v in A}
                for label in P:
                    gaps=[w for w in range(1,6) if endpoint[w:]==label[:-w]]
                    if gaps!=[4]:continue
                    raw=endpoint+label[-4:]
                    if any(len(set(raw[i:i+6]))==6 for i in range(1,4)):continue
                    for B in ext[db]:
                        bb=[IX[tuple(label[x] for x in P[v])] for v in B];overlap=Ah&{h(P[v]) for v in bb}
                        row=dict(G=G,deficits=[da,db],left=A,right=bb,label=label,overlap=[list(x) for x in sorted(overlap)])
                        if overlap:row['status']='HEX_COLLISION'
                        else:
                            word,ww=full_word(A+bb);assert ww.count(4)==1 and max(ww)==4
                            row.update(status='COVER_NEEDED',word=word,sharing=20-len({q(P[v]) for v in A+bb}))
                            row['completion_cover']=cover_instance(A+bb,G)
                            assert row['completion_cover']['status']=='UNSAT';row['status']='STATIC_COMPLETION_UNSAT'
                        seams.append(row)
        seam_status[G]=all(r['status'] in ['HEX_COLLISION','STATIC_COMPLETION_UNSAT'] for r in seams if r['G']==G)
    covers=[cover_instance(v,6) for v in ext[14]];assert all(r['status']=='UNSAT' for r in covers)
    first=load('rr_round141_completion_cover_codex.json');assert first['status_counts']=={'UNSAT':len(covers)}
    assert {tuple(r['entries']) for r in covers}=={tuple(r['entries']) for r in first['instances']}
    ledger=arithmetic(seam_status,True)
    out=dict(schema='codex/round141-outer-independent/1',source_commit=head,committed_source_sha256=committed,runtime_source_sha256=runtime,
        build=build,compiler=subprocess.check_output([str(zig),'version'],text=True).strip(),executable_sha256=sha(exe),jobs=jobs,
        seams=seams,completion_covers=covers,ledger=ledger,verified=True,NR6='ASSUMED',global_L6_ge872='NOT_PROVED',seconds=time.perf_counter()-start)
    out['input_sha256']={f:sha(ROOT/'outputs'/f) for f in ['rr_round141_extrema_codex.json','rr_round141_outer_codex.json','rr_round141_completion_cover_codex.json','rr_f0_column_115.json','rr_round140_capacity_codex.json','rr_round136_capacity_codex.json']}
    out['deterministic_digest']=digest(dict(extrema=ext,seams=seams,completion_covers=covers,ledger=ledger))
    (ROOT/'outputs/rr_round141_outer_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(verified=True,closed=ledger['closed'],seams={str(k):v for k,v in collections.Counter((r['G'],r['status']) for r in seams).items()},cover_nodes=[r['nodes'] for r in covers])))
if __name__=='__main__':main()
