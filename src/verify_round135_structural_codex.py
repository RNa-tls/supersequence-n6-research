"""Independent run-level extreme-chain replay, resource and surgery checks."""
import hashlib,itertools,json,subprocess,sys
from collections import Counter
from research_alpha_gap_codex import Geometry,ROOT
from research_round135_contraction_codex import resources,geometry,sha,maximal
from verify_g2_k4_contraction_certificate_codex import measure


def run_enum(g,target,cap):
    nodes=0;answer=[]
    def rec(v,prefix,hs,qs,d):
        nonlocal nodes
        nodes+=1;Q=g.q[v];assert Q not in qs
        path=prefix[:];used=set(hs)
        for length in range(1,6):
            u=g.e(v,length-1)
            if g.h[u] in used:break
            used.add(g.h[u]);path.append(u);nd=d+5-length
            if len(path)>target:break
            if nd>cap:continue
            if len(path)==target:answer.append(tuple(path));continue
            ep=g.words[g.s(u,-1)]
            # Direct positional formulas; no joint-list construction.
            for tail in [(ep[2],ep[0],ep[1]),(ep[2],ep[1],ep[0])]:
                t=g.idx[ep[3:]+tail]
                if g.q[t] not in qs|{Q}:rec(t,path,used,qs|{Q},nd)
    rec(0,[],set(),set(),0)
    return nodes,answer


