"""R138 privacy-only finite controls, targeted falsification, event-order CSP.
Never calls a capacity executable or enumerates complete NR6 walks.
"""
import hashlib,itertools,json,subprocess,sys,time
from collections import Counter
from pathlib import Path
from research_alpha_gap_codex import Geometry,ROOT
from verify_g2_k4_contraction_certificate_codex import measure
from verify_round137_gap_capacity_codex import audit_gap

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def classify(g,ps,raw):
    m,_,_,_=measure(raw,g.n);entries={v:i for i,(v,l) in enumerate(ps)}
    nu=[entries[g.s(v,l)] for v,l in ps]
    qs=[g.q[v] for v,l in ps]
    wt=[g.weight(g.words[g.s(v,l-1)],g.words[t]) for (v,l),(t,b) in zip(ps,ps[1:])]
    free={i for i,w in enumerate(wt) if w==2 and qs[i]!=qs[i+1]}
    asc={i for i,j in enumerate(nu) if i<j};ordinary={i+1 for i in free if i>nu[i]}
    seen={qs[0]};repeat=[]
    for i,q in enumerate(qs[1:],1):
        if q!=qs[i-1] and q in seen:repeat.append(i)
        seen.add(q)
    extra=set(repeat)-ordinary;a=len(asc-free);eta=len(extra)
    assert a+eta==len(asc)+m['e']-len(free)
    return dict(F=len(asc),G=len(ps)-len({g.h[v] for v,l in ps}),a=a,eta=eta,delta=a+eta,
                metrics=m,nu=nu,repeat=repeat,ordinary=sorted(ordinary),exceptional=sorted(extra))

def controls_and_extensions():
    path=ROOT/'outputs/rr_round137_gap_cut_codex.json';data=json.loads(path.read_text())
    gg={n:Geometry(n) for n in [4,6]};count=Counter();examples={};configs=0;local=[]
    for row in data['rows']:
        audit_gap(row);g=gg[row['n']];n=g.n
        _,words,_,_=measure(row['word'],n);ps=[(g.idx[v],l) for v,l in words]
        cert=row['certificate']
        for s in cert['ordinary_before']:
            i,j=s['i'],s['j'];v,a=ps[i];_,b=ps[j];ps=ps[:i]+[(v,a+b)]+ps[j+1:]
        i,j=cert['cut'];inside={g.q[v] for v,l in ps[i+1:j+1]}
        outer={g.q[v] for v,l in ps[:i+1]+ps[j+1:]};assert inside.isdisjoint(outer)
        # Add an actual external port of EACH inside orbit. No privacy filter
        # and no delta/resource filter is used before literal replay.
        for v in range(len(g.words)):
            if g.q[v] not in inside:continue
            for side in ['before','after']:
                configs+=1;seq=([(v,n)]+ps) if side=='before' else (ps+[(v,n)])
                rep=g.replay(seq)
                if rep is None:count[f'n{n}/literal_rejected']+=1;continue
                d=classify(g,seq,rep['word']);tag=f'n{n}/{cert["kind"]}/{side}/delta{d["delta"]}/x{d["metrics"]["x"]}'
                count[tag]+=1
                rec=dict(n=n,source_word_sha256=digest(row['word']),word=rep['word'],side=side,
                         inserted_port=v,shared_orbit=g.q[v],mechanism=cert['kind'],classification=d)
                local.append(rec)
                key=(len(rep['word']),rep['word'])
                if tag not in examples or key<(len(examples[tag]['word']),examples[tag]['word']):examples[tag]=rec
                assert d['delta']>=2 or d['metrics']['x']>0 or d['metrics']['H']>0
    # Independent symbolic tiling / exterior endpoint checks; not gap replay.
    identities=0;contexts=0;g=gg[6]
    for v in range(720):
        for a in range(1,6):
            c=g.s(v,a);left={g.s(v,k) for k in range(a)};right={g.s(c,k) for k in range(6-a)}
            assert left.isdisjoint(right) and left|right=={g.s(v,k) for k in range(6)}
            assert g.s(c,5-a)==g.s(v,5);contexts+=1
            y=g.s(v,a-1)
            for tail,offset in [((1,2,0),(2,3,4,0,1,5)),((2,0,1),(2,3,4,1,5,0)),((2,1,0),(2,3,4,1,0,5))]:
                w=g.words[y];t=w[3:]+tuple(w[k] for k in tail);inv={z:k for k,z in enumerate(g.words[c])}
                assert tuple(inv[z] for z in t)==offset
                assert g.q[g.idx[t]]!=g.q[v]
                if t[-1]==g.words[v][-1]:assert a==5 and tail==(2,0,1)
                identities+=1
    return dict(input_sha256=sha(path),preserved_gap_controls=len(data['rows']),positional_identities=identities,
                complementary_context_checks=contexts,attempted_one_port_contexts=configs,histogram=dict(count),
                legal_shared_orbit_contexts=len(local),scope='specified finite external-one-full-pass domain; not universal enumeration',
                capped=False,node_cap=None,rows=local,minimal_examples=examples)

def run_words(maxlen):
    def rec(w):
        yield tuple(w)
        if len(w)==maxlen:return
        for q in range(max(w)+2):
            if q!=w[-1]:yield from rec(w+[q])
    yield from rec([0])

