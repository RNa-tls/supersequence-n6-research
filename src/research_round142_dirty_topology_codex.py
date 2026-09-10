"""Finite first-occurrence dirty-splicing controls; no continuation search.

This file deliberately does not feed sigma edges to the clean capacity
engine.  Every dirty joint is cut before any resulting piece is treated as
a clean full-pass chain.  Literal controls corroborate the separate hand
proof, not a claim to enumerate n=6 covers.
"""
import hashlib
import itertools
import json
import math
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = "outputs/rr_round141_repeat_credit_codex.json"
OUTPUT = "outputs/rr_round142_dirty_topology_codex.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sigma(word, exponent=1):
    exponent %= len(word)
    return word[exponent:] + word[:exponent]


def orbit(word):
    return min(sigma(word[:-1], i) + word[-1:] for i in range(len(word)-1))


def hexagon(word):
    return min(sigma(word, i) for i in range(len(word)))


def E(word):
    return word[1:-1] + word[:1] + word[-1:]


def windows(word, n):
    alphabet = set(map(str, range(n)))
    return [(i, word[i:i+n]) for i in range(len(word)-n+1)
            if set(word[i:i+n]) == alphabet]


def first_windows(word, n):
    result, seen = [], set()
    for position, value in windows(word, n):
        if value not in seen:
            seen.add(value)
            result.append((position, value))
    assert len(result) == math.factorial(n)
    return result


def spelling(order):
    word = order[0]
    n = len(word)
    for target in order[1:]:
        weight = next(d for d in range(1, n+1) if word[-n:][d:] == target[:n-d])
        word += target[n-weight:]
    return word


def fixed_point(word, n):
    lengths = [len(word)]
    while True:
        projected = spelling([value for _, value in first_windows(word, n)])
        assert len(projected) <= len(word)
        if len(projected) == len(word):
            assert projected == word
            return word, lengths
        word = projected
        lengths.append(len(word))


def component_paths(P, edge):
    components, unseen = [], set(range(P))
    current = 0
    path = []
    while current in unseen:
        unseen.remove(current)
        path.append(current)
        if current not in edge:
            break
        current = edge[current]["target_index"]
    assert path[-1] not in edge
    components.append(path)
    while unseen:
        start = current = min(unseen)
        cycle = []
        while current in unseen:
            unseen.remove(current)
            cycle.append(current)
            current = edge[current]["target_index"]
        assert current == start
        components.append(cycle)
    return components


