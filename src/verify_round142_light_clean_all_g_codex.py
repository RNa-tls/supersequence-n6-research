"""Two independently generated heavy seam domains for light-clean FO covers.

Primary tails: permutations of removed prefix. Independent: all720 value
maps and direct string overlap/substring scan. Both allow dirty heavy joints.
Capacity extrema were independently exhausted by two compiled algorithms.
"""
import collections,functools,hashlib,itertools,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source=Path(__file__);rel=source.relative_to(ROOT).as_posix()
    assert source.read_bytes()==subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)
    start=time.perf_counter()
    paths=['outputs/rr_round142_light_clean_domains_codex.json','outputs/rr_round142_light_clean_envelopes_codex.json',
           'outputs/rr_f0_column_115.json','outputs/rr_round141_outer_verified_codex.json']
    domain,env,old,prior=[json.loads((ROOT/p).read_text()) for p in paths]
    assert domain['completed'] and not domain['capped']
    pp=tuple(itertools.permutations(range(6)));ix={p:i for i,p in enumerate(pp)}
    labels=tuple(''.join(map(str,p)) for p in pp);sx={p:i for i,p in enumerate(labels)}
    def hx(p):return min(p[j:]+p[:j] for j in range(6))
    hh=[hx(p) for p in pp];hi={p:i for i,p in enumerate(sorted(set(hh)))};masks=[1<<hi[h] for h in hh]
    ds={}
    for r in domain['rows']:
        assert len(r['jobs'])==2 and all(not j['capped'] for j in r['jobs'])
        a,b=[{tuple(p) for p in j['paths']} for j in r['jobs']];assert a==b
        ds[r['T'],r['D']]=sorted(a)
    C={int(k.split(',')[2]):v['passes'] for k,v in old['table'].items() if k.startswith('0,0,')}
    cases=sorted({(r['G'],r['H'],r['m'],r['D'],r['P']) for r in env['rows'] if r['status']!='STRICT'})
    assert all(r['b']==0 and r['z']==0 and r['heavy'] in ([4],[4,4],[]) for r in env['rows'] if r['status']!='STRICT')
    def alloc(n,m):
        if m==1:yield (n,);return
        for j in range(n+1):
            for z in alloc(n-j,m-1):yield (j,)+z
    def choices(D,m,P):
        out=[]
        for DD in alloc(D,m):
            if sum(C[d] for d in DD)<P:continue
            ranges=[range(max(1,P-sum(C[x] for j,x in enumerate(DD) if j!=i)),C[d]+1) for i,d in enumerate(DD)]
            for TT in itertools.product(*ranges):
                if sum(TT)!=P:continue
                for t,d in zip(TT,DD):assert (t,d) in ds,(t,d)
                if all(ds[t,d] for t,d in zip(TT,DD)):out.append((TT,DD))
        return out
    @functools.lru_cache(None)
    def targets(end,independent):
        p=pp[end];out=[]
        if not independent:
            for tail in itertools.permutations(p[:4]):
                raw=p+tail;t=raw[-6:]
                if any(p[j:]==t[:-j] for j in range(1,4)):continue
                dirty=any(len(set(raw[j:j+6]))==6 for j in range(1,4))
                out.append((ix[t],dirty))
        else:
            src=labels[end]
            for j,t in enumerate(labels):
                if src[4:]!=t[:2]:continue
                shift=next((z for z in range(1,7) if src[z:]==t[:6-z]),6)
                if shift!=4:continue
                text=src+t[-4:];dirty=any(text[z:z+6] in sx for z in (1,2,3))
                out.append((j,dirty))
        return tuple(sorted(out))
    summaries=[];all_rows=[]
    for G,H,m,D,P in cases:
        patterns=choices(D,m,P);transcripts=[]
        for independent in (False,True):
            records={}
            def chain_mask(chain):
                if not independent:return functools.reduce(int.__or__,(masks[v] for v in chain),0)
                # independent literal rotation names, not cached integer hex masks
                names={min(labels[v][j:]+labels[v][:j] for j in range(6)) for v in chain}
                return sum(1<<hi[tuple(map(int,h))] for h in names)
            def append(parts,DD,TT):
                if len(parts)==m:
                    flat=tuple(v for part in parts for v in part)
                    records[('FULL',flat)]=dict(status='FULL_DISJOINT',parts=parts)
                    return
                endp=pp[parts[-1][-1]];end=ix[endp[-1:]+endp[:-1]]
                used=chain_mask(tuple(v for part in parts for v in part));at=len(parts)
                for q,dirty in targets(end,independent):
                    for normalized in ds[TT[at],DD[at]]:
                        if not independent:child=tuple(ix[tuple(pp[q][x] for x in pp[v])] for v in normalized)
                        else:child=tuple(sx[''.join(labels[q][int(x)] for x in labels[v])] for v in normalized)
                        newparts=parts+(child,);flat=tuple(v for part in newparts for v in part)
                        collision=bool(used&chain_mask(child))
                        key=('SEAM',at,tuple(map(tuple,newparts)))
                        row=dict(stage=at,dirty=dirty,collision=collision,parts=newparts)
                        assert key not in records or records[key]==row
                        records[key]=row
                        if not collision:append(newparts,DD,TT)
            for TT,DD in patterns:
                for a in ds[TT[0],DD[0]]:append((a,),DD,TT)
            normalized=sorted(records.values(),key=lambda r:json.dumps(r,sort_keys=True))
            transcripts.append(normalized)
        assert transcripts[0]==transcripts[1]
        records=transcripts[0];whole=[r for r in records if r.get('status')=='FULL_DISJOINT']
        retained=[]
        for r in whole:
            flat=[v for part in r['parts'] for v in part]
            if G==6 and m==1:
                cert=next(x for x in prior['completion_covers'] if x['entries']==flat)
            else:
                cert=next((x['completion_cover'] for x in prior['seams'] if x['left']+x['right']==flat and x['G']==G),None)
            retained.append(dict(parts=r['parts'],status='PRESERVED_STATIC_UNSAT' if cert and cert['status']=='UNSAT' else 'OPEN',
                certificate=cert))
        summary=dict(G=G,H=H,m=m,D=D,P=P,patterns=patterns,
            seams=sum('stage' in r for r in records),dirty_seams=sum(r.get('dirty',False) for r in records),
            hex_collisions=sum(r.get('collision',False) for r in records),
            full_disjoint=len(whole),survivors=retained,independent_digest=dig(records),
            closed=all(r['status']=='PRESERVED_STATIC_UNSAT' for r in retained))
        summaries.append(summary);all_rows.append(dict(case=[G,H,m,D,P],records=records))
        print(json.dumps({k:summary[k] for k in ['G','H','m','seams','dirty_seams','hex_collisions','full_disjoint','closed']}),flush=True)
    closed=all(x['closed'] for x in summaries)
    out=dict(schema='round142-light-clean-heavy-inclusive-closure-v1',source_commit=head,source_sha256=sha(source),
        inputs={p:sha(ROOT/p) for p in paths},complete=True,capped=False,independent_seam_agreement=True,
        literal_NR_not_assumed=True,required='EVERY_SELECTED_W2_AND_W3_JOINT_CLEAN',
        direct_normalization='NOT_PROVED',all_light_clean_cells_closed=closed,
        envelope_counts=env['status_counts'],cases=summaries,transcripts=all_rows,
        seconds=time.perf_counter()-start)
    (ROOT/'outputs/rr_round142_light_clean_all_g_verified_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(all_light_clean_cells_closed=closed,seconds=out['seconds'])))
if __name__=='__main__':main()
