"""Independent finite budget convolution for unrestricted lengths<=868.
No claim about lengths869..871. Hand inclusions in Round142 Route B report.
"""
import functools,hashlib,itertools,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    path=ROOT/'outputs/rr_round142_shadow_capacities_codex.json';d=json.loads(path.read_text())
    assert d['completed'] and d['independent_match'] and not d['capped']
    table={r['D']:r['producer']['max_passes'] for r in d['rows'] if r['mode']=='AB'}
    assert set(table)==set(range(6))
    @functools.lru_cache(None)
    def conv(m,D):
        if m==1:return table[D]
        return max(table[j]+conv(m-1,D-j) for j in range(D+1))
    rows=[]
    # At k0, G=D2=c=Z=0. The only possibilities at t<=1 are
    # H0,B*<=1 (one clean piece, no shadow deficits), or H1,B*=0
    # (at most two clean b0,D0 pieces). Use old paired C(1,0,3)=48
    # as a conservative upper bound on C(1,0,0), rather than a new cell.
    oldpath=ROOT/'outputs/rr_round139_master_capacities_codex.json';old=json.loads(oldpath.read_text())
    controls=[r for r in old['rows'] if r['result']['b']==1 and r['result']['g']==0 and r['result']['s']==3]
    assert len(controls)==2 and {r['independent'] for r in controls}=={False,True}
    assert all(not r['result']['capped'] for r in controls)
    bound=max(r['result']['passes'] for r in controls);assert bound==48
    rows.extend([dict(k=0,G=0,H=0,upper=bound,required=120,status='STRICT'),
                 dict(k=0,G=0,H=1,upper=2*table[0],required=120,status='STRICT')])
    for G in range(6):
        for D2 in range(0,G+1,2):
            c=G-D2;Z=H=B=0;m=D2+1;D=5-G;P=120-4*G+5*D2
            upper=conv(m,D)
            assert upper<P
            rows.append(dict(k=1,G=G,D2=D2,c=c,Z=Z,H=H,Bstar=B,m=m,D=D,upper=upper,required=P,status='STRICT'))
    # Independent composition enumeration, no convolution recurrence.
    for r in rows:
        if r['k']!=1:continue
        vals=[sum(table[x] for x in dd) for dd in itertools.product(range(r['D']+1),repeat=r['m']) if sum(dd)==r['D']]
        assert max(vals)==r['upper']<r['required']
    src=Path(__file__);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert src.read_bytes()==subprocess.check_output(['git','show',head+':'+src.relative_to(ROOT).as_posix()],cwd=ROOT)
    out=dict(schema='round142-unconditional-low-slack-v1',source_commit=head,source_sha256=sha(src),
        inputs={path.relative_to(ROOT).as_posix():sha(path),oldpath.relative_to(ROOT).as_posix():sha(oldpath)},
        rows=rows,verified=True,capped=False,NR6_assumed=False,
        conclusion='NO_LITERAL_N6_COVER_OF_LENGTH_AT_MOST_868',L6_lower_bound=869,L6_upper_bound=872,
        not_proved='LENGTHS_869_870_871_REMAIN_UNRESOLVED',
        load_bearing_hand_dependencies=['first_occurrence_geodesic_projection','dirty_same_hex_genus_charge',
            'retained_mixed_shadow_injection','Bstar_identity','marked_AB_capacity_inclusion'])
    (ROOT/'outputs/rr_round142_low_slack_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(verified=True,rows=len(rows),lower=869,upper=872)))
if __name__=='__main__':main()
