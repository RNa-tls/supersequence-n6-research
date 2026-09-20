"""Check Round171 endpoint evidence; preserve historical certificates unchanged."""
import collections, gzip, hashlib, json, sys
from pathlib import Path
from joint_endpoint_codex import ROOT, ClosedSystem, key, text, load, sha, save, minimal_masks

def certificates():
    cases=[('r170','target_h_170','targeth_170','genuine_target_h_170'),
           ('r170','target_a2_170','targeta2_170','genuine_target_a2_170'),
           ('r171','lb_batch1_171','lb1_171','genuine_lb_batch1_171'),
           ('r171','lb_b1a10_d5_171','lb_d5_171','genuine_lb_b1a10_d5_171'),
           ('r171','lb_b1a10_d7_171','lb_d7_171','genuine_lb_b1a10_d7_171'),
           ('r171','lb_b1a10_d7_joint119_171','d7j_171','genuine_lb_b1a10_d7_joint119_171')]
    result=[]
    for rd,batchtag,tag,gen in cases:
        batch=f'{rd}/certs/extree_{batchtag}.txt.gz'
        pa=f'{rd}/certs/verification_a_{tag}.json';pb=f'{rd}/certs/verification_b_{tag}.json'
        a,b,g=load(pa),load(pb),load(f'{rd}/certs/{gen}.json')
        assert a['all_ok'] and b['all_ok'] and b['histogram_mismatches']==0
        assert a['extree152_sha256']==sha('r152/src/extree152.py')
        assert b['routeb164_sha256']==sha('r164/src/routeb164.py')
        plain=gzip.decompress((ROOT/batch).read_bytes())
        digest=hashlib.sha256(plain).hexdigest()
        aa,bb=a['batches'][batch],b['batches'][batch]
        assert aa['sha256']==bb['sha256']==g['stored_sha256']==sha(batch)
        assert aa['plain_sha256']==bb['plain_sha256']==g['plain_sha256']==digest
        assert aa['nodes']==bb['nodes']==bb['hist_checks']==g['proof_nodes']
        for dep,dr in b['batches'].items():
            assert dr['ok'] and dr['sha256']==sha(dep)
            assert dr['plain_sha256']==hashlib.sha256(gzip.decompress((ROOT/dep).read_bytes())).hexdigest()
        c=a['per_cell'][batch];assert len(c)==1 and c[0]['status']=='UPPER_CERTIFIED'
        headers=[s.split() for s in plain.decode().splitlines() if s.startswith('tree ')]
        assert len(headers)==1 and tuple(map(int,headers[0][1:7]))==key(c[0]['cell']) and int(headers[0][7])==c[0]['cap']
        result.append(dict(cell=c[0]['cell'],cap=c[0]['cap'],batch=batch,sha256=sha(batch),
                           proof_nodes=aa['nodes'],reports={pa:sha(pa),pb:sha(pb)},
                           status='PRESERVED_DUAL_VERIFIED_BOUND',
                           verification_here='report/source/container/plain/dependency hashes and four-way node agreement; NOT a fresh EXTREE replay'))
    return result

