"""Finite local alpha-gap experiments. No complete n=6 walk search.

Standalone literal geometry; no production pruning engine is imported.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
import time
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Geometry:
    def __init__(self, n):
        self.n = n
        self.words = list(itertools.permutations(range(n)))
        self.idx = {w: i for i, w in enumerate(self.words)}
        self.h, self.q = [], []
        for w in self.words:
            self.h.append(min(self.idx[self.sigma(w, j)] for j in range(n)))
            self.q.append(min(self.idx[self.E(w, j)] for j in range(n-1)))
        self.oh = {q: {self.h[i] for i, a in enumerate(self.q) if a == q}
                   for q in set(self.q)}
        self.joint = {}
        for a, w in enumerate(self.words):
            out = []
            for wt in (2, 3):
                for tail in itertools.permutations(w[:wt]):
                    t = w[wt:] + tail
                    if self.weight(w, t) != wt:
                        continue
                    raw = w + tail
                    if any(len(set(raw[j:j+n])) == n for j in range(1, wt)):
                        continue
                    out.append((self.idx[t], wt))
            self.joint[a] = out

    def sigma(self, w, k=1):
        k %= self.n
        return w[k:] + w[:k]

    def E(self, w, k=1):
        k %= self.n-1
        a = w[:-1]
        return a[k:] + a[:k] + w[-1:]

    def s(self, i, k=1):
        return self.idx[self.sigma(self.words[i], k)]

    def e(self, i, k=1):
        return self.idx[self.E(self.words[i], k)]

    def weight(self, a, b):
        return next((k for k in range(1, self.n) if a[k:] == b[:-k]), self.n)

    def half(self, v, b):
        c = self.s(v, b)
        return [(v, b)] + [(self.e(c, j), self.n) for j in range(1, self.n-1)] + [(c, self.n-b)]

    def windows(self, passes):
        return [self.s(v, j) for v, length in passes for j in range(length)]

    def replay(self, passes):
        """Validate every literal window, including hidden joint windows."""
        raw = list(self.words[passes[0][0]])
        weights = []
        for k, (v, length) in enumerate(passes):
            if k:
                prev, plen = passes[k-1]
                ep = self.s(prev, plen-1)
                wt = self.weight(self.words[ep], self.words[v])
                if (v, wt) not in self.joint[ep]:
                    return None
                raw.extend(self.words[v][-wt:])
                weights.append(wt)
            for j in range(length-1):
                raw.append(self.words[self.s(v, j)][0])
        literal = [self.idx[tuple(raw[j:j+self.n])] for j in range(len(raw)-self.n+1)
                   if len(set(raw[j:j+self.n])) == self.n]
        expected = self.windows(passes)
        if literal != expected or len(set(literal)) != len(literal):
            return None
        return dict(word=''.join(map(str, raw)), passes=passes, weights=weights,
                    literal_sha256=hashlib.sha256(bytes(raw)).hexdigest(),
                    windows=len(literal))


def guard_census(g):
    """Full finite phase-footprint identity, all words and split lengths."""
    hist, violations = Counter(), []
    for v in range(len(g.words)):
        for b in range(1, g.n):
            block = g.half(v,b)
            used = {g.h[w] for w, _ in block}
            hit = tuple(j for j in range(g.n-1) if g.h[g.e(v,j)] in used)
            predicted = tuple(sorted({0} | ({1} if b == 1 else set()) |
                                      ({g.n-2} if b == g.n-1 else set())))
            hist[str((b,hit))] += 1
            if hit != predicted:
                violations.append([v,b,hit,predicted])
    return dict(tested=len(g.words)*(g.n-1), intersection_histogram=dict(hist),
                violations=violations)


def pair_census(g):
    """Static necessary conditions; SAT here is only a local configuration."""
    rows=[]
    for kind, free0, free1 in [('P0',True,False),('P1-alpha',False,True),('D-alpha',True,True)]:
        for b0 in range(1,g.n):
            A=g.half(0,b0); HA={g.h[v] for v,l in A}
            for b1 in range(1,g.n):
                hist=Counter(); live=[]
                for v1 in range(len(g.words)):
                    B=g.half(v1,b1); HB={g.h[v] for v,l in B}
                    if HA & HB:
                        hist['half_footprint_collision']+=1; continue
                    if kind!='P0' and g.q[v1]==g.q[0]:
                        hist['repeat_budget']+=1; continue
                    # Free c0 may land directly on o1. Only that exact port is an exception.
                    t0=g.e(0)
                    if free0 and (g.h[t0] in HA or (g.h[t0] in HB and t0!=v1)):
                        hist['first_free_exit_collision']+=1;continue
                    # After closer1 all four short passes are finished.
                    t1=g.e(v1)
                    if free1 and g.h[t1] in HA|HB:
                        hist['last_free_exit_collision']+=1;continue
                    hist['local_survivor']+=1;live.append(v1)
                rows.append(dict(kind=kind,b0=b0,b1=b1,counts=dict(hist),v1=live))
    return rows


def relaxed_gap(g, b0, free0):
    """Finite overapproximation dropping global occupancy and fresh-orbit history.

    Full gap passes avoid the completed first half. Paid same-orbit edges remain
    forbidden. This is used to falsify a *local* small-image argument, not to prune.
    """
    A=g.half(0,b0); forbidden={g.h[v] for v,l in A}; q0=g.q[0]
    endpoint=g.s(0,-1)
    starts=[(v,w) for v,w in g.joint[endpoint] if (w==2)==free0 and
            g.h[v] not in forbidden and (w==2 or g.q[v]!=q0)]
    prev={v:None for v,w in starts}; queue=deque(prev)
    while queue:
        u=queue.popleft()
        for v,w in g.joint[g.s(u,-1)]:
            if g.h[v] in forbidden or (w==3 and g.q[v]==g.q[u]):continue
            if v not in prev:prev[v]=u;queue.append(v)
    return dict(b0=b0,free0=free0,reachable=len(prev),endpoints=sorted(prev),
                global_occupancy_preserved=False,verdict='UNSAT_COMPLETE' if not prev else 'SAT')


def exact_gap(g, max_full=7):
    """Every local full-gap path to max_full, at ell0=1; all five b1 tested.

    Maintains literal occupancy, registered ports, and no paid repeat run. Terminal
    block conditions are checked with literal replay. Full walk extendability is unknown.
    """
    rows=[]; global_witnesses={}
    for kind,free0,free1 in [('P0',True,False),('P1-alpha',False,True),('D-alpha',True,True)]:
        for b0 in range(1,g.n):
            A=g.half(0,b0); HA={g.h[v] for v,l in A}; QA={g.q[v] for v,l in A}
            counts=Counter(); endpoints=set(); by_b1=Counter(); costhist=Counter(); witnesses={}
            def visit(path, hs, qs, ports, full, gapcost, first):
                counts['expanded_local_nodes']+=1
                u,length=path[-1];ep=g.s(u,length-1)
                for v,wt in g.joint[ep]:
                    if first and (wt==2)!=free0:continue
                    if wt==3 and (g.q[v] in qs):continue
                    if wt==2 and not first and g.q[v]!=g.q[u]:raise AssertionError('full w2')
                    if v in ports or g.h[v] in hs:continue
                    cost=gapcost+(wt==3)
                    for b1 in range(1,g.n):
                        if kind!='P0' and g.q[v]==g.q[0]:continue
                        B=g.half(v,b1); bw=g.windows(B)
                        Bhs={g.h[z] for z,l in B}
                        # h(v) is repeated inside B only; all its windows are complementary.
                        if Bhs & hs or len(set(bw))!=len(bw):continue
                        Bports=[z for z,l in B]
                        if len(set(Bports))!=len(Bports) or set(Bports)&ports:continue
                        # Locked T1 must be fresh; no paid re-entry, repeats only free descents.
                        T1=g.q[B[1][0]]
                        if T1 in qs or T1==g.q[v]:continue
                        candidate=path+B
                        if free1:
                            nxt=g.e(v)
                            if g.h[nxt] in hs|Bhs or nxt in ports|set(Bports):continue
                            candidate=candidate+[(nxt,g.n)]
                        rep=g.replay(candidate)
                        if rep is None:raise AssertionError('local candidate literal mismatch')
                        counts['valid_local_two_block_paths']+=1
                        by_b1[str((b1,full))]+=1;endpoints.add(v);costhist[str(cost)]+=1
                        key=str(b1)
                        if key not in witnesses:witnesses[key]=rep|dict(gap_full=full,gap_cost=cost,v1=v)
                        if cost>=3 and 'cost_ge3' not in global_witnesses:
                            global_witnesses['cost_ge3']=rep|dict(kind=kind,b0=b0,b1=b1,full=full,cost=cost)
                    if full<max_full:
                        visit(path+[(v,g.n)],hs|{g.h[v]},qs|{g.q[v]},ports|{v},full+1,cost,False)
            visit(A,HA,QA,{v for v,l in A},0,0,True)
            rows.append(dict(kind=kind,b0=b0,depth_bound_full_gap=max_full,
                             counts=dict(counts),endpoint_count=len(endpoints),endpoints=sorted(endpoints),
                             by_b1_gap_length=dict(by_b1),gap_cost_histogram=dict(costhist),witnesses=witnesses,
                             verdict='SAT' if endpoints else 'UNSAT_COMPLETE',
                             scope='local paths with at most stated full-gap length and ell0=1'))
    return dict(rows=rows,counterexamples=global_witnesses)


def n4_control():
    # Established exhaustive enumerator is used only as a source of complete controls.
    from verify_f2_structure_126 import n4_walks
    from verify_fg_repair_128 import walk_measure
    from verify_b_machine_132 import _structure
    g,W,walks=n4_walks(39)
    stat=Counter();bad=[]
    for L,seq in walks:
        m=walk_measure(g,W,seq,L)
        if m['G']!=2 or m['x'] or m['f_out']!=m['F']+m['e']:continue
        s=_structure(g,m)
        if not s:continue
        stat['TypeB_x0_equality']+=1
        for j in range(2):
            if not s['lock'+str(j)]:continue
            o,c=s['o'+str(j)],s['c'+str(j)]
            b=m['passes'][o][1]
            stat['locked_half']+=1
            if s['free'][c]:
                stat['locked_half_free_closer']+=1
                if b==1:bad.append(dict(seq=seq,o=o,c=c))
    return dict(counts=dict(stat),false_rejections=len(bad),counterexamples=bad)


def main():
    p=argparse.ArgumentParser();p.add_argument('--depth',type=int,default=7)
    p.add_argument('--n4',action='store_true');args=p.parse_args()
    t=time.perf_counter();g=Geometry(6)
    result=dict(scope='finite local structural research; no n6 complete-walk search',
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                binary_sha256=None,driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                interpreter='Python; no native binary',parameters=vars(args),
                guards={str(n):guard_census(Geometry(n)) for n in (4,5,6)},
                pair_census=pair_census(g),
                relaxed_gaps=[relaxed_gap(g,b,f) for b in range(1,6) for f in (False,True)],
                exact_local_gaps=exact_gap(g,args.depth))
    if args.n4:result['n4_control']=n4_control()
    result['seconds']=time.perf_counter()-t
    result['deterministic_digest']=hashlib.sha256(json.dumps({k:v for k,v in result.items()
                if k not in ('seconds','source_commit','source_sha256','driver_sha256')},sort_keys=True).encode()).hexdigest()
    dest=ROOT/'outputs'/'rr_alpha_gap_research_codex.json'
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(seconds=result['seconds'],digest=result['deterministic_digest'],
          pair_live_splits=Counter(r['kind'] for r in result['pair_census'] if r['v1']),
          relaxed_counts=[(r['b0'],r['free0'],r['reachable']) for r in result['relaxed_gaps']],
          local_counts=[(r['kind'],r['b0'],r['counts'],r['endpoint_count']) for r in result['exact_local_gaps']['rows']],
          n4=result.get('n4_control')),indent=2))

if __name__=='__main__':main()
