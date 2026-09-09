"""Literal repetition-credit audit, separate from the NR6 outer proof.

No no-repeat engine or outer-cell capacity function is imported.
"""
import collections, hashlib, itertools, json, math, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rotate(p): return p[1:]+p[:1]
def orbit(p): return min(p[i:-1]+p[:i]+p[-1:] for i in range(len(p)-1))
def analyse(word, n):
    alphabet=set(map(str,range(n)))
    occ=[(i,word[i:i+n]) for i in range(len(word)-n+1) if set(word[i:i+n])==alphabet]
    assert len({v for _,v in occ})==math.factorial(n)
    assert occ[0][0]==0 and occ[-1][0]+n==len(word), 'trim endpoints first'
    starts=[j for j in range(len(occ)) if j==0 or occ[j][0]>occ[j-1][0]+1]
    ends=starts[1:]+[len(occ)]
    entries=[occ[j][1] for j in starts]
    qs=[orbit(p) for p in entries]
    seen=set(); repeat_indices=[]
    for j,(_,v) in enumerate(occ):
        if v in seen: repeat_indices.append(j)
        seen.add(v)
    seen=set(); opened={qs[0]}; registered={entries[0]}; joints=[]
    F=S=H=x=e=fout=Y=Ord=a=0
    for i,(lo,stop) in enumerate(zip(starts,ends)):
        for j in range(lo,stop): seen.add(occ[j][1])
        if i==len(starts)-1: break
        j=stop-1; p=occ[j][1]; t=entries[i+1]; w=occ[stop][0]-occ[j][0]
        blocker=rotate(p); abandon=blocker not in seen; fresh=qs[i+1] not in opened
        inter=qs[i+1]!=qs[i]; repeated_run=inter and not fresh
        if w==2: assert t==p[2:]+p[1]+p[0]
        bad=w==2 and not abandon and fresh
        ordinary=w==2 and not abandon and inter and not fresh
        F+=abandon; S+=w>=3; H+=max(0,w-3); x+=w>=3 and not inter
        e+=repeated_run; fout+=w==2 and inter; Y+=bad; Ord+=ordinary
        a+=abandon and not(w==2 and inter)
        if bad:
            assert blocker not in registered and j in repeat_indices
            assert any(occ[u][1]==p and occ[u+1][1]==blocker and occ[u+1][0]==occ[u][0]+1 for u in range(j))
        joints.append(dict(pass_index=i,source_occurrence=j,source=p,target=t,weight=w,
            source_entry_orbit=qs[i],target_orbit=qs[i+1],abandonment=abandon,fresh=fresh,
            bad_fresh_blocked=bad,source_repeated=j in repeat_indices,blocker=blocker))
        opened.add(qs[i+1]);registered.add(t)
    O=len(opened); P=len(starts); R=len(repeat_indices); G=P-math.factorial(n-1); J=G-F
    k=O-math.factorial(n-2); eta=e-Ord; delta=F+e-fout; epsilon=R+delta
    base=math.factorial(n)+math.factorial(n-1)+math.factorial(n-2)+n-3
    assert min(k,J,a,eta,R-Y)>=0 and Y<=min(R,O-1)
    assert S==O+e-1-fout+x and delta==a+eta-Y and epsilon==a+eta+R-Y
    assert len(word)==base+k+J+epsilon+x+H
    assert R<=math.factorial(n-2)-1+len(word)-base
    return dict(word=word,n=n,L=len(word),base=base,M=len(occ),P=P,G=G,F=F,J=J,O=O,k=k,
        R=R,Y=Y,a=a,eta=eta,e=e,x=x,S=S,H=H,f_out=fout,delta=delta,epsilon=epsilon,
        repeat_occurrence_indices=repeat_indices,pass_entries=entries,
        pass_lengths=[b-a for a,b in zip(starts,ends)],joints=joints)
def spell(order):
    out=order[0]
    for target in order[1:]:
        n=len(target);over=max(i for i in range(n) if out[-i:]==target[:i] or i==0)
        out+=target[over:]
    return out
def main():
    start=time.perf_counter();rel=Path(__file__).relative_to(ROOT).as_posix()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)==Path(__file__).read_bytes()
    foundation=json.loads((ROOT/'outputs/rr_round141_nr6_foundation_codex.json').read_text())
    orders=list(itertools.permutations(['012','021','102','120','201','210']))
    words=sorted({spell(o) for o in orders})
    # A full rotation detour returns to the identical literal window, preserving
    # coverage. Repetitions and long passes are deliberately retained.
    detours=[]
    for w in words:
        for i in range(len(w)-2):
            if len(set(w[i:i+3]))==3: detours.append(w[:i+3]+w[i:i+3]+w[i+3:])
    controls=sorted(set(words+detours));rows=[analyse(w,3) for w in controls]
    w6=(ROOT/'data/verified_872_witness.txt').read_text().strip();w6=''.join(w6.split())
    # The repository witness may use 1..6; transport only symbol names.
    syms=sorted(set(w6));assert len(syms)==6
    w6=''.join(str(syms.index(c)) for c in w6)
    nr6=[analyse(w6,6)]
    for i in [0,100,300,600]:
        positions=[j for j in range(len(w6)-5) if len(set(w6[j:j+6]))==6]
        at=positions[i];nr6.append(analyse(w6[:at+6]+w6[at:at+6]+w6[at+6:],6))
    bad=min((r for r in rows if r['Y']),key=lambda r:(r['L'],r['word']))
    trap=foundation['nr4_bounded_control']['minimal_found'];nr4=analyse(trap['word'],4)
    # At the n=4 classical bound, the only possible R=1 layout has five
    # length-4 passes and one length-5 pass, all free joints; test ALL six slots.
    n4layouts=[]
    for long_at in range(6):
        word='0123';entries=[]
        for i in range(6):
            p=word[-4:];entries.append(p);length=5 if i==long_at else 4
            for _ in range(length-1):word+=word[-4]
            if i<5:p=word[-4:];word+=p[1]+p[0]
        occ=[word[i:i+4] for i in range(len(word)-3) if len(set(word[i:i+4]))==4]
        n4layouts.append(dict(long_at=long_at,word=word,entries=entries,occurrences=len(occ),distinct=len(set(occ))))
    assert all(z['distinct']<24 for z in n4layouts)
    out=dict(schema='round141-repeat-credit-v1',source_commit=head,source_sha256=sha(__file__),
        input_sha256={'foundation':sha(ROOT/'outputs/rr_round141_nr6_foundation_codex.json'),
                      '872_witness':sha(ROOT/'data/verified_872_witness.txt')},
        complete_control_domain='distinct S3 Hamilton spellings and one full literal rotation detour at each permutation occurrence',
        base_words=len(words),controls=len(rows),Y_positive=sum(r['Y']>0 for r in rows),
        histogram=[dict(R=r,Y=y,epsilon=e,count=v) for (r,y,e),v in sorted(collections.Counter((r['R'],r['Y'],r['epsilon']) for r in rows).items())],
        bad_fresh_minimal_in_control_domain=bad,nr4_trap=nr4,nr4_bound_single_repeat_layouts=n4layouts,
        n6_controls=nr6,verified_identities=True,NR6='UNPROVED',seconds=time.perf_counter()-start)
    (ROOT/'outputs/rr_round141_repeat_credit_codex.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
    print(json.dumps(dict(controls=len(rows),Y_positive=out['Y_positive'],minimal_bad_word=bad['word'],NR6='UNPROVED')))
if __name__=='__main__':main()
