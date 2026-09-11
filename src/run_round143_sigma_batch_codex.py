"""Paired bounded/complete SIGMA capacities with immutable hashed binaries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
ZIG=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cells',required=True,help='A:b:D comma-separated')
    ap.add_argument('--cap',type=int,default=0)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    dest=ROOT/a.output
    assert not dest.exists(),'Use a new output; historical capped files are immutable'
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
    assert head==remote,'Freeze/push before capacity computation'
    sources=['src/round143_marked_runs_codex.c','src/round143_marked_ports_independent.c',
             Path(__file__).relative_to(ROOT).as_posix()]
    provenance=[];binaries=[]
    for rel in sources:
        raw=subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
        assert raw==(ROOT/rel).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        record=dict(path=rel,committed_lf_sha256=digest,runtime_sha256=sha(ROOT/rel))
        if rel.endswith('.c'):
            exe=ROOT/'outputs'/('round143_'+Path(rel).stem+'_'+digest[:12]+'.exe')
            argv=[str(ZIG),'cc','-O3','-std=c11',str(ROOT/rel),'-o',str(exe)]
            # Names cannot collide with the already running original driver.
            if not exe.exists():
                subprocess.run(argv,cwd=ROOT,check=True)
            binaries.append(exe)
            record.update(compile_argv=argv,binary_sha256=sha(exe))
        provenance.append(record)
    out=dict(schema='round143-sigma-capacities-paired-v2',source_commit=head,
             source_provenance=provenance,argv=sys.argv,
             compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
             scope='COUPLED_SIGMA_NECESSARY_PATH: exactly A same-hex sigma edges; every non-A target hex new',rows=[])
    for A,b,D in [tuple(map(int,x.split(':'))) for x in a.cells.split(',')]:
        assert A>=0 and b>=0 and D>=0
        runs=[]
        for exe in binaries:
            argv=[str(exe),str(b),str(D),str(a.cap),'SIGMA:'+str(A)]
            started=time.perf_counter()
            pr=subprocess.run(argv,cwd=ROOT,check=True,capture_output=True,text=True)
            r=json.loads(pr.stdout)
            r.update(argv=argv,seconds=time.perf_counter()-started,
                     stdout_sha256=hashlib.sha256(pr.stdout.encode()).hexdigest())
            assert r['A_exact']==A
            runs.append(r)
        complete=all(r['completed'] and not r['capped'] for r in runs)
        if complete:
            for field in ('max_passes','accepted_prefixes','endpoint_max_passes','rich_endpoint_max_passes'):
                assert runs[0][field]==runs[1][field],(A,b,D,field)
        out['rows'].append(dict(A=A,b=b,D=D,producer=runs[0],independent=runs[1],complete=complete,
                               status='VERIFIED_CAPACITY' if complete else 'UNKNOWN_CAP'))
        temporary=dest.with_suffix('.tmp')
        temporary.write_text(json.dumps(out,indent=2)+'\n',newline='\n')
        os.replace(temporary,dest)
        print(json.dumps(dict(A=A,b=b,D=D,complete=complete,
                              maxima=[r['max_passes'] for r in runs],nodes=[r['nodes'] for r in runs])),flush=True)


if __name__=='__main__':
    main()
