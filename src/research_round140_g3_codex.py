"""Finite G3 support, literal splicing and extreme-seam domains. No NR6 DFS."""
import functools,hashlib,itertools,json,subprocess,time
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rot(v,k=1):k%=len(v);return v[k:]+v[:k]
def eq(v):return v[1:-1]+v[:1]+v[-1:]
def Q(v):return min(rot(v[:-1],i)+v[-1:] for i in range(len(v)-1))
def X(v):return min(rot(v,i) for i in range(len(v)))
def cycles(p):
    seen=set();out=[]
    for v in range(len(p)):
        if v in seen:continue
        s=v;a=[]
        while v not in seen:seen.add(v);a.append(v);v=p[v]
        assert v==s;out.append(a)
    return out
def compose6(parts):
    if parts==1:yield (6,);return
    for cuts in itertools.combinations(range(1,6),parts-1):
        a=(0,)+cuts+(6,);yield tuple(a[i+1]-a[i] for i in range(parts))
def support(nu):
    n=len(nu);alpha=list(nu)+[n];inv=[alpha.index(i) for i in range(n+1)]
    beta=[(inv[i]+1)%(n+1) for i in range(n+1)]
    aa=cycles(alpha);bb=cycles(beta);ac={v:i for i,z in enumerate(aa) for v in z};bc={v:i for i,z in enumerate(bb) for v in z}
    incidences=Counter((ac[v],bc[v]) for v in range(n+1));R=sum(z-1 for z in incidences.values())
    G=n+1-len(aa);K=len(bb)
    assert K+R<=G+1 and (K-G-1)%2==0
    return dict(nu=nu,G=G,F=sum(i<j for i,j in enumerate(nu)),components=bb,K=K,R=R,
        incidence_multiplicities=[[a,b,z] for (a,b),z in sorted(incidences.items())],simple_graph_cycle_rank=G+1-K-R)
def finite_support():
    out=[];counts=Counter();general=Counter();nc=0
    for n in range(1,9):
        for p in itertools.permutations(range(n)):
            z=support(p);nc+=1;general[str((z['G'],z['K'],z['R']))]+=1
            lengths=sorted(len(c) for c in cycles(p) if len(c)>1)
            if z['G']==3 and all(p[i]!=i for i in range(n)):
                name={ (4,):'A4',(2,3):'A3B2',(2,2,2):'B222'}[tuple(lengths)]
                comps=[list(compose6(l)) for l in lengths]
                local_shapes=1
                for c in comps:local_shapes*=len(c)
                z.update(type=name,short_count=n,arc_compositions=comps,local_shape_count=local_shapes)
                out.append(z);counts[name]+=1
    assert len(out)==41
    return dict(g3_supports=out,support_count=41,local_shapes=sum(z['local_shape_count'] for z in out),
        types=dict(counts),F_histogram=dict(Counter(z['F'] for z in out)),
        KR_histogram=dict(Counter(str((z['K'],z['R'])) for z in out)),
        all_permutations_through_8=nc,general_histogram=dict(general),capped=False)
def parse(raw,n):
    raw=tuple(map(int,raw));seen={};order=[];pos=[]
    for i in range(len(raw)-n+1):
        v=raw[i:i+n]
        if len(set(v))==n:
            assert v not in seen;seen[v]=i;order.append(v);pos.append(i)
    assert pos[0]==0 and pos[-1]+n==len(raw)
    starts=[0]+[i for i in range(1,len(pos)) if pos[i]!=pos[i-1]+1]
    ps=[(order[a],b-a) for a,b in zip(starts,starts[1:]+[len(pos)])]
    entry={v:i for i,(v,l) in enumerate(ps)}
    assert all(rot(v,l) in entry for v,l in ps),'control requires complete touched hexagons'
    nu=[entry[rot(v,l)] for v,l in ps];weights=[pos[i]-pos[i-1] for i in starts[1:]]
    qs=[Q(v) for v,l in ps];repeats={i for i in range(1,len(ps)) if qs[i]!=qs[i-1] and qs[i] in qs[:i]}
    free={i for i,w in enumerate(weights) if w==2 and qs[i]!=qs[i+1]}
    asc={i for i,j in enumerate(nu) if i<j};ordinary={i+1 for i in free if nu[i]<i}
    for i in free:
        ep=rot(ps[i][0],ps[i][1]-1);target=ep[2:]+ep[1::-1]
        assert target==ps[i+1][0]==eq(ps[nu[i]][0])
    assert ordinary<=repeats
    P=len(ps);O=len(set(qs));G=P-len({X(v) for v,l in ps});F=len(asc);e=len(repeats)
    S=sum(w>=3 for w in weights);H=sum(max(0,w-3) for w in weights);x=sum(w>=3 and qs[i]==qs[i+1] for i,w in enumerate(weights))
    a=len(asc-free);eta=len(repeats-ordinary);delta=F+e-len(free)
    assert delta==a+eta>=0 and F<=G and O<=1+S+F-x<=1+S+G
    return dict(passes=ps,weights=weights,nu=nu,P=P,O=O,G=G,F=F,J=G-F,e=e,x=x,S=S,H=H,
        D=(n-1)*O-P,a=a,eta=eta,delta=delta,f_out=len(free),ordinary=sorted(ordinary),repeat_events=sorted(repeats))
