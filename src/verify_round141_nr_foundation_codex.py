"""Independent NR3 order graph, NR4 local plateau, and repeat-credit verifier."""
import collections,hashlib,itertools,json,math,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def spelling(order):
    text=order[0];n=len(text)
    for target in order[1:]:
        for w in range(1,n+1):
            candidate=text+target[n-w:]
            if candidate[-n:]==target:break
        text=candidate
    return text
def literal(text,n):
    words=set(''.join(v) for v in itertools.permutations(map(str,range(n))))
    return [(i,text[i:i+n]) for i in range(len(text)-n+1) if text[i:i+n] in words]
def independent_credit(word,n):
    # Prefix-scanned labels; no producer pass parser, transition function or
    # visited-set implementation is used.
    ww=literal(word,n);assert len({v for _,v in ww})==math.factorial(n)
    def E(v):return v[1:-1]+v[:1]+v[-1:]
    def orb(v):
        members=[]
        for _ in range(n-1):members.append(v);v=E(v)
        return min(members)
    entry_indices=[j for j in range(len(ww)) if j==0 or ww[j][0]!=ww[j-1][0]+1]
    entries=[ww[j][1] for j in entry_indices];orbit_seq=list(map(orb,entries))
    F=S=H=x=fout=Y=Ord=a=0;bad_sources=[]
    for index in range(1,len(entry_indices)):
        j=entry_indices[index];source=ww[j-1][1];w=ww[j][0]-ww[j-1][0]
        prior=[v for _,v in ww[:j]];fresh=orbit_seq[index] not in orbit_seq[:index]
        abandoned=source[1:]+source[0] not in prior;inter=orbit_seq[index]!=orbit_seq[index-1]
        F+=abandoned;S+=w>2;H+=max(w-3,0);x+=w>2 and not inter;fout+=w==2 and inter
        a+=abandoned and not(w==2 and inter)
        Ord+=w==2 and inter and not fresh and not abandoned
        if w==2 and fresh and not abandoned:
            assert source in prior[:-1];Y+=1;bad_sources.append(j-1)
    O=len(set(orbit_seq));runs=1+sum(v!=u for u,v in zip(orbit_seq,orbit_seq[1:]));e=runs-O
    R=len(ww)-math.factorial(n);P=len(entries);G=P-math.factorial(n-1);J=G-F
    eta=e-Ord;epsilon=a+eta+R-Y;k=O-math.factorial(n-2)
    base=sum(math.factorial(n-i) for i in range(3))+n-3
    assert all(z>=0 for z in [J,eta,k,R-Y])
    assert len(word)==base+k+J+epsilon+x+H
    return dict(R=R,P=P,G=G,F=F,J=J,O=O,k=k,Y=Y,a=a,eta=eta,e=e,x=x,S=S,H=H,
        f_out=fout,delta=a+eta-Y,epsilon=epsilon,bad_sources=bad_sources)
def nr3_graph():
    vertices=list(itertools.permutations(['012','021','102','120','201','210']))
    lengths=[len(spelling(v)) for v in vertices]
    # Undirected relocation adjacency is induced by common deleted-element
    # signatures. This is independent of the producer's pop/insert generator.
    signatures=collections.defaultdict(list)
    for i,v in enumerate(vertices):
        for p in v:signatures[(p,tuple(q for q in v if q!=p))].append(i)
    neighbors=[set() for _ in vertices]
    for group in signatures.values():
        for u in group:neighbors[u].update(v for v in group if v!=u)
    reverse=[set() for _ in vertices];edge_count=0
    for u,ns in enumerate(neighbors):
        for v in ns:
            if lengths[v]<=lengths[u]:reverse[v].add(u);edge_count+=1
    clean={u for u,v in enumerate(vertices) if len(literal(spelling(v),3))==6}
    todo=list(clean);seen=set(clean)
    for v in todo:
        for u in sorted(reverse[v]):
            if u not in seen:seen.add(u);todo.append(u)
    assert len(seen)==720
    return dict(vertices=720,clean=len(clean),edges=edge_count,normalized=len(seen))
