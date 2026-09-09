"""Independent static completion check for the Round141 k4,G6 equality.

No capacity enumerator or earlier cover solver is imported.  Orbit and hexagon
incidence is regenerated from tuples.  The search is an exhaustive uncovered-
column recurrence, not a continuation search.  The distinct six-block condition
is equivalent to a <=6 cover followed by arbitrary distinct padding, because
there are at least six closed candidates.  Padding may overlap covered windows:
this is a necessary *static* model, not a claim of literal realizability.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERMS = tuple(itertools.permutations(range(6)))
INDEX = {p: i for i, p in enumerate(PERMS)}


def rotate(p):
    return p[1:] + p[:1]


def e_step(p):
    return p[1:5] + p[:1] + p[5:]


def orbit(p, step):
    out = [p]
    t = step(p)
    while t != p:
        assert t not in out
        out.append(t)
        t = step(t)
    return tuple(out)


def geometry():
    hexes = sorted({min(orbit(p, rotate)) for p in PERMS})
    qs = sorted({min(orbit(p, e_step)) for p in PERMS})
    hi = {h: i for i, h in enumerate(hexes)}
    qi = {q: i for i, q in enumerate(qs)}
    phex = tuple(hi[min(orbit(p, rotate))] for p in PERMS)
    pq = tuple(qi[min(orbit(p, e_step))] for p in PERMS)
    blocks = []
    for q in qs:
        hh = {phex[INDEX[p]] for p in orbit(q, e_step)}
        assert len(hh) == 5
        blocks.append(sum(1 << h for h in hh))
    assert len(hexes) == 120 and len(qs) == 144
    return phex, pq, tuple(blocks), tuple(INDEX[q] for q in qs)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def exact_k_cover(uncovered, candidates, blocks, k):
    """Complete finite decision; no caps and no stored-verdict input.

    At each call choose one uncovered column h. Any cover contains a block
    meeting h, so branching on all such blocks is exhaustive. Every choice
    strictly removes a column and uses one slot. Already selected blocks cannot
    meet a remaining column, hence cannot be chosen twice; memoization on
    (uncovered, slots) does not require a selected-set coordinate.
    """
    candidates = tuple(sorted(candidates))
    assert len(set(candidates)) == len(candidates)
    assert 0 <= k <= len(candidates)
    assert all(0 <= q < len(blocks) for q in candidates)
    incidence = {h: tuple(q for q in candidates if blocks[q] >> h & 1)
                 for h in range(uncovered.bit_length()) if uncovered >> h & 1}
    failures = set()
    prune = Counter()
    nodes = 0
    transcript = hashlib.sha256()

    def dfs(rem, slots):
        nonlocal nodes
        nodes += 1
        transcript.update(f'{rem:x}/{slots};'.encode())
        if not rem:
            return ()
        if slots == 0:
            prune['no_slots'] += 1
            return None
        if rem.bit_count() > 5 * slots:
            prune['five_hex_capacity'] += 1
            return None
        key = rem, slots
        if key in failures:
            prune['memoized_complete_failure'] += 1
            return None
        live_h = [h for h in incidence if rem >> h & 1]
        h = min(live_h, key=lambda v: (len(incidence[v]), v))
        if not incidence[h]:
            prune['uncoverable_hexagon'] += 1
            failures.add(key)
            return None
        # Optimistic bound: permit the same maximally useful block each slot.
        best_gain = max((blocks[q] & rem).bit_count() for q in candidates)
        if slots * best_gain < rem.bit_count():
            prune['optimistic_max_gain'] += 1
            failures.add(key)
            return None
        for q in sorted(incidence[h], key=lambda v: (-(blocks[v] & rem).bit_count(), v)):
            tail = dfs(rem & ~blocks[q], slots - 1)
            if tail is not None:
                assert q not in tail
                return (q,) + tail
        failures.add(key)
        return None

    started = time.perf_counter()
    cover = dfs(uncovered, k)
    witness = None
    if cover is not None:
        witness = list(cover)
        witness.extend(q for q in candidates if q not in cover)
        witness = witness[:k]
        assert len(witness) == len(set(witness)) == k
        union = 0
        for q in witness:
            assert q in candidates
            union |= blocks[q]
        assert uncovered & ~union == 0
    return dict(status='SAT' if witness is not None else 'UNSAT',
                witness=witness, nodes=nodes, memo_failures=len(failures),
                prune_counts=dict(sorted(prune.items())), capped=False,
                complete_finite_decision=True, transcript_sha256=transcript.hexdigest(),
                elapsed_seconds=time.perf_counter() - started)


def verify_chain(entries, expected_passes=96, expected_orbits=22):
    """Literal hex-simple full-pass light chain; no use of producer geometry."""
    phex, pq, blocks, q_representatives = geometry()
    assert len(entries) == expected_passes and len(set(entries)) == len(entries)
    hh = {phex[v] for v in entries}
    qq = {pq[v] for v in entries}
    assert len(hh) == expected_passes and len(qq) == expected_orbits
    seen_orbits = set()
    previous_q = None
    edge_weights = []
    raw = list(PERMS[entries[0]])
    for i, v in enumerate(entries):
        p = PERMS[v]
        q = pq[v]
        if q != previous_q:
            assert q not in seen_orbits
            seen_orbits.add(q)
        previous_q = q
        raw.extend(p[:5])
        if i + 1 == len(entries):
            break
        end = p[-1:] + p[:-1]
        target = PERMS[entries[i + 1]]
        gaps = [w for w in (2, 3) if end[w:] == target[:-w]]
        assert len(gaps) == 1
        w = gaps[0]
        if w == 2:
            assert target == e_step(p)
        else:
            assert pq[entries[i + 1]] != q
        local = end + target[-w:]
        assert all(len(set(local[j:j + 6])) < 6 for j in range(1, w))
        edge_weights.append(w)
        raw.extend(target[-w:])
    windows = [tuple(raw[i:i + 6]) for i in range(len(raw) - 5)
               if len(set(raw[i:i + 6])) == 6]
    assert len(windows) == len(set(windows)) == 6 * expected_passes
    covered = sum(1 << h for h in hh)
    uncovered = ((1 << 120) - 1) ^ covered
    assert uncovered.bit_count() == 120 - expected_passes
    return dict(covered=covered, uncovered=uncovered, open_orbits=qq,
                blocks=blocks, orbit_representatives=q_representatives,
                word=''.join(map(str, raw)), edge_weights=edge_weights)


def complete_chain(entries):
    d = verify_chain(entries)
    closed = [q for q in range(144) if q not in d['open_orbits']]
    assert len(closed) == 122
    out = exact_k_cover(d['uncovered'], closed, d['blocks'], 6)
    if out['status'] == 'SAT':
        selected = out['witness']
        union = 0
        for q in selected:
            union |= d['blocks'][q]
        excess = 30 - (union & ~d['covered']).bit_count()
        assert excess == 6
        out['excess'] = excess
        out['witness_orbit_representatives'] = [d['orbit_representatives'][q] for q in selected]
        out['witness_hexagons'] = [[h for h in range(120) if d['blocks'][q] >> h & 1] for q in selected]
    out.update(entries=entries, chain_sha256=digest(entries),
               literal_word_sha256=hashlib.sha256(d['word'].encode()).hexdigest(),
               covered_hexagons=[h for h in range(120) if d['covered'] >> h & 1],
               open_orbits=sorted(d['open_orbits']), deficit=14)
    return out


def controls():
    # Three closed-family known-SAT instances at different overlap densities.
    _, _, blocks, _ = geometry()
    rows = []
    for selected in [(0, 1, 2, 3, 4, 5), (0, 24, 48, 72, 96, 120), (1, 9, 22, 38, 77, 139)]:
        U = 0
        for q in selected:
            U |= blocks[q]
        r = exact_k_cover(U, range(144), blocks, 6)
        assert r['status'] == 'SAT'
        rows.append(dict(uncovered_hexagons=U.bit_count(), status=r['status'], nodes=r['nodes']))
    r = exact_k_cover((1 << 31) - 1, range(144), blocks, 6)
    assert r['status'] == 'UNSAT'
    rows.append(dict(guaranteed_unsat_31_hex=True, status=r['status'], nodes=r['nodes']))
    # Brute subsets independently validate the recurrence on tiny instances,
    # including padding, zero-gain candidates, and convergent histories.
    tiny = (0b0011, 0b0101, 0b1001, 0b1110, 0b0000)
    for U in range(16):
        for k in range(6):
            truth = any(U & ~__import__('functools').reduce(int.__or__, (tiny[q] for q in ss), 0) == 0
                        for ss in itertools.combinations(range(5), k))
            assert (exact_k_cover(U, range(5), tiny, k)['status'] == 'SAT') == truth
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default='outputs/rr_round141_extrema_codex.json')
    ap.add_argument('--output', default='outputs/rr_round141_completion_cover_codex.json')
    args = ap.parse_args()
    source = Path(__file__).read_bytes()
    rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + rel], cwd=ROOT)
    assert source == committed, 'Run only committed exact source.'
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    start = time.perf_counter()
    artifact = json.loads((ROOT / args.input).read_text())
    assert not artifact.get('capped', False)
    assert artifact.get('completed', True)
    extrema = [r for r in artifact['rows'] if r['target'] == 96 and r['deficit'] == 14]
    assert len(extrema) == 1 and not extrema[0]['capped']
    chains = extrema[0]['paths']
    assert chains and len({tuple(v) for v in chains}) == len(chains)
    decisions = [complete_chain(v) for v in chains]
    result = dict(schema='round141-independent-static-completion-cover-v1',
                  source_commit=commit, committed_source_sha256=hashlib.sha256(committed).hexdigest(),
                  runtime_source_sha256=hashlib.sha256(source).hexdigest(),
                  input_path=args.input, input_sha256=hashlib.sha256((ROOT / args.input).read_bytes()).hexdigest(),
                  controls=controls(), instances=decisions,
                  status_counts=dict(Counter(r['status'] for r in decisions)),
                  capped=False, elapsed_seconds=time.perf_counter() - start,
                  scope='Static necessary completion only; SAT is not literal realizability.')
    result['deterministic_digest'] = digest([{k: v for k, v in row.items() if k != 'elapsed_seconds'} for row in decisions])
    (ROOT / args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status_counts=result['status_counts'], chains=len(chains),
                          nodes=sum(r['nodes'] for r in decisions))))


if __name__ == '__main__':
    main()
