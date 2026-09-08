"""Independent tuple/run formulation of Round136 finite local domains.
Does not import the macro generator or Geometry/its joint table.
"""
import hashlib,json,subprocess,sys
from collections import Counter
from pathlib import Path
from verify_g2_k4_contraction_certificate_codex import measure
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rot(v,k=1):k%=len(v);return v[k:]+v[:k]
def E(v,k=1):return rot(v[:-1],k)+v[-1:]
def Q(v):return min(E(v,j) for j in range(len(v)-1))
def hexid(v):return min(rot(v,j) for j in range(len(v)))
def joint3(ep):return [ep[3:]+tuple(ep[j] for j in tail) for tail in [(1,2,0),(2,0,1),(2,1,0)]]
def literal(ps):
    raw=list(ps[0][0])
    for i,(v,l) in enumerate(ps):
        if i:
            ep=rot(ps[i-1][0],ps[i-1][1]-1)
            w=next((w for w in range(1,7) if w==6 or ep[w:]==v[:-w]),6)
            raw+=list(v[-w:])
        raw+=list(v[:l-1])
    word=''.join(map(str,raw))
    try:
        m,replayed,_,_=measure(word,6)
        assert replayed==ps
        return word
    except AssertionError:return None

def run_domain(repeat_mode):
    result=set();nodes=0;p=tuple(range(6));limit=4 if repeat_mode else 3
    for a in range(1,6):
        c=rot(p,a);T=Q(c)
        starts=[E(c)] if repeat_mode else joint3(rot(p,a-1))
        def rec(v,ps,hs,seen,runs,repeated):
            nonlocal nodes
            nodes+=1;block=list(ps);used=set(hs)
            for ell in range(5):
                u=E(v,ell)
                if u==c:
                    if not repeat_mode or repeated:
                        word=literal(block+[(c,6-a)])
                        if word:result.add(word)
                    break
                if hexid(u) in used:break
                block.append((u,6));used.add(hexid(u))
                if not literal(block):break
                if runs==limit:continue
                # The same-orbit 120 tail is excluded by x=0.
                for t in joint3(rot(u,-1))[1:]:
                    q=Q(t)
                    if q not in seen:rec(t,block,used,seen|{q},runs+1,repeated)
                    elif repeat_mode and q==T and not repeated:rec(t,block,used,seen,runs+1,True)
        for t in starts:rec(t,[(p,a)],{hexid(p)},{Q(p),Q(t)},1,False)
    return nodes,result

def audit_control(row):
    m,ps,used,_=measure(row['word'],4);assert m==row['metrics']
    assert len(used)==24
    entries={v:i for i,(v,l) in enumerate(ps)}
    nu=[entries[rot(v,l)] for v,l in ps]
    q=[Q(v) for v,l in ps]
    weights=[next(k for k in range(1,5) if k==4 or rot(v,l-1)[k:]==t[:-k]) for (v,l),(t,_) in zip(ps,ps[1:])]
    asc={i for i,j in enumerate(nu) if i<j}
    fd={i for i,w in enumerate(weights) if w==2 and i>nu[i]}
    fa={i for i,w in enumerate(weights) if w==2 and i<nu[i]}
    repeat=[];seen={q[0]};runs=[0]
    for i in range(1,len(q)):
        runs.append(runs[-1]+(q[i]!=q[i-1]))
        if q[i]!=q[i-1]:
            if q[i] in seen:repeat.append(i)
            seen.add(q[i])
    extras=set(repeat)-{i+1 for i in fd}
    assert len(asc-fa)+len(extras)==1
    assert sorted(asc-fa)==row['missing_ascents'] and sorted(extras)==[x['pass_index'] for x in row['extra_repeat']]
    assert nu==row['nu'] and runs==row['run_sequence']
    if extras:assert all(weights[i-1]==3 for i in extras)
    assert sorted(i for i in fa if runs[i+1]!=runs[nu[i]])==row['broken_free_locks']
    for step in row['contractions']:
        i,j=step['i'],step['j'];v,a=ps[i];c,b=ps[j];T=Q(c)
        assert rot(v,a)==c and a+b<=4
        assert all(Q(t)==T and l==4 for t,l in ps[i+1:j])
        assert all(Q(t)!=T for t,l in ps[:i]+ps[j+1:])
        ps=ps[:i]+[(v,a+b)]+ps[j+1:]
    assert measure(row['contracted']['word'],4)[1]==ps

def main():
    files=['rr_round136_defects_codex.json','rr_round136_repeat_macros_codex.json','rr_round136_capacity_codex.json']
    d,r,c=[json.loads((ROOT/'outputs'/f).read_text()) for f in files]
    cap=c['capacity']['result'];assert cap['passes']==98 and cap['nodes']==681902414 and not cap['capped']
    assert (cap['b'],cap['g'],cap['s'])==(1,0,13)
    assert len(d['rows'])==7 and sum(len(z['patterns']) for z in d['rows'])==18
    for z in d['rows']:
        assert (z['P'],z['O'],z['D'],z['S'],z['N'],z['F'],z['H'],z['x'],z['delta'])==(122,27,13,25,0,2,0,0,1)
        assert z['f_out']==z['e']+1
    for row in d['n4']['rows']:audit_control(row)
    local_counts={};nodes={}
    for mode,rows in [(False,d['local_n6']['macros']),(True,r['result']['macros'])]:
        n,words=run_domain(mode);name='R' if mode else 'M';nodes[name]=n
        assert words=={z['original']['word'] for z in rows}
        local_counts[name]=len(words)
        for word in words:assert measure(word,6)[0]['H']==measure(word,6)[0]['x']==0
    for z in r['result']['beta_paid_return']:
        m,ps,used,_=measure(z['original']['word'],6)
        assert m['x']==m['H']==0 and m['S']==1
        # Explicit inner-first surgery, independent of maximal()'s choice.
        u=z['inner_phase'];i=u;j=u+5
        v,a=ps[i];c1,b=ps[j];assert rot(v,a)==c1 and a+b==6
        mid=ps[:i]+[(v,6)]+ps[j+1:];midword=literal(mid);assert midword
        mm,*_=measure(midword,6)
        assert mm['x']==1 and mm['e']==0
        assert all(Q(t)==Q(mid[-1][0]) for t,l in mid[1:])
        assert literal([(ps[0][0],6)])==z['contracted']['word']
        assert len(mid)==5 and m['P']==10 and mm['D']==m['D']
    for z in r['result']['free_closer_controls']:measure(z['word'],6)
    result=dict(schema='codex/round136-independent-verification/1',verified=True,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256=sha(__file__),binary_sha256=sha(sys.executable),argv=[sys.executable,*sys.argv],
        input_sha256={f:sha(ROOT/'outputs'/f) for f in files},rows=7,free_patterns=18,n4_controls=155,
        run_domain_nodes=nodes,local_macro_counts=local_counts,beta_paid_return_controls=len(r['result']['beta_paid_return']),
        free_closer_positive_controls=len(r['result']['free_closer_controls']),
        subclass_counts=dict(Counter(z['residual_model'] for z in d['n4']['rows'])),
        capacity=cap,cap_reenumerated_by_this_verifier=False,new_whole_rows_closed=0,rows_remaining=7,
        outer_ledger='10/55',NR6='ASSUMED',full_NR6_search=False,node_cap=None,capped=False,
        proof_scope='finite artifacts independently checked; no-AF and model-coverage claims use the separate hand proof')
    result['mathematical_digest']=digest({k:v for k,v in result.items() if k not in ['source_commit','source_sha256','binary_sha256','argv','input_sha256']})
    (ROOT/'outputs/rr_round136_verified_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
