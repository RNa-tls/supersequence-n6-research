"""Fast final replay/test/hash package. Does not execute capacity or walk DFS."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    source=[str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'src').glob('*round140*')) if p.is_file()]
    source+=['tests/test_round140_g3_codex.py','research/RR_ROUND140_GENERAL_THEOREM_A_AND_G3_SPLICING_CODEX.md']
    hashes={p:sha(ROOT/p) for p in source}
    committed={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in source}
    assert hashes==committed,'commit audited source before final packaging'
    commands=[
        [sys.executable,'-m','py_compile']+[p for p in source if p.endswith('.py')],
        [sys.executable,'src/certify_round140_g3_codex.py'],
        [sys.executable,'src/verify_round140_g3_codex.py'],
        [sys.executable,'-m','unittest','discover','-s','tests','-p','test_round140_g3_codex.py','-v'],
        [sys.executable,'-m','unittest','discover','-s','tests','-p','test_round13*_codex.py','-v']]
    results=[]
    for argv in commands:
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
        results.append(dict(argv=argv,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if p.returncode:raise RuntimeError(json.dumps(results[-1]))
    tests=[int(re.search(r'Ran (\d+) tests',r['stderr']).group(1)) for r in results[-2:]]
    assert tests==[19,66]
    verified=json.loads((ROOT/'outputs/rr_round140_verified_codex.json').read_text())
    assert verified['verified'] and verified['committed_source_sha256']==verified['runtime_source_sha256']
    artifacts=[p for p in sorted((ROOT/'outputs').glob('rr_round140*')) if p.is_file() and p.name!='rr_round140_publication_codex.json']
    payload=dict(schema='codex/round140-publication/1',source_commit=head,verified=True,tests=dict(new=tests[0],retained=tests[1],total=sum(tests)),
        committed_source_sha256=committed,runtime_source_sha256=hashes,
        artifacts={str(p.relative_to(ROOT)).replace('\\','/'):dict(sha256=sha(p),bytes=p.stat().st_size) for p in artifacts},
        commands=results,NR6='ASSUMED',global_L6_ge_872='NOT_PROVED',combined_provisional_ledger='17/55',
        inherited_R139='PROVISIONAL_PENDING_EXTERNAL_AUDIT')
    (ROOT/'outputs/rr_round140_publication_codex.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(dict(verified=True,source_commit=head,tests=payload['tests'],artifacts=len(artifacts))))
if __name__=='__main__':main()