def splice(raw,n):
    d=parse(raw,n);ps=d['passes'];P=len(ps);edge={}
    for i,w in enumerate(d['weights']):
        source=d['nu'][i];assert rot(ps[source][0],-1)==rot(ps[i][0],ps[i][1]-1)
        edge[source]=(i+1,w)
        if w==2:assert ps[i+1][0]==eq(ps[source][0])
    t=support(tuple(d['nu']));dummy=P
    ordered=[]
    for cyc in t['components']:
        if dummy in cyc:
            j=cyc.index(dummy);seq=cyc[j+1:]+cyc[:j];assert not seq or seq[0]==0
            ordered.insert(0,seq)
        else:ordered.append(cyc)
    pure=[z for z in ordered[1:] if all(edge[v][1]==2 for v in z)]
    for z in pure:assert len(z)==n-1 and len({Q(ps[v][0]) for v in z})==1
    removed={v for z in pure for v in z};keep=set(range(P))-removed
    assert {Q(ps[v][0]) for v in removed}.isdisjoint(Q(ps[v][0]) for v in keep)
    cuts={i for i,(j,w) in edge.items() if i in keep and w>3}
    for z in ordered[1:]:
        if z not in pure and not set(z)&cuts:cuts.add(min(i for i in z if edge[i][1]>=3))
    def pieces():
        targets={j for i,(j,w) in edge.items() if i in keep and i not in cuts};out=[]
        for i in sorted(keep-targets):
            seq=[]
            while True:
                seq.append(i)
                if i not in edge or i in cuts:break
                i=edge[i][0]
            out.append(seq)
        assert len(set(sum(out,[])))==sum(map(len,out))==len(keep)
        return out
    duplicates=[]
    for seq in pieces():
        blocks=[];block=[]
        for i in seq:
            if block and edge[block[-1]][1]!=2:blocks.append(block);block=[]
            block.append(i)
        blocks.append(block);seen=set();last=None
        for block in blocks:
            hh={X(ps[v][0]) for v in block};assert len(hh)==len(block)
            if hh&seen:assert last is not None;cuts.add(last);duplicates.append(last);seen=set()
            seen|=hh;last=block[-1]
    assert len(duplicates)<=t['R']
    pp=[]
    for seq in pieces():
        word=list(ps[seq[0]][0])
        for j,v in enumerate(seq):
            if j:word.extend(ps[v][0][-edge[seq[j-1]][1]:])
            word.extend(ps[v][0][:n-1])
        s=''.join(map(str,word));m=parse(s,n)
        assert m['G']==0 and m['H']==0 and all(l==n for v,l in m['passes'])
        pp.append(dict(indices=seq,word=s,metrics={k:m[k] for k in ['P','O','D','e','x','S','H']}))
    c=len(pure);sharing=sum(z['metrics']['O'] for z in pp)-(d['O']-c);b=sum(z['metrics']['e']+z['metrics']['x'] for z in pp)
    assert b+sharing==d['S']+1-d['O']+c
    assert sum(z['metrics']['D'] for z in pp)==d['D']+(n-1)*sharing
    assert len(pp)<=d['G']+1-c+sum(w>3 for w in d['weights'])
    return dict(n=n,word=raw,original={k:v for k,v in d.items() if k not in ['passes']},K=t['K'],R=t['R'],
        c=c,b=b,s=sharing,pieces=pp,duplicate_cuts=duplicates,pure_cycles=pure)
