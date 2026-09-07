"""Literal tests of locked-detour contraction, not a complete n6 search."""
import hashlib
import itertools
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry, ROOT


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def metrics(g, ps):
    qs = [g.q[v] for v, l in ps]
    ws = [g.weight(g.words[g.s(v,l-1)],g.words[t])
          for (v,l),(t,m) in zip(ps,ps[1:])]
    r = 1 + sum(a != b for a,b in zip(qs,qs[1:]))
    return dict(P=len(ps),O=len(set(qs)),D=(g.n-1)*len(set(qs))-len(ps),
                r=r,e=r-len(set(qs)),S=sum(w>=3 for w in ws),
                H=sum(max(w-3,0) for w in ws),
                x=sum(w>=3 and a==b for w,a,b in zip(ws,qs,qs[1:])),
                windows=len(g.windows(ps)))


def contract_once(g, ps):
    ps = [tuple(p) for p in ps]
    for i,(v,b) in enumerate(ps):
        if b==g.n: continue
        block = g.half(v,b)
        if ps[i:i+g.n] != block: continue
        new = ps[:i]+[(v,g.n)]+ps[i+g.n:]
        assert g.replay(ps) is not None and g.replay(new) is not None
        oldwin, newwin = set(g.windows(ps)),set(g.windows(new))
        assert newwin < oldwin
        assert len(oldwin-newwin)==g.n*(g.n-2)
        assert ps[0][0]==new[0][0]
        assert g.s(*[ps[-1][0],ps[-1][1]-1])==g.s(new[-1][0],new[-1][1]-1)
        before,after=metrics(g,ps),metrics(g,new)
        assert after['P']==before['P']-(g.n-1)
        assert after['O']==before['O']-1
        for key in ('D','S','H'): assert before[key]==after[key],(key,before,after)
        removed=set(g.q[z] for z,l in ps)-set(g.q[z] for z,l in new)
        assert removed=={g.q[g.s(v,b)]}
        return new,dict(index=i,entry=v,split=b,before=before,after=after,
                        removed_orbit=list(removed)[0])
    raise AssertionError(('no locked detour',ps))


def contract_two(g, ps):
    original=[tuple(p) for p in ps]
    assert g.replay(original)
    ps,a=contract_once(g,original)
    ps,b=contract_once(g,ps)
    assert all(l==g.n for v,l in ps)
    assert len({g.h[v] for v,l in ps})==len(ps)
    before,after=metrics(g,original),metrics(g,ps)
    assert after['e']==0 and after['x']==0,(before,after)
    return dict(original=g.replay(original),contracted=g.replay(ps),steps=[a,b],
                before=before,after=after)


def finite_blocks():
    g=Geometry(6);stat=Counter();rows=[]
    # All literal words/splits: exact local replacement identities.
    for v in range(720):
        for b in range(1,6):
            ps=g.half(v,b);new,rec=contract_once(g,ps)
            assert new==[(v,6)]
            stat['all_S6_single_detours']+=1
    # No production block builder used. Include every run-prefix length and exit.
    for kind in ('beta_e1','beta_e2','T'):
        for b0,b1,u,ell in itertools.product(range(1,6),range(1,6),range(1,5),range(1,6)):
            stat[kind+'_input']+=1
            pre=[(g.e(0,-j),6) for j in range(ell-1,0,-1)]
            c0=g.s(0,b0)
            if kind.startswith('beta'):
                o1=g.e(c0,u)
                ps=pre+[(0,b0)]+[(g.e(c0,j),6) for j in range(1,u)]
                ps+=g.half(o1,b1)+[(g.e(c0,j),6) for j in range(u+1,5)]+[(c0,6-b0)]
                if kind=='beta_e2':ps += [(g.e(0),6)]
            else:
                ps=pre+g.half(0,b0)+[(g.e(0,j),6) for j in range(1,u)]
                ps+=g.half(g.e(0,u),b1)+[(g.e(0,u+1),6)]
            if g.replay(ps) is None:stat[kind+'_literal_collision']+=1;continue
            result=contract_two(g,ps)
            stat[kind+'_accepted']+=1
            rows.append(dict(kind=kind,b0=b0,b1=b1,u=u,ell=ell,**result))
    archive=json.loads((ROOT/'outputs/rr_alpha_gap_research_codex.json').read_text())
    alpha=[]
    for row in archive['exact_local_gaps']['rows']:
        for b1,w in row['witnesses'].items():
            a=contract_two(g,w['passes']);stat['alpha_preserved_witnesses']+=1
            alpha.append(dict(kind=row['kind'],b0=row['b0'],b1=b1,**a))
    return dict(counts=dict(stat),rigid_controls=rows,alpha_controls=alpha)


def n4():
    from verify_f2_structure_126 import n4_walks
    from verify_fg_repair_128 import walk_measure
    from verify_b_machine_132 import _structure
    table,W,walks=n4_walks(39);g=Geometry(4);out=[];counts=Counter()
    # NR4 positive controls can contain heavy joints; the n6 local experiment
    # intentionally listed only weights 2/3. Extend the literal checker, not the
    # theorem premises, to retain those valid NR4 controls.
    for a,w in enumerate(g.words):
        for tail in itertools.permutations(w):
            if g.weight(w,tail)!=4:continue
            raw=w+tail
            if any(len(set(raw[j:j+4]))==4 for j in range(1,4)):continue
            g.joint[a].append((g.idx[tail],4))
    for L,seq in walks:
        m=walk_measure(table,W,seq,L)
        if m['G']!=2 or m['x'] or m['f_out']!=m['F']+m['e']:continue
        s=_structure(table,m)
        if not s:continue
        kind='alpha' if s['lock0'] else 'beta'
        result=contract_two(g,m['passes']);counts[kind]+=1
        out.append(dict(kind=kind,L=L,**result))
    return dict(universe='all NR4 words from start0123, length<=39',
                input_complete_walks=len(walks),counts=dict(counts),controls=out)


def main():
    t=time.perf_counter()
    result=dict(schema='codex/locked-detour-contraction/1',
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                geometry_sha256=hashlib.sha256((ROOT/'src/research_alpha_gap_codex.py').read_bytes()).hexdigest(),
                driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                binary_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                full_argv=[sys.executable,*sys.argv],parameters={'n4_maxlen':39,'n6_rigid_inputs':1500},
                finite_blocks=finite_blocks(),n4=n4())
    result['verdict']='UNSAT_COMPLETE'
    result['scope']='no counterexample to contraction in the stated finite controls; theorem is separately proved'
    result['node_count']=sum(result['finite_blocks']['counts'].get(k,0) for k in ('all_S6_single_detours','beta_e1_input','beta_e2_input','T_input'))
    result['seconds']=time.perf_counter()-t
    result['deterministic_digest']=digest({k:v for k,v in result.items() if k not in ('seconds','source_commit','full_argv')})
    (ROOT/'outputs/rr_locked_detour_contraction_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(counts=result['finite_blocks']['counts'],n4=result['n4']['counts'],seconds=result['seconds'],digest=result['deterministic_digest'])))


if __name__=='__main__':main()
