"""Independent exit-window/runs/incidence verifier for the Round140 certificate.
Does not call the producer's parse, support, splice, or convolution functions.
"""
import hashlib,itertools,json,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(f):return json.loads((ROOT/'outputs'/f).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def turns(v):return [v[i:]+v[:i] for i in range(len(v))]
def hx(v):return min(turns(v))
def orb(v):return min(t+v[-1:] for t in turns(v[:-1]))
def full_exit(v):return v[-1:]+v[:-1]
def data_word(word,n):
    w=tuple(map(int,word));at=[i for i in range(len(w)-n+1) if set(w[i:i+n])==set(range(n))]
    ws=[w[i:i+n] for i in at];assert at[0]==0 and at[-1]+n==len(w) and len(set(ws))==len(ws)
    groups=[]
    for i,v in enumerate(ws):
        if i==0 or at[i]!=at[i-1]+1:groups.append([])
        groups[-1].append(v)
    entries=[g[0] for g in groups];lookup={v:i for i,v in enumerate(entries)};q=[orb(v) for v in entries]
    end_to_joint={};weights=[]
    for A,B in zip(groups,groups[1:]):
        a,b=A[-1],B[0];gap=at[ws.index(b)]-at[ws.index(a)];weights.append(gap);end_to_joint[a]=(b,gap)
    # Complete touched rotation classes, not mere registered incidence.
    occ=Counter(hx(v) for v in ws);assert all(c==n for c in occ.values())
    F=0;free=[];ordinary=[];registered=set();run_q=[];repeat=[];x=0
    for i,g in enumerate(groups):
        v=g[0];block=g[-1][1:]+g[-1][:1];assert block in lookup
        if lookup[block]>i:F+=1
        if not run_q or q[i]!=run_q[-1]:
            if q[i] in registered:repeat.append(i)
            run_q.append(q[i])
        registered.add(q[i])
        if i==len(weights):continue
        if weights[i]>=3 and q[i]==q[i+1]:x+=1
        if weights[i]==2 and q[i]!=q[i+1]:
            free.append(i)
            t=block[1:-1]+block[:1]+block[-1:];assert t==entries[i+1]
            if lookup[block]<i:ordinary.append(i+1)
    assert set(ordinary)<=set(repeat)
    P=len(entries);O=len(registered);G=P-len(occ);e=len(run_q)-O;S=sum(z>=3 for z in weights);H=sum(max(z-3,0) for z in weights)
    a=sum(lookup[g[-1][1:]+g[-1][:1]]>i and i not in free for i,g in enumerate(groups))
    eta=e-len(ordinary);delta=F+e-len(free)
    assert delta==a+eta>=0 and F<=G and O==1+S+len(free)-e-x
    assert O<=1+S+F-x<=1+S+G
    successor={v:end_to_joint[full_exit(v)] for v in entries if full_exit(v) in end_to_joint}
    assert len(successor)==P-1 and len({t for t,w in successor.values()})==P-1
    comps=[];unseen=set(entries);seq=[];v=entries[0]
    while True:
        assert v in unseen;unseen.remove(v);seq.append(v)
        if v not in successor:break
        v=successor[v][0]
    comps.append(seq)
    while unseen:
        v=start=min(unseen);seq=[]
        while v in unseen:unseen.remove(v);seq.append(v);v=successor[v][0]
        assert v==start;comps.append(seq)
    K=len(comps);R=sum(len(z)-len({hx(v) for v in z}) for z in comps)
    assert K+R<=G+1 and (K-G-1)%2==0
    pure=[z for z in comps[1:] if all(successor[v][1]==2 for v in z)]
    for z in pure:assert len(z)==n-1 and len({orb(v) for v in z})==1
    c=len(pure);assert S+1-O+c>=0
    return dict(entries=entries,successor=successor,pure=pure,K=K,R=R,c=c,
        metrics=dict(P=P,O=O,G=G,F=F,J=G-F,e=e,x=x,S=S,H=H,D=(n-1)*O-P,delta=delta,a=a,eta=eta,f_out=len(free)))
def pieces_verify(row):
    n=row['n'];d=data_word(row['word'],n);assert (d['K'],d['R'],d['c'])==(row['K'],row['R'],row['c'])
    for k,v in d['metrics'].items():assert row['original'][k]==v
    removed=set(sum(d['pure'],[]));kept=set(d['entries'])-removed
    assert {orb(v) for v in kept}.isdisjoint(orb(v) for v in removed)
    used=set();retained=set();P=D=O=b=0
    for p in row['pieces']:
        z=data_word(p['word'],n);vv=[d['entries'][i] for i in p['indices']]
        assert z['entries']==vv and z['metrics']['G']==z['metrics']['H']==0
        assert not used&set(vv);used.update(vv)
        for v,t in zip(vv,vv[1:]):assert d['successor'][v]==z['successor'][v] and d['successor'][v][0]==t;retained.add(v)
        for k in p['metrics']:assert p['metrics'][k]==z['metrics'][k]
        P+=z['metrics']['P'];D+=z['metrics']['D'];O+=z['metrics']['O'];b+=z['metrics']['e']+z['metrics']['x']
    assert kept==used
    for v,(t,w) in d['successor'].items():
        if v in kept and v not in retained:assert w>=3
    s=O-(d['metrics']['O']-d['c']);assert (b,s)==(row['b'],row['s'])
    assert b+s==d['metrics']['S']+1-d['metrics']['O']+d['c']
    assert P==d['metrics']['P']-(n-1)*d['c'] and D==d['metrics']['D']+(n-1)*s
    assert len(row['pieces'])<=d['metrics']['G']+1-d['c']+sum(w>3 for t,w in d['successor'].values())
    return d
def graph_check(nu):
    n=len(nu);p=list(nu)+[n];rev={j:i for i,j in enumerate(p)};t={i:(rev[i]+1)%(n+1) for i in range(n+1)}
    def classes(f):
        cc={};nc=0
        for i in range(n+1):
            if i in cc:continue
            v=i
            while v not in cc:cc[v]=nc;v=f[v]
            nc+=1
        return cc,nc
    a,na=classes(p);b,nb=classes(t);edges=Counter((a[i],na+b[i]) for i in range(n+1));adj={i:set() for i in range(na+nb)}
    for v,w in edges:adj[v].add(w);adj[w].add(v)
    stack=[0];seen={0}
    while stack:
        for v in adj[stack.pop()]-seen:seen.add(v);stack.append(v)
    assert len(seen)==na+nb
    G=n+1-na;R=(n+1)-len(edges)
    assert R<=G+1-nb and (nb-G-1)%2==0
    return G,nb,R
def allocations(v,m):
    if m==1:yield (v,);return
    for a in range(v+1):
        for z in allocations(v-a,m-1):yield (a,)+z
def capacities(cert):
    old=load('rr_f0_column_115.json')['table'];fresh=load('rr_round140_capacity_codex.json');new={}
    assert fresh['verified']
    for r in fresh['rows']:
        d=r['result'];assert not d['capped'] and r['exit_code']==0
        new.setdefault((d['b'],d['s']),[]).append(d['passes'])
        assert hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()==r['result_digest']
    assert all(len(v)==2 and v[0]==v[1] for v in new.values())
    # The seam certificate is complete only if these are ALL extremal
    # deficit allocations, not merely two convenient extremal chains.
    equality_splits=[]
    for d in range(13):
        lhs=old[f'0,0,{d}'];rhs=old[f'0,0,{12-d}']
        assert not lhs['capped'] and not rhs['capped']
        total=lhs['passes']+rhs['passes'];assert total<=108
        if total==108:equality_splits.append([d,12-d])
    assert equality_splits==[[4,8],[8,4]]
    def C(b,d):
        if b==3:assert d<=2;return new[3,2][0]
        if b==2:assert d<=7;return new[2,2 if d<=2 else 7][0]
        if b==1 and d>7:
            assert d<=13;r=load('rr_round136_capacity_codex.json')['capacity']['result'];assert not r['capped'];return r['passes']
        z=old[f'{b},0,{18 if b==0 and d>12 else d}'];assert not z['capped'];return z['passes']
    expected=set()
    for k,K,c,H in itertools.product(range(1,5),[2,4],range(4),range(4)):
        B=1-k+c-H
        if c>=K or B<0:continue
        for h in range(4):
            for heavy in itertools.combinations_with_replacement([4,5,6],h):
                if sum(w-3 for w in heavy)!=H:continue
                for s in range(B+1):
                    if 4-c+h==1 and s:continue
                    expected.add((k,K,c,H,heavy,s))
    actual=set();equal=0
    for row in cert['bounds']['rows']:
        k,K,c,H,heavy,s=[row[z] for z in ['k','K','c','H','heavy','s']];key=(k,K,c,H,tuple(heavy),s)
        assert key not in actual;actual.add(key)
        b=1-k+c-H-s;d=5*k-3+5*s;m=4-c+len(heavy);P=123-5*c
        assert (b,d,m,P)==(row['b'],row['D_sum'],row['m_max'],row['P_required'])
        upper=max(sum(C(x,y) for x,y in zip(bs,ds)) for bs in allocations(b,m) for ds in allocations(d,m))
        assert upper==row['capacity_bound']<=P
        if upper==P:assert (K,c,H,heavy,b,d,m)==(4,3,1,[4],0,12,2);equal+=1
    assert actual==expected and len(actual)==40 and equal==3
    # Independent original resource enumeration via length, not producer delta loops.
    rs=set()
    for k in range(1,5):
        for name,shorts,fs in [('A4',4,[1,2,3]),('A3B2',5,[2,3]),('B222',6,[3])]:
            for F,e,free,x,H in itertools.product(fs,range(10),range(shorts+1),range(4),range(4)):
                S=23+k+e+x-free
                if free>F+e or 847+S+H>871:continue
                rs.add((k,name,F,e,free,x,H))
    rows=cert['resource_coverage'];assert rs=={tuple(r[k] for k in ['k','type','F','e','f_out','x','H']) for r in rows}
    assert len(rows)==516
    supports=load('rr_round140_g3_codex.json')['support']['g3_supports']
    for r in rows:
        Ks={z['K'] for z in supports if (z['type'],z['F'])==(r['type'],r['F'])}
        expected_indices=[i for i,z in enumerate(cert['bounds']['rows']) if z['k']==r['k'] and z['K'] in Ks and z['H']==r['H'] and 0<=z['s']<=r['S']+1-r['O']+z['c']]
        assert expected_indices==r['master_envelope_indices'] and r['status']=='CLOSED'
        if not expected_indices:assert all(r['S']+1-r['O']+c<0 for K in Ks for c in range(K))
    return dict(envelopes=40,equalities=3,equality_deficit_splits=equality_splits,
        resource_rows=516,by_k=dict(Counter(r['k'] for r in rows)))
def seams(base):
    from research_alpha_gap_codex import Geometry
    from verify_round135_structural_codex import run_enum
    g=Geometry(6);ext={};nodes={}
    for T,D in [(46,4),(62,8)]:
        nc,paths=run_enum(g,T,D);assert set(paths)=={tuple(z) for z in base['seams']['extrema'][str(D)]['witnesses']}
        ext[D]=paths;nodes[str(D)]=nc
    records=[]
    for da,db in [(4,8),(8,4)]:
        for a in ext[da]:
            endpoint=full_exit(g.words[a[-1]])
            for label in itertools.permutations(range(6)):
                overlap=next((w for w in range(1,6) if endpoint[w:]==label[:-w]),6)
                if overlap!=4:continue
                raw=endpoint+label[-4:]
                if any(len(set(raw[i:i+6]))==6 for i in range(1,4)):continue
                for b in ext[db]:
                    bb=[g.idx[tuple(label[j] for j in g.words[v])] for v in b]
                    intersection={hx(g.words[v]) for v in a}&{hx(g.words[v]) for v in bb};assert intersection
                    records.append((da,db,tuple(a),tuple(bb),label))
    assert len(records)==52 and set(records)=={(r['deficits'][0],r['deficits'][1],tuple(r['a']),tuple(r['b']),tuple(r['target'])) for r in base['seams']['rows']}
    return dict(attempts=52,hex_collision=52,independent_extreme_nodes=nodes,extreme_counts={str(d):len(z) for d,z in ext.items()})
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();cert=load('rr_round140_certificate_codex.json');base=load('rr_round140_g3_codex.json')
    support_count=0;general_count=0;expected_support=set()
    for n in range(1,9):
        for p in itertools.permutations(range(n)):
            G,K,R=graph_check(p);general_count+=1
            if G==3 and all(p[i]!=i for i in range(n)):expected_support.add(p)
    for row in base['support']['g3_supports']:
        assert graph_check(row['nu'])==(3,row['K'],row['R']);support_count+=1
        unseen=set(range(len(row['nu'])));lengths=[]
        while unseen:
            v=min(unseen);nc=0
            while v in unseen:unseen.remove(v);nc+=1;v=row['nu'][v]
            lengths.append(nc)
        lengths.sort();comps=[{x for x in itertools.product(range(1,7),repeat=m) if sum(x)==6} for m in lengths]
        assert [set(map(tuple,z)) for z in row['arc_compositions']]==comps
        count=1
        for z in comps:count*=len(z)
        assert row['local_shape_count']==count
    assert expected_support=={tuple(r['nu']) for r in base['support']['g3_supports']}
    assert sum(r['local_shape_count'] for r in base['support']['g3_supports'])==2935
    assert support_count==41 and general_count==46233
    nr4=load('rr_round140_nr4_codex.json');hist=Counter();fnv=1469598103934665603
    assert not nr4['summary']['capped'] and len(nr4['words'])==len(set(nr4['words']))
    for word in nr4['words']:
        d=data_word(word,4);hist[str((d['metrics']['G'],d['metrics']['F'],d['metrics']['delta']))]+=1
        for a in tuple(map(int,word))+(255,):fnv=((fnv^a)*1099511628211)&((1<<64)-1)
    assert f'{fnv:016x}'==nr4['summary']['path_digest_fnv64'] and len(nr4['words'])==29255
    checked=0
    for row in base['controls']['rows']+cert['nr4']['representatives']+cert['actual_gap_controls']:pieces_verify(row);checked+=1
    identities=0
    for n in [4,5,6]:
        for v in itertools.permutations(range(n)):
            for l in range(1,n+1):
                endpoint=turns(v)[l-1];block=endpoint[1:]+endpoint[:1]
                target=endpoint[2:]+endpoint[1::-1];assert target==block[1:-1]+block[:1]+block[-1:]
                assert full_exit(block)==endpoint;identities+=1
    fresh=load('rr_round140_capacity_codex.json')
    for p,h in fresh['committed_source_sha256'].items():assert hashlib.sha256(subprocess.check_output(['git','show',fresh['commit']+':'+p])).hexdigest()==h
    for f,h in cert['inputs'].items():assert sha(ROOT/'outputs'/f)==h
    out=dict(schema='codex/round140-independent/1',commit=head,verified=True,
        supports=41,all_permutation_graph_controls=general_count,identities=identities,nr4_words=29255,nr4_histogram=dict(hist),
        spliced_literal_controls=checked,capacity_arithmetic=capacities(cert),seams=seams(base),
        theorem_A='PROVED_ALL_G',splicing='PROVED_ALL_G',new_G3_cells=[[k,3] for k in range(1,5)],
        inherited_R139='PROVISIONAL_PENDING_EXTERNAL_AUDIT',combined_provisional_ledger='17/55',NR6='ASSUMED',global_L6_ge_872='NOT_PROVED',
        inputs={f:sha(ROOT/'outputs'/f) for f in ['rr_round140_g3_codex.json','rr_round140_nr4_codex.json','rr_round140_certificate_codex.json','rr_round140_capacity_codex.json']})
    sources=['src/verify_round140_g3_codex.py','src/verify_round135_structural_codex.py','src/research_alpha_gap_codex.py']
    out['committed_source_sha256']={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in sources}
    out['runtime_source_sha256']={p:sha(ROOT/p) for p in sources}
    (ROOT/'outputs/rr_round140_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['verified','nr4_words','spliced_literal_controls','capacity_arithmetic','seams']}))
if __name__=='__main__':main()
