"""Necessary splice envelopes for LIGHT-CLEAN first-occurrence structures.
Heavy joints may be dirty. No inherited G<=3 exclusion is assumed here.
Missing exact cells are replaced only by verified monotone upper bounds.
"""
import collections,functools,hashlib,itertools,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    paths=['outputs/rr_f0_column_115.json','outputs/rr_round139_master_capacities_codex.json',
           'outputs/rr_round140_capacity_codex.json','outputs/rr_round136_capacity_codex.json']
    inputs=[json.loads((ROOT/p).read_text()) for p in paths];table={};sources={}
    def add(b,d,value,source):
        if (b,d) in table:assert table[b,d]==value
        table[b,d]=value;sources.setdefault((b,d),[]).append(source)
    for key,r in inputs[0]['table'].items():
        b,g,d=map(int,key.split(','))
        if g==0:
            assert not r['capped'];add(b,d,r['passes'],paths[0])
    for p,data in zip(paths[1:3],inputs[1:3]):
        for r in data['rows']:
            s=r['result'];assert not s['capped'];add(s['b'],s['s'],s['passes'],p)
    r=inputs[3]['capacity']['result'];assert not r['capped'];add(r['b'],r['s'],r['passes'],paths[3])
    used={}
    def cap(b,d):
        choices=[(val,bb,dd) for (bb,dd),val in table.items() if bb>=b and dd>=d]
        if not choices: return 120 # safe hex-simple universal upper bound
        val,bb,dd=min(choices);used[str((b,d))]=dict(upper=val,dominating_cell=[bb,dd],sources=sources[bb,dd]);return val
    @functools.lru_cache(None)
    def conv(m,b,d):
        if m==1:return cap(b,d)
        return max(conv(m-1,b-i,d-j)+cap(i,j) for i in range(b+1) for j in range(d+1))
    rows=[]
    for k in range(5):
        for G in range(5*k+1):
            for z in range(min(G,4-k)+1):
                for H in range(5-k-z):
                    B=4-k-z-H
                    for h in range(H+1):
                        for heavy in itertools.combinations_with_replacement(range(4,8),h):
                            if sum(w-3 for w in heavy)!=H:continue
                            m=z+1+h
                            for s in range(B+1):
                                if m==1 and s:continue
                                b=B-s;D=5*k-G+5*s;P=120-4*G+5*z;bound=conv(m,b,D)
                                rows.append(dict(k=k,G=G,z=z,c=G-z,H=H,heavy=heavy,m=m,s=s,b=b,D=D,P=P,upper=bound,
                                    status='STRICT' if bound<P else 'EQUALITY' if bound==P else 'OPEN_UPPER_BOUND'))
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    out=dict(schema='round142-light-clean-all-g-envelopes-v1',source_commit=head,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        inputs={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        scope='LIGHT_CLEAN_SELECTED_JOINTS_ONLY; HEAVY MAY BE DIRTY; NO EXCLUSION FROM EQUALITY ALONE',
        rows=rows,used_capacities=used,status_counts=dict(collections.Counter(r['status'] for r in rows)))
    (ROOT/'outputs/rr_round142_light_clean_envelopes_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(out['status_counts']));print(json.dumps([r for r in rows if r['status']!='STRICT' and r['G']<4]))
if __name__=='__main__':main()
