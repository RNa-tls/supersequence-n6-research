"""Read-only accepted-DAG audit and historical-fallback-disabled census snapshot.

Does not replay immutable trees or alter the production driver's base manifest.
The complete J census is conditional until all 35 required values are backed.
"""
import argparse
import collections
import hashlib
import json
import bulk_j171 as W


def audit(output):
    raw = (W.ROOT / W.MAN).read_bytes()
    m = json.loads(raw)
    f, refs, dep, env, base = W.initial()
    refs, dep = W.add_accepted(refs, m['accepted'])
    backed = sorted(c for c, j in f['J'].items()
                    if W.key(c) in dep and dep[W.key(c)][0] <= j)
    assert len(backed) == m['certified'] == 6 + len(m['accepted'])
    assert len(f['J']) == 35 and m['remaining'] == 35 - len(backed)
    residual = []
    for t in m['targets']:
        if t['cell'] in backed:
            assert t['status'] == 'CERTIFIED'
            continue
        attempts = t['attempts']
        for a in attempts:
            row = W.load(W.BASE + 'jobs/' + a['id'] + '.json')
            assert row['nodes'] == a['nodes'] and row['status'] == a['status']
            assert row['bound'] == f['J'][t['cell']]
        k = W.key(t['cell'])
        dominators = [(v[0],W.text(q)) for q,v in dep.items()
                      if all(x>=y for x,y in zip(q,k))]
        analytic = W.G.R.UBFALL + sum(k[2:5])
        best = min([analytic] + [v for v,c in dominators])
        residual.append(dict(cell=t['cell'],required_bound=t['bound'],
            strongest_exact_genuine_bound=dep.get(W.key(t['cell']), (None,))[0],
            strongest_P1_or_analytic_bound=best,
            strongest_P1_dominators=[c for v,c in dominators if v==best],
            cost_lower_bounds_by_environment={str(e):max(a['cap'] for a in attempts if a['environment_count']==e and a['status']=='DEFERRED')
                for e in sorted({a['environment_count'] for a in attempts if a['status']=='DEFERRED'})},
            attempts=attempts,
            reason='No dual-accepted certificate at required J; caps are environment-specific deferrals.'))
    nodes = collections.Counter()
    for t in m['targets']:
        for a in t['attempts']:
            nodes['production' if a['status']=='CERTIFIED' else 'research_cap_attempts'] += a['nodes']
    restricted = W.ClosedSystem()
    restricted.value_of = lambda k: None
    restricted.chain_tab = {k:None for k in restricted.chain_tab}
    restricted.piece_tab = {k:None for k in restricted.piece_tab}
    restricted.apply(set(dep),values={k:v[0] for k,v in dep.items()})
    verdicts = restricted.verdicts()
    exposed = W.load(W.PREFIX+'joint_endpoint_codex_171.json')['rows']
    actual_exposed = collections.Counter(verdicts[(r['t'],tuple(r['coordinates']))] for r in exposed)
    out = dict(manifest_snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=W.sha('r171/src/audit_bulk_progress_j171.py'),
        driver_sha256=W.sha(W.DRIVER), J_sha256=f['J_sha256'],
        backed_cells=backed, certified=len(backed), remaining=residual,
        accepted_dag_hashes_valid=True, dual_report_rows_and_histograms_agree=True,
        verification_mode='Hash/version-bound prior dual acceptance; no new tree replay claimed.',
        nodes_completed_attempts=dict(nodes),
        interrupted_attempts_with_unknown_nodes=[r for t in m['targets'] for r in t.get('interruptions',[])],
        research_cost_scope='Completed cap attempts only; interrupted generation with unknown node count is additional unquantified cost.',
        independence_restricted_census=dict(tally=dict(collections.Counter(verdicts.values())),
            exposed_tally=dict(actual_exposed),granted_genuine_cells=len(dep),
            unbacked_J_not_granted=True,historical_basis_fallback=False),
        census_scope='Genuine accepted cells only; unbacked J entries are not granted.',
        historical_capacity_fallback=False)
    W.atomic(output,out)
    print(json.dumps(dict(certified=len(backed),remaining=len(residual),nodes=dict(nodes),census=out['independence_restricted_census'])),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    audit(p.parse_args().output)
