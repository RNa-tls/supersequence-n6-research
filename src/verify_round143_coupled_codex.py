"""Independent literal replay and threshold application of coupled capacities.

No capacity recurrence is imported. Capped searches supply witnesses only,
never upper bounds. A is exact; only b and D can be relaxed upwards.
"""
import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS = list(itertools.permutations(range(6)))


def sigma(p):
    return p[1:] + p[:1]


def orbit(p):
    return min(p[s:5] + p[:s] + p[5:] for s in range(5))


def hexagon(p):
    return min(p[s:] + p[:s] for s in range(6))


def replay(entries):
    if not entries:
        return None
    words = [WORDS[i] for i in entries]
    assert words[0] == tuple(range(6))
    assert len(set(words)) == len(words), 'Repeated entry port'
    opened = {orbit(words[0])}
    covered = {hexagon(words[0])}
    a = b = 0
    kinds = []
    for source, target in zip(words, words[1:]):
        # Derive the shortest literal full-pass connector, not C lookup tables.
        end = source[-1:] + source[:-1]
        weight = next(w for w in range(1, 7) if end[w:] == target[:6-w])
        assert weight in (2, 3)
        raw = end + target[-weight:]
        hidden = [raw[j:j+6] for j in range(1, weight)
                  if len(set(raw[j:j+6])) == 6]
        free = weight == 2 and not hidden
        dirty_a = weight == 2 and hidden == [source]
        if weight == 3:
            assert len(hidden) <= 1, 'Same-hex dirty B is not in SIGMA model'
        if dirty_a:
            assert target == sigma(source)
            assert hexagon(target) == hexagon(source)
            a += 1
        else:
            assert hexagon(target) not in covered, 'Unpaid repeated hex'
        if not free and orbit(target) in opened:
            b += 1
        opened.add(orbit(target))
        covered.add(hexagon(target))
        kinds.append('A' if dirty_a else ('E' if free else 'W3'))
    p = len(entries)
    assert p - len(covered) == a
    return dict(P=p, O=len(opened), D=5*len(opened)-p, A=a, b=b,
                kinds=kinds, literal_entries_sha256=hashlib.sha256(
                    json.dumps(words, separators=(',', ':')).encode()).hexdigest())


def validate_capacity_file(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    assert data['schema'] not in ('round143-paired-exact-P-v1','round143-paired-general-exact-P-v1'), 'Exact-P decisions are not capacity maxima'
    cells = []
    for row in data['rows']:
        first, second = row['producer'], row['independent']
        assert first['mode'] == second['mode'] == 'AB', 'Restricted A-only alphabet cannot bound the complete marked model'
        assert not any(x.get('suffix_bound_enabled',False) for x in (first,second)), 'Threshold-pruned results are not scalar capacities'
        # Earlier AB certificates predate the optional SIGMA alphabet.
        # Only an explicit ordinary mode justifies interpreting absent A as 0.
        if 'A_exact' not in first or 'A_exact' not in second:
            assert first['mode'] == second['mode'] == 'AB'
            assert all('SIGMA:' not in str(x.get('argv',[])) for x in (first,second))
        A = first.get('A_exact',0)
        assert A == second.get('A_exact',0)
        assert first['b'] == second['b'] == row['b']
        assert first['D'] == second['D'] == row['D']
        for result in (first, second):
            witness = result['witness']
            entries = witness['entries'] if isinstance(witness, dict) else witness
            check = replay(entries)
            assert len(entries) == result['max_passes']
            if check:
                assert check['A'] == A and check['b'] <= row['b'] and check['D'] <= row['D']
        complete = all(x['completed'] and not x['capped'] for x in (first, second))
        assert complete == row['complete']
        if complete:
            for field in ('max_passes', 'accepted_prefixes', 'endpoint_max_passes', 'rich_endpoint_max_passes'):
                if field == 'rich_endpoint_max_passes' and field not in first:
                    assert field not in second
                    continue
                assert first[field] == second[field], (path, A, row['b'], row['D'], field)
            cells.append(dict(A=A, b=row['b'], D=row['D'], upper=first['max_passes'],
                              endpoints=first['endpoint_max_passes'],
                              source=path.relative_to(ROOT).as_posix()))
    return cells, hashlib.sha256(raw).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--output', default='outputs/rr_round143_coupled_envelopes_codex.json')
    args = ap.parse_args()
    table, hashes = [], {}
    for name in args.inputs:
        cells, sha = validate_capacity_file(ROOT/name)
        table.extend(cells)
        hashes[name] = sha
    base = ROOT/'outputs/rr_round143_general_endpoint_corrected_codex.json'
    hashes[base.relative_to(ROOT).as_posix()] = hashlib.sha256(base.read_bytes()).hexdigest()
    out = json.loads(base.read_text())
    for r in out['rows']:
        if r['Z'] or r['H']:
            continue
        # Current theorem applies only to the ONE nonpure component, no heavy.
        options = [x for x in table if x['A'] == r['D2'] and x['b'] >= r['Bstar']
                   and x['D'] >= 5*r['k']-r['G']]
        if not options:
            continue
        choice = min(options, key=lambda x: x['upper'])
        r['coupled_capacity'] = choice
        if r['upper'] is None or choice['upper'] < r['upper']:
            r['upper'] = choice['upper']
            r['status'] = ('STRICT' if r['upper'] < r['P_required'] else
                           'EQUALITY' if r['upper'] == r['P_required'] else 'OPEN_CAPACITY')
    out.update(schema='round143-coupled-sigma-envelopes-v1', input_sha256=hashes,
               coupled_domain='Z=H=0 ONLY; A exact; b,D upper budgets',
               independently_replayed_maximum_witnesses=True)
    out['counts'] = {str(L):dict(Counter(r['status'] for r in out['rows'] if r['L']==L))
                     for L in (869,870,871)}
    out['threshold_closed'] = {str(L):all(r['status']=='STRICT' for r in out['rows'] if r['L']==L)
                               for L in (869,870,871)}
    (ROOT/args.output).write_text(json.dumps(out, indent=2)+'\n', newline='\n')
    print(json.dumps(out['counts']))


if __name__ == '__main__':
    main()
