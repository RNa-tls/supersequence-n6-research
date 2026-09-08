"""Round137 finite literal-tail and inverse-expansion audit. No NR6 DFS."""
import hashlib,itertools,json,subprocess,sys
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry,ROOT
from research_round136_defect_codex import dissect,digest,sha,seven_rows
from research_round135_contraction_codex import maximal
from verify_g2_k4_contraction_certificate_codex import measure

def tailcode(source,target):
    assert source[3:]==target[:-3]
    return ''.join(str(source.index(z)) for z in target[-3:])

def seams(word,n):
    m,ps,_,paid=measure(word,n)
    return [(tuple(a),tuple(b),tailcode(a,b)) for a,b,w in paid if w==3]

def local_geometry():
    g=Geometry(6);hist=Counter();offsets={};total=0
    for v in range(720):
        for a in range(1,6):
            ep=g.s(v,a-1);c=g.s(v,a)
            inv={z:i for i,z in enumerate(g.words[c])}
            for t,w in g.joint[ep]:
                if w!=3:continue
                code=tailcode(g.words[ep],g.words[t]);rel=tuple(inv[z] for z in g.words[t])
                assert rel=={'120':(2,3,4,0,1,5),'201':(2,3,4,1,5,0),'210':(2,3,4,1,0,5)}[code]
                assert g.q[t]!=g.q[v]
                assert (g.q[t]==g.q[c])==(code=='120')
                hist[code]+=1;total+=1
                rep=min(g.E(rel,j) for j in range(5));phase=next(j for j in range(5) if g.E(rep,j)==rel)
                offsets[code]=dict(relative_permutation=rel,normalized_target_orbit=rep,normalized_target_phase=phase)
    internal=Counter()
    for v in range(720):
        for t,w in g.joint[g.s(v,-1)]:
            if w==3 and g.q[t]==g.q[v]:internal[tailcode(g.words[g.s(v,-1)],g.words[t])]+=1
    assert dict(internal)=={'120':720}
    return dict(pair_count=3600,candidate_count=total,tail_counts=dict(hist),offsets=offsets,
                fullpass_intra_orbit= dict(internal),node_cap=None,capped=False)

def local_expansions():
    g=Geometry(6);M=json.loads((ROOT/'outputs/rr_round136_defects_codex.json').read_text())['local_n6']['macros']
    R=json.loads((ROOT/'outputs/rr_round136_repeat_macros_codex.json').read_text())['result']['macros']
    base={};base_hist=Counter()
    for mechanism,rows in [('M',M),('R',R)]:
        for r in rows:
            if r['merge_count']:continue
            ps=[tuple(p) for p in r['original']['passes']]
            for extra in [False,True]:
                path=ps+([(g.e(ps[0][0]),6)] if extra else [])
                rep=g.replay(path)
                if rep:base[rep['word']]=(mechanism,path);base_hist[f'{mechanism}/free_closer={extra}']+=1
    counts=Counter();byword={};input_configs=0
    for raw,(kind,ps) in base.items():
        for i,(v,l) in enumerate(ps):
            for a in range(1,l):
                input_configs+=1;c=g.s(v,a)
                block=[(v,a)]+[(g.e(c,j),6) for j in range(1,5)]+[(c,l-a)]
                path=ps[:i]+block+ps[i+1:];rep=g.replay(path)
                if not rep:counts['literal_rejected']+=1;continue
                counts['legal_raw']+=1
                d=dissect(rep['word'],6)
                hh=Counter(g.h[t] for t,b in path)
                assert sum(n-1 for n in hh.values())==2 and d['F']==2 and d['delta']==1
                assert d['metrics']['x']==d['metrics']['H']==0
                d['type']='A' if max(hh.values())==3 else 'B'
                asc=[j for j,k in enumerate(d['nu']) if j<k]
                d['ascents']=asc;targets=[g.q[path[d['nu'][j]][0]] for j in asc]
                if kind=='M':event=d['missing_ascents'][0]
                else:event=d['extra_repeat'][0]['incoming_pass']
                src=g.words[g.s(path[event][0],path[event][1]-1)];target=g.words[path[event+1][0]]
                code=tailcode(src,target);assert code in ['201','210']
                if kind=='R':assert d['extra_repeat'][0]['target_orbit'] in targets and len(set(targets))==2
                d['mechanism']=kind;d['event_pass']=event;d['event_tail']=code
                d['event_source_pass_length']=path[event][1]
                d['target_index']=targets.index(g.q[path[event+1][0]]) if kind=='R' else None
                # Safe future-registration relaxation, conditional on the row's
                # fresh-opening rules; all opener orbits/current orbit exempted.
                allow={g.q[path[j][0]] for j in asc}|{g.q[path[-1][0]]}
                phases=Counter(g.q[t] for t,b in path)
                d['phase_slots']={str(q):dict(used=k,deficit=5-k,exempt_from_sealed_bound=q in allow) for q,k in phases.items()}
                d['sealed_deficit_lower_bound']=sum(5-k for q,k in phases.items() if q not in allow)
                assert d['maximal_merges']==1
                before=[s for s in seams(d['word'],6) if s[2]!='120']
                after=[s for s in seams(d['contracted']['word'],6) if s[2]!='120']
                assert before==after
                d['inverse_expansion_parent']=dict(word=raw,pass_index=i,split=a)
                byword.setdefault(d['word'],d)
    rows=list(byword.values());counts['unique_left_S6_literal_classes']=len(rows)
    histogram=Counter();near=Counter();representatives={}
    for d in rows:
        key=f"{d['type']}/e{d['metrics']['e']}/{d['mechanism']}"
        histogram[key]+=1
        if d['sealed_deficit_lower_bound']<=13:near[key]+=1
        if key not in representatives or (len(d['word']),d['word'])<(len(representatives[key]['word']),representatives[key]['word']):representatives[key]=d
    return dict(scope='finite inverse expansions of preserved local one-fragment M/R macros, with optional free closer; NOT complete NR6 cell enumeration',
        base_count=len(base),base_histogram=dict(base_hist),nodes=input_configs,node_cap=None,capped=False,
        counts=dict(counts),histogram=dict(histogram),sealed_bound_at_most13=dict(near),
        representatives=representatives,rows=rows)

def controls():
    data=json.loads((ROOT/'outputs/rr_round136_defects_codex.json').read_text())['n4']['rows']
    hist=Counter()
    for row in data:
        a=[s for s in seams(row['word'],4) if s[2]!='120']
        b=[s for s in seams(row['contracted']['word'],4) if s[2]!='120']
        assert a==b
        hist[row['residual_model']]+=1
    return dict(scope='read-only adversarial check of 155 retained controls, not re-exclusion of solved rows',
                controls=len(data),histogram=dict(hist),protected_seam_mismatches=0)

if __name__=='__main__':
    data=dict(schema='codex/round137-protected-seam/1',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        remote_branch='codex/round137-mr-hard-core',source_sha256=sha(__file__),binary_sha256=sha(sys.executable),argv=[sys.executable,*sys.argv],
        seven_rows=seven_rows(),geometry=local_geometry(),controls=controls(),local=local_expansions(),
        rows_closed=0,rows_remaining=7,outer_ledger='10/55',NR6='ASSUMED')
    data['mathematical_digest']=digest({k:v for k,v in data.items() if k in ['seven_rows','geometry','controls','local']})
    (ROOT/'outputs/rr_round137_protected_seam_codex.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(geometry=data['geometry'],controls=data['controls'],local={k:v for k,v in data['local'].items() if k not in ['rows','representatives']})))
