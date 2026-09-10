"""Publication audit only; no proof search. Preserve exact local/blob hashes."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    sources=sorted(ROOT.glob('src/*round142*.py'));tests=[]
    subprocess.run([sys.executable,'-m','py_compile',*[str(p) for p in sources]],cwd=ROOT,check=True)
    for pattern in ['test_round142*.py','test_round141*.py','test_round140*.py',
                    'test_round139*.py','test_round138*.py','test_round137*.py','test_round136*.py','test_round135*.py']:
        argv=[sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'];t=time.perf_counter()
        r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);log=r.stdout+r.stderr
        assert r.returncode==0,log
        count=int(re.search(r'Ran (\d+) tests?',log).group(1))
        tests.append(dict(pattern=pattern,count=count,exit_code=r.returncode,argv=argv,seconds=time.perf_counter()-t,log=log))
        print(json.dumps(dict(pattern=pattern,tests=count,passed=True)),flush=True)
    names=sorted(p for p in ROOT.glob('outputs/rr_round142*.json') if 'publication' not in p.name)
    outputs={p.name:json.loads(p.read_text()) for p in names}
    assert outputs['rr_round142_selected_outer_verified_codex.json']['verified']
    assert outputs['rr_round142_shadow_budget_verified_codex.json']['verified']
    assert outputs['rr_round142_light_clean_all_g_verified_codex.json']['all_light_clean_cells_closed']
    assert outputs['rr_round142_low_slack_verified_codex.json']['L6_lower_bound']==869
    assert outputs['rr_round142_route_a_codex.json']['NR_UNIVERSAL_6']=='UNPROVED'
    blobs={}
    for p in sources:
        rel=p.relative_to(ROOT).as_posix();raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==p.read_bytes(),'Uncommitted source '+rel
        blobs[rel]=hashlib.sha256(raw).hexdigest()
    files=names+sources+sorted(ROOT.glob('research/RR_ROUND142*.md'))+sorted(ROOT.glob('tests/test_round142*.py'))
    result=dict(schema='round142-publication-v1',source_commit=head,source_blob_sha256=blobs,
        files={p.relative_to(ROOT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},
        tests=tests,total_tests=sum(r['count'] for r in tests),verified=True,
        route_A=dict(NR_UNIVERSAL_6='UNPROVED',boundary_fixed_domination='REFUTED',local_catalog='COMPLETE'),
        route_B=dict(selected_master='PROVED',representative_R_bound=20,light_clean_outer='CLOSED',
            unconditional_lower_bound=869,upper_bound=872,remaining_lengths=[869,870,871]),
        NR6_prime_normalization='UNPROVED',global_L6_872='NOT_PROVED',
        searches='NO_GLOBAL_COVER_SEARCH_OR_CONTINUATION',final_status='ASTRA_REPEAT_DOMAIN_MAJOR_REDUCTION')
    (ROOT/'outputs/rr_round142_publication_codex.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(tests=result['total_tests'],files=len(files),status=result['final_status'])))
if __name__=='__main__':main()
