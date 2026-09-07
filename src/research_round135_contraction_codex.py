"""Round135: resources, local surgery, NR4 controls, inherited capacity replays.
Never searches complete NR6 words.
"""
import argparse,hashlib,itertools,json,subprocess,sys,time
from collections import Counter,defaultdict
from pathlib import Path
from research_alpha_gap_codex import Geometry,ROOT
from verify_locked_detour_contraction_codex import metrics

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resources():
    out=[]
    for typ,F in [('A',1),('A',2),('B',2)]:
        for delta,x,H in itertools.product(range(2),repeat=3):
            if delta+x+H>F-1:continue
            for e in range(5):
                f=F+e-delta
                if not 0<=f<= (3 if typ=='A' else 4):continue
                S=26+e+x-f;N=S+2-27;L=846+S+H
                assert L<=871 and 5*27-122==13
                out.append(dict(id=f'{typ}_F{F}_d{delta}_x{x}_H{H}_e{e}',type=typ,F=F,
                                delta=delta,e=e,x=x,H=H,f_out=f,S=S,N=N,L=L,P=122,O=27,D=13))
    assert len(out)==25
    return out

def geometry(n):
    g=Geometry(n)
    for a,w in enumerate(g.words):
        for tail in itertools.permutations(w[:4]):
            target=w[4:]+tail
            if g.weight(w,target)!=4:continue
            raw=w+tail
            if any(len(set(raw[j:j+n]))==n for j in range(1,4)):continue
            g.joint[a].append((g.idx[target],4))
    return g

def contractions(g,ps):
    ps=[tuple(p) for p in ps]
    for i,(v,a) in enumerate(ps):
        if a==g.n:continue
        c=g.s(v,a)
        for j in range(i+1,len(ps)):
            if ps[j][0]!=c:continue
            b=ps[j][1]
            if a+b>g.n:continue
            T=g.q[c]
            if any(g.q[w]!=T or l!=g.n for w,l in ps[i+1:j]):continue
            if any(g.q[w]==T for w,l in ps[:i]+ps[j+1:]):continue
            new=ps[:i]+[(v,a+b)]+ps[j+1:]
            assert g.replay(ps) and g.replay(new)
            assert set(g.windows(new))<set(g.windows(ps))
            oldm,newm=metrics(g,ps),metrics(g,new)
            assert newm['O']==oldm['O']-1 and newm['P']==oldm['P']-(j-i)
            internal=[g.weight(g.words[g.s(w,l-1)],g.words[t]) for (w,l),(t,m) in zip(ps[i:j],ps[i+1:j+1])]
            assert newm['S']==oldm['S']-sum(w>=3 for w in internal)
            assert newm['H']==oldm['H']-sum(max(w-3,0) for w in internal)
            yield new,dict(i=i,j=j,arc_lengths=[a,b],internal_weights=internal,before=oldm,after=newm)

def maximal(g,ps):
    best=(ps,[])
    for nxt,step in contractions(g,ps):
        end,steps=maximal(g,nxt)
        if len(steps)+1>len(best[1]):best=end,[step]+steps
    return best

def controls():
    from verify_f2_structure_126 import setup
    from verify_fg_repair_128 import walk_measure
    g=geometry(4);table=setup(4);W=[[g.weight(a,b) for b in g.words] for a in g.words]
    adj={v:sorted([(g.s(v),1)]+g.joint[v]) for v in range(24)}
    nodes=0;complete=0;rows=[];hist=Counter()
    def dfs(v,used,path,cost):
        nonlocal nodes,complete
        nodes+=1;left=24-len(path)
        if 4+cost+left>39:return
        if not left:
            complete+=1;m=walk_measure(table,W,path,4+cost)
            if m['G']!=2:return
            delta=m['F']+m['e']-m['f_out']
            if delta+m['x']+m['H']>m['F']-1:return
            assert delta>=0
            typ='A' if m['partition']==(2,) else 'B'
            ps=m['passes'];end,steps=maximal(g,ps)
            key=(typ,m['F'],delta,m['x'],m['H'],m['e'],len(steps))
            hist[str(key)]+=1
            rows.append(dict(type=typ,F=m['F'],delta=delta,x=m['x'],H=m['H'],e=m['e'],
                             original=g.replay(ps),contracted=g.replay(end),steps=steps,
                             remaining_short=sum(l<4 for v,l in end)))
            return
        for t,w in adj[v]:
            if used>>t&1 or 4+cost+w+left-1>39:continue
            dfs(t,used|(1<<t),path+[t],cost+w)
    dfs(0,1,[0],0)
    assert complete==29255
    return dict(nodes=nodes,complete_walks=complete,controls=rows,histogram=dict(hist),node_cap=None)

