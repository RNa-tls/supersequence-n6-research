"""Independent finite direct-clean distance audit for NR-UNIVERSAL Route A.

Only 7,776 suffix vertices / 46,656 character edges at n=6. No covering
continuation search. The closed formula and the suffix BFS share no overlap
or endpoint-distance implementation.
"""
from collections import Counter, deque
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def window_list(word, n):
    return [(i, word[i:i+n]) for i in range(len(word)-n+1)
            if len(set(word[i:i+n])) == n]


def formula_catalog(n):
    p = ''.join(map(str, range(n)))
    rows = {}
    for tup in itertools.permutations(p):
        q = ''.join(tup)
        if p == q:
            continue
        k = max(k for k in range(n) if not k or p[-k:] == q[:k])
        word = p+q[k:]
        occ = window_list(word, n)
        h = len(occ)-2
        d = n-k
        joined = p+q
        j = max(j for j in range(n) if p[j] != q[j])
        spacer_word = p+p[j]+q
        assert window_list(spacer_word, n) == [(0, p), (n+1, q)]
        if not h:
            c, witness = d, word
        elif len(window_list(joined, n)) == 2:
            c, witness = n, joined
        else:
            c, witness = n+1, spacer_word
        assert c-d <= n-2
        rows[q] = dict(source=p, target=q, geodesic_word=word, geodesic_gap=d,
                       intermediate_windows=occ[1:-1], hidden_count=h,
                       clean_cost=c, clean_witness=witness, extra_cost=c-d,
                       rightmost_mismatch=j, spacer=p[j], spacer_witness=spacer_word)
    return rows


def independent_suffix_bfs(n):
    """First permutation windows are absorbing; all non-permutation suffix
    transitions are exhausted. No shortest-overlap or formula helper called.
    """
    letters = ''.join(map(str, range(n)))
    targets = {''.join(x) for x in itertools.permutations(letters)}
    initial = letters[1:]
    tails = {initial: ''}
    todo = deque([initial])
    reached = {}
    edges = 0
    while todo:
        suffix = todo.popleft()
        for x in letters:
            edges += 1
            full = suffix+x
            tail = tails[suffix]+x
            if full in targets:
                if full != letters and full not in reached:
                    reached[full] = tail
                continue
            child = full[1:]
            if child not in tails:
                tails[child] = tail
                todo.append(child)
    return reached, dict(suffix_vertices=len(tails), examined_edges=edges,
                         reached_endpoints=len(reached), exhausted=True, capped=False)


def transport_clean(a, b, rows):
    """Transport only by simultaneous value-renaming, not orbit relabeling."""
    inv = {x: str(i) for i, x in enumerate(a)}
    normalized = ''.join(inv[x] for x in b)
    row = rows[normalized]
    tail = row['clean_witness'][len(a):]
    return ''.join(a[int(x)] for x in tail)


def local_counterexample(row, rows):
    n = len(row['source'])
    old = [p for _, p in row['intermediate_windows']]
    assert old and len(set(old)) == len(old)
    selected = old+[row['source']]
    prefix = selected[0]
    for a, b in zip(selected, selected[1:]):
        prefix += transport_clean(a, b, rows)
    assert [p for _, p in window_list(prefix, n)] == selected
    word = prefix+row['geodesic_word'][n:]
    after = [p for i, p in window_list(word, n) if i > len(prefix)-n]
    assert after == old+[row['target']]
    assert set(after)-set(selected) == {row['target']}
    return dict(prefix=prefix, appended_tail=row['geodesic_word'][n:], word=word,
                previously_covered=selected, newly_covered=[row['target']],
                repeated_ear_windows=old, feasible_repeat_cost=row['geodesic_gap'],
                exact_repeat_free_cost=row['clean_cost'], strict_gap=row['extra_cost'])


