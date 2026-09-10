"""Recheck R141 equality seams allowing DIRTY heavy w4 joints.

This does not recompute capacities. The archived independent extrema are
explicit inputs. Distinct selected hexes, not literal hidden-window NR,
are the rejection condition. Any unclosed seam is preserved, not discarded.
"""
import collections,hashlib,itertools,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    start=time.perf_counter();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    rel=Path(__file__).relative_to(ROOT).as_posix()
    assert Path(__file__).read_bytes()==subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
    paths=['outputs/rr_round141_extrema_codex.json','outputs/rr_round141_outer_verified_codex.json']
    extrema=json.loads((ROOT/paths[0]).read_text());old=json.loads((ROOT/paths[1]).read_text())
    assert old['verified']
    pp=list(itertools.permutations(range(6)));ix={p:i for i,p in enumerate(pp)}
    def hx(p):return min(p[i:]+p[:i] for i in range(6))
    ext={r['deficit']:r['paths'] for r in extrema['rows']}
    kept_old={(r['G'],tuple(r['left']),tuple(r['right'])):r for r in old['seams']}
    rows=[]
    for G,splits in [(4,[(4,7),(7,4)]),(7,[(4,4)])]:
        for da,db in splits:
            for a in ext[da]:
                p=pp[a[-1]][-1:]+pp[a[-1]][:-1]; ah={hx(pp[v]) for v in a}
                for tail in itertools.permutations(p[:4]):
                    raw=p+tail;t=raw[-6:]
                    if any(p[d:]==t[:-d] for d in range(1,4)):continue
                    hidden=[raw[j:j+6] for j in range(1,4) if len(set(raw[j:j+6]))==6]
                    for b in ext[db]:
                        bb=[ix[tuple(t[x] for x in pp[v])] for v in b]
                        overlap=ah&{hx(pp[v]) for v in bb}
                        previous=kept_old.get((G,tuple(a),tuple(bb)))
                        if overlap:status='SELECTED_HEX_COLLISION'
                        elif previous and previous['status']=='STATIC_COMPLETION_UNSAT':status='PRESERVED_STATIC_UNSAT'
                        else:status='OPEN_DIRTY_HEAVY_SEAM'
                        rows.append(dict(G=G,left=a,right=bb,joint_source=p,target=t,tail=tail,
                            hidden_windows=hidden,dirty=bool(hidden),selected_hex_overlap=sorted(overlap),
                            status=status,old_seam_found=previous is not None))
    out=dict(schema='round142-heavy-dirty-equality-seams-v1',source_commit=head,source_sha256=sha(__file__),
        input_sha256={p:sha(ROOT/p) for p in paths},capped=False,complete_seam_enumeration=True,
        domain='R141 six equality cases only, retain proved extrema; allow all minimal w4 seams including dirty',
        rows=rows,status_counts=dict(collections.Counter(r['status'] for r in rows)),
        dirty_seams=sum(r['dirty'] for r in rows),open_seams=sum(r['status']=='OPEN_DIRTY_HEAVY_SEAM' for r in rows),
        deterministic_digest=digest(rows),seconds=time.perf_counter()-start)
    (ROOT/'outputs/rr_round142_light_clean_seams_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps({k:out[k] for k in ['status_counts','dirty_seams','open_seams','seconds']}))
if __name__=='__main__':main()
