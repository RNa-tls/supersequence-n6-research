"""Fresh production comparison AFTER independent whole-orbit DP completion."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);a=p.parse_args()
    src=ROOT/'r147/src/l6_chain_capacity_147.c';exe=ROOT/'r150/build/production147.exe'
    subprocess.run([a.compiler,'cc','-O3',str(src),'-o',str(exe)],check=True)
    independent=json.loads((ROOT/'r150/certs/blocks.json').read_text());rows=[]
    for r in independent['records']:
        cmd=[str(exe),*map(str,r['cell']),'5000000','-','0','-','0']
        run=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=30)
        v=json.loads(run.stdout)
        status='UNKNOWN_CAP' if v['capped'] else ('MATCH' if v['cc']==r['independent_capacity'] else 'DISAGREE')
        rows.append(dict(cell=r['cell'],independent_capacity=r['independent_capacity'],production_capacity=v['cc'],comparison=status,production=v,command=cmd))
        assert status!='DISAGREE',rows[-1]
    out=ROOT/'r150/certs/blocks_production_comparison.json';assert not out.exists()
    out.write_text(json.dumps(dict(rows=rows,source_sha256=sha256(src.read_bytes()).hexdigest(),exe_sha256=sha256(exe.read_bytes()).hexdigest(),
        oracle_note='production uses feas; independent DP does not. This is a comparison, not an independent proof of the pruning theorem.'),indent=2)+'\n')
    print({s:sum(r['comparison']==s for r in rows) for s in ('MATCH','DISAGREE','UNKNOWN_CAP')})

if __name__=='__main__':main()
