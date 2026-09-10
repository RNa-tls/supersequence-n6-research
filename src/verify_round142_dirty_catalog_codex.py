"""Round142 independent append-tail dirty-joint catalogue.

The producer enumerates removed-prefix permutations, not endpoint overlaps.
All 873 normalized connector variants of weights1..6 are examined; the719
distinct nonidentity targets retain their minimum-weight connector.  Variants
are also kept, because a nonminimal weight6 connector can be clean although
the minimum connector is dirty.  No global continuation search is performed.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sigma(p):
    return p[1:] + p[:1]


def E(p):
    return p[1:-1] + p[:1] + p[-1:]


def cyclic(p, move):
    found = [p]
    q = move(p)
    while q != p:
        assert q not in found
        found.append(q)
        q = move(q)
    return found


def hx(p):
    return min(cyclic(p, sigma))


def oq(p):
    return min(cyclic(p, E))


def hidden(raw, n):
    universe = set(range(n))
    return [(i, tuple(raw[i:i+n])) for i in range(1, len(raw)-n)
            if set(raw[i:i+n]) == universe]


def encode(p):
    return ''.join(map(str, p))


def catalog(n=6):
    source = tuple(range(n))
    full_entry = sigma(source)
    all_perms = tuple(itertools.permutations(source))
    hex_reps = sorted({hx(p) for p in all_perms})
    q_reps = sorted({oq(p) for p in all_perms})
    hi = {p: i for i, p in enumerate(hex_reps)}
    qi = {p: i for i, p in enumerate(q_reps)}

    def geom(p):
        q = oq(p)
        return dict(permutation=encode(p), hexagon=hi[hx(p)],
                    orbit=qi[q], phase=cyclic(q, E).index(p))

    variants, by_target = [], {}
    for weight in range(1, n+1):
        # Every shift-w endpoint permutation must append exactly the removed
        # prefix symbols. This is complete even for no-overlap w=n.
        for tail in itertools.permutations(source[:weight]):
            raw = source + tail
            target = raw[-n:]
            assert set(target) == set(source)
            unseen = hidden(raw, n)
            clean = not unseen
            if weight == 1:
                kind = 'CLEAN_SIGMA'
            elif weight == 2:
                kind = 'DIRTY_SIGMA2' if tail == source[:2] else 'CLEAN_TAU'
            elif weight == 3 and tail == source[:3]:
                kind = 'DIRTY_SIGMA3'
            elif weight == 3 and not clean:
                kind = 'DIRTY_W3_MIXED_' + encode(tail)
            elif weight == 3:
                kind = 'CLEAN_W3_' + encode(tail)
            else:
                kind = ('CLEAN_' if clean else 'DIRTY_') + 'HEAVY_W' + str(weight)
            row = dict(source=geom(source), spliced_full_entry=geom(full_entry),
                       weight=weight, tail=encode(tail), literal_connector=encode(raw),
                       target=geom(target), dirty_type=kind, clean=clean,
                       hidden_windows=[dict(offset=i, **geom(p)) for i, p in unseen],
                       repeat_charge_if_actual_consecutive_first_occurrences=len(unseen),
                       repeat_charge_domain='ACTUAL_LITERAL_CONNECTOR_WITH_NO_INTERMEDIATE_FIRST_OCCURRENCE',
                       source_target_same_hexagon=hx(source) == hx(target),
                       source_target_same_orbit=oq(source) == oq(target),
                       spliced_entry_target_same_hexagon=hx(full_entry) == hx(target),
                       spliced_entry_target_same_orbit=oq(full_entry) == oq(target),
                       clean_tau_successor_identity=target == E(full_entry),
                       spliced_full_pass_endpoint=encode(source),
                       splice_joint_endpoint_preserved=True,
                       component_effect='GLOBAL_INCIDENCE_DEPENDENT_NOT_DETERMINED_BY_LOCAL_TRIPLE',
                       identity_target=target == source)
            variants.append(row)
            if target != source:
                by_target.setdefault(target, row)
    assert len(variants) == sum(math.factorial(i) for i in range(1, n+1))
    assert len(by_target) == math.factorial(n)-1
    selected = [by_target[p] for p in sorted(by_target)]
    for row in selected:
        h = [v['permutation'] for v in row['hidden_windows']]
        assert len(h) == len(set(h))
        assert row['source']['permutation'] not in h and row['target']['permutation'] not in h
    # A second direct endpoint overlap check is verification only: it does not
    # generate the catalogue and does not import the previous round's code.
    for p, row in by_target.items():
        possible = [w for w in range(1, n+1) if source[w:] == p[:-w]]
        assert row['weight'] == min(possible)
    variant_by_target = {}
    for row in variants:
        if row['identity_target']:
            continue
        variant_by_target.setdefault(row['target']['permutation'], []).append(row)
    clean_longer = []
    for row in selected:
        clean_choices = [r for r in variant_by_target[row['target']['permutation']] if r['clean']]
        if not row['clean'] and clean_choices:
            r = min(clean_choices, key=lambda t: t['weight'])
            clean_longer.append(dict(target=row['target']['permutation'],
                                     dirty_minimum_weight=row['weight'],
                                     minimum_clean_weight=r['weight'],
                                     dirty_connector=row['literal_connector'],
                                     clean_connector=r['literal_connector']))
    return dict(n=n, source=encode(source), variant_count=len(variants),
                normalized_nonidentity_targets=len(selected),
                minimum_rows=selected, all_actual_tail_variants=variants,
                minimum_clean_longer_than_metric=clean_longer,
                by_weight=[dict(weight=w, targets=sum(r['weight'] == w for r in selected),
                                clean=sum(r['weight'] == w and r['clean'] for r in selected),
                                dirty=sum(r['weight'] == w and not r['clean'] for r in selected))
                           for w in range(1, n+1)],
                dirty_type_counts=dict(sorted(Counter(r['dirty_type'] for r in selected).items())),
                clean_actual_variant_count=sum(r['clean'] for r in variants if not r['identity_target']))


def renaming_check(data):
    """Literal check of every720source x719target, not an empirical walk census."""
    n = data['n']
    checked = 0
    for source in itertools.permutations(range(n)):
        for row in data['minimum_rows']:
            tail = tuple(source[int(i)] for i in row['tail'])
            raw = source + tail
            target = tuple(source[int(i)] for i in row['target']['permutation'])
            assert raw[-n:] == target
            expected = [(r['offset'], tuple(source[int(i)] for i in r['permutation']))
                        for r in row['hidden_windows']]
            assert hidden(raw, n) == expected
            assert sigma(source)[-1:] + sigma(source)[:-1] == source
            if row['dirty_type'] == 'CLEAN_TAU':
                assert target == E(sigma(source))
            checked += 1
    return dict(source_count=math.factorial(n), pairs=checked, failures=0)


def assemble(order):
    n = len(order[0])
    text = order[0]
    for a, b in zip(order, order[1:]):
        shift = next(w for w in range(1, n+1) if a[w:] == b[:-w])
        text += b[-shift:]
    return text


def first_occurrence_check(word, n):
    universe = set(itertools.permutations(range(n)))
    raw = tuple(map(int, word))
    literal = [(i, raw[i:i+n]) for i in range(len(raw)-n+1) if raw[i:i+n] in universe]
    seen = set()
    first = []
    for i, p in literal:
        if p not in seen:
            first.append((i, p))
            seen.add(p)
    assert seen == universe
    order = [p for i, p in first]
    # Audit both actual first-occurrence gaps and metric-renormalized gaps.
    outputs = []
    for mode in ('actual_first_occurrence_gaps', 'minimum_overlap_gaps'):
        weights = [b[0]-a[0] for a, b in zip(first, first[1:])] if mode.startswith('actual') else [
            next(w for w in range(1, n+1) if a[w:] == b[:-w]) for a, b in zip(order, order[1:])]
        starts = [0] + [i+1 for i, w in enumerate(weights) if w != 1]
        ends = starts[1:] + [len(order)]
        groups = [order[a:b] for a, b in zip(starts, ends)]
        entries = [g[0] for g in groups]
        entry_index = {p: i for i, p in enumerate(entries)}
        assert len(entry_index) == len(entries)
        assert all(g == cyclic(g[0], sigma)[:len(g)] for g in groups)
        nu = [entry_index[sigma(g[-1])] for g in groups]
        assert sorted(nu) == list(range(len(groups)))
        lengths = Counter()
        for g in groups:
            lengths[hx(g[0])] += len(g)
        assert len(lengths) == math.factorial(n-1) and set(lengths.values()) == {n}
        joins = [weights[e-1] for e in ends[:-1]]
        S = sum(w >= 3 for w in joins)
        H = sum(max(w-3, 0) for w in joins)
        P = len(groups)
        L = n + sum(weights)
        assert L == n + math.factorial(n) + P - 2 + S + H
        outputs.append(dict(mode=mode, H1_partition=True, H2_nu_permutation=True,
                            H3_resource_identity=True, selected_length=L,
                            P=P, G=P-math.factorial(n-1), S=S, H=H,
                            F=sum(v > i for i, v in enumerate(nu))))
    return dict(n=n, literal_length=len(raw), literal_repeats=len(literal)-len(first), modes=outputs)


def small_corpus_checks():
    path = ROOT/'outputs/rr_round141_nr6_foundation_codex.json'
    old = json.loads(path.read_text())
    orders = [row['start_order'] for row in old['graph']['single_vertex']['certificates']]
    assert len(orders) == 720 and len({tuple(o) for o in orders}) == 720
    words = sorted({assemble([tuple(map(int, p)) for p in order]) for order in orders})
    rows = [first_occurrence_check(encode(w), 3) for w in words]
    trap = old['nr4_bounded_control']['minimal_found']['word']
    rows.append(first_occurrence_check(trap, 4))
    return dict(scope='PRESERVED_ALL_S3_HAMILTON_SPELLINGS_AND_ONE_PRESERVED_NR4_TRAP',
                source_path=str(path.relative_to(ROOT)),
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                S3_distinct_literal_words=len(words), NR4_controls=1,
                checked_literal_words=len(rows), failures=0,
                repeat_bearing=sum(r['literal_repeats'] > 0 for r in rows),
                mode_checks=2*len(rows), records=rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='outputs/rr_round142_dirty_catalog_codex.json')
    ap.add_argument('--skip-all-renamings', action='store_true')
    args = ap.parse_args()
    source = Path(__file__).read_bytes()
    rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    committed = subprocess.check_output(['git', 'show', 'HEAD:'+rel], cwd=ROOT)
    assert source == committed, 'Commit exact source before producing certificate.'
    t0 = time.perf_counter()
    data = catalog()
    data.update(schema='round142-independent-dirty-joint-catalog-v1',
                source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                committed_source_sha256=hashlib.sha256(committed).hexdigest(),
                runtime_source_sha256=hashlib.sha256(source).hexdigest(),
                executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                argv=[sys.executable, *sys.argv], capped=False,
                scope='Complete normalized minimal connector catalogue; no global history realizability claimed.',
                no_repeat_assumption=False,
                caveat='Hidden repeat charge requires actual consecutive first-occurrence connector; metric recompression alone does not preserve its history.',
                first_occurrence_controls=small_corpus_checks())
    data['all_source_renaming_check'] = dict(status='NOT_RUN') if args.skip_all_renamings else renaming_check(data)
    data['deterministic_digest'] = hashlib.sha256(json.dumps(
        {k: data[k] for k in ('minimum_rows', 'all_actual_tail_variants', 'first_occurrence_controls')},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    data['seconds'] = time.perf_counter()-t0
    (ROOT/args.output).write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps({k: data[k] for k in ('variant_count', 'normalized_nonidentity_targets', 'by_weight',
                                           'clean_actual_variant_count', 'all_source_renaming_check')}))


if __name__ == '__main__':
    main()
