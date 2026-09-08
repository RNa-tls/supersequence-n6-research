"""Package existing Round139 certificates and fast regressions; no research search."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    master=json.loads((ROOT/'outputs/rr_round139_master_verified_codex.json').read_text())
    assert master['verified'] and master['outer_after']=='13/55'
    for f,v in master['inputs'].items():assert sha(ROOT/'outputs'/f)==v
    mathematical={}
    for f in ['rr_round139_capacities_codex.json','rr_round139_master_capacities_codex.json','rr_round139_independent_codex.json']:
        d=json.loads((ROOT/'outputs'/f).read_text());rows=d.get('rows',d.get('independent_b2'))
        mathematical[f]=[dict(argv=r['argv'],result_sha256=digest(r['result']),nodes=r['result']['nodes'],
            capped=r['result']['capped'],executable_sha256=r['executable_sha256']) for r in rows]
    argv=[sys.executable,'-m','unittest','discover','-s','tests','-p','test_round13[5-9]*.py','-v']
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
    assert p.returncode==0 and 'Ran 66 tests' in p.stderr and 'skipped' not in p.stderr
    files=sorted(list((ROOT/'outputs').glob('rr_round139*.json'))+
        list((ROOT/'src').glob('*round139*.*'))+list((ROOT/'tests').glob('test_round139*.py'))+
        list((ROOT/'research').glob('RR_ROUND139*.md')))
    files=[p for p in files if p.name!='rr_round139_package_codex.json' and p.is_file()]
    data=dict(schema='codex/round139-package/1',commit=head,branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
        source_blob_sha256=hashlib.sha256(subprocess.check_output(['git','show',head+':src/package_round139_certificates_codex.py'])).hexdigest(),
        files={str(p.relative_to(ROOT)).replace('\\','/'):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files},
        deterministic_capacity_results=mathematical,
        tests=dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,count=66,passed=66,skipped=0),
        master_input_sha256=sha(ROOT/'outputs/rr_round139_master_verified_codex.json'),
        status='ASTRA_G2_K2_AND_K1_CLOSED',conditional_outer_ledger='13/55',NR6='ASSUMED',L6_ge_872='NOT_PROVED')
    (ROOT/'outputs/rr_round139_package_codex.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(files=len(files),tests=66,status=data['status'])))
if __name__=='__main__':main()
