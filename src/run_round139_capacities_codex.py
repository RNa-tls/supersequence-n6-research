"""Persist new capacity runs with pinned committed bytes and runtime bytes."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round139-g2-k2-multidefect'],text=True).split()[0]
    assert head==remote,'push before long jobs'
    sources=['src/chain_capacity_115.c','src/round139_marked_return_codex.c','src/verify_round139_marked_return_codex.c', 'src/run_round139_capacities_codex.py']
    d=dict(commit=head,remote_head=remote,compiler='zig cc 0.16.0 -O3',rows=[],
           committed_blob_sha256={p:hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+p])).hexdigest() for p in sources},
           runtime_file_sha256={p:sha(ROOT/p) for p in sources})
    jobs=[(ROOT/'outputs'/exe,[str(m),'20000000000']) for m in range(3)
          for exe in ['round139_marked_return_codex.exe','verify_round139_marked_return_codex.exe']]
    jobs+=[(ROOT.parent/'supersequence-n6-research-round115-f0-audit/outputs/chain_capacity_115_codex.exe',['2','0','8','20000000000'])]
    for exe,args in jobs:
        t=time.perf_counter();argv=[str(exe),*args];print('START',argv,flush=True)
        p=subprocess.run(argv,capture_output=True,text=True)
        result=json.loads(p.stdout)
        d['rows'].append(dict(argv=argv,executable_sha256=sha(exe),exit_code=p.returncode,seconds=time.perf_counter()-t,result=result))
        (ROOT/'outputs/rr_round139_capacities_codex.json').write_text(json.dumps(d,indent=2)+'\n')
        print('END',exe.name,args,result['nodes'],'capped',result['capped'],flush=True)
        assert p.returncode==0 and not result['capped'],'UNKNOWN_CAP is not a capacity bound'
    for m in range(3):
        a,b=[d['rows'][2*m+j]['result']['rows'] for j in range(2)]
        assert [{k:v for k,v in r.items() if k!='witness'} for r in a]==b
    d['independent_root_return_equal']=True
    (ROOT/'outputs/rr_round139_capacities_codex.json').write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':main()
