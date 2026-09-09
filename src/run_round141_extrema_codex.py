"""Committed finite extrema jobs; retained source and runtime hashes separate."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZIG=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0]
    assert remote==head,'push first'
    files=['src/run_round141_extrema_codex.py','src/round141_extrema_codex.c','src/chain_capacity_115.c']
    committed={p:hashlib.sha256(subprocess.check_output(['git','show',head+':'+p])).hexdigest() for p in files}
    runtime={p:sha(ROOT/p) for p in files}
    newline_only=[]
    for p in files:
        local=(ROOT/p).read_bytes();blob=subprocess.check_output(['git','show',head+':'+p])
        assert local.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
        if local!=blob:newline_only.append(p)
    binary=ROOT/'outputs/round141_extrema_codex.exe'
    build=[str(ZIG),'cc','-O3','src/round141_extrema_codex.c','-o',str(binary)]
    subprocess.run(build,cwd=ROOT,check=True,capture_output=True)
    out=dict(schema='codex/round141-extrema/1',source_commit=head,build=build,
        compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
        executable_sha256=sha(binary),committed_source_sha256=committed,runtime_source_sha256=runtime,
        newline_only_runtime_differences=newline_only,rows=[])
    for T,D in [(46,4),(58,7),(62,8),(96,14)]:
        argv=[str(binary),str(T),str(D),'20000000000'];start=time.perf_counter()
        r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
        data=json.loads(r.stdout);data.update(argv=argv,exit_code=r.returncode,seconds=time.perf_counter()-start)
        data['deterministic_digest']=hashlib.sha256(json.dumps({k:data[k] for k in ['target','deficit','nodes','count','capped','paths']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        out['rows'].append(data)
        (ROOT/'outputs/rr_round141_extrema_codex.json').write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({k:data[k] for k in ['target','deficit','nodes','count','capped','seconds']}),flush=True)
        if r.returncode or data['capped']:raise RuntimeError('UNKNOWN_CAP or failed computation')
if __name__=='__main__':main()
