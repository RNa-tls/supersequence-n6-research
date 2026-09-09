"""Complete LOCAL repeat-geodesic catalog, with two independent enumerators.

Not a global NR6 search: 719 normalized endpoint pairs versus every appended
tail over 6 symbols of lengths 1..6. The latter never calls overlap().
"""
import collections,hashlib,itertools,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def endpoint_catalog(n):
    a=''.join(map(str,range(n)));out={}
    for tup in itertools.permutations(a):
        b=''.join(tup)
        if b==a:continue
        overlap=max(k for k in range(n) if k==0 or a[-k:]==b[:k])
        word=a+b[overlap:];d=n-overlap
        occ=[(i,word[i:i+n]) for i in range(d+1) if len(set(word[i:i+n]))==n]
        gaps=[y[0]-x[0] for x,y in zip(occ,occ[1:])]
        hidden=occ[1:-1];eligible=[i for i in range(1,len(occ)-1) if gaps[i]==2]
        H=sum(max(0,g-3) for g in gaps);u=len(hidden)-len(eligible)+H
        assert u>=0 and len({v for _,v in occ})==len(occ)
        out[b]=dict(source=a,target=b,word=word,gap=d,windows=occ,actual_gaps=gaps,
                    hidden_count=len(hidden),eligible_Y_source_positions=[occ[i][0] for i in eligible],
                    eligible_Y_count=len(eligible),H_local=H,necessary_credit=u)
    return out
def tail_catalog(n):
    # Independent enumeration of ALL symbol tails, recording the first length
    # attaining each new endpoint; sorted-string membership, not set test.
    a=''.join(map(str,range(n)));out={};nodes=0
    for length in range(1,n+1):
        for tup in itertools.product(a,repeat=length):
            nodes+=1;text=a+''.join(tup);target=text[-n:]
            if ''.join(sorted(target))!=a or target==a or target in out:continue
            windows=[];last=None;gaps=[];hidden_with_free_next=0
            for pos in range(length+1):
                p=text[pos:pos+n]
                if ''.join(sorted(p))==a:
                    if last is not None:
                        g=pos-last;gaps.append(g)
                        if last!=0 and g==2:hidden_with_free_next+=1
                    windows.append((pos,p));last=pos
            H=sum(g-3 for g in gaps if g>3)
            out[target]=dict(word=text,gap=length,windows=windows,actual_gaps=gaps,
                hidden_count=len(windows)-2,eligible_Y_count=hidden_with_free_next,
                H_local=H,necessary_credit=len(windows)-2-hidden_with_free_next+H)
    return out,nodes
def main():
    start=time.perf_counter();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    rel=Path(__file__).relative_to(ROOT).as_posix();raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
    assert raw==Path(__file__).read_bytes() and sys.flags.optimize==0
    controls=[];n6=None
    for n in range(3,7):
        p=endpoint_catalog(n);q,nodes=tail_catalog(n);assert set(p)==set(q)
        for target,row in q.items():assert all(row[k]==p[target][k] for k in row)
        controls.append(dict(n=n,endpoint_pairs=len(p),tail_nodes=nodes,capped=False,completed=True,
            independent_catalog_digest=digest(q)))
        if n==6:n6=p
    zero=[r for r in n6.values() if r['hidden_count'] and not r['necessary_credit']]
    assert len(zero)==7
    expected={'103254':[2,2,2],'345021':[1,2],'451032':[2,2],'502143':[1,2,2],
              '512043':[3,2],'520143':[3,2],'521043':[3,2]}
    assert {r['target']:r['actual_gaps'] for r in zero}==expected
    histogram=collections.Counter((r['hidden_count'],r['necessary_credit']) for r in n6.values())
    result=dict(schema='round141-nr-geodesic-template-certificate-v1',source_commit=head,
        committed_source_sha256=hashlib.sha256(raw).hexdigest(),runtime_source_sha256=sha(__file__),
        argv=[sys.executable,*sys.argv],python_version=platform.python_version(),executable_sha256=sha(sys.executable),
        completed=True,capped=False,continuation_search=False,verified=True,controls=controls,
        table=list(n6.values()),histogram=[dict(hidden=h,necessary_credit=u,count=c) for (h,u),c in sorted(histogram.items())],
        zero_credit_repeating_templates=zero,zero_credit_repeating_count=len(zero),gap_shape_count=len({tuple(r['actual_gaps']) for r in zero}),
        hand_dependency='First-occurrence Hamilton projection is literal equality for a global minimum; every repetition is an internal connector window',
        proved_scope='Local catalog plus necessary summed-credit bound for globally shortest complete words; NOT global history feasibility or NR6',
        exact_global_relation='sum(h-y_eligible+H_local)<=R_rep-Y+H<=4-k-J-a-eta-x',
        NR6='UNPROVED',seconds=time.perf_counter()-start)
    result['deterministic_digest']=digest(dict(table=result['table'],histogram=result['histogram'],controls=controls))
    (ROOT/'outputs/rr_round141_nr_geodesic_templates_codex.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,targets=len(n6),zero_credit_repeating=len(zero),gap_types=result['gap_shape_count'],tail_nodes=controls[-1]['tail_nodes'])))
if __name__=='__main__':main()