def moves(order,block_length=1):
    children=set()
    for a in range(len(order)-block_length+1):
        block=order[a:a+block_length];rest=order[:a]+order[a+block_length:]
        for b in range(len(rest)+1):children.add(rest[:b]+block+rest[b:])
    children.discard(order);return children
def plateau(order,limit=10000):
    queue=[order];seen={order};edges=[];escapes=[];word0=spelling(order);parent={order:None}
    for u in queue:
        for v in sorted(moves(u)):
            if len(spelling(v))<=len(spelling(u)):
                edges.append((u,v))
                if len(literal(spelling(v),4))==24:escapes.append(v)
                if v not in seen:
                    if len(seen)==limit:return dict(completed=False,cap=limit,states=len(seen))
                    seen.add(v);queue.append(v);parent[v]=u
    block_escapes=[]
    for length in [2,3,4]:
        for v in sorted(moves(order,length)):
            text=spelling(v)
            if len(text)<=len(word0) and len(literal(text,4))==24:
                block_escapes.append(dict(block_length=length,order=v,word=text,length=len(text)))
        if block_escapes:break
    path=[]
    if escapes:
        u=escapes[0]
        while u is not None:path.append(u);u=parent[u]
        path.reverse()
    return dict(completed=True,states=len(seen),edges=len(edges),clean_reachable=len(set(escapes)),
        orders=sorted(seen),reachable_words=sorted({spelling(v) for v in seen}),
        normalization_path=path,normalization_lengths=[len(spelling(v)) for v in path],
        single_relocation_normalization_refuted=not escapes,block_escape=block_escapes[:1],
        scope='THIS COMPLETE NONINCREASING-LENGTH RELOCATION REACHABILITY DOMAIN, NOT A GENERAL NR4/NR6 PROOF')
def main():
    start=time.perf_counter();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    rel=Path(__file__).relative_to(ROOT).as_posix()
    assert subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)==Path(__file__).read_bytes()
    foundation=json.loads((ROOT/'outputs/rr_round141_nr6_foundation_codex.json').read_text())
    repeat=json.loads((ROOT/'outputs/rr_round141_repeat_credit_codex.json').read_text())
    graph=nr3_graph();assert graph['edges']==foundation['graph']['single_vertex']['edges']
    base=sorted({spelling(v) for v in itertools.permutations(['012','021','102','120','201','210'])})
    domain=set(base)
    for w in base:
        for i,p in literal(w,3):domain.add(w[:i+3]+p+w[i+3:])
    hist=collections.Counter()
    for w in sorted(domain):
        r=independent_credit(w,3);hist[r['R'],r['Y'],r['epsilon']]+=1
    assert len(domain)==repeat['controls']
    assert [dict(R=r,Y=y,epsilon=e,count=v) for (r,y,e),v in sorted(hist.items())]==repeat['histogram']
    for record in [repeat['bad_fresh_minimal_in_control_domain'],repeat['nr4_trap'],*repeat['n6_controls']]:
        independent=independent_credit(record['word'],record['n'])
        assert all(independent[k]==record[k] for k in independent if k!='bad_sources')
        assert independent['bad_sources']==[j['source_occurrence'] for j in record['joints'] if j['bad_fresh_blocked']]
    trap=tuple(foundation['nr4_bounded_control']['minimal_found']['order']);local=plateau(trap)
    assert local['completed']
    for row in repeat['nr4_bound_single_repeat_layouts']:
        oo=literal(row['word'],4);assert len(oo)==row['occurrences'] and len({v for _,v in oo})==row['distinct']<24
    out=dict(schema='round141-nr-independent-v1',source_commit=head,source_sha256=sha(__file__),
        input_sha256={f:sha(ROOT/'outputs'/f) for f in ['rr_round141_nr6_foundation_codex.json','rr_round141_repeat_credit_codex.json']},
        nr3=graph,repeat_credit_controls=len(domain),local_plateau=local,
        n4_bound_layouts_verified=6,verified=True,NR6='UNPROVED',seconds=time.perf_counter()-start)
    (ROOT/'outputs/rr_round141_nr6_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,nr3=graph,controls=len(domain),plateau=local,NR6='UNPROVED')))
if __name__=='__main__':main()
