"""Pinned finite NR4 controls and paired ordinary-chain capacity certificates."""
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/round140-g3-general-splicing'],text=True).split()[0]==head
    zig=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe')
    builds=[('src/round140_nr4_controls_codex.c','outputs/round140_nr4_controls_codex.exe'),
            ('src/chain_capacity_115.c','outputs/round140_port_capacity_codex.exe'),
            ('src/verify_round139_b2_capacity_codex.c','outputs/round140_run_capacity_codex.exe')]
    buildlog=[]
    for source,target in builds:
        argv=[str(zig),'cc','-O3',source,'-o',target];p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True);assert p.returncode==0,p.stderr
        buildlog.append(dict(argv=argv,executable_sha256=sha(ROOT/target)))
    exe=ROOT/builds[0][1];argv=[str(exe),'2000000000'];t=time.perf_counter();p=subprocess.run(argv,capture_output=True,text=True)
    lines=p.stdout.splitlines();summary=json.loads(lines[-1]);assert p.returncode==0 and not summary['capped']
    words=lines[:-1];assert len(words)==summary['walks']==len(set(words))
    data=dict(commit=head,summary=summary,words=words,argv=argv,seconds=time.perf_counter()-t,build=buildlog[0])
    (ROOT/'outputs/rr_round140_nr4_codex.json').write_text(json.dumps(data,indent=2)+'\n');print('NR4',summary,flush=True)
    rows=[]
    for b,d in [(0,7),(1,7),(2,7),(0,2),(1,2),(2,2),(3,2)]:
        for rep in ['port','run']:
            exe=ROOT/f'outputs/round140_{rep}_capacity_codex.exe'
            args=[str(b),'0',str(d),'20000000000'] if rep=='port' else [str(b),'20000000000',str(d)]
            argv=[str(exe),*args];t=time.perf_counter();p=subprocess.run(argv,capture_output=True,text=True);z=json.loads(p.stdout)
            assert p.returncode==0 and not z['capped'];rows.append(dict(representation=rep,argv=argv,seconds=time.perf_counter()-t,
                executable_sha256=sha(exe),exit_code=p.returncode,result=z,
                result_digest=hashlib.sha256(json.dumps(z,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
            print(b,d,rep,z['passes'],z['nodes'],flush=True)
        assert rows[-1]['result']['passes']==rows[-2]['result']['passes']
    sources=[s for s,t in builds]+['src/verify_round139_marked_return_codex.c','src/run_round140_finite_codex.py']
    out=dict(commit=head,builds=buildlog,compiler=subprocess.check_output([str(zig),'version'],text=True).strip(),rows=rows,verified=True,
        committed_source_sha256={s:hashlib.sha256(subprocess.check_output(['git','show',head+':'+s])).hexdigest() for s in sources},
        runtime_source_sha256={s:sha(ROOT/s) for s in sources})
    (ROOT/'outputs/rr_round140_capacity_codex.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
