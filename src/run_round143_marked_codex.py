"""Freeze/hash/compile and compare independent necessary marked-chain models."""
import argparse,hashlib,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZIG=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cap',type=int,default=0);ap.add_argument('--cells',default='0:0,0:1,0:2,0:3,0:4,0:5,0:6,0:7,0:8,0:9,0:10,1:0,1:1,1:2,1:3,1:4,1:5,2:0');ap.add_argument('--output',default='outputs/rr_round143_marked_capacities_codex.json');args=ap.parse_args()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert remote==head,'Push frozen source before capacity run'
    sources=['src/round143_marked_runs_codex.c','src/round143_marked_ports_independent.c',Path(__file__).relative_to(ROOT).as_posix()]
    provenance=[];bins=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==(ROOT/rel).read_bytes(),'Uncommitted source '+rel
        item=dict(path=rel,committed_sha256=hashlib.sha256(raw).hexdigest(),runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/rel.replace('.c','.exe');argv=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            subprocess.run(argv,check=True,cwd=ROOT);bins.append(exe);item.update(binary_sha256=sha(exe),compile_argv=argv)
        provenance.append(item)
    result=dict(schema='round143-marked-capacities-paired-v1',source_commit=head,source_provenance=provenance,
      compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),python=platform.python_version(),argv=sys.argv,
      scope='NECESSARY_HEX_SIMPLE_MARKED_CAPACITY_NOT_COVER_SEARCH',rows=[])
    for b,D in [tuple(map(int,x.split(':'))) for x in args.cells.split(',')]:
        runs=[]
        for exe in bins:
            argv=[str(exe),str(b),str(D),str(args.cap),'AB'];t=time.perf_counter();pr=subprocess.run(argv,capture_output=True,text=True,check=True)
            rr=json.loads(pr.stdout);rr.update(argv=argv,seconds=time.perf_counter()-t,stdout_sha256=hashlib.sha256(pr.stdout.encode()).hexdigest());runs.append(rr)
        complete=all(not r['capped'] for r in runs)
        if complete:
            assert runs[0]['max_passes']==runs[1]['max_passes'],runs
            assert runs[0]['endpoint_max_passes']==runs[1]['endpoint_max_passes'],runs
            assert runs[0]['rich_endpoint_max_passes']==runs[1]['rich_endpoint_max_passes'],runs
        row=dict(b=b,D=D,producer=runs[0],independent=runs[1],complete=complete,status='VERIFIED_CAPACITY' if complete else 'UNKNOWN_CAP')
        result['rows'].append(row)
        (ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n',newline='\n')
        print(json.dumps(dict(b=b,D=D,passes=[r['max_passes'] for r in runs],nodes=[r['nodes'] for r in runs],status=row['status'])),flush=True)
if __name__=='__main__':main()