def local_controls():
    g=geometry(6);rows=[];counts=Counter()
    # Consecutive partial arcs, with zero or one omitted full E-phase (M3a).
    for a in range(1,6):
        for b in range(1,7-a):
            c=g.s(0,a)
            for skip in [None,1,2,3]:
                entries=[g.e(c,j) for j in range(1,5)]+[c]
                if skip is not None:del entries[skip]
                ps=[(0,a)]+[(v,6) for v in entries[:-1]]+[(c,b)]
                if not g.replay(ps):continue
                new,steps=maximal(g,ps);assert len(steps)==1
                assert new==[(0,a+b)]
                counts['partial_merge']+=1
                # Heavy seam outside the surgery: literal boundary must survive.
                for t,w in g.joint[g.s(c,b-1)]:
                    if w!=4:continue
                    longer=ps+[(t,6)]
                    if not g.replay(longer):continue
                    end,ss=maximal(g,longer);assert len(ss)==1 and metrics(g,end)['H']==1
                    counts['external_heavy_context']+=1
                rows.append(dict(original=g.replay(ps),contracted=g.replay(new),steps=steps))
    return dict(counts=dict(counts),witnesses=rows)

def capacities():
    old=ROOT.parent/'supersequence-n6-research-round115-f0-audit'
    exe=old/'outputs/chain_capacity_115_codex.exe'
    src=ROOT/'src/chain_capacity_115.c'
    assert sha(src)=='c7694b66f3d31770f5ed9d91b7b61a1973c2138d22513a0d7ca40615dc74544a'
    stored=json.loads((ROOT/'outputs/rr_f0_column_115.json').read_text())['table']
    out=[]
    for b,g,s in [(0,0,s) for s in range(14)]+[(1,0,15)]:
        argv=[str(exe),str(b),str(g),str(s),'20000000000']
        t=time.perf_counter();p=subprocess.run(argv,capture_output=True,text=True,check=True)
        data=json.loads(p.stdout);key=f'{b},{g},{s}'
        assert data==stored[key],(key,data,stored[key])
        assert data['capped'] is False
        row=dict(parameters=[b,g,s],argv=argv,result=data,seconds=time.perf_counter()-t,
                 source_sha256=sha(src),binary_sha256=sha(exe))
        out.append(row);print(key,data,flush=True)
    C=[r['result']['passes'] for r in out[:14]]
    conv=[dict(left=s,right=13-s,bound=C[s]+C[13-s]) for s in range(14)]
    return dict(replays=out,two_chain_deficit13=conv,max_bound=max(r['bound'] for r in conv))

def main():
    p=argparse.ArgumentParser();p.add_argument('--controls',action='store_true');p.add_argument('--capacity',action='store_true');a=p.parse_args()
    start=time.perf_counter()
    d=dict(schema='codex/round135-structural-research/1',rows=resources(),
           source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           source_sha256=sha(__file__),driver_sha256=sha(__file__),binary_sha256=sha(sys.executable),
           argv=[sys.executable,*sys.argv],scope='resources/local controls/chain table only; no complete NR6 DFS')
    if a.controls:d['n4']=controls();d['n6_local']=local_controls()
    if a.capacity:d['capacity']=capacities()
    d['seconds']=time.perf_counter()-start
    d['deterministic_digest']=hashlib.sha256(json.dumps({k:v for k,v in d.items() if k!='seconds'},sort_keys=True).encode()).hexdigest()
    suffix='controls' if a.controls else 'capacity' if a.capacity else 'resources'
    (ROOT/f'outputs/rr_round135_{suffix}_codex.json').write_text(json.dumps(d,indent=2)+'\n')
    print('COMPLETE',suffix,flush=True)

if __name__=='__main__':main()
