"""Two independent SMALL marked-chain capacities, b=0, D<=3.

Model A admits E-sigma dirty w3 (locally literal-realizable wrap).
Model AB also admits sigma-E with explicit external-visited ghost obligation.
The latter is a necessary structural relaxation, not literal feasibility.
No covering walk, frontier, or global n6 continuation is enumerated.
"""
import hashlib,itertools,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sigma(p):return p[1:]+p[:1]
def E(p):return p[1:-1]+p[:1]+p[-1:]
def q(p):return min(p[j:-1]+p[:j]+p[-1:] for j in range(5))
def hx(p):return min(p[j:]+p[:j] for j in range(6))
P=tuple(itertools.permutations(range(6)));IX={p:i for i,p in enumerate(P)}
Q=[q(p) for p in P];HE=[hx(p) for p in P];EE=[IX[E(p)] for p in P]
def nexts(v,mode):
    p=P[v][-1:]+P[v][:-1]
    tails=[(2,0,1),(2,1,0),(0,2,1)]+([(1,0,2)] if mode=='AB' else [])
    return [(IX[p[3:]+tuple(p[x] for x in tail)],''.join(map(str,tail))) for tail in tails]
def whole(D,mode):
    nodes=0;best=[];paths=0;h=hashlib.sha256()
    def rec(v,deficit,hs,qs,trail,kinds):
        nonlocal nodes,best,paths
        nodes+=1;h.update(f'{v},{deficit},{len(trail)};'.encode())
        assert Q[v] not in qs
        qq=qs|{Q[v]};local=[];u=v
        for length in range(1,6):
            if HE[u] in hs:break
            hs=hs|{HE[u]};local.append(u);nd=deficit+5-length
            if nd<=D:
                t=trail+local
                if len(t)>len(best):best=list(t)
                paths+=1
                for target,kind in nexts(u,mode):
                    if Q[target] not in qq and HE[target] not in hs:rec(target,nd,hs,qq,t,kinds+[kind])
            u=EE[u]
    rec(0,0,set(),set(),[],[])
    return dict(nodes=nodes,max_passes=len(best),witness=best,accepted_prefixes=paths,transcript_sha256=h.hexdigest(),capped=False)
def port(D,mode):
    # Independently derive ALL endpoint-overlap options and retain EXACT
    # hidden-window type; no nexts(), E(), q(), or hx() call in recurrence.
    strings=[''.join(map(str,p)) for p in P];ids={p:i for i,p in enumerate(strings)}
    hid=[];qid=[];successors=[];fre=[]
    for s in strings:
        hid.append(min(s[j:]+s[:j] for j in range(6)))
        qid.append(min(s[j:5]+s[:j]+s[5] for j in range(5)))
        endpoint=s[-1]+s[:-1];full=[]
        for target in strings:
            gap=next((j for j in range(1,7) if endpoint[j:]==target[:6-j]),6)
            if gap not in (2,3):continue
            raw=endpoint+target[-gap:];hidden=[raw[j:j+6] for j in range(1,gap) if raw[j:j+6] in ids]
            if gap==2 and not hidden:free=ids[target]
            if gap!=3:continue
            if not hidden:full.append(ids[target]);continue
            if hidden==[s]:full.append(ids[target]);continue
            if mode=='AB' and len(hidden)==1 and hidden[0][1:]+hidden[0][:1]==target:full.append(ids[target])
        successors.append(full);fre.append(free)
    nodes=0;best=[];trace=hashlib.sha256()
    def rec(v,runlength,closed,hs,qs,trail):
        nonlocal nodes,best
        nodes+=1;trace.update(f'{v},{runlength},{closed},{len(trail)};'.encode())
        if closed+5-runlength<=D and len(trail)>len(best):best=trail
        f=fre[v]
        if runlength<5 and hid[f] not in hs:rec(f,runlength+1,closed,hs|{hid[f]},qs,trail+[f])
        nd=closed+5-runlength
        if nd>D:return
        for t in successors[v]:
            if qid[t] not in qs and hid[t] not in hs:rec(t,1,nd,hs|{hid[t]},qs|{qid[t]},trail+[t])
    rec(0,1,0,{hid[0]},{qid[0]},[0])
    return dict(nodes=nodes,max_passes=len(best),witness=best,transcript_sha256=trace.hexdigest(),capped=False)
def verify_witness(entries,mode):
    raw=list(P[entries[0]]);edges=[];shadows=set();visited=set()
    for j,v in enumerate(entries):
        p=P[v]
        assert HE[v] not in visited;visited.add(HE[v]);raw+=list(p[:5])
        if j+1==len(entries):break
        t=P[entries[j+1]];end=tuple(raw[-6:]);w=next(d for d in range(1,7) if end[d:]==t[:6-d])
        local=end+t[-w:]; hidden=[local[a:a+6] for a in range(1,w) if local[a:a+6] in IX]
        subtype='CLEAN'
        if hidden:
            if hidden==[p]:subtype='E_SIGMA';ghost=sigma(p)
            else:assert mode=='AB' and hidden==[E(p)];subtype='SIGMA_E';ghost=E(p)
            assert IX[ghost] not in entries;shadows.add(IX[ghost])
        edges.append(dict(source=v,target=entries[j+1],weight=w,hidden=hidden,subtype=subtype))
        raw+=list(t[-w:])
    actual=[tuple(raw[j:j+6]) for j in range(len(raw)-5) if tuple(raw[j:j+6]) in IX]
    if mode=='A':assert len(set(actual))==6*len(entries)
    deficit=5*len({Q[v] for v in entries})-len(entries)
    assert len(shadows)<=deficit
    return dict(entries=entries,word=''.join(map(str,raw)),passes=len(entries),deficit=deficit,edges=edges,
        shadow_ports=sorted(shadows),literal_repeat_count=len(actual)-len(set(actual)),
        required_external_visited_windows=[e['hidden'][0] for e in edges if e['subtype']=='SIGMA_E'])
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    path=Path(__file__);rel=path.relative_to(ROOT).as_posix()
    assert path.read_bytes()==subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
    rows=[];start=time.perf_counter()
    for mode in ['A','AB']:
        for D in range(4):
            a=whole(D,mode);b=port(D,mode);assert a['max_passes']==b['max_passes']
            witnesses=[verify_witness(x['witness'],mode) for x in [a,b]]
            rows.append(dict(mode=mode,D=D,producer=a,independent=b,witnesses=witnesses))
            print(json.dumps(dict(mode=mode,D=D,passes=a['max_passes'],nodes=[a['nodes'],b['nodes']])),flush=True)
    out=dict(schema='round142-shadow-capacity-small-v1',source_commit=head,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        capped=False,completed=True,independent_match=True,rows=rows,seconds=time.perf_counter()-start,
        scope='EXACT_FINITE_b0_D0to3_MARKED_CHAIN_MODELS; AB IS GLOBAL-HISTORY RELAXATION; NOT NR6 SEARCH')
    (ROOT/'outputs/rr_round142_shadow_capacities_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
if __name__=='__main__':main()
