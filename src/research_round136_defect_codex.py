"""Round136: seven rows, exact one-defect bookkeeping, preserved NR4 controls,
and at-most-three-run LOCAL NR6 paid-ascent macros. No full NR6 search.
"""
import argparse,hashlib,itertools,json,subprocess,sys,time
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry,ROOT
from research_round135_contraction_codex import resources,maximal
from verify_g2_k4_contraction_certificate_codex import measure

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def seven_rows():
    rows=[]
    for r in resources():
        if r['delta']!=1:continue
        roles=['a0','a1','d0'] if r['type']=='A' else ['a0','a1','d0','d1']
        patterns=[]
        for free in itertools.product([False,True],repeat=len(roles)):
            if sum(free)!=r['f_out']:continue
            a=2-sum(free[:2]);eta=r['e']-sum(free[2:])
            if a>=0 and eta>=0 and a+eta==1:
                patterns.append(dict(free=[z for z,f in zip(roles,free) if f],a=a,eta=eta,
                                     mechanism='MISSING_ASCENT' if a else 'EXTRA_REPEAT'))
        r=r|dict(patterns=patterns,short_shape='a+b+c=6, a,b,c>=1' if r['type']=='A' else '(b0,6-b0),(b1,6-b1), b0,b1=1..5')
        rows.append(r)
    assert len(rows)==7 and sum(len(r['patterns']) for r in rows)==18
    return rows

def dissect(raw,n):
    g=Geometry(n);m,words,used,_=measure(raw,n)
    ps=[(g.idx[v],l) for v,l in words];P=len(ps)
    entries={v:i for i,(v,l) in enumerate(ps)}
    assert len(entries)==P
    nu={i:entries[g.s(v,l)] for i,(v,l) in enumerate(ps) if g.s(v,l) in entries}
    # The archived controls are COMPLETE: every rotational successor is registered.
    assert len(nu)==P
    q=[g.q[v] for v,l in ps]
    run=[0]
    for a,b in zip(q,q[1:]):run.append(run[-1]+(a!=b))
    wt=[g.weight(g.words[g.s(v,l-1)],g.words[t]) for (v,l),(t,k) in zip(ps,ps[1:])]
    free={i for i,w in enumerate(wt) if w==2 and q[i]!=q[i+1]}
    asc={i for i,j in nu.items() if i<j};desc={i for i,j in nu.items() if i>j}
    rep=[];seen={q[0]}
    for i in range(1,P):
        if run[i]!=run[i-1]:
            if q[i] in seen:rep.append(i)
            seen.add(q[i])
    ordinary={i+1 for i in free&desc}
    extras=[i for i in rep if i not in ordinary]
    a=len(asc-free);eta=len(extras);delta=len(asc)+m['e']-len(free)
    assert set(ordinary)<=set(rep) and len(rep)==m['e'] and delta==a+eta
    bad=[i for i in sorted(asc&free) if run[i+1]!=run[nu[i]]]
    causes=[]
    for i in bad:
        tq=q[nu[i]]
        later=[j for j in rep if j>i and j<=nu[i] and q[j]==tq]
        assert later
        causes.append(dict(ascent=i,target_orbit=tq,target_arc=nu[i],
            first_opening_run=run[i+1],closer_run=run[nu[i]],intervening_repeat_openings=later,
            ordinary=[j for j in later if j in ordinary],exceptional=[j for j in later if j in extras]))
    extra_info=[dict(pass_index=i,incoming_pass=i-1,weight=wt[i-1],target_orbit=q[i],
        kind='FREE_ASCENT_REENTRY' if wt[i-1]==2 else 'PAID_REENTRY') for i in extras]
    end,steps=maximal(g,ps)
    return dict(word=raw,literal_hash=digest(raw),metrics=m,F=len(asc),f_out=len(free),delta=delta,
        a=a,eta=eta,missing_ascents=sorted(asc-free),free_descents=sorted(free&desc),
        repeats=rep,extra_repeat=extra_info,broken_free_locks=bad,lock_causes=causes,
        registered_orbit_sequence=q,run_sequence=run,nu=[nu[i] for i in range(P)],
        passes=ps,weights=wt,maximal_merges=len(steps),contractions=steps,
        contracted=g.replay(end))