def main():
    data=json.loads((ROOT/'outputs/rr_round135_controls_codex.json').read_text())
    cap=json.loads((ROOT/'outputs/rr_round135_capacity_codex.json').read_text())
    seam=json.loads((ROOT/'outputs/rr_round135_heavy_seams_codex.json').read_text())
    rs=resources();assert rs==data['rows']==cap['rows']
    from verify_g2_cells_129 import rows
    old=rows(3,3);old=[r for r in old if not r['dead']]
    keys=['type','F','e','x','H','f_out','S','N','L']
    assert {tuple(r[k] for k in keys) for r in rs}=={tuple(r[k] for k in keys) for r in old}
    g=Geometry(6);ext={};nodes={}
    for T,D in [(46,4),(66,9)]:
        nc,paths=run_enum(g,T,D);nodes[str(T)]=nc;ext[T]=paths
        archived=next(r['rows'] for r in seam['chains'] if r['target']==T)
        assert set(paths)=={tuple(r['path']) for r in archived}
        for p in paths:
            rep=g.replay([(v,6) for v in p]);assert rep
            m,*_=measure(rep['word'],6)
            assert m['P']==T and m['D']==D and m['e']==m['x']==m['H']==0
    counts=Counter();seam_rows=[]
    for A_len,B_len in [(46,66),(66,46)]:
        for ai,A in enumerate(ext[A_len]):
            aw=g.words[g.s(A[-1],-1)]
            Aq={g.q[v] for v in A};Ah={g.h[v] for v in A}
            for bi,B in enumerate(ext[B_len]):
                for label in itertools.permutations(range(6)):
                    counts['all_label_tests']+=1
                    wt=next((k for k in range(1,6) if aw[k:]==label[:-k]),6)
                    if wt!=4:continue
                    raw=aw+label[-4:]
                    if any(len(set(raw[j:j+6]))==6 for j in range(1,4)):continue
                    bp=[g.idx[tuple(label[z] for z in g.words[v])] for v in B]
                    reason='orbit_collision' if Aq&{g.q[v] for v in bp} else 'hex_collision' if Ah&{g.h[v] for v in bp} else 'SAT'
                    counts[reason]+=1
                    seam_rows.append(dict(left_length=A_len,left_index=ai,right_index=bi,label=label,reason=reason))
    assert counts['SAT']==0 and counts['orbit_collision']==158 and counts['hex_collision']==154
    assert len(seam_rows)==312
    C=[r['result']['passes'] for r in cap['capacity']['replays'][:14]]
    assert all(not r['result']['capped'] for r in cap['capacity']['replays'])
    assert max(C[i]+C[13-i] for i in range(14))==112
    assert [i for i in range(14) if C[i]+C[13-i]==112]==[4,9]
    cg=geometry(4);cc=Counter();counterexamples={};decompositions=0
    for row in data['n4']['controls']:
        orig=row['original'];ps=[tuple(p) for p in orig['passes']]
        for step in row['steps']:
            i,j=step['i'],step['j'];v,a=ps[i];c,b=ps[j]
            assert cg.s(v,a)==c and a+b<=4
            new=ps[:i]+[(v,a+b)]+ps[j+1:]
            aa=measure(cg.replay(ps)['word'],4);bb=measure(cg.replay(new)['word'],4)
            assert bb[2]<aa[2] and bb[0]['O']==aa[0]['O']-1
            ps=new
        assert cg.replay(ps)['word']==row['contracted']['word']
        if row['delta']==0:
            assert row['F']==2 and len(row['steps'])==2
        cc[str((row['delta'],len(row['steps'])))]+=1
        if row['delta']==1 and len(row['steps'])<2:
            ck=f"{row['type']}_merges{len(row['steps'])}"
            old=counterexamples.get(ck)
            if old is None or (len(row['original']['word']),row['original']['word'])<(len(old['original']['word']),old['original']['word']):counterexamples[ck]=row
        if not row['remaining_short']:
            m,passes,_,_=measure(row['contracted']['word'],4)
            pieces=[];cur=[]
            for v,l in ps:
                if cur and cg.weight(cg.words[cg.s(cur[-1],-1)],cg.words[v])>=4:
                    pieces.append(cur);cur=[]
                cur.append(v)
            pieces.append(cur)
            assert len(pieces)<=m['H']+1
            orbitsets=[{cg.q[v] for v in p} for p in pieces]
            qocc=Counter(q for s in orbitsets for q in s);z=sum(t-1 for t in qocc.values())
            bs=gs=ss=0
            for p,qs in zip(pieces,orbitsets):
                mm,*_=measure(cg.replay([(v,4) for v in p])['word'],4)
                bs+=mm['e']+mm['x'];gs+=sum(qocc[q]>1 for q in qs)
                ss+=sum(3-sum(cg.q[v]==q for v in p) for q in qs if qocc[q]==1)
            assert bs==m['e']+m['x']-z and gs<=2*z and ss<=m['D']
            decompositions+=1
    # Literal no-hidden-window w3 geometry: all short lengths change entry orbit.
    same_short=0
    for v in range(720):
        for b in range(1,6):
            same_short+=sum(w==3 and g.q[t]==g.q[v] for t,w in g.joint[g.s(v,b-1)])
    assert same_short==0
    extra_geometry=Counter();extra_witnesses=[]
    for a in range(1,5):
        for b in range(1,6-a):
            c=6-a-b;v1=g.s(0,a);v2=g.s(0,a+b)
            ps=[(0,a)]+[(g.e(v1,j),6) for j in range(1,5)]+[(v1,b)]
            ps += [(g.e(v2,j),6) for j in range(1,5)]+[(v2,c)]
            variants=[ps]+[ps[:i]+ps[i+1:] for i in [2,3,4,7,8,9]]
            for variant in variants:
                assert g.replay(variant)
                end,steps=maximal(g,variant);assert len(steps)==2 and end==[(0,6)]
                extra_geometry['A_two_merges']+=1
                extra_witnesses.append(dict(type='A',original=g.replay(variant),contracted=g.replay(end)))
    oldcontrols=json.loads((ROOT/'outputs/rr_locked_detour_contraction_codex.json').read_text())
    for row in oldcontrols['finite_blocks']['rigid_controls']:
        ps=[tuple(p) for p in row['original']['passes']]
        for i in range(1,len(ps)-1):
            if ps[i-1][1]!=6 or ps[i][1]!=6:continue
            if len({g.q[ps[j][0]] for j in [i-1,i,i+1]})!=1:continue
            variant=ps[:i]+ps[i+1:];assert g.replay(variant)
            end,steps=maximal(g,variant);assert len(steps)==2 and all(l==6 for v,l in end)
            extra_geometry['B_one_M3a_two_merges']+=1
    ledger=[]
    for r in rs:
        if r['F']==1:status='CLOSED';proof='F1 equality order contradiction';shape='0: incompatible nu order'
        elif r['delta']==0:
            status='CLOSED'
            proof='two-chain extremal seam UNSAT' if r['H'] else 'one-chain N*(1,0,15)<=106' if r['x'] else 'one-chain N*(0,0,13)<=83'
            shape='two generalized partial-arc merges' if r['type']=='A' else 'two contractions (inner-first if nested); one may use four-port generalization when x=1'
        else:
            status='OPEN_EXCEPTIONAL';proof='two-removal instances closed, residual has <2 removable orbit intervals'
            shape='at least one partial-arc merge; hard core exactly one' if r['type']=='A' else '0 or 1 in hard core; state-specific'
        ledger.append(r|dict(status=status,proof=proof,contraction_shape=shape))
    result=dict(schema='codex/round135-independent-structural-verifier/1',verified=True,
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=sha(__file__),binary_sha256=sha(sys.executable),argv=[sys.executable,*sys.argv],
                input_sha256={f:sha(ROOT/'outputs'/f) for f in ['rr_round135_controls_codex.json','rr_round135_capacity_codex.json','rr_round135_heavy_seams_codex.json']},
                run_level_nodes=nodes,extreme_counts={str(k):len(v) for k,v in ext.items()},
                independent_seam_counts=dict(counts),seam_ledger=seam_rows,n4_counts=dict(cc),
                n4_decomposition_controls=decompositions,short_w3_same_orbit_candidates=same_short,
                n6_extra_geometry=dict(extra_geometry),n6_A_witnesses=extra_witnesses,
                naive_two_contraction_counterexamples=counterexamples,ledger=ledger,
                closed_rows=sum(r['status']=='CLOSED' for r in ledger),open_rows=sum(r['status']!='CLOSED' for r in ledger),
                cell_closed=False,outer_closed=10,outer_total=55,NR6='ASSUMED',global_bound_proved=False)
    result['deterministic_digest']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    (ROOT/'outputs/rr_round135_verified_codex.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k in ['verified','run_level_nodes','extreme_counts','independent_seam_counts','n4_counts','closed_rows','open_rows','n4_decomposition_controls']}))

if __name__=='__main__':main()