def local_controls():
    result=[];hist=Counter()
    for n in [4,5,6]:
        g=Geometry(n);current={((0,n),)}
        for depth in range(4):
            nexts=set()
            for ps in sorted(current):
                rep=g.replay(ps);assert rep
                s=splice(rep['word'],n);assert s['original']['G']==depth
                result.append(s);hist[str((n,depth,s['original']['F'],s['original']['delta']))]+=1
                if depth==3:continue
                for i,(v,l) in enumerate(ps):
                    for a in range(1,l):
                        c=g.s(v,a);np=ps[:i]+((v,a),)+tuple((g.e(c,j),n) for j in range(1,n-1))+((c,l-a),)+ps[i+1:]
                        if g.replay(np):nexts.add(np)
            current=nexts
    return dict(rows=result,histogram=dict(hist),count=len(result),scope='all legal three-step local arc-lock insertions at n4,n5,n6; not complete NR6 search')
def resources():
    out=[]
    for k in range(1,5):
        for typ,shorts,Fs in [('A4',4,[1,2,3]),('A3B2',5,[2,3]),('B222',6,[3])]:
            for F in Fs:
                budget=F+1-k
                for delta in range(budget+1):
                    for x in range(budget-delta+1):
                        for H in range(budget-delta-x+1):
                            for free in range(shorts+1):
                                e=free-F+delta
                                if e<0:continue
                                S=23+k+e+x-free;L=847+S+H
                                assert L==870+k-F+delta+x+H<=871
                                out.append(dict(k=k,type=typ,F=F,J=3-F,delta=delta,x=x,H=H,e=e,f_out=free,
                                    P=123,O=24+k,D=5*k-3,S=S,L=L))
    return dict(rows=out,counts_by_k=dict(Counter(z['k'] for z in out)),total=len(out))
def equality_seams():
    # Recompute finite extreme sets; provisional R139 tool is only a producer.
    from research_round139_multidefect_codex import full_chains
    g=Geometry(6);C={d:full_chains(d) for d in [4,8]};counts=Counter();rows=[]
    for da,db in [(4,8),(8,4)]:
        for a in C[da]['witnesses']:
            source=rot(g.words[a[-1]],-1)
            for tail in itertools.permutations(source[:4]):
                target=source[4:]+tail;word=source+tail
                if g.weight(source,target)!=4 or any(len(set(word[i:i+6]))==6 for i in range(1,4)):continue
                for rawb in C[db]['witnesses']:
                    bb=[g.idx[tuple(target[z] for z in g.words[v])] for v in rawb]
                    overlap=sorted({g.h[v] for v in a}&{g.h[v] for v in bb})
                    tag='HEX_COLLISION' if overlap else 'SEAM_SURVIVOR';counts[tag]+=1
                    rows.append(dict(deficits=[da,db],a=a,b=bb,target=target,overlapping_hexagons=overlap,status=tag))
    return dict(extrema=C,counts=dict(counts),rows=rows,capped=False)
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();start=time.perf_counter()
    result=dict(schema='codex/round140-g3/1',support=finite_support(),resources=resources(),controls=local_controls(),seams=equality_seams())
    sources=['src/research_round140_g3_codex.py','src/research_alpha_gap_codex.py','src/research_round139_multidefect_codex.py']
    result.update(commit=head,committed_source_sha256={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in sources},
        runtime_source_sha256={p:sha(ROOT/p) for p in sources},seconds=time.perf_counter()-start)
    result['mathematical_digest']=digest({k:result[k] for k in ['support','resources','controls','seams']})
    (ROOT/'outputs/rr_round140_g3_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(supports=result['support']['support_count'],shapes=result['support']['local_shapes'],
        resources=result['resources']['counts_by_k'],controls=result['controls']['histogram'],seams=result['seams']['counts'],seconds=result['seconds'])))
if __name__=='__main__':main()
