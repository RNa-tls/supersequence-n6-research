"""Finite local one-split, one-paid-repeat macro controls; not complete NR6."""
import json,subprocess,sys
from collections import Counter
from research_alpha_gap_codex import Geometry,ROOT
from research_round135_contraction_codex import maximal
from research_round136_defect_codex import digest,sha
from verify_g2_k4_contraction_certificate_codex import measure

def enumerate_macros():
    g=Geometry(6);rows=[];nodes=0;counts=Counter()
    for a in range(1,6):
        c=g.s(0,a);T=g.q[c]
        def visit(v,ps,hs,seen,runs,repeat):
            nonlocal nodes
            nodes+=1
            if v==c:
                if not repeat:counts['unmarked_completion']+=1;return
                path=ps+[(c,6-a)];rep=g.replay(path)
                if not rep:counts['closing_collision']+=1;return
                m,*_=measure(rep['word'],6)
                assert m['e']==1 and m['x']==m['H']==0
                end,steps=maximal(g,path)
                counts[f'legal_runs{runs}_merges{len(steps)}']+=1
                rows.append(dict(split=a,original=rep,metrics=m,run_count=runs,
                    repeated_orbit=T,merge_count=len(steps),contracted=g.replay(end)))
                return
            if g.h[v] in hs:counts['hex_collision']+=1;return
            path=ps+[(v,6)]
            if not g.replay(path):counts['literal_collision']+=1;return
            nh=hs|{g.h[v]}
            t=g.e(v)
            if g.h[t] not in nh or t==c:visit(t,path,nh,seen,runs,repeat)
            else:counts['E_collision']+=1
            if runs>=4:return
            for t,w in g.joint[g.s(v,-1)]:
                if w!=3 or g.q[t]==g.q[v]:continue
                q=g.q[t]
                if q not in seen:visit(t,path,nh,seen|{q},runs+1,repeat)
                elif q==T and not repeat:visit(t,path,nh,seen,runs+1,True)
        visit(g.e(c),[(0,a)],{g.h[0]},{g.q[0],T},1,False)
    return dict(scope='one local split, free opener, exactly one paid return to its closer orbit, <=4 orbit runs',
        nodes=nodes,node_cap=None,capped=False,counts=dict(counts),macros=rows)

if __name__=='__main__':
    data=dict(schema='codex/round136-local-repeat-macros/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256=sha(__file__),binary_sha256=sha(sys.executable),argv=[sys.executable,*sys.argv],result=enumerate_macros())
    data['mathematical_digest']=digest(data['result'])
    (ROOT/'outputs/rr_round136_repeat_macros_codex.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data['result'].items() if k!='macros'}))