def trim_catalog(rows):
    p = next(iter(rows.values()))['source']
    n = len(p)
    q = p[-1:]+p[:-1]
    records = []
    for r in rows.values():
        if r['hidden_count']:
            continue
        t = r['target']
        old = q+p[-1:]+r['geodesic_word'][n:]
        assert old[n-1:n-1+n] != ''
        overlap = max(k for k in range(n+1) if not k or q[-k:] == t[:k])
        new = q+t[overlap:]
        strict = len(new) < len(old)
        assert strict == (r['geodesic_gap'] == n)
        if not strict:
            assert new == old
        records.append(dict(target=t, exit_weight=r['geodesic_gap'], before=old,
                            after=new, strict=strict, no_op=old == new))
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output')
    args = ap.parse_args()
    controls = []
    n6 = None
    for n in range(3, 7):
        table = formula_catalog(n)
        independent, stats = independent_suffix_bfs(n)
        assert set(table) == set(independent)
        for q, tail in independent.items():
            assert table[q]['clean_cost'] == len(tail)
            assert len(window_list(table[q]['source']+tail, n)) == 2
        controls.append(dict(n=n, **stats,
                             clean_cost_histogram=dict(sorted(Counter(r['clean_cost'] for r in table.values()).items()))))
        if n == 6:
            n6 = table
    historical_path = ROOT/'outputs/rr_round141_nr_geodesic_templates_codex.json'
    historical = json.loads(historical_path.read_text())
    assert len(historical['table']) == 719
    for row in historical['table']:
        actual = n6[row['target']]
        assert row['word'] == actual['geodesic_word']
        assert row['gap'] == actual['geodesic_gap']
        assert row['hidden_count'] == actual['hidden_count']
    dirty = [r for r in n6.values() if r['hidden_count']]
    assert len(dirty) == 322
    for row in dirty:
        row['literal_boundary_counterexample'] = local_counterexample(row, n6)
    # One explicit FULL covering extension, to rule out an empty local domain.
    counter = n6['234501']['literal_boundary_counterexample']
    full = counter['word']
    chosen = set(p for _, p in window_list(full, 6))
    for q in ['012345']+sorted(n6):
        if q not in chosen:
            full += transport_clean(full[-6:], q, n6)
            chosen.add(q)
    occ = window_list(full, 6)
    assert len(chosen) == 720 and len(occ) == 721
    trims = trim_catalog(n6)
    data = dict(schema='round142-route-a-direct-clean-v1',
                source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                runtime_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                input_sha256={str(historical_path.relative_to(ROOT)): hashlib.sha256(historical_path.read_bytes()).hexdigest()},
                completed=True, capped=False, continuation_search=False,
                scope='Direct clean connector theorem, complete finite local audit; NOT NR-UNIVERSAL(6)',
                controls=controls, table=list(n6.values()),
                clean_geodesics=397, dirty_geodesics=322,
                dirty_extra_cost_histogram=dict(sorted(Counter(r['extra_cost'] for r in dirty).items())),
                hidden_count_histogram=dict(sorted(Counter(r['hidden_count'] for r in dirty).items())),
                penalty_le_hidden_failures=[r['target'] for r in dirty if r['extra_cost'] > r['hidden_count']],
                seven_zero_credit_templates=[dict(target=r['target'], hidden=n6[r['target']]['hidden_count'],
                    gap=n6[r['target']]['geodesic_gap'], clean_cost=n6[r['target']]['clean_cost'],
                    extra_cost=n6[r['target']]['extra_cost']) for r in historical['zero_credit_repeating_templates']],
                trim_records=trims, trim_counts=dict(no_op=sum(r['no_op'] for r in trims),
                    strict=sum(r['strict'] for r in trims)),
                complete_cover_counterexample=dict(word=full, length=len(full), permutation_occurrences=len(occ),
                    distinct_permutations=len(chosen), repeated_count=1, prefix=counter['word']),
                NR_UNIVERSAL_6='UNPROVED', boundary_fixed_nonincreasing_clean_replacement='REFUTED')
    text = json.dumps(data, indent=2)+'\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps(dict(verified=True, controls=controls, dirty_extra_costs=data['dirty_extra_cost_histogram'],
                         penalty_le_hidden_failures=len(data['penalty_le_hidden_failures']),
                         trim_counts=data['trim_counts'], full_cover_length=len(full))))


if __name__ == '__main__':
    main()