def main():
    e=load('r171/certs/joint_endpoint_codex_171.json');J={key(k):v for k,v in e['J'].items()};I={key(k):v for k,v in e['I'].items()}
    active=list(map(key,e['active']));n=1<<len(active)
    assert n==8192 and len(e['assignments'])==n
    rows=[(r['t'],tuple(r['coordinates'])) for r in e['rows']]
    S=ClosedSystem(); S.full();base=S.verdicts();S.apply(set());empty=S.verdicts()
    assert rows==sorted(r for r in base if base[r]=='STRICTLY_CLOSED' and empty[r]!='STRICTLY_CLOSED')
    eq=sorted(r for r in base if base[r]=='EQUALITY')
    # No historical basis defaults, nor accidental exact-table reads in this path.
    S.value_of=lambda k:None
    S.chain_tab={k:None for k in S.chain_tab};S.piece_tab={k:None for k in S.piece_tab}
    def direct(v):
        assert set(v)==set(J)
        S.apply(set(v),values=v);return S.verdicts()
    j=direct(J)
    assert collections.Counter(j.values())=={'STRICTLY_CLOSED':1607,'EQUALITY':2}
    all_open=collections.defaultdict(set)
    for m,r in enumerate(e['assignments']):
        assert r['mask']==m and r['closed']==180-len(r['open_rows'])
        assert len(set(r['open_rows']))==len(r['open_rows'])
        for i in r['open_rows']:assert 0<=i<180;all_open[i].add(m)
    actual={(i,m) for i,ms in all_open.items() for m in minimal_masks(ms)}
    assert actual=={(h['row_index'],h['mask']) for h in e['minimal_row_hyperedges']}
    # These are all rowwise minimal forbidden masks, not pairwise approximations.
    for i,ms in all_open.items():
        mins=[m for ii,m in actual if ii==i]
        assert all(any((m & f)==f for f in mins)==(m in ms) for m in range(n))
    checkmasks={0,n-1,*[1<<i for i in range(len(active))],*[m for _,m in actual]}
    for mask in sorted(checkmasks):
        v=dict(J)
        for i,k in enumerate(active):
            if mask>>i&1:v[k]=I[k]
        got=direct(v);record=e['assignments'][mask]
        assert record['open_rows']==[i for i,r in enumerate(rows) if got[r]!='STRICTLY_CLOSED']
        assert record['equality']==[got[r] for r in eq]
    # Exact first breakpoints along rays with all other coordinates fixed at J.
    ray=[]
    for k in active:
        v=dict(J);v[k]+=1;got=direct(v)
        ray.append(dict(cell=text(k),safe_at=J[k],first_unsafe=J[k]+1,
                        open_rows=[i for i,r in enumerate(rows) if got[r]!='STRICTLY_CLOSED']))
        assert ray[-1]['open_rows']
    # Real conjunction regression. Historical numbers are supplied explicitly
    # ONLY to reproduce this diagnostic example, never used in the J census.
    old=load('r171/certs/joint_vector_171.json')['comparison']
    diagnostic={key(r['cell']):r['historical_capacity_DIAGNOSTIC_ONLY'] for r in old}
    A,B=key('1|5|10|0|0|0'),key('1|7|8|0|0|0')
    pair=[]
    for mask in range(4):
        v=dict(diagnostic)
        if mask&1:v[A]=129
        if mask&2:v[B]=123
        got=direct(v)
        pair.append(dict(mask=mask,open_rows=[i for i,r in enumerate(rows) if got[r]!='STRICTLY_CLOSED']))
    assert not pair[0]['open_rows'] and not pair[1]['open_rows'] and not pair[2]['open_rows'] and pair[3]['open_rows']
    # Synthetic monotone 3-way conjunction defeats both singleton and pair probes.
    assert minimal_masks([7])==[7]
    assert all(m!=7 for m in range(8) if m.bit_count()<=2)
    certs=certificates();best={}
    for c in certs:best[c['cell']]=min(best.get(c['cell'],10**9),c['cap'])
    dossier=[]
    components={k:i for i,c in enumerate(e['components']) for k in c}
    for r in old:
        k=r['cell'];cap=best.get(k)
        dossier.append(dict(cell=k,individual_safe_bound=r['individual_safe_bound'],selected_joint_safe_bound=J[key(k)],
                            historical_capacity_DIAGNOSTIC_ONLY=r['historical_capacity_DIAGNOSTIC_ONLY'],currently_certified_bound=cap,
                            status=('NEEDS_GENUINE_BOUND' if cap is None else ('JOINTLY_USABLE' if cap<=J[key(k)] else 'VALID_BUT_NOT_JOINTLY_SUFFICIENT')),
                            ray_breakpoints=next((x for x in ray if x['cell']==k),None),
                            endpoint_component=components.get(k),
                            component_scope='I/J endpoint slice only; fixed-background coordinates are NOT proved independent'))
    for c in certs:c['joint_usability']='JOINTLY_USABLE' if c['cap']<=J[key(c['cell'])] else 'VALID_BUT_NOT_JOINTLY_SUFFICIENT'
    basis=load('r170/certs/basis_170.json');audit=load('r170/certs/basis_audit_170.json')
    assert audit['audited_sha256']==sha('r170/certs/basis_170.json')
    assert basis['minimum']['cells']==35 and audit['ok'] and audit['verdict']=='EXACT_MINIMUM_35_CONFIRMED'
    # Dependency audit only: do not redo the cardinality optimization.
    sources=['r170/src/basis170.py','r170/src/checkbasis170.py','r169/src/closure169.py','r168/src/recheck168.py','r163/src/hidden163.py']
    assert all('r171' not in (ROOT/p).read_text() for p in sources)
    report=dict(status='JOINT_SAFE_VECTOR_PARTIAL',endpoint_assignments=n,
                feasible_assignments=e['feasible'],highest_interaction_order=e['highest_order'],
                minimal_hyperedges=len(actual),scalar_assignments_rechecked=len(checkmasks),
                full_J_census=dict(collections.Counter(j.values())),exposed_closed=180,equality_preserved=True,
                direct_production_basis_values='COMPLETE J OVERRIDE; HISTORICAL FALLBACK DISABLED',
                certificates=certs,genuine_distinct_basis_cells=len(best),jointly_usable=sum(r['status']=='JOINTLY_USABLE' for r in dossier),
                remaining_joint_safe_bounds=sum(r['status']!='JOINTLY_USABLE' for r in dossier),
                actual_historical_basis_reads_in_J_census=0,
                basis_OPT35=dict(status='FROZEN_IN_EXISTING_UNIVERSE_AND_RULE_SYSTEM',dependency_sources={p:sha(p) for p in sources},
                                depends_on_individual_safe_derivation=False,not_reoptimized=True),
                dossier=dossier,ray_breakpoints=ray,diagnostic_pair_regression=pair,
                synthetic_three_way=dict(universe=8,infeasible_masks=[7],minimal_hyperedges=[7],singletons_and_pairs_safe=True),
                box_frontier=dict(domain='integer box J<=v<=I with other coordinates fixed at J',pareto_vectors=[e['J']],
                                  proof='Every active coordinate increment by one opens a row at J. Coordinatewise monotonicity makes every other point in this box infeasible.',
                                  NOT_claimed='Global Pareto frontier permitting decreases below J or varying fixed coordinates.'),
                halt_reason=e['known_pair_diagnosis'],production_started=False,
                old_dossier_status=['INDIVIDUAL_ONLY','SUPERSEDED_FOR_PRODUCTION_TARGETS'])
    save('r171/certs/joint_dossier_codex_171.json',report)
    print(json.dumps({k:report[k] for k in ['status','endpoint_assignments','feasible_assignments','highest_interaction_order','minimal_hyperedges','scalar_assignments_rechecked','genuine_distinct_basis_cells','jointly_usable','remaining_joint_safe_bounds']},indent=1))

if __name__=='__main__':main()