def controls():
    data=json.loads((ROOT/'outputs/rr_round135_controls_codex.json').read_text())
    out=[];hist=Counter();examples={}
    for row in data['n4']['controls']:
        if row['delta']!=1:continue
        d=dissect(row['original']['word'],4);assert d['delta']==1 and d['a']+d['eta']==1
        d['type']=row['type'];out.append(d)
        subtype='MISSING_ASCENT' if d['a'] else d['extra_repeat'][0]['kind']
        if d['a']:
            i=d['missing_ascents'][0];j=d['nu'][i]
            aligned=d['registered_orbit_sequence'][i+1]==d['registered_orbit_sequence'][j]
            d['residual_model']='M_ALIGNED' if aligned else 'M_OFF_TARGET'
            if aligned:assert d['maximal_merges']==2
        else:
            assert subtype=='PAID_REENTRY', 'free-ascent exception would refute the no-AF lemma'
            targets={d['registered_orbit_sequence'][d['nu'][i]] for i in range(len(d['nu'])) if i<d['nu'][i]}
            attached=d['extra_repeat'][0]['target_orbit'] in targets
            d['residual_model']='R_ASCENT_TARGET' if attached else 'R_OTHER_TARGET'
            if not attached:assert d['maximal_merges']==2
        key=f"{d['type']}/{subtype}/broken{len(d['broken_free_locks'])}/merges{d['maximal_merges']}"
        hist[key]+=1
        # A literal minimum within this preserved finite control set only.
        for tag,predicate in [('two_free_locks_broken',len(d['broken_free_locks'])>=2),
                              ('no_merge',d['maximal_merges']==0),
                              ('free_ascent_is_the_exception',subtype=='FREE_ASCENT_REENTRY'),
                              ('paid_exception',subtype=='PAID_REENTRY'),
                              ('missing_ascent_but_other_lock_broken',d['a']==1 and bool(d['broken_free_locks']))]:
            if predicate and (tag not in examples or (len(d['word']),d['word'])<(len(examples[tag]['word']),examples[tag]['word'])):examples[tag]=d
    assert len(out)==155
    return dict(input_sha256=sha(ROOT/'outputs/rr_round135_controls_codex.json'),
        scope='all 155 delta1 controls in preserved exhaustive NR4 L<=39 corpus; no NR6 completeness claim',
        rows=out,histogram=dict(hist),counterexamples=examples)

def local_macros():
    g=Geometry(6);finite=Counter();local=[];nodes=0
    # Entire length-bounded local domain: one split hex, paid opener, <=3 runs,
    # fresh orbits, x=H=0; finish at the complementary short arc.
    for a in range(1,6):
        c=g.s(0,a);T=g.q[c]
        for t,w in g.joint[g.s(0,a-1)]:
            if w!=3:continue
            finite['paid_entry_types']+=1
            def rec(v,prefix,hs,qs,runs):
                nonlocal nodes
                nodes+=1
                if v==c:
                    ps=prefix+[(v,6-a)];rep=g.replay(ps)
                    if not rep:finite['closing_collision']+=1;return
                    end,steps=maximal(g,ps)
                    row=dict(split=a,initial_target=t,initial_target_orbit=g.q[t],closer_orbit=T,
                        run_count=runs,original=rep,merge_count=len(steps),contracted=g.replay(end))
                    finite[f'legal_runs{runs}_merges{len(steps)}']+=1;local.append(row);return
                if g.h[v] in hs:finite['full_hex_collision']+=1;return
                new=prefix+[(v,6)]
                # Joint legality and literal no-repeat do not depend on future runs.
                if not g.replay(new):finite['literal_collision']+=1;return
                nh=hs|{g.h[v]}
                free=g.e(v)
                if g.h[free] not in nh or free==c:rec(free,new,nh,qs,runs)
                else:finite['E_collision']+=1
                if runs<3:
                    for target,wt in g.joint[g.s(v,-1)]:
                        if wt==3 and g.q[target]!=g.q[v] and g.q[target] not in qs:
                            rec(target,new,nh,qs|{g.q[target]},runs+1)
            rec(t,[(0,a)],{g.h[0]},{g.q[0],g.q[t]},1)
    # All 720 starts: exactly one paid tail stays in the successor-arc orbit,
    # and it lands two E phases ahead. This is independent of split length.
    identity_count=0
    for v in range(720):
        for a in range(1,6):
            c=g.s(v,a)
            hits=[t for t,w in g.joint[g.s(v,a-1)] if w==3 and g.q[t]==g.q[c]]
            assert hits==[g.e(c,2)]
            identity_count+=1
    return dict(scope='finite local <=3 fresh runs; NOT all possible defect gaps',node_cap=None,capped=False,
        nodes=nodes,identity_pairs=identity_count,counts=dict(finite),macros=local,
        guaranteed_SAT_controls=sum(r['merge_count']==0 for r in local))

def capacity():
    exe=ROOT.parent/'supersequence-n6-research-round115-f0-audit/outputs/chain_capacity_115_codex.exe'
    argv=[str(exe),'1','0','13','20000000000'];t=time.perf_counter()
    result=json.loads(subprocess.check_output(argv,text=True))
    assert result['capped'] is False and result['passes']==98 and result['nodes']==681902414
    return dict(argv=argv,parameters=[1,0,13],result=result,seconds=time.perf_counter()-t,
        binary_sha256=sha(exe),source_sha256=sha(ROOT/'src/chain_capacity_115.c'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--capacity',action='store_true');a=p.parse_args()
    result=dict(schema='codex/round136-one-defect/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256=sha(__file__),binary_sha256=sha(sys.executable),argv=[sys.executable,*sys.argv],rows=seven_rows())
    if a.capacity:result['capacity']=capacity();name='capacity'
    else:result['n4']=controls();result['local_n6']=local_macros();name='defects'
    result['mathematical_digest']=digest({k:v for k,v in result.items() if k in ['rows','n4','local_n6']} if not a.capacity else result['capacity']['result'])
    (ROOT/f'outputs/rr_round136_{name}_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k=='capacity'} if a.capacity else
        dict(n4=len(result['n4']['rows']),n4_hist=result['n4']['histogram'],counterexamples=list(result['n4']['counterexamples']),
             local_nodes=result['local_n6']['nodes'],local_counts=result['local_n6']['counts'])))

if __name__=='__main__':main()
