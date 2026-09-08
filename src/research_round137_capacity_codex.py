"""Run the committed LOCAL root-return model, preserve complete provenance."""
import hashlib,json,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    exe=ROOT/'outputs/round137_root_return_capacity_codex.exe'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round137-mr-hard-core'],text=True).strip()
    assert remote.split()[0]==commit,'commit/push before computation'
    argv=[str(exe),'20000000000'];t=time.perf_counter()
    proc=subprocess.run(argv,capture_output=True,text=True);r=json.loads(proc.stdout)
    C0=[20,20,33,33,46,46,49,58,62,66,70,74,83,83]
    result=dict(schema='codex/round137-local-capacity-run/1',source_commit=commit,remote=remote,
        argv=argv,exit_code=proc.returncode,seconds=time.perf_counter()-t,stderr=proc.stderr,
        source_sha256={p:sha(ROOT/p) for p in ['src/round137_root_return_capacity_codex.c','src/chain_capacity_115.c','src/research_round137_capacity_codex.py']},
        binary_sha256=sha(exe),compiler='ziglang 0.16.0 cc -O3',result=r,
        ordinary_capacity=C0,ordinary_convolution=[C0[d]+C0[13-d] for d in range(14)],
        root_return_convolution=[dict(deficit=v['deficit'],bound=C0[13-v['deficit']]+v['passes']) for v in r['rows'] if v['passes']>=0])
    result['mathematical_digest']=digest(r)
    out=ROOT/'outputs/rr_round137_root_return_capacity_codex.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['seconds','exit_code','root_return_convolution']}));print('nodes',r['nodes'],'capped',r['capped'])
if __name__=='__main__':main()