def audit_word(word, n, keep_mixed=False):
    selected = first_windows(word, n)
    assert spelling([value for _, value in selected]) == word, "Requires geodesic first-occurrence fixed point"
    assert selected[0][0] == 0 and selected[-1][0] + n == len(word)
    groups = []
    for index, item in enumerate(selected):
        if index == 0 or item[0] != selected[index-1][0] + 1:
            groups.append([])
        groups[-1].append(item)
    entries = [group[0][1] for group in groups]
    index_of = {entry: i for i, entry in enumerate(entries)}
    P, O = len(entries), len(set(map(orbit, entries)))
    G, k = P - math.factorial(n-1), O - math.factorial(n-2)
    assert min(G, k) >= 0 and P <= (n-1)*O
    nu = [index_of[sigma(group[-1][1])] for group in groups]
    assert sorted(nu) == list(range(P))
    assert all(sigma(group[0][1], len(group)) == entries[nu[i]] for i, group in enumerate(groups))
    edge = {}
    types = Counter()
    for i, (first, second) in enumerate(zip(groups, groups[1:])):
        source_position, source = first[-1]
        target_position, target = second[0]
        weight = target_position-source_position
        assert 2 <= weight <= n
        segment = word[source_position:target_position+n]
        intermediate = windows(segment, n)[1:-1]
        assert all(source_position+offset > selected[0][0] for offset, _ in intermediate)
        assert all(next(p for p, v in selected if v == value) < source_position+offset
                   for offset, value in intermediate)
        dirty = bool(intermediate)
        spliced_source = entries[nu[i]]
        assert sigma(spliced_source, -1) == source
        same_hex = hexagon(spliced_source) == hexagon(target)
        if weight == 2:
            if dirty:
                assert target == sigma(source, 2) == sigma(spliced_source)
                assert nu[i] < i and orbit(entries[i]) != orbit(target)
                kind = "DIRTY_W2_SIGMA"
            else:
                assert target == E(spliced_source)
                kind = "CLEAN_W2_E"
        elif weight == 3 and dirty:
            if same_hex:
                assert target == sigma(source, 3) == sigma(spliced_source, 2)
                assert nu[i] < i
                kind = "DIRTY_W3_SAME_HEX"
            else:
                assert [b-a for (a, _), (b, _) in zip(windows(segment, n), windows(segment, n)[1:])] in ([1, 2], [2, 1])
                kind = "DIRTY_W3_CROSS_HEX"
        elif weight == 3:
            kind = "CLEAN_W3"
        else:
            kind = "HEAVY"
        types[kind] += 1
        edge[nu[i]] = dict(original_source_index=i, source=source, target=target,
                           target_index=i+1, weight=weight, dirty=dirty, kind=kind,
                           intermediate=intermediate)
    components = component_paths(P, edge)
    K = len(components)
    component_of = {v: j for j, component in enumerate(components) for v in component}
    counts = Counter((hexagon(entries[v]), component_of[v]) for v in range(P))
    R_int = sum(count-1 for count in counts.values())
    assert G+1-K >= R_int >= 0 and (G+1-K) % 2 == 0
    genus = (G+1-K)//2
    same_dirty = {v for v, joint in edge.items()
                  if joint["kind"] in ("DIRTY_W2_SIGMA", "DIRTY_W3_SAME_HEX")}
    by_hex_component = Counter((hexagon(entries[v]), component_of[v]) for v in same_dirty)
    for key, count in by_hex_component.items():
        assert count <= counts[key]-1
    assert len(same_dirty) <= R_int
    pure = [cycle for cycle in components[1:]
            if all(edge[v]["kind"] == "CLEAN_W2_E" for v in cycle)]
    for cycle in pure:
        assert len(cycle) == n-1 and len({orbit(entries[v]) for v in cycle}) == 1
    c = len(pure)
    removed = set(sum(pure, []))
    keep = set(range(P)) - removed
    assert len({orbit(entries[v]) for v in keep}) == O-c
    assert {orbit(entries[v]) for v in keep}.isdisjoint(orbit(entries[v]) for v in removed)
    mandatory = ("HEAVY",) if keep_mixed else ("HEAVY", "DIRTY_W3_CROSS_HEX")
    cuts = {v for v, joint in edge.items() if v in keep and joint["kind"] in mandatory}
    cycle_cuts = []
    for cycle in components[1:]:
        if cycle in pure or set(cycle) & cuts:
            continue
        candidates = set(cycle) & same_dirty
        if not candidates:
            candidates = {v for v in cycle if edge[v]["weight"] == 3}
        assert candidates
        cut = min(candidates)
        cuts.add(cut)
        cycle_cuts.append(cut)

    def pieces():
        incoming = {joint["target_index"] for v, joint in edge.items()
                    if v in keep and v not in cuts}
        answer = []
        for start in sorted(keep-incoming):
            current, path = start, []
            while True:
                path.append(current)
                if current not in edge or current in cuts:
                    break
                current = edge[current]["target_index"]
            answer.append(path)
        assert len(set(sum(answer, []))) == sum(map(len, answer)) == len(keep)
        return answer

    def current_excess():
        return sum(len(path)-len({hexagon(entries[v]) for v in path}) for path in pieces())

    linear_dirty_cuts = []
    for v in sorted(same_dirty - cuts):
        before = current_excess()
        cuts.add(v)
        after = current_excess()
        assert after <= before-1
        linear_dirty_cuts.append(dict(source=v, before=before, after=after))
    remaining_excess = current_excess()
    duplicate_cuts = []
    for path in pieces():
        blocks, block = [], []
        for v in path:
            if block and edge[block[-1]]["kind"] != "CLEAN_W2_E":
                blocks.append(block)
                block = []
            block.append(v)
        blocks.append(block)
        seen, previous = set(), None
        for block in blocks:
            block_hexagons = {hexagon(entries[v]) for v in block}
            assert len(block_hexagons) == len(block)
            if block_hexagons & seen:
                assert previous is not None and edge[previous]["weight"] == 3
                cuts.add(previous)
                duplicate_cuts.append(previous)
                seen = set()
            seen.update(block_hexagons)
            previous = block[-1]
    assert len(duplicate_cuts) <= remaining_excess
    S = sum(joint["weight"] >= 3 for joint in edge.values())
    H = sum(max(joint["weight"]-3, 0) for joint in edge.values())
    h = sum(joint["weight"] >= 4 for joint in edge.values())
    D2 = types["DIRTY_W2_SIGMA"]
    D3_cross = types["DIRTY_W3_CROSS_HEX"]
    certificate = []
    total_b = total_O = total_D = 0
    retained_mixed = 0
    for path in pieces():
        piece_word = entries[path[0]]
        for j, v in enumerate(path):
            if j:
                joint = edge[path[j-1]]
                assert joint["weight"] <= 3 and (not joint["dirty"] or keep_mixed)
                piece_word += entries[v][-joint["weight"]:]
            piece_word += entries[v][:n-1]
        literal = windows(piece_word, n)
        if not keep_mixed:
            assert len(literal) == n*len(path) == len({value for _, value in literal})
            assert len({hexagon(value) for _, value in literal}) == len(path)
        assert len({hexagon(entries[v]) for v in path}) == len(path)
        qs = [orbit(entries[v]) for v in path]
        piece_O = len(set(qs))
        repeat_runs = 1 + sum(a != b for a, b in zip(qs, qs[1:])) - piece_O
        intra_paid = sum(edge[v]["weight"] >= 3 and a == b for v, a, b in zip(path, qs, qs[1:]))
        b = repeat_runs+intra_paid
        deficit = (n-1)*piece_O-len(path)
        assert min(b, deficit) >= 0
        ghosts=[]
        for v in path[:-1]:
            if edge[v]['kind'] != 'DIRTY_W3_CROSS_HEX': continue
            source_entry=entries[v]; target=entries[edge[v]['target_index']]
            if target==E(sigma(source_entry)):
                ghost=sigma(source_entry); subtype='E_SIGMA'
            else:
                assert target==sigma(E(source_entry))
                ghost=E(source_entry); subtype='SIGMA_E'
            assert ghost not in [entries[i] for i in path]
            assert orbit(ghost) in set(qs)
            ghosts.append(dict(source=v,ghost=ghost,subtype=subtype))
        assert len(ghosts)==len({x['ghost'] for x in ghosts})<=deficit
        retained_mixed+=len(ghosts)
        total_b += b
        total_O += piece_O
        total_D += deficit
        certificate.append(dict(indices=path, word=piece_word, P=len(path), O=piece_O, b=b, D=deficit,
                                shadow_ports=ghosts, literal_NR_claimed=not keep_mixed))
    sharing = total_O-(O-c)
    Bstar = total_b+sharing
    z = G-c
    Z = z-D2
    assert len(certificate) <= K-c+h+D3_cross+R_int <= G+1-c+h+D3_cross
    assert sharing >= 0 and Bstar == S+1+D2-O+c >= 0
    assert total_D == (n-1)*O-P+(n-1)*sharing
    assert D2 <= len(same_dirty) <= R_int <= 2*genus <= z
    assert Z >= types["DIRTY_W3_SAME_HEX"] >= 0
    base = math.factorial(n)+math.factorial(n-1)+math.factorial(n-2)+n-3
    assert len(word) == base+k+Z+H+Bstar
    R_literal = len(windows(word, n))-math.factorial(n)
    dirty_count = sum(joint["dirty"] for joint in edge.values())
    assert D2 <= dirty_count <= R_literal
    mixed_cut=sum(edge[v]['kind']=='DIRTY_W3_CROSS_HEX' for v in cuts)
    new_repeat_bound=None
    if keep_mixed:
        assert len(certificate)<=z+1+h
        assert mixed_cut<=Z-types['DIRTY_W3_SAME_HEX']
        assert D3_cross==retained_mixed+mixed_cut<=total_D+Z-types['DIRTY_W3_SAME_HEX']
        hidden_heavy=sum(len(j['intermediate']) for j in edge.values() if j['weight']>=4)
        assert hidden_heavy<=3*H
        assert R_literal==D2+2*types['DIRTY_W3_SAME_HEX']+D3_cross+hidden_heavy
        t=len(word)-base
        new_repeat_bound=(n-1)*t-c-(n-2)*Z-(n-4)*H
        assert R_literal<=new_repeat_bound
    return dict(n=n, word=word, length=len(word), selected_P=P, selected_O=O,
                G=G, k=k, S=S, H=H, h=h, nu=nu, K=K, g=genus, R_int=R_int,
                c=c, z=z, Z=Z, D2=D2, D3_cross=D3_cross,
                D3_same=types["DIRTY_W3_SAME_HEX"], dirty_count=dirty_count,
                R_literal=R_literal, joint_types=dict(types), Bstar=Bstar,
                b_sum=total_b, orbit_sharing=sharing, pieces=certificate,
                cycle_cuts=cycle_cuts, linear_dirty_cuts=linear_dirty_cuts,
                duplicate_cuts=duplicate_cuts, exact_length_base=base,
                exact_length_rhs=base+k+Z+H+Bstar,keep_mixed=keep_mixed,
                mixed_cut=mixed_cut,retained_mixed=retained_mixed,new_repeat_bound=new_repeat_bound)


