"""Only the two additional small-deficit capacities needed by the k1 corollary."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round139-g2-k2-multidefect'],text=True).split()[0]==commit
    data=dict(commit=commit,rows=[],compiler='zig cc 0.16.0 -O3',sources={p:hashlib.sha256(subprocess.check_output(['git','show',commit+':'+p])).hexdigest() for p in
              ['src/chain_capacity_115.c','src/verify_round139_b2_capacity_codex.c','src/verify_round139_marked_return_codex.c','src/run_round139_master_capacity_codex.py']})
    for b in [0,1,2,3]:
        for independent in [False,True]:
            exe=(ROOT/'outputs/verify_round139_b2_capacity_codex.exe') if independent else ROOT.parent/'supersequence-n6-research-round115-f0-audit/outputs/chain_capacity_115_codex.exe'
            args=[str(b),'20000000000','3'] if independent else [str(b),'0','3','20000000000']
            t=time.perf_counter();p=subprocess.run([str(exe),*args],capture_output=True,text=True);r=json.loads(p.stdout)
            data['rows'].append(dict(independent=independent,argv=[str(exe),*args],executable_sha256=sha(exe),result=r,seconds=time.perf_counter()-t))
            (ROOT/'outputs/rr_round139_master_capacities_codex.json').write_text(json.dumps(data,indent=2)+'\n')
            print(b,independent,r['passes'],r['nodes'],r['capped'],flush=True)
            assert p.returncode==0 and not r['capped']
        assert data['rows'][-1]['result']['passes']==data['rows'][-2]['result']['passes']
    data['verified']=True
    (ROOT/'outputs/rr_round139_master_capacities_codex.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
