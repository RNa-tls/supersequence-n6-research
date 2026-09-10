"""Small fixed b0-chain domains for dirty-heavy seam audit; two algorithms.
No superpermutation/covering-word search; commit and remote required first.
"""
import hashlib,json,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZIG=Path('C:/Users/parks/AppData/Local/Temp/round137_compiler/ziglang/zig.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]==head
    files=['src/run_round142_light_clean_domains_codex.py','src/round141_extrema_codex.c',
        'src/chain_capacity_115.c','src/round141_verify_extrema_codex.c','src/verify_round139_marked_return_codex.c']
    hashes={};runtime={}
    for f in files:
        raw=subprocess.check_output(['git','show',head+':'+f],cwd=ROOT); local=(ROOT/f).read_bytes()
        assert raw.replace(b'\r\n',b'\n')==local.replace(b'\r\n',b'\n')
        hashes[f]=hashlib.sha256(raw).hexdigest();runtime[f]=sha(ROOT/f)
    binaries=[]
    for c in ['src/round141_extrema_codex.c','src/round141_verify_extrema_codex.c']:
        exe=ROOT/('outputs/round142_'+Path(c).stem+'.exe')
        build=[str(ZIG),'cc','-O3',c,'-o',str(exe)]
        subprocess.run(build,cwd=ROOT,check=True,capture_output=True)
        binaries.append(dict(exe=str(exe),sha256=sha(exe),build=build))
    domains=sorted(set([(20,0),(33,2),(46,4),(58,7),(62,8),(66,9),(70,10),(74,11),(83,12),(96,14)]
        +[(t,2) for t in range(28,34)]+[(t,4) for t in range(41,47)]))
    result=dict(schema='round142-light-clean-fixed-domains-v1',source_commit=head,committed_sha256=hashes,
        runtime_sha256=runtime,compiler=subprocess.check_output([str(ZIG),'version'],text=True).strip(),
        binaries=binaries,rows=[],completed=False,capped=False,scope='FINITE_FIXED_LENGTH_ORDINARY_CHAIN_DOMAINS')
    output=ROOT/'outputs/rr_round142_light_clean_domains_codex.json'
    for T,D in domains:
        jobs=[]
        for binary in binaries:
            argv=[binary['exe'],str(T),str(D),'20000000000'];t=time.perf_counter()
            r=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
            data=json.loads(r.stdout);data.update(argv=argv,seconds=time.perf_counter()-t,exit_code=r.returncode)
            data['digest']=dig({k:data[k] for k in ['target','deficit','paths','nodes','count','capped']})
            jobs.append(data)
            if data['capped'] or r.returncode:
                result['capped']=True;result['rows'].append(dict(T=T,D=D,jobs=jobs,status='UNKNOWN_CAP'))
                output.write_text(json.dumps(result,indent=2)+'\n',newline='\n');raise RuntimeError('UNKNOWN_CAP')
        assert {tuple(p) for p in jobs[0]['paths']}=={tuple(p) for p in jobs[1]['paths']}
        assert len(jobs[0]['paths'])==len(set(map(tuple,jobs[0]['paths'])))==jobs[0]['count']==jobs[1]['count']
        result['rows'].append(dict(T=T,D=D,jobs=jobs,status='COMPLETE_MATCH'))
        output.write_text(json.dumps(result,indent=2)+'\n',newline='\n')
        print(json.dumps(dict(T=T,D=D,count=jobs[0]['count'],nodes=[j['nodes'] for j in jobs],seconds=sum(j['seconds'] for j in jobs))),flush=True)
    result['completed']=True;output.write_text(json.dumps(result,indent=2)+'\n',newline='\n')
if __name__=='__main__':main()