def event_csp():
    # Restricted growth strings enumerate ALL orbit equality patterns on up
    # to seven RUNS, not paths/words. This over-approximates literal geometry.
    nodes=0;hist=Counter();examples={};spectrum=Counter()
    for word in run_words(7):
        for left in range(1,len(word)):
            for stop in range(left+1,len(word)+1):
                L=set(word[:left]);I=set(word[left:stop]);R=set(word[stop:]);shared=I&(L|R)
                opener=word[left-1]
                for width in [1,2]:
                    for bb in itertools.combinations(sorted(L),width):
                        if opener not in bb:continue
                        B=set(bb);seen=set(L);future=[]
                        for k in range(left,len(word)):
                            q=word[k]
                            if q in seen:future.append(k)
                            seen.add(q)
                        ordinary={k for k in future if k>=stop and word[k] in B}
                        modes=[('M',None)]
                        T=word[left]
                        if T not in L:
                            internal=[k for k in future if k<stop and word[k]==T]
                            if internal:modes.append(('R',internal[0]))
                        for mode,exception in modes:
                            nodes+=1
                            unsupported=set(future)-ordinary-({exception} if exception is not None else set())
                            # Explicit injective charge: first inside occurrence
                            # if also on left, otherwise first right occurrence.
                            charge={q:(next(k for k in range(left,stop) if word[k]==q) if q in L else
                                       next(k for k in range(stop,len(word)) if word[k]==q)) for q in shared}
                            assert set(charge.values())<=unsupported
                            assert len(set(charge.values()))==len(shared)
                            extra=len(unsupported);assert extra>=len(shared)
                            hist[f'{mode}/shared{len(shared)}/extra{extra}']+=1
                            spectrum[f'{mode}/B{width}']+=1
                            if shared:
                                tag=f'{mode}/B{width}/s{len(shared)}'
                                rec=dict(run_orbits=word,inside=[left,stop],boundary_targets=bb,mode=mode,
                                         root_return_event=exception,ordinary_repeat_events=sorted(ordinary),
                                         unsupported_repeat_events=sorted(unsupported),shared_orbits=sorted(shared),
                                         injection=charge,delta_lower_bound=1+extra)
                                if tag not in examples:examples[tag]=rec
    return dict(domain='ALL restricted-growth run equality patterns of length <=7; both one/two boundary-target models',
                nodes=nodes,node_cap=None,capped=False,histogram=dict(hist),model_counts=dict(spectrum),minimal_shared_models=examples,
                violations=0,proof_status='finite check of the symbolic injection, not universal reachability proof')

def metadata_correction():
    commit='ec8a5f1aaa2d5b42dc885dca86420877287555aa';p='src/chain_capacity_115.c'
    oldpath=ROOT/'outputs/rr_round137_root_return_capacity_codex.json';old=json.loads(oldpath.read_text())
    raw=(ROOT/p).read_bytes();blob=subprocess.check_output(['git','show',commit+':'+p])
    recorded=old['source_sha256'][p]
    assert hashlib.sha256(raw).hexdigest()==recorded
    assert raw.replace(b'\r\n',b'\n')==blob
    return dict(schema='codex/round138-source-provenance-correction/1',historical_certificate=str(oldpath.relative_to(ROOT)),
                historical_certificate_sha256=sha(oldpath),file=p,recorded_ambiguous_source_sha256=recorded,
                correct_committed_blob_sha256=hashlib.sha256(blob).hexdigest(),commit=commit,
                historical_worktree_sha256=hashlib.sha256(raw).hexdigest(),CRLF_lines=raw.count(b'\r\n'),
                committed_CRLF_lines=blob.count(b'\r\n'),LF_normalized_equal=True,
                correction='Old source_sha256 was the compiled WORKTREE byte hash, not the remotely retrievable committed blob hash. Explicitly distinguish both; content differs only by CRLF/LF.',
                old_certificate_modified=False,capacity_recomputed=False)

def main():
    t=time.perf_counter();commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round138-universal-privacy'],text=True).split()[0]
    assert remote==commit,'push before finite computation'
    sources=['src/research_round138_privacy_codex.py','src/research_alpha_gap_codex.py','src/verify_round137_gap_capacity_codex.py','src/verify_g2_k4_contraction_certificate_codex.py']
    out=dict(schema='codex/round138-privacy-audit/1',source_commit=commit,remote_commit=remote,
             argv=[sys.executable,*sys.argv],source_sha256={p:sha(ROOT/p) for p in sources},binary_sha256=sha(sys.executable),
             controls=controls_and_extensions(),event_csp=event_csp(),metadata_correction=metadata_correction(),seconds=time.perf_counter()-t)
    out['mathematical_digest']=digest([out['controls'],out['event_csp'],out['metadata_correction']])
    (ROOT/'outputs/rr_round138_privacy_controls_codex.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'contexts':out['controls']['attempted_one_port_contexts'],'legal_sharing':out['controls']['legal_shared_orbit_contexts'],
                      'csp_nodes':out['event_csp']['nodes'],'violations':out['event_csp']['violations'],'seconds':out['seconds']}))
if __name__=='__main__':main()
