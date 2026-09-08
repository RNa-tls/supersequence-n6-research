"""Literal NR4 controls and general multi-colour repeat-event injection.
No complete NR6 search. Counterexamples are never labelled complete NR6 words.
"""
import itertools,json,time,hashlib,subprocess
from collections import Counter
from research_alpha_gap_codex import Geometry,ROOT
from research_round135_contraction_codex import geometry
from research_round138_privacy_codex import classify,run_words
from verify_g2_k4_contraction_certificate_codex import measure

def injection(word,colours):
    """One charge per newly seen piece colour after an orbit's first colour.
    Adjacent runs differ, so every such charge is an actual repeat opening.
    """
    seen={};charge=[];repeats=[]
    for i,(q,c) in enumerate(zip(word,colours)):
        if q in seen:
            repeats.append(i)
            if c not in seen[q]:charge.append(i)
        seen.setdefault(q,set()).add(c)
    sharing=sum(len(cs)-1 for cs in seen.values())
    assert len(charge)==sharing and set(charge)<=set(repeats)
    return sharing,charge,repeats

def event_csp():
    total=0;hist=Counter();counter=None
    for word in run_words(7):
        # ALL ordered partitions into <=3 nonempty consecutive run pieces.
        for count in range(1,min(3,len(word))+1):
            for cuts in itertools.combinations(range(1,len(word)),count-1):
                colours=[sum(i>=j for j in cuts) for i in range(len(word))]
                s,charge,repeats=injection(word,colours)
                # Every subset of repeat openings is allowed as ordinary.
                for mask in range(1<<len(repeats)):
                    ordinary={j for z,j in enumerate(repeats) if mask>>z&1}
                    eta=set(repeats)-ordinary
                    # Designate 0,1,2 eta units; no disjointness is assumed.
                    for nq in range(min(2,len(eta))+1):
                        for ds in itertools.combinations(sorted(eta),nq):
                            designated=set(ds);a=2-nq;q=a+nq
                            o=len(set(charge)&ordinary);z=len(set(charge)&designated)
                            delta=a+len(eta);bound=q+s-o-z
                            assert delta>=bound
                            total+=1;hist[f's{s}/ordinary{o}/overlap{z}']+=1
                            if delta==2 and q==2 and s>0 and counter is None:
                                counter=dict(run_orbits=word,colours=colours,ordinary=sorted(ordinary),
                                    designated=ds,a=a,eta=len(eta),delta=delta,q=q,s=s,
                                    charge=charge,corrected_bound=bound)
    return dict(models=total,histogram=dict(hist),naive_q_plus_s_counterexample=counter,
                capped=False,scope='run equality patterns <=7, <=3 chronological pieces; arbitrary ordinary/designated repeat subsets')

def all_contractions(g,ps):
    """Safe literal arc surgery WITHOUT orbit privacy. Its orbit decrement is
    measured, not presumed to be one. A local operation, not a capacity prune.
    """
    for i,(v,a) in enumerate(ps):
        if a==g.n:continue
        c=g.s(v,a);q=g.q[c]
        for j in range(i+1,len(ps)):
            t,b=ps[j]
            if t!=c or a+b>g.n:continue
            if any(g.q[w]!=q or l!=g.n for w,l in ps[i+1:j]):continue
            nxt=ps[:i]+[(v,a+b)]+ps[j+1:]
            assert g.replay(nxt) is not None
            yield nxt,dict(i=i,j=j,removed=j-i,orbit_removed=not any(g.q[w]==q for w,l in nxt))

def reductions(g,ps):
    yield ps,[]
    for new,step in all_contractions(g,ps):
        for end,steps in reductions(g,new):yield end,[step]+steps

def piece_kind(g,ps):
    rep=g.replay(ps)
    if rep is None or any(l!=g.n for v,l in ps):return None
    m,_,_,_=measure(rep['word'],g.n)
    q=[g.q[v] for v,l in ps];run=[q[0]]
    for a,b in zip(q,q[1:]):
        if a!=b:run.append(b)
    rootreturn=(len(run)>=3 and run[0]==run[-1] and len(set(run))==len(run)-1
        and run.count(run[0])==2 and g.e(ps[-1][0])==ps[0][0])
    return dict(metrics=m,root_return=rootreturn,word=rep['word'])

