"""Finite adversarial tests of MULTI-orbit gap extraction. No word search."""
import json,hashlib,subprocess,sys
from collections import Counter
from research_alpha_gap_codex import Geometry,ROOT
from research_round135_contraction_codex import contractions
from verify_locked_detour_contraction_codex import metrics

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def root_return(g,ps):
    qs=[g.q[v] for v,l in ps];runs=[qs[0]]
    for q in qs[1:]:
        if q!=runs[-1]:runs.append(q)
    return (runs[0]==runs[-1] and len(runs)==len(set(runs))+1
            and len(set(runs[1:-1]))==len(runs)-2
            and g.e(ps[-1][0])==ps[0][0])

def candidates(g,ps):
    # All sound ordinary contraction orders, with exactly one gap extraction.
    for i,(v,a) in enumerate(ps):
        if a==g.n:continue
        c=g.s(v,a)
        for j in range(i+1,len(ps)):
            if ps[j]!=(c,g.n-a):continue
            if any(l!=g.n for t,l in ps[i+1:j]):continue
            inner=ps[i+1:j]+[(c,g.n)]
            outer=ps[:i]+[(v,g.n)]+ps[j+1:]
            qi={g.q[t] for t,l in inner};qo={g.q[t] for t,l in outer}
            if qi&qo:continue
            if not g.replay(inner) or not g.replay(outer):continue
            im=metrics(g,inner)
            if im['H'] or im['x']:continue
            if im['e']==0:kind='M_FRESH_GAP'
            elif im['e']==1 and root_return(g,inner):kind='R_ROOT_RETURN_GAP'
            else:continue
            for out,ordinary in ordinary_ends(g,outer):
                om=metrics(g,out)
                if any(l!=g.n for t,l in out) or om['e'] or om['x'] or om['H']:continue
                yield dict(kind=kind,cut=[i,j],inner=g.replay(inner),outer=g.replay(out),
                           inner_metrics=im,outer_metrics=om,ordinary_after=ordinary,ordinary_before=[])
    for new,step in contractions(g,ps):
        for result in candidates(g,new):
            result['ordinary_before']=[step]+result['ordinary_before'];yield result

def ordinary_ends(g,ps):
    yield ps,[]
    for new,step in contractions(g,ps):
        for end,steps in ordinary_ends(g,new):yield end,[step]+steps

def main():
    a=json.loads((ROOT/'outputs/rr_round136_defects_codex.json').read_text())
    b=json.loads((ROOT/'outputs/rr_round137_protected_seam_codex.json').read_text())
    rows=[];hist=Counter()
    domains=[(4,r) for r in a['n4']['rows'] if r['residual_model']=='M_OFF_TARGET']
    domains += [(6,r) for r in b['local']['rows']]
    gg={n:Geometry(n) for n in [4,6]}
    for n,r in domains:
        g=gg[n];ps=[tuple(p) for p in r['passes']];before=metrics(g,ps)
        opts=list(candidates(g,ps))
        rec=dict(n=n,word=r['word'],before=before,solutions=len(opts))
        if opts:
            best=opts[0];im=best['inner_metrics'];om=best['outer_metrics']
            assert len(best['ordinary_before'])+len(best['ordinary_after'])==1
            assert im['P']+om['P']==before['P']-(n-1)
            assert im['O']+om['O']==before['O']-1
            assert im['D']+om['D']==before['D']
            rec['certificate']=best;hist[f'{n}/{best["kind"]}']+=1
        else:hist[f'{n}/NO_EXTRACTION']+=1
        rows.append(rec)
    result=dict(schema='codex/round137-gap-cut/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                source_sha256=hashlib.sha256(__file__ and open(__file__,'rb').read()).hexdigest(),
                scope='preserved finite controls; not a universal proof',histogram=dict(hist),rows=rows)
    result['mathematical_digest']=digest(rows)
    out=ROOT/'outputs/rr_round137_gap_cut_codex.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['histogram']))
if __name__=='__main__':main()