def main():
    assert not sys.flags.optimize
    start = time.perf_counter()
    source = Path(__file__).relative_to(ROOT).as_posix()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    committed = subprocess.check_output(["git", "show", head+":"+source], cwd=ROOT)
    assert hashlib.sha256(committed).hexdigest() == sha(__file__), "Commit source before certificate run"
    archive = json.loads((ROOT/INPUT).read_text())
    controls = {}
    n3_orders = list(itertools.permutations(["012", "021", "102", "120", "201", "210"]))
    for order in n3_orders:
        word, lengths = fixed_point(spelling(order), 3)
        controls[3, word] = dict(normalization_lengths=lengths)
    for record in [archive["nr4_trap"], *archive["n6_controls"]]:
        word, lengths = fixed_point(record["word"], record["n"])
        controls[record["n"], word] = dict(normalization_lengths=lengths)
    rows = []
    for (n, word), meta in sorted(controls.items()):
        row = audit_word(word, n)
        row.update(meta)
        rows.append(row)
    result = dict(schema="codex/round142-dirty-splicing-controls/1", completed=True,
                  verified=True, capped=False, continuation_search=False,
                  scope="All720 NR3 order projections plus preserved NR4 trap and five NR6 literal controls; no global NR6 closure",
                  hand_claim="Cut every dirty joint; same-hex dirty edges charge R_int; clean pieces only",
                  exact_length="L=B_n+k+(G-c-D2)+H+sum(b_j)+s",
                  selected_outer_consequence="At n6,L<=871: k<=4 and G<=5k, without claiming unchanged clean capacities",
                  n3_order_count=len(n3_orders), control_count=len(rows), rows=rows,
                  source_commit=head, committed_source_sha256=hashlib.sha256(committed).hexdigest(),
                  runtime_source_sha256=sha(__file__), input_sha256={INPUT: sha(ROOT/INPUT)},
                  argv=sys.argv, executable=sys.executable, executable_sha256=sha(sys.executable),
                  seconds=time.perf_counter()-start)
    result["deterministic_digest"] = digest(rows)
    (ROOT/OUTPUT).write_text(json.dumps(result, indent=2)+"\n", newline="\n")
    print(json.dumps(dict(completed=True, controls=len(rows), output=OUTPUT, seconds=result["seconds"])))


if __name__ == "__main__":
    main()
