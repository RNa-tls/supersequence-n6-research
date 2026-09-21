"""Promote only the dual-accepted tree and report measured, not projected, cost."""
from production_j171 import ROOT, PREFIX, load, save, sha, canonical, key, text, VERSIONS

def main():
    r=load(PREFIX+'helper_decision_codex_171.json');f=load(PREFIX+'production_J_codex_171.json')
    assert r['verdict']=='ROUND171_HELPER_TARGET_CERTIFIED'
    assert r['driver_sha256']==sha('r171/src/helper_decision_j171.py')
    assert r['environment_sha256']==f['environment_sha256']
    env=load(PREFIX+'production_environment_codex_171.json')
    assert canonical(env)==f['environment_sha256']
    assert env['versions']=={p:sha(p) for p in VERSIONS}
    c=r['selected'];m=r['certificate'];a=r['verifier_A'];b=r['verifier_B']
    assert sha(m['path'])==m['sha256']==a['sha256']==b['sha256']
    assert a['ok'] and b['ok'] and r['histogram_mismatches']==0
    assert a['nodes']==b['nodes']==b['hist_checks']==m['nodes']
    assert [(x['cell'],x['cap']) for x in a['rows']]==[(c,f['J'][c])]
    assert [(x['cell'],x['cap']) for x in b['rows']]==[(c,f['J'][c])]
    backed={x['cell'] for x in f['dossier'] if x['value_role']=='GENUINELY_BACKED_VALUE'}
    assert len(backed)==5 and c not in backed;backed.add(c)
    remaining=sorted(set(f['J'])-backed);assert len(remaining)==29
    ctrl=r['direct_control'];assert ctrl['status']=='DEFERRED' and ctrl['nodes']==ctrl['cap']+1
    assert ctrl['target']==f['J'][c]+1 and not ctrl['with_helper']
    total=r['helper_investment']+m['nodes'];saving=ctrl['cap']+1-total;assert saving>0
    stage=sum(x['nodes'] for x in r['stages']);assert stage==r['cumulative_escalation_nodes']
    probe=sum(x[y]['nodes'] for x in r['probe'] for y in ['direct','helper'])
    cost=dict(target=c,bound=f['J'][c],search_target=f['J'][c]+1,
        direct_cost_strict_lower_bound=ctrl['cap'],helper_target_nodes=m['nodes'],
        helper_investment_nodes=r['helper_investment'],helper_plus_target_nodes=total,
        net_saving_integer_lower_bound=saving,net_saving_exact=None,
        staged_attempted_visits=stage,paired_probe_attempted_visits=probe,
        direct_control_attempted_visits=ctrl['nodes'],new_round_attempted_visits=stage+probe+ctrl['nodes'],
        includes_restarted_prefixes=True,excludes_prior_round_search_and_verifier_work=True,
        observation_wrapper_tests='2/2 PASS; old tests not rerun',
        report_sha256=sha(PREFIX+'helper_decision_codex_171.json'))
    save(PREFIX+'helper_decision_cost_codex_171.json',cost)
    save(PREFIX+'production_progress_codex_171.json',dict(
        new_load_bearing_certificates=[dict(cell=c,cap=f['J'][c],**m)],
        jointly_usable=len(backed),remaining=len(remaining),backed_cells=sorted(backed),
        remaining_historical_load_bearing_dependencies=remaining,
        new_helpers=1,helper_counts_as_load_bearing=False,J_sha256=f['J_sha256'],
        J_census=r['independence_restricted_J_census'],source_versions=env['versions'],
        dual_verification_report=PREFIX+'helper_decision_codex_171.json',
        dual_verification_report_sha256=cost['report_sha256'],full_independence=False,
        verdict='ROUND171_HELPER_TARGET_CERTIFIED'))
    lines=['# Round 171 — one helper / one target production decision','',
        'Base: `424953a3b86f3361baf4e059e2f784dd1feba6c5`, `codex/round171-joint-audit`.',
        'No endpoint rescan, historical re-audit, new helper generation or other large target search.',
        '', '## Matched 200k measurements','',
        'The old files omitted fallback/first-prune telemetry. Only these six bounded runs were repeated to fill it.',
        'Every run deferred at 200,000 processed / 200,001 attempted visits. `(p)` counts are leaf occurrences.',
        '', '| Cell | J / target | Direct fallback | Helper fallback | Direct / helper (p) leaves | New-helper essential (p) | First depth |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for x in r['probe']:
        d,h=x['direct'],x['helper']
        lines.append(f"| ({x['cell'].replace('|', ',')}) | {h['J']} / {h['target']} | {d['fallback_fraction']:.6%} | {h['fallback_fraction']:.6%} | {d['useful_p_leaf_count']:,} / {h['useful_p_leaf_count']:,} | {h['new_helper_essential_p_leaves']:,} | {h['first_new_helper_prune_depth']} |")
    lines += ['', '## Selection and staged execution','',
        'Selected `'+c+'`: the only target with positive observed counterfactual helper-prune effect.',
        'Selection clarification: the second target has a lower **absolute** fallback but zero measured helper effect.',
        'We prioritized measured effect before applying fallback/count/depth ranking; this is not the literal absolute-fallback-only ordering.',
        'At a new-helper-essential leaf, the direct certified upper bound would not prune the same state.',
        'Different pruned traversals are not identical samples; leaf-count ratios are not cost ratios.',
        '', '| Cap | Actual attempted visits | Result |','|---:|---:|---|']
    for x in r['stages']:lines.append(f"| {x['cap']:,} | {x['nodes']:,} | {x['status']} |")
    lines += ['',f'Staged restarts actually consumed **{stage:,}** visits, not just the final tree size.',
        f'Paired probes: {probe:,}; direct control: {ctrl["nodes"]:,}; current-round total: **{stage+probe+ctrl["nodes"]:,}**.',
        'This total excludes previous-round work and validation replay. It is not the reusable certificate cost.',
        '', '## Economics','',
        f'- Direct route: **>{ctrl["cap"]:,}** nodes; capped, not refuted.',
        f'- Helper-assisted target tree: **{m["nodes"]:,}** nodes.',
        f'- Genuine helper investment: **{r["helper_investment"]:,}** nodes.',
        f'- Reusable helper + target proof: **{total:,}** nodes.',
        f'- Certified-cost saving lower bound: **at least {saving} nodes**. Exact saving and percentage remain unknown.',
        '', 'The control was deliberately stopped just above break-even. This proves positive amortized node benefit, not a large speedup.',
        'Exploration/restarts are sunk measurement work, not silently charged as zero and not included in that reusable-proof comparison.',
        '', '## Certification and scope','',
        f'A ACCEPT / B ACCEPT; both cap {f["J"][c]}, nodes {m["nodes"]:,}; histogram mismatches 0.',
        f'Certificate: `{m["path"]}`; container SHA-256 `{m["sha256"]}`.',
        'All dependencies are genuine hash-pinned accepted predecessors, including the dual-accepted 122,892-node helper.',
        'Two new wrapper non-interference tests passed. Previously passing regression tests were not rerun.',
        'Independence-restricted census, with historical basis fallback disabled: 180 exposed strict rows; full tally 1,607 strict and two equality rows.',
        'The remaining 29 J bounds remain production assumptions in that sufficiency census, not certified theorems.',
        '**Genuine load-bearing progress: 6/35; remaining historical load-bearing dependencies: 29.**',
        'The frozen initial J dossier is unchanged; `production_progress_codex_171.json` is the updated progress ledger.',
        '', 'ROUND171_HELPER_TARGET_CERTIFIED','']
    (ROOT/'r171/HELPER_TARGET_DECISION_CODEX.md').write_text('\n'.join(lines),encoding='utf-8')
    print(cost)

if __name__=='__main__':main()
