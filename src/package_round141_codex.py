"""Final separate-track test/hash package; no capacity or continuation search."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    start=time.perf_counter();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    sources=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'src').glob('*round141*')) if p.is_file()]
    sources+=['tests/test_round141_separate_tracks.py',
        'research/RR_ROUND141_ALL_G_OUTER_CLOSURE_CODEX.md',
        'research/RR_ROUND141_NR6_REPETITION_REDUCTION_CODEX.md']
    committed={};runtime={}
    for name in sources:
        raw=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)
        committed[name]=hashlib.sha256(raw).hexdigest();runtime[name]=sha(ROOT/name)
        assert committed[name]==runtime[name] and b'\r\n' not in raw,'new canonical sources must be committed LF'
    commands=[
        [sys.executable,'-m','py_compile',*[p for p in sources if p.endswith('.py')]],
        [sys.executable,'-m','unittest','discover','-s','tests','-p','test_round141*.py','-v'],
        [sys.executable,'-m','unittest','discover','-s','tests','-p','test_round140*.py','-v'],
        [sys.executable,'-m','unittest','discover','-s','tests','-p','test_round13*_codex.py','-v']]
    results=[];testcounts=[]
    for argv in commands:
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
        result=dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr);results.append(result)
        assert p.returncode==0,json.dumps(result)
        if 'unittest' in argv:
            assert 'skipped=' not in p.stderr
            testcounts.append(int(re.search(r'Ran (\d+) tests',p.stderr).group(1)))
    assert testcounts==[25,19,66]
    names=['rr_round141_extrema_codex.json','rr_round141_completion_cover_codex.json',
        'rr_round141_outer_codex.json','rr_round141_outer_verified_codex.json',
        'rr_round141_j_topology_verified_codex.json','rr_round141_nr6_foundation_codex.json',
        'rr_round141_repeat_credit_codex.json','rr_round141_nr6_verified_codex.json',
        'rr_round141_nr_geodesic_templates_codex.json']
    data={f:json.loads((ROOT/'outputs'/f).read_text()) for f in names}
    outer=data['rr_round141_outer_verified_codex.json'];assert outer['verified'] and outer['ledger']['closed']==55
    assert len(outer['ledger']['new_cells'])==38 and len(outer['ledger']['rows'])==160
    for artifact in data.values():
        if 'input_sha256' in artifact:
            for f,h in artifact['input_sha256'].items():
                if (ROOT/'outputs'/f).is_file():assert sha(ROOT/'outputs'/f)==h
    for f in ['rr_round141_j_topology_verified_codex.json','rr_round141_nr6_verified_codex.json','rr_round141_nr_geodesic_templates_codex.json']:
        assert data[f]['verified']
    assert all(data[f]['NR6']=='UNPROVED' for f in ['rr_round141_nr6_foundation_codex.json','rr_round141_repeat_credit_codex.json','rr_round141_nr6_verified_codex.json','rr_round141_nr_geodesic_templates_codex.json'])
    payload=dict(schema='codex/round141-separate-publication/1',source_commit=head,
        committed_source_sha256=committed,runtime_source_sha256=runtime,canonical_new_sources='LF',
        artifacts={'outputs/'+f:dict(sha256=sha(ROOT/'outputs'/f),bytes=(ROOT/'outputs'/f).stat().st_size) for f in names},
        tests=dict(round141=testcounts[0],round140=testcounts[1],retained_round13x=testcounts[2],total=sum(testcounts)),
        commands=results,verified=True,seconds=time.perf_counter()-start,
        outer=dict(accepted_baseline=17,new_closed=38,total_closed=55,total=55,NR6='ASSUMED',status='ASTRA_OUTER_55_OF_55'),
        nr6=dict(NR6='UNPROVED',repeat_bound_at_871=27,unpaid_repeat_budget='4-k',
            fixed_point_reduction='PROVED_BY_HAND',zero_credit_repeating_templates=7,gap_shapes=5,
            positive_local_credit_budget='4-k-J-a-eta-x',
            missing_lemma='Bounded repetition plateau escape for first-occurrence-geodesic fixed points',
            status='ASTRA_NR6_HARD_CORE'),unrestricted_L6_ge872='NOT_PROVED')
    (ROOT/'outputs/rr_round141_publication_codex.json').write_text(json.dumps(payload,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,tests=payload['tests'],source_commit=head,outer=payload['outer']['status'],nr6=payload['nr6']['status'])))
if __name__=='__main__':main()
