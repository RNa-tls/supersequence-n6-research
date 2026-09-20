"""Small upper-bound trials after capped discovery; no exact-value assumption."""
from production_j171 import *

def main():
    f=frozen();refs,dep,env=environment();assert canonical(env)==f['environment_sha256']
    cert={k:v[0] for k,v in dep.items()};rows=[]
    for d,bound in [(2,80),(1,64),(0,64)]:
        k=(1,d,5,1,0,0);g=G.Engine(cert,200000);toks,err=g.build(k,bound)
        r=dict(cell=text(k),proposed_upper_bound=bound,nodes=g.nodes,node_cap=200000,complete=toks is not None,detail=err)
        if toks is not None:
            path=PREFIX+f'extree_J_B1_upper_d{d}_codex_171.txt.gz';assert not (ROOT/path).exists()
            plain=G.write_batch(ROOT/path,refs,[(k,*v) for k,v in sorted(dep.items())],[(k,bound,toks)])
            r.update(path=path,sha256=sha(path),plain_sha256=hashlib.sha256(plain.encode()).hexdigest())
        rows.append(r);save(PREFIX+'family_B1_upper_trials_codex_171.json',dict(rows=rows,scope='proposed upper bounds, not exact-capacity discovery',environment_sha256=canonical(env)))
        print(r,flush=True)
        if toks is not None:break

if __name__=='__main__':main()