def decompositions(g,ps):
    out=[]
    for red,steps in reductions(g,ps):
        k=piece_kind(g,red)
        if k:out.append(dict(kind='full',ordinary=steps,pieces=[k]));continue
        for i,(v,a) in enumerate(red):
            if a==g.n:continue
            c=g.s(v,a)
            for j in range(i+1,len(red)):
                if red[j]!=(c,g.n-a) or any(l!=g.n for w,l in red[i+1:j]):continue
                inside=red[i+1:j]+[(c,g.n)]
                outside=red[:i]+[(v,g.n)]+red[j+1:]
                A=piece_kind(g,inside)
                if not A:continue
                for end,ss in reductions(g,outside):
                    B=piece_kind(g,end)
                    if not B:continue
                    shared=sorted({g.q[w] for w,l in inside}&{g.q[w] for w,l in end})
                    out.append(dict(kind='gap',ordinary=steps,cut=[i,j],after=ss,pieces=[A,B],shared=shared))
    return out

def nr4():
    g=geometry(4);adj={v:[(g.s(v),1)]+g.joint[v] for v in range(24)}
    nodes=complete=0;rows=[];hist=Counter()
    def visit(v,mask,path,cost,pcount):
        nonlocal nodes,complete
        nodes+=1;left=24-len(path)
        if 4+cost+left>39 or pcount>8:return
        if not left:
            complete+=1
            if pcount!=8:return
            raw=list(g.words[path[0]])
            for a,b in zip(path,path[1:]):raw.extend(g.words[b][-g.weight(g.words[a],g.words[b]):])
            word=''.join(map(str,raw));m,pp,_,_=measure(word,4);ps=[(g.idx[v],l) for v,l in pp]
            d=classify(g,ps,word)
            if d['delta']+m['x']+m['H']>d['F']:return
            typ='A' if max(Counter(g.h[v] for v,l in ps).values())==3 else 'B'
            if typ=='A' and d['F']==1:assert d['delta']>=1
            dec=decompositions(g,ps)
            selected=min(dec,key=lambda z:(len(z['pieces']),sum(p['metrics']['e']+p['metrics']['x'] for p in z['pieces']))) if dec else None
            tag=str((typ,d['F'],d['delta'],m['x'],m['H'],bool(dec)))
            hist[tag]+=1
            a_events={i+1 for i,j in enumerate(d['nu']) if i<j and (i+1>=len(ps) or g.weight(g.words[g.s(*ps[i])],g.words[ps[i+1][0]])==0)} if False else []
            rows.append(dict(word=word,n=4,type=typ,classification=d,decomposition=selected))
            return
        for t,w in adj[v]:
            if mask>>t&1:continue
            visit(t,mask|1<<t,path+[t],cost+w,pcount+(w!=1))
    visit(0,1,[0],0,1)
    return dict(nodes=nodes,complete_walks_in_domain=complete,rows=rows,histogram=dict(hist),
                scope='ALL normalized NR4 literal walks L<=39, pass count<=8; record G2 and delta+x+H<=F',capped=False)

def local_fusions():
    old=json.loads((ROOT/'outputs/rr_round138_privacy_controls_codex.json').read_text())['controls']['rows']
    out=[];cache={n:Geometry(n) for n in [4,6]}
    for row in old:
        g=cache[row['n']];m,pp,_,_=measure(row['word'],g.n);ps=[(g.idx[v],l) for v,l in pp]
        d=classify(g,ps,row['word']);weights=[g.weight(g.words[g.s(v,l-1)],g.words[t]) for (v,l),(t,b) in zip(ps,ps[1:])]
        free={i for i,w in enumerate(weights) if w==2 and g.q[ps[i][0]]!=g.q[ps[i+1][0]]}
        missing={i+1 for i,j in enumerate(d['nu']) if i<j and i not in free}
        fused=sorted(missing&set(d['exceptional']))
        out.append(dict(word=row['word'],n=g.n,classification=d,missing_ascent_events=sorted(missing),
                        fused_events=fused,shared_orbit=row['shared_orbit'],decompositions=decompositions(g,ps)))
    return out

def main():
    start=time.perf_counter();data=dict(schema='codex/round139-controls/1',local=local_fusions(),n4=nr4(),csp=event_csp())
    data['seconds']=time.perf_counter()-start
    data['commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    data['committed_source_sha256']=hashlib.sha256(subprocess.check_output(['git','show','HEAD:src/research_round139_controls_codex.py'])).hexdigest()
    (ROOT/'outputs/rr_round139_controls_codex.json').write_text(json.dumps(data,indent=2)+'\n')
    print(data['n4']['histogram']);print('CSP',data['csp']['models']);print('seconds',data['seconds'])
if __name__=='__main__':main()
