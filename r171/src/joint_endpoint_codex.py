"""Round 171: finite I/J audit. No capacity search or historical basis fallback.

Memoization is by the COMPLETE capacity-read signature of one arithmetic row,
not by an inferred interaction graph. Cache misses assert read-set containment;
selected assignments are also replayed with the unmodified scalar census.
"""
from pathlib import Path
import collections, hashlib, json, sys, time, gzip

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'r169/src'))
from closure169 import ClosedSystem, H

def load(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def key(s): return tuple(map(int,s.split('|')))
def text(k): return '|'.join(map(str,k))
def save(p,v):
    (ROOT/p).write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
def verdict(req,b):
    return 'STRICTLY_CLOSED' if b and min(b.values())<req else ('EQUALITY' if b and min(b.values())==req else 'SURVIVING')

class Oracle:
    def __init__(self):
        self.S=ClosedSystem()
        self.S.full(); self.base=self.S.verdicts()
        self.S.apply(set()); self.empty=self.S.verdicts()
        self.ex=sorted(k for k in self.base if self.base[k]=='STRICTLY_CLOSED' and self.empty[k]!='STRICTLY_CLOSED')
        self.eq=sorted(k for k in self.base if self.base[k]=='EQUALITY')
        j=load('r171/certs/joint_vector_171.json')
        self.J={key(k):v for k,v in j['joint_safe_vector'].items()}
        self.I=dict(self.J)
        for r in j['comparison']:
            if r['individual_safe_bound'] is not None: self.I[key(r['cell'])]=r['individual_safe_bound']
        self.active=sorted(k for k in self.J if self.I[k]>self.J[k])
        assert len(self.J)==35 and len(self.ex)==180 and len(self.eq)==2
        assert not set(self.J)&set(self.S.dual_chain)
        # System.apply evaluates .get's default eagerly. Replace that accessor:
        # supplied values remain complete, no historical basis value is read.
        self.S.value_of=lambda k: None
        self.S.chain_tab={k:None for k in self.S.chain_tab}
        self.S.piece_tab={k:None for k in self.S.piece_tab}
        self.rows=self.ex+self.eq
        self.cc,self.pc=H.CC,H.PC
        self.reads=set()
        def cc(*k):
            if len(k)==5:k=k+(0,)
            self.reads.add(('c',k));return self.cc(*k)
        def pc(*k):
            self.reads.add(('p',k));return self.pc(*k)
        H.CC,H.PC=cc,pc
        self.deps={r:set() for r in self.rows}
        for v in (self.J,self.I):
            self.apply(v)
            for r in self.rows:
                self.eval_row(r)
                self.deps[r]|=self.reads
        self.deps={r:sorted(x) for r,x in self.deps.items()}
        self.cache={r:{} for r in self.rows}
        self.scalar_checks=[]

    def apply(self,v):
        assert set(v)==set(self.J) and all(isinstance(x,int) for x in v.values())
        self.S.apply(set(v),values=v)

    def eval_row(self,r):
        H.best.cache_clear();self.reads=set()
        return verdict(*H.bounds(self.S.groups[r[0]][r[1]]))

    def evaluate(self,v,scalar=False):
        self.apply(v);out={}
        for r in self.rows:
            dep=self.deps[r]
            signature=tuple(self.cc(*k) if kind=='c' else self.pc(*k) for kind,k in dep)
            if signature not in self.cache[r]:
                result=self.eval_row(r)
                assert self.reads<=set(dep),('uncovered arithmetic dependency',r,self.reads-set(dep))
                self.cache[r][signature]=result
            out[r]=self.cache[r][signature]
        if scalar:
            H.best.cache_clear()
            direct=self.S.verdicts(set(self.rows))
            assert out==direct
            self.scalar_checks.append(hashlib.sha256(json.dumps(sorted((text(k),x) for k,x in v.items())).encode()).hexdigest())
        return out

def minimal_masks(open_masks):
    opened=set(open_masks)
    return [m for m in sorted(opened) if m and all(m^(1<<i) not in opened for i in range(m.bit_length()) if m>>i&1)]

def main():
    t=time.monotonic();o=Oracle()
    frozen=['r171/certs/joint_vector_171.json','r171/certs/remaining_171.json',
            'r170/certs/basis_170.json','r169/src/closure169.py','r168/src/recheck168.py','r163/src/hidden163.py']
    print('active',len(o.active),'rows',len(o.ex),flush=True)
    jresult=o.evaluate(o.J,scalar=True)
    assert all(jresult[r]=='STRICTLY_CLOSED' for r in o.ex)
    assert all(jresult[r]=='EQUALITY' for r in o.eq)
    rows_open=collections.defaultdict(list);records=[]
    n=1<<len(o.active)
    for mask in range(n):
        v=dict(o.J)
        for i,k in enumerate(o.active):
            if mask>>i&1:v[k]=o.I[k]
        result=o.evaluate(v,scalar=mask in {0,1,n-1,170,1023,4095})
        opened=[i for i,r in enumerate(o.ex) if result[r]!='STRICTLY_CLOSED']
        for i in opened:rows_open[i].append(mask)
        records.append(dict(mask=mask,closed=180-len(opened),open_rows=opened,equality=[result[r] for r in o.eq]))
        if mask%512==0:print('assignments',mask,'elapsed',round(time.monotonic()-t,1),flush=True)
    edges=[]
    for i,ms in sorted(rows_open.items()):
        # Verify upward closure exhaustively, not merely on random samples.
        st=set(ms)
        assert all(m|1<<j in st for m in ms for j in range(len(o.active)))
        for m in minimal_masks(ms):
            edges.append(dict(row_index=i,mask=m,cells=[text(k) for j,k in enumerate(o.active) if m>>j&1]))
    parent=list(range(len(o.active)))
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    for e in edges:
        ix=[i for i in range(len(o.active)) if e['mask']>>i&1]
        for i in ix[1:]:parent[find(i)]=find(ix[0])
    components=collections.defaultdict(list)
    for i,k in enumerate(o.active):components[find(i)].append(text(k))
    a,b=key('1|5|10|0|0|0'),key('1|7|8|0|0|0')
    # Requested known pair cannot be an edge in this 13-dimensional slice:
    # the first coordinate is fixed, identically 129 at both endpoints.
    pair_diagnosis=dict(a=text(a),b=text(b),a_in_active=a in o.active,b_in_active=b in o.active,
                        a_J=o.J[a],a_I=o.I[a],b_J=o.J[b],b_I=o.I[b],
                        expected_pair_can_appear=all(k in o.active for k in (a,b)),
                        action='STOP_FULL_FRONTIER_DECOMPOSITION_AND_DIAGNOSE_FIXED_BACKGROUND')
    # Do not overwrite the historical (already retracted) graph or dossier.
    out=dict(base_commit='0029fe2905d01db805d162230b54e9a1e2d2b161',inputs={p:sha(p) for p in frozen},
             scope='COMPLETE_I_J_ENDPOINT_UNIVERSE_ONLY',active=[text(k) for k in o.active],
             J={text(k):v for k,v in o.J.items()},I={text(k):v for k,v in o.I.items()},
             rows=[dict(t=r[0],coordinates=r[1]) for r in o.ex],equality_rows=o.eq,
             assignments=records,total_assignments=n,feasible=sum(not r['open_rows'] and r['equality']==['EQUALITY']*2 for r in records),
             joint_census_closed=180,historical_basis_fallback_disabled=True,
             background='Unchanged pre-existing dual_chain/dual_piece layer; not a claim all certificate dependencies freshly replayed.',
             minimal_row_hyperedges=edges,hyperedge_sizes=dict(collections.Counter(len(e['cells']) for e in edges)),
             unique_hyperedges=len({e['mask'] for e in edges}),components=list(components.values()),
             highest_order=max((len(e['cells']) for e in edges),default=0),
             largest_component=max(map(len,components.values()),default=0),
             cache_entries=sum(map(len,o.cache.values())),scalar_crosschecks=o.scalar_checks,
             known_pair_diagnosis=pair_diagnosis,status='JOINT_SAFE_VECTOR_PARTIAL')
    save('r171/certs/joint_endpoint_codex_171.json',out)
    substantive=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    save('r171/certs/joint_endpoint_execution_codex_171.json',dict(seconds_noncanonical=time.monotonic()-t,content_sha256=substantive))
    print(json.dumps({k:out[k] for k in ('total_assignments','feasible','hyperedge_sizes','highest_order','largest_component','cache_entries','known_pair_diagnosis')},indent=1),flush=True)

if __name__=='__main__':main()
