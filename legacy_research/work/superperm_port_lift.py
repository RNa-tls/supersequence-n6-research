#!/usr/bin/env python3
"""Independent n=6 E-orbit / skeleton / port-lift verifier.

Conventions
-----------
Words are tuples p=(p(0),...,p(5)).  A position permutation g acts on the
right by (p*g)(i)=p(g(i)); composition is therefore (g*h)(i)=g(h(i)).

The script deliberately contains no archived superpermutation.  It provides
the finite group calculations needed to (1) build E-orbit exact-cover
skeletons, (2) attach a 25th E-orbit, (3) calculate the deterministic w=2
port permutation, and (4) run the port-lift dynamic programme described in
the research log.

Use --help for commands.  Results are JSON so that a second implementation
can verify them independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, permutations
from math import factorial as math_factorial
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence, Set, Tuple


N = 6
Perm = Tuple[int, ...]


def compose(g: Perm, h: Perm) -> Perm:
    """Right-action composition: p*(g*h) = (p*g)*h."""
    return tuple(g[h[i]] for i in range(N))


def inverse(g: Perm) -> Perm:
    ans = [0] * N
    for i, value in enumerate(g):
        ans[value] = i
    return tuple(ans)


def power(g: Perm, exponent: int) -> Perm:
    if exponent < 0:
        return power(inverse(g), -exponent)
    ans = tuple(range(N))
    base = g
    while exponent:
        if exponent & 1:
            ans = compose(ans, base)
        base = compose(base, base)
        exponent >>= 1
    return ans


IDENTITY: Perm = tuple(range(N))
SIGMA: Perm = (1, 2, 3, 4, 5, 0)
TAU: Perm = (2, 3, 4, 5, 1, 0)
E: Perm = (1, 2, 3, 4, 0, 5)  # (0 1 2 3 4), fixing 5


def orbit(seed: Perm, generator: Perm) -> Tuple[Perm, ...]:
    out: List[Perm] = []
    current = seed
    while current not in out:
        out.append(current)
        current = compose(current, generator)
    return tuple(out)


ALL_WORDS: Tuple[Perm, ...] = tuple(permutations(range(N)))
WORD_ID: Dict[Perm, int] = {p: i for i, p in enumerate(ALL_WORDS)}


def canonical_rotation(word: Perm) -> Perm:
    return min(orbit(word, SIGMA))


def canonical_e_orbit(word: Perm) -> Perm:
    return min(orbit(word, E))


ROT_REPS: Tuple[Perm, ...] = tuple(sorted({canonical_rotation(p) for p in ALL_WORDS}))
ROT_ID: Dict[Perm, int] = {p: i for i, p in enumerate(ROT_REPS)}
E_REPS: Tuple[Perm, ...] = tuple(sorted({canonical_e_orbit(p) for p in ALL_WORDS}))
E_ID: Dict[Perm, int] = {p: i for i, p in enumerate(E_REPS)}


def hexagon_id(word: Perm) -> int:
    return ROT_ID[canonical_rotation(word)]


def e_orbit_id(word: Perm) -> int:
    return E_ID[canonical_e_orbit(word)]


def ports_of_e_orbit(q: Perm) -> Tuple[Perm, ...]:
    return orbit(q, E)


def kset_of_e_orbit(q: Perm) -> Tuple[int, ...]:
    return tuple(hexagon_id(p) for p in ports_of_e_orbit(q))


KSETS: Tuple[Tuple[int, ...], ...] = tuple(kset_of_e_orbit(q) for q in E_REPS)
KSET_BITSETS: Tuple[int, ...] = tuple(sum(1 << h for h in ks) for ks in KSETS)


def is_indecomposable(pi: Tuple[int, ...]) -> bool:
    """No proper initial block preserves its value set."""
    w = len(pi)
    for t in range(1, w):
        if set(pi[:t]) == set(range(t)):
            return False
    return True


@lru_cache(maxsize=None)
def tail_permutations(w: int) -> Tuple[Tuple[int, ...], ...]:
    return tuple(pi for pi in permutations(range(w)) if is_indecomposable(pi))


def tail_action(w: int, pi: Tuple[int, ...]) -> Perm:
    """Exact overlap-(6-w) position action with tail pi."""
    if len(pi) != w:
        raise ValueError("tail length mismatch")
    return tuple(list(range(w, N)) + list(pi))


def word_after(word: Perm, action: Perm) -> Perm:
    return compose(word, action)


def left_relabel(word: Perm, alphabet_permutation: Perm) -> Perm:
    """Relabel values, not positions.  This commutes with every right action."""
    return tuple(alphabet_permutation[value] for value in word)


def arc_endpoint(port: Perm, length: int) -> Perm:
    if not 1 <= length <= N:
        raise ValueError("arc length must be in 1..6")
    return word_after(port, power(SIGMA, length - 1))


def arc_mask(port: Perm, length: int) -> int:
    """Six-bit mask in the port's rotation hexagon."""
    h = canonical_rotation(port)
    positions = {word_after(h, power(SIGMA, i)): i for i in range(N)}
    mask = 0
    current = port
    for _ in range(length):
        mask |= 1 << positions[current]
        current = word_after(current, SIGMA)
    return mask


def rotation_distance(source: Perm, target: Perm) -> int:
    """d in 0..5 with source*sigma^d=target; requires same hexagon."""
    current = source
    for d in range(N):
        if current == target:
            return d
        current = word_after(current, SIGMA)
    raise ValueError("different rotation hexagons")


@dataclass(frozen=True)
class Skeleton:
    base_orbits: Tuple[int, ...]
    extra_orbit: int

    @property
    def orbit_ids(self) -> Tuple[int, ...]:
        return tuple(sorted(self.base_orbits + (self.extra_orbit,)))


def verify_exact_partition(orbit_ids: Sequence[int]) -> bool:
    if len(orbit_ids) != 24 or len(set(orbit_ids)) != 24:
        return False
    seen: Set[int] = set()
    for qid in orbit_ids:
        ks = KSETS[qid]
        if len(set(ks)) != 5 or set(ks) & seen:
            return False
        seen.update(ks)
    return len(seen) == 120


def find_exact_partition(limit: int = 1) -> List[Tuple[int, ...]]:
    """Algorithm-X style exact cover of 120 hexagons by 24 K-sets."""
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)

    solutions: List[Tuple[int, ...]] = []
    used: Set[int] = set()
    covered: Set[int] = set()

    def recurse() -> None:
        if len(solutions) >= limit:
            return
        if len(covered) == 120:
            solutions.append(tuple(sorted(used)))
            return
        candidate_hex = min(
            (h for h in range(120) if h not in covered),
            key=lambda h: sum(1 for q in by_hex[h] if q not in used and not (set(KSETS[q]) & covered)),
        )
        candidates = [q for q in by_hex[candidate_hex] if q not in used and not (set(KSETS[q]) & covered)]
        for qid in candidates:
            used.add(qid)
            covered.update(KSETS[qid])
            recurse()
            for h in KSETS[qid]:
                # It was disjoint from every other currently selected K-set.
                covered.remove(h)
            used.remove(qid)

    recurse()
    return solutions


def port_data(skeleton: Skeleton) -> Tuple[Tuple[Perm, ...], Dict[Perm, int], Dict[int, List[Perm]]]:
    ports: List[Perm] = []
    by_hex: Dict[int, List[Perm]] = defaultdict(list)
    for qid in skeleton.orbit_ids:
        for p in ports_of_e_orbit(E_REPS[qid]):
            ports.append(p)
            by_hex[hexagon_id(p)].append(p)
    if len(ports) != 125 or len(set(ports)) != 125:
        raise ValueError("expected 125 distinct ports")
    index = {p: i for i, p in enumerate(ports)}
    return tuple(ports), index, by_hex


def fixed_arc_lengths(skeleton: Skeleton) -> Dict[Perm, int]:
    """Determine all rotation-arc lengths from a saturated 25-orbit cover.

    This does *not* assume a 24-orbit exact partition.  In each hexagon, the
    selected ports are cyclically ordered; the pass starting at a port ends
    immediately before the next selected port.  Thus a one-, two-, or
    three-way (etc.) split has a unique directed arc decomposition.
    """
    ports, _, by_hex = port_data(skeleton)
    lengths: Dict[Perm, int] = {}
    for h, members in by_hex.items():
        if not members:
            raise ValueError(f"hexagon {h} is uncovered")
        positions = sorted((rotation_distance(ROT_REPS[h], u), u) for u in members)
        for index, (pos, u) in enumerate(positions):
            next_pos, _next_u = positions[(index + 1) % len(positions)]
            length = (next_pos - pos) % N
            lengths[u] = N if length == 0 else length
    if set(lengths) != set(ports):
        raise AssertionError("missing port length")
    total = sum(lengths.values())
    if total != 720:
        raise AssertionError(f"arcs cover {total}, not 720 permutations")
    return lengths


def w2_permutation(skeleton: Skeleton) -> Tuple[Tuple[Perm, ...], Dict[Perm, Perm], Dict[Perm, int]]:
    ports, port_index, _ = port_data(skeleton)
    lengths = fixed_arc_lengths(skeleton)
    successor: Dict[Perm, Perm] = {}
    for u in ports:
        endpoint = arc_endpoint(u, lengths[u])
        v = word_after(endpoint, TAU)
        if v not in port_index:
            raise ValueError("w=2 target leaves fixed port skeleton")
        successor[u] = v
    indegrees = Counter(successor.values())
    if any(indegrees[p] != 1 for p in ports):
        raise ValueError("w=2 successor is not a permutation on ports")
    return ports, successor, lengths


def cycle_decomposition(successor: Dict[Perm, Perm]) -> List[Tuple[Perm, ...]]:
    unseen = set(successor)
    cycles: List[Tuple[Perm, ...]] = []
    while unseen:
        start = min(unseen)
        current = start
        cyc: List[Perm] = []
        while current not in cyc:
            cyc.append(current)
            unseen.remove(current)
            current = successor[current]
        if current != start:
            raise AssertionError("not a permutation cycle")
        cycles.append(tuple(cyc))
    return cycles


def strongly_connected_component_sizes(vertex_count: int, arcs: Set[Tuple[int, int]]) -> List[int]:
    """Kosaraju, retained here to expose possible port-lift invariants."""
    forward = [[] for _ in range(vertex_count)]
    backward = [[] for _ in range(vertex_count)]
    for a, b in arcs:
        forward[a].append(b)
        backward[b].append(a)
    seen: Set[int] = set()
    order: List[int] = []

    def visit(v: int) -> None:
        seen.add(v)
        for nxt in forward[v]:
            if nxt not in seen:
                visit(nxt)
        order.append(v)

    for v in range(vertex_count):
        if v not in seen:
            visit(v)
    seen.clear()
    sizes: List[int] = []

    def reverse_visit(v: int) -> int:
        seen.add(v)
        return 1 + sum(reverse_visit(nxt) for nxt in backward[v] if nxt not in seen)

    for v in reversed(order):
        if v not in seen:
            sizes.append(reverse_visit(v))
    return sorted(sizes)


def weak_component_sizes(vertex_count: int, arcs: Set[Tuple[int, int]]) -> List[int]:
    adjacent = [[] for _ in range(vertex_count)]
    for a, b in arcs:
        adjacent[a].append(b)
        adjacent[b].append(a)
    seen: Set[int] = set()
    sizes: List[int] = []
    for root in range(vertex_count):
        if root in seen:
            continue
        stack = [root]
        seen.add(root)
        size = 0
        while stack:
            v = stack.pop()
            size += 1
            for nxt in adjacent[v]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        sizes.append(size)
    return sorted(sizes)


def deep_edges(ports: Sequence[Perm], lengths: Dict[Perm, int], port_set: Set[Perm]) -> Dict[Perm, List[Tuple[Perm, int, int, Tuple[int, ...]]]]:
    """u -> (target, heavy_cost, weight, pi) for all exact deep tails in port_set."""
    ans: Dict[Perm, List[Tuple[Perm, int, int, Tuple[int, ...]]]] = defaultdict(list)
    for u in ports:
        endpoint = arc_endpoint(u, lengths[u])
        for w in range(3, N + 1):
            for pi in tail_permutations(w):
                target = word_after(endpoint, tail_action(w, pi))
                if target in port_set:
                    ans[u].append((target, w - 3, w, pi))
    return ans


def ribbon_invariants_for_orbits(orbit_ids: Sequence[int]) -> Dict[str, int]:
    """Ribbon invariants for an arbitrary nonempty family of E-orbits.

    White vertices are exactly the rotation hexagons met by the family.  This
    general version is used to enumerate small positive-genus cores; the
    25-orbit saturated specialization is ``port_ribbon_invariants`` below.
    """
    ids = tuple(sorted(orbit_ids))
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("orbit family must be a nonempty set")
    ports = tuple(port for qid in ids for port in ports_of_e_orbit(E_REPS[qid]))
    by_hex: Dict[int, List[Perm]] = defaultdict(list)
    for port in ports:
        by_hex[hexagon_id(port)].append(port)
    rho: Dict[Perm, Perm] = {}
    for h, members in by_hex.items():
        ordered = sorted(members, key=lambda p: rotation_distance(ROT_REPS[h], p))
        for index, port in enumerate(ordered):
            rho[port] = ordered[(index + 1) % len(ordered)]
    successor = {port: word_after(rho[port], E) for port in ports}
    cycle_count = len(cycle_decomposition(successor))

    parent = {port: port for port in ports}

    def find(port: Perm) -> Perm:
        while parent[port] != port:
            parent[port] = parent[parent[port]]
            port = parent[port]
        return port

    for port in ports:
        for neighbor in (rho[port], word_after(port, E)):
            left, right = find(port), find(neighbor)
            if left != right:
                parent[left] = right
    components = len({find(port) for port in ports})
    orbit_count = len(ids)
    hexagon_count = len(by_hex)
    edge_count = len(ports)
    excess = edge_count - hexagon_count
    beta = edge_count - (orbit_count + hexagon_count) + components
    numerator = orbit_count - excess + 2 * beta - cycle_count
    if numerator < 0 or numerator % 2:
        raise AssertionError("ribbon Euler identity failed")
    return {
        "ribbon_orbits": orbit_count,
        "ribbon_hexagons": hexagon_count,
        "ribbon_excess": excess,
        "ribbon_components": components,
        "ribbon_beta1": beta,
        "ribbon_genus": numerator // 2,
        "cycle_count": cycle_count,
    }


def incidence_beta_for_orbits(orbit_ids: Sequence[int]) -> int:
    """Cycle rank of the unembedded E-orbit/hexagon incidence graph.

    Unlike genus, this is monotone under adding E-orbits.  Once it is positive
    a partial family cannot extend to a forest saturated cover.
    """
    ids = tuple(orbit_ids)
    active = set(ids)
    parent: Dict[int, int] = {qid: qid for qid in ids}

    def find(vertex: int) -> int:
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    edge_count = 0
    for qid in ids:
        for h in KSETS[qid]:
            vertex = len(E_REPS) + h
            if vertex not in parent:
                parent[vertex] = vertex
            active.add(vertex)
            left, right = find(qid), find(vertex)
            if left != right:
                parent[left] = right
            edge_count += 1
    components = len({find(vertex) for vertex in active})
    return edge_count - len(active) + components


def port_ribbon_invariants(skeleton: Skeleton, successor: Dict[Perm, Perm] | None = None) -> Dict[str, int]:
    """Euler data of the 25-orbit/120-hexagon port-incidence ribbon graph.

    The black cyclic order is E and the white cyclic order is rotation order,
    so the face permutation is the w=2 port successor.  The returned genus is
    the total genus over all components.
    """
    if len(skeleton.orbit_ids) != 25:
        raise ValueError("ribbon invariant is defined here only for 25-orbit covers")
    result = ribbon_invariants_for_orbits(skeleton.orbit_ids)
    if result["ribbon_hexagons"] != 120:
        raise ValueError("25-orbit family does not cover all rotation hexagons")
    if successor is not None and len(cycle_decomposition(successor)) != result["cycle_count"]:
        raise AssertionError("port successor disagrees with intrinsic ribbon successor")
    return {
        "ribbon_components": result["ribbon_components"],
        "ribbon_beta1": result["ribbon_beta1"],
        "ribbon_genus": result["ribbon_genus"],
    }


def port_lift_dp(skeleton: Skeleton, heavy_budget: int = 3) -> Dict[str, object]:
    """Exact cycle-subset DP for the port-lift relaxation.

    The DP enforces u ->deep-> f(u_next) and never revisits an f-cycle.
    It does not yet impose fragment chronology; it is deliberately the
    intermediate necessary condition from the research plan.
    """
    ports, f, lengths = w2_permutation(skeleton)
    cycles = cycle_decomposition(f)
    ribbon = port_ribbon_invariants(skeleton, f)
    cycle_of: Dict[Perm, int] = {}
    finv = {v: u for u, v in f.items()}
    for cid, cyc in enumerate(cycles):
        for u in cyc:
            cycle_of[u] = cid
    candidates = deep_edges(ports, lengths, set(ports))
    count = len(cycles)
    if count > 24:
        raise ValueError("DP implementation intentionally limited to <=24 f-cycles")

    # The cycle-level transition graph is weaker than the lift DP (it forgets
    # which port is forced on entry), but its SCC/weak-component data is a
    # useful diagnostic for a prospective algebraic obstruction.
    cycle_arcs: Set[Tuple[int, int]] = set()
    for u, options in candidates.items():
        source_cycle = cycle_of[u]
        for target, extra, _w, _pi in options:
            if extra <= heavy_budget:
                cycle_arcs.add((source_cycle, cycle_of[finv[target]]))

    # Mapping (mask, exit_port) -> minimum heavy cost.
    current: Dict[Tuple[int, Perm], int] = {}
    for u in ports:
        current[(1 << cycle_of[u], u)] = 0
    best_size = 1
    terminal_costs: List[int] = []
    transition_counts = Counter()

    # A forward relaxation in increasing cardinality; no transition can reduce a
    # mask.  Storing *layers*, rather than scanning every subset of [count] at
    # every level, matters already for count=20.
    layers: List[Dict[Tuple[int, Perm], int]] = [dict() for _ in range(count + 1)]
    for state, cost in current.items():
        layers[1][state] = cost
    seen: Dict[Tuple[int, Perm], int] = dict(current)

    for cardinality in range(1, count + 1):
        for (mask, u), cost in list(layers[cardinality].items()):
            best_size = max(best_size, cardinality)
            if cardinality == count:
                terminal_costs.append(cost)
                continue
            for target, extra, _w, _pi in candidates.get(u, []):
                if cost + extra > heavy_budget:
                    continue
                u_next = finv[target]
                cid = cycle_of[u_next]
                if mask & (1 << cid):
                    transition_counts["revisited_cycle"] += 1
                    continue
                new_mask = mask | (1 << cid)
                state = (new_mask, u_next)
                new_cost = cost + extra
                old = seen.get(state)
                if old is None or new_cost < old:
                    seen[state] = new_cost
                    layers[cardinality + 1][state] = new_cost
                    transition_counts["accepted"] += 1
                else:
                    transition_counts["dominated"] += 1

    min_complete = min(terminal_costs) if terminal_costs else None
    # One run at budget B contains every path of cost <= b for every b<=B.
    # Because ``seen`` retains the minimum cost for each exact (mask, port)
    # state, filtering it by cost gives the *exact*, not heuristic, smaller
    # budget reachability table.  This avoids rerunning the exponential DP
    # four times when certifying H=0,1,2,3.
    budget_summaries: List[Dict[str, object]] = []
    for budget in range(heavy_budget + 1):
        eligible_layers = [
            {state: cost for state, cost in layer.items() if cost <= budget}
            for layer in layers[1:]
        ]
        reachable_cards = [index + 1 for index, layer in enumerate(eligible_layers) if layer]
        complete_costs = [cost for cost in terminal_costs if cost <= budget]
        budget_summaries.append({
            "heavy_budget": budget,
            "min_heavy_to_cover_all_cycles": min(complete_costs) if complete_costs else None,
            "max_cycles_reached": max(reachable_cards) if reachable_cards else 0,
            "dp_states": sum(len(layer) for layer in eligible_layers),
            "layer_state_counts": [len(layer) for layer in eligible_layers],
            "layer_cycle_mask_counts": [len({mask for (mask, _u) in layer}) for layer in eligible_layers],
        })
    return {
        "cycle_count": count,
        "cycle_lengths": sorted(len(c) for c in cycles),
        "w2_sign": "odd" if ((len(ports) - count) % 2) else "even",
        "min_heavy_to_cover_all_cycles": min_complete,
        "max_cycles_reached": best_size,
        "dp_states": len(seen),
        "layer_state_counts": [len(layer) for layer in layers[1:]],
        "layer_cycle_mask_counts": [len({mask for (mask, _u) in layer}) for layer in layers[1:]],
        "budget_summaries": budget_summaries,
        "transition_counts": dict(transition_counts),
        "cycle_transition_arc_count": len(cycle_arcs),
        "cycle_transition_scc_sizes": strongly_connected_component_sizes(count, cycle_arcs),
        "cycle_transition_weak_component_sizes": weak_component_sizes(count, cycle_arcs),
        **ribbon,
    }


def stable_sha256(value: object) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def cmd_basic(_: argparse.Namespace) -> None:
    assert len(ROT_REPS) == 120
    assert len(E_REPS) == 144
    assert power(E, 5) == IDENTITY
    assert power(SIGMA, 6) == IDENTITY
    # Under our right-action convention, applying r^{-1} and then flip is
    # the product sigma^{-1}*tau.  As a function of words this is
    # flip \u2218 r^{-1}=E.
    assert compose(inverse(SIGMA), TAU) == E
    counts = [len(tail_permutations(w)) for w in range(1, 7)]
    # Regression test for the optimized 5d canonical-image calculation.
    # The reference calculation deliberately uses all 720 left-S6 images.
    rng = random.Random(0xC0FFEE)
    canonical_cases = 0
    for size in (1, 2, 3, 5, 10, 25):
        for _ in range(12):
            ids = tuple(sorted(rng.sample(range(len(E_REPS)), size)))
            mask = sum(1 << qid for qid in ids)
            fast = ids_from_mask(canonical_orbit_mask(mask))
            slow = min(tuple(sorted(action[qid] for qid in ids)) for action in left_s6_e_actions())
            assert fast == slow
            canonical_cases += 1
    result = {
        "rotation_hexagons": len(ROT_REPS),
        "e_orbits": len(E_REPS),
        "indecomposable_tail_counts": counts,
        "flip_r_inverse_equals_E": True,
        "left_s6_canonicalization_cases_checked": canonical_cases,
        "sha256": stable_sha256({"rot": len(ROT_REPS), "e": len(E_REPS), "tails": counts}),
    }
    print(json.dumps(result, indent=2))


def cmd_find_partition(args: argparse.Namespace) -> None:
    solutions = find_exact_partition(args.limit)
    result = {
        "solutions_found": len(solutions),
        "solutions": [list(s) for s in solutions],
        "verified": [verify_exact_partition(s) for s in solutions],
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "solutions_found": len(solutions),
        "all_verified": all(result["verified"]),
        "output": args.output,
    }, indent=2))


def load_partition(path: str) -> Tuple[int, ...]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(obj, dict) and "solutions" in obj:
        obj = obj["solutions"][0]
    partition = tuple(int(x) for x in obj)
    if not verify_exact_partition(partition):
        raise ValueError("not a valid 24-orbit exact partition")
    return partition


def load_partitions(path: str) -> List[Tuple[int, ...]]:
    """Load a list emitted by find-partition and re-verify every row."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = obj["solutions"] if isinstance(obj, dict) and "solutions" in obj else obj
    result = [tuple(int(x) for x in row) for row in rows]
    if not all(verify_exact_partition(row) for row in result):
        raise ValueError("input contains a non-partition")
    return result


def cmd_scan_extra(args: argparse.Namespace) -> None:
    base = load_partition(args.partition)
    rows = []
    histogram = Counter()
    for extra in range(len(E_REPS)):
        if extra in base:
            continue
        if args.extra and extra not in args.extra:
            continue
        skeleton = Skeleton(base, extra)
        try:
            # For the F=5, N=0, S=20 branch there are exactly 19 deep
            # transitions.  A w=2 cycle needs a distinct deep exit, except
            # for the final cycle; hence c>20 is already impossible.  The
            # port-lift DP below is the sharp c=20 test.  (For c<20 one must
            # additionally model interior deep transitions, which is a
            # different branch and is deliberately not silently discarded.)
            ports, successor, _lengths = w2_permutation(skeleton)
            cycles = cycle_decomposition(successor)
            cycle_count = len(cycles)
            if cycle_count > 20:
                data = {
                    "cycle_count": cycle_count,
                    "cycle_lengths": sorted(len(c) for c in cycles),
                    "precheck": "impossible: c-1 > 19 deep transitions",
                }
            elif cycle_count < 20:
                data = {
                    "cycle_count": cycle_count,
                    "cycle_lengths": sorted(len(c) for c in cycles),
                    "precheck": "not evaluated: interior deep transitions required",
                }
            elif args.lift:
                data = port_lift_dp(skeleton, args.heavy)
            else:
                data = {
                    "cycle_count": cycle_count,
                    "cycle_lengths": sorted(len(c) for c in cycles),
                    "precheck": "c=20; port-lift not requested",
                }
            row = {"extra_orbit": extra, **data}
            rows.append(row)
            histogram[f"c={cycle_count}"] += 1
        except ValueError as exc:
            rows.append({"extra_orbit": extra, "error": str(exc)})
            histogram["error"] += 1
    result = {
        "base_partition": list(base),
        "heavy_budget": args.heavy,
        "histogram": dict(histogram),
        "rows": rows,
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"histogram": result["histogram"], "rows": len(rows)}, indent=2))


def cmd_scan_partitions(args: argparse.Namespace) -> None:
    """Fast cycle-count survey over many exact partitions.

    This intentionally runs no exponential lift DP.  It produces the exact
    set of c=20 candidates within the supplied finite partition list, so the
    expensive test can be replayed independently one pair at a time.
    """
    partitions = load_partitions(args.partitions)
    if args.indices:
        requested = [int(i) for i in args.indices.split(",") if i.strip()]
        selected_partitions = [(i, partitions[i]) for i in requested]
    elif args.limit is not None:
        selected_partitions = list(enumerate(partitions[: args.limit]))
    else:
        selected_partitions = list(enumerate(partitions))
    histogram: Counter = Counter()
    c20_pairs: List[Dict[str, object]] = []
    errors: Counter = Counter()
    for partition_index, base in selected_partitions:
        for extra in range(len(E_REPS)):
            if extra in base:
                continue
            try:
                ports, successor, _lengths = w2_permutation(Skeleton(base, extra))
                c = len(cycle_decomposition(successor))
                histogram[c] += 1
                if c == 20:
                    c20_pairs.append({"partition_index": partition_index, "extra_orbit": extra})
            except ValueError as exc:
                errors[str(exc)] += 1
    result = {
        "partitions_scanned": len(selected_partitions),
        "pairs_scanned": sum(histogram.values()) + sum(errors.values()),
        "cycle_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "c20_pairs": c20_pairs,
        "errors": dict(errors),
        "source_sha256": hashlib.sha256(Path(args.partitions).read_bytes()).hexdigest(),
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "partitions_scanned": result["partitions_scanned"],
        "pairs_scanned": result["pairs_scanned"],
        "cycle_histogram": result["cycle_histogram"],
        "c20_candidates": len(c20_pairs),
        "errors": result["errors"],
    }, indent=2))


def cmd_lift_candidate(args: argparse.Namespace) -> None:
    partitions = load_partitions(args.partitions)
    if not 0 <= args.partition_index < len(partitions):
        raise ValueError("partition index outside supplied list")
    base = partitions[args.partition_index]
    if args.extra_orbit in base:
        raise ValueError("extra E-orbit already belongs to the base partition")
    skeleton = Skeleton(base, args.extra_orbit)
    result = {
        "partition_index": args.partition_index,
        "base_partition": list(base),
        "extra_orbit": args.extra_orbit,
        "heavy_budget": args.heavy,
        **port_lift_dp(skeleton, args.heavy),
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


@lru_cache(maxsize=1)
def left_s6_e_actions() -> Tuple[Tuple[int, ...], ...]:
    """The genuine left S6 action on E-orbit IDs.

    Value relabeling commutes with all position permutations, hence preserves
    the E-orbit/hexagon incidence structure.  No unproved reversal or
    position symmetry is included here.
    """
    actions: List[Tuple[int, ...]] = []
    for alpha in permutations(range(N)):
        a = tuple(alpha)
        actions.append(tuple(e_orbit_id(left_relabel(q, a)) for q in E_REPS))
    assert len(actions) == 720
    return tuple(actions)


def canonical_skeleton_pair(base: Tuple[int, ...], extra: int) -> Tuple[Tuple[int, ...], int]:
    return min((tuple(sorted(action[q] for q in base)), action[extra]) for action in left_s6_e_actions())


def canonical_partition(base: Tuple[int, ...]) -> Tuple[int, ...]:
    return min(tuple(sorted(action[q] for q in base)) for action in left_s6_e_actions())


def cmd_classify_c20(args: argparse.Namespace) -> None:
    partitions = load_partitions(args.partitions)
    survey = json.loads(Path(args.survey).read_text(encoding="utf-8"))
    classes: Dict[Tuple[Tuple[int, ...], int], List[Tuple[int, int]]] = defaultdict(list)
    for row in survey["c20_pairs"]:
        partition_index = int(row["partition_index"])
        extra = int(row["extra_orbit"])
        if not 0 <= partition_index < len(partitions):
            raise ValueError("survey partition index outside partition file")
        key = canonical_skeleton_pair(partitions[partition_index], extra)
        classes[key].append((partition_index, extra))
    serialised = []
    for key, members in sorted(classes.items()):
        base, extra = key
        serialised.append({
            "representative_base": list(base),
            "representative_extra": extra,
            "members_in_input": len(members),
            "first_input_member": {"partition_index": members[0][0], "extra_orbit": members[0][1]},
        })
    result = {
        "input_c20_pairs": len(survey["c20_pairs"]),
        "left_s6_orbit_classes_in_input": len(serialised),
        "classes": serialised,
        "note": "This is only the left S6 quotient of the supplied finite list; it is not a claim that the supplied list contains every exact partition.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "input_c20_pairs": result["input_c20_pairs"],
        "left_s6_orbit_classes_in_input": result["left_s6_orbit_classes_in_input"],
        "output": args.output,
    }, indent=2))


def cmd_classify_partitions(args: argparse.Namespace) -> None:
    partitions = load_partitions(args.partitions)
    if args.limit is not None:
        partitions = partitions[: args.limit]
    classes: Dict[Tuple[int, ...], List[int]] = defaultdict(list)
    for index, partition in enumerate(partitions):
        classes[canonical_partition(partition)].append(index)
    serialised = [
        {
            "representative_base": list(base),
            "members_in_input": len(members),
            "first_input_index": members[0],
        }
        for base, members in sorted(classes.items())
    ]
    result = {
        "input_partitions": len(partitions),
        "left_s6_orbit_classes_in_input": len(serialised),
        "classes": serialised,
        "note": "Only a quotient of the supplied finite input list; no completeness claim is made.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "input_partitions": len(partitions),
        "left_s6_orbit_classes_in_input": len(serialised),
        "output": args.output,
    }, indent=2))


def transition_weight(source: Perm, target: Perm) -> int:
    """Characters appended when the window source is followed by target."""
    for overlap in range(N - 1, -1, -1):
        if source[N - overlap :] == target[:overlap]:
            return N - overlap
    raise AssertionError("overlap zero must always work")


def cmd_verify_word(args: argparse.Namespace) -> None:
    """Verify a concrete n=6 no-repeat permutation walk from a digit word."""
    raw = Path(args.word).read_text(encoding="utf-8")
    symbols = [ch for ch in raw if ch.isdigit()]
    if not symbols:
        raise ValueError("the input contains no digits")
    alphabet = sorted(set(symbols))
    if len(alphabet) != N:
        raise ValueError(f"expected exactly six symbols, found {alphabet}")
    to_internal = {symbol: i for i, symbol in enumerate(alphabet)}
    word = tuple(to_internal[ch] for ch in symbols)
    if len(word) < N:
        raise ValueError("word is shorter than six")
    occurrences = tuple(
        (i, word[i : i + N])
        for i in range(len(word) - N + 1)
        if len(set(word[i : i + N])) == N
    )
    positions = tuple(i for i, _p in occurrences)
    windows = tuple(p for _i, p in occurrences)
    if len(set(windows)) != len(windows):
        raise ValueError("the walk repeats a permutation")
    weights = [b - a for a, b in zip(positions, positions[1:])]
    if any(not 1 <= w <= N for w in weights):
        raise ValueError("successive permutation occurrences are more than six positions apart")
    for source, target, weight in zip(windows, windows[1:], weights):
        if transition_weight(source, target) != weight:
            raise ValueError("successive occurrences disagree with their overlap weight")
    pass_starts = [0] + [i + 1 for i, w in enumerate(weights) if w != 1]
    P = len(pass_starts)
    pass_lengths = {
        windows[start]: (pass_starts[index + 1] if index + 1 < P else len(windows)) - start
        for index, start in enumerate(pass_starts)
    }
    F = 0
    visited: Set[Perm] = {windows[0]}
    for i, w in enumerate(weights):
        if w != 1:
            endpoint = windows[i]
            if word_after(endpoint, SIGMA) not in visited:
                F += 1
        visited.add(windows[i + 1])
    S = 1 + sum(w >= 3 for w in weights)
    H = sum(max(w - 3, 0) for w in weights)
    pass_start_orbits = [e_orbit_id(windows[i]) for i in pass_starts]
    O = len(set(pass_start_orbits))
    D = 5 * O - P
    Ndef = S + F - O
    k = O - 24
    e_orbit_start_counts = Counter(pass_start_orbits)
    hexagon_start_counts = Counter(hexagon_id(windows[i]) for i in pass_starts)
    result = {
        "input_length": len(word),
        "window_count": len(windows),
        "all_720_permutations_covered": len(windows) == 720 and len(set(windows)) == 720,
        "weight_histogram": {str(w): c for w, c in sorted(Counter(weights).items())},
        "P": P,
        "F": F,
        "S": S,
        "H": H,
        "O": O,
        "D": D,
        "N": Ndef,
        "k": k,
        "cost": F + S + H,
        "coordinate_check_cost": O + Ndef + H,
        "coordinate_check_D": 5 * O - P,
        "coordinate_check_P": 120 + F,
        "coordinate_check_length": 867 + k + Ndef + H,
        "input_sha256": hashlib.sha256("".join(symbols).encode("ascii")).hexdigest(),
        "e_orbit_start_count_histogram": {str(m): c for m, c in sorted(Counter(e_orbit_start_counts.values()).items())},
        "hexagon_start_multiplicity_histogram": {str(m): c for m, c in sorted(Counter(hexagon_start_counts.values()).items())},
    }
    if O == 25 and all(count == 5 for count in e_orbit_start_counts.values()):
        selected_orbits = tuple(sorted(e_orbit_start_counts))
        saturated = Skeleton(selected_orbits[:-1], selected_orbits[-1])
        model_lengths = fixed_arc_lengths(saturated)
        result["saturated_port_model"] = {
            "selected_e_orbits": list(selected_orbits),
            "arc_lengths_match_actual_passes": all(model_lengths[p] == pass_lengths[p] for p in pass_lengths),
            "w2_cycle_count": len(cycle_decomposition(w2_permutation(saturated)[1])),
        }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def maximal_overlap_concat(prefix: Tuple[int, ...], suffix: Tuple[int, ...]) -> Tuple[int, ...]:
    for overlap in range(min(len(prefix), len(suffix)), -1, -1):
        if prefix[len(prefix) - overlap :] == suffix[:overlap]:
            return prefix + suffix[overlap:]
    raise AssertionError("overlap zero must work")


def standard_superpermutation(n: int) -> Tuple[int, ...]:
    """The classical recursive construction of length sum_{i=1}^n i!."""
    if not 1 <= n <= 9:
        raise ValueError("this digit-output implementation accepts 1 <= n <= 9")
    word: Tuple[int, ...] = (0,)
    for current_n in range(2, n + 1):
        old_n = current_n - 1
        seen: Set[Tuple[int, ...]] = set()
        order: List[Tuple[int, ...]] = []
        for index in range(len(word) - old_n + 1):
            candidate = word[index : index + old_n]
            if set(candidate) == set(range(old_n)) and candidate not in seen:
                seen.add(candidate)
                order.append(candidate)
        if len(order) != len(list(permutations(range(old_n)))):
            raise AssertionError("recursive input did not contain each smaller permutation")
        blocks = [p + (old_n,) + p for p in order]
        word = blocks[0]
        for block in blocks[1:]:
            word = maximal_overlap_concat(word, block)
    return word


def cmd_generate_standard(args: argparse.Namespace) -> None:
    word = standard_superpermutation(args.n)
    expected = sum(math_factorial(i) for i in range(1, args.n + 1))
    if len(word) != expected:
        raise AssertionError(f"standard length {len(word)} != {expected}")
    text_word = "".join(str(x) for x in word)
    if args.output:
        Path(args.output).write_text(text_word + "\n", encoding="ascii")
    print(json.dumps({
        "n": args.n,
        "length": len(word),
        "expected_length": expected,
        "sha256": hashlib.sha256(text_word.encode("ascii")).hexdigest(),
        "output": args.output,
    }, indent=2))


def cmd_lift_classes(args: argparse.Namespace) -> None:
    """Run the exact port-lift DP once per left-S6 class from classify-c20."""
    partitions = load_partitions(args.partitions)
    classes = json.loads(Path(args.classes).read_text(encoding="utf-8"))["classes"]
    if args.limit is not None:
        classes = classes[: args.limit]
    rows: List[Dict[str, object]] = []
    summary: Counter = Counter()
    for class_index, row in enumerate(classes):
        source = row["first_input_member"]
        partition_index = int(source["partition_index"])
        extra = int(source["extra_orbit"])
        data = port_lift_dp(Skeleton(partitions[partition_index], extra), args.heavy)
        verdict = "survives" if data["min_heavy_to_cover_all_cycles"] is not None else "fails"
        summary[verdict] += 1
        summary[f"max={data['max_cycles_reached']}"] += 1
        rows.append({
            "class_index": class_index,
            "members_in_input": row["members_in_input"],
            "partition_index": partition_index,
            "extra_orbit": extra,
            "verdict": verdict,
            **data,
        })
    result = {
        "classes_scanned": len(classes),
        "heavy_budget": args.heavy,
        "summary": dict(summary),
        "rows": rows,
        "note": "Each row is a complete port-lift result for one actual left-S6 class representative from the supplied finite sample.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "classes_scanned": result["classes_scanned"],
        "summary": result["summary"],
        "output": args.output,
    }, indent=2))


def cmd_random_cover(args: argparse.Namespace) -> None:
    """Try to falsify the unproved '24-partition plus one' normal form.

    This is deliberately an *experiment*, not an enumeration: it searches for
    a 25-element family of E-orbits covering every hexagon but containing no
    24-orbit exact partition.  A witness invalidates the normal-form premise.
    Failure to find one proves nothing.
    """
    exact = {frozenset(row) for row in load_partitions(args.partitions)}
    rng = random.Random(args.seed)
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    witness = None
    successes = 0
    decomposable = 0
    for _trial in range(args.trials):
        selected: Set[int] = {0}  # harmless symmetry breaking for this experiment
        cover: Counter = Counter(KSETS[0])
        while len(selected) < 25:
            uncovered = [h for h in range(120) if cover[h] == 0]
            if uncovered:
                h = min(uncovered, key=lambda z: sum(q not in selected for q in by_hex[z]))
                candidates = [q for q in by_hex[h] if q not in selected]
                scores = [sum(cover[z] == 0 for z in KSETS[q]) for q in candidates]
                top = max(scores)
                # Occasionally accept a one-less-greedy move; otherwise the
                # search only reproduces exact partitions plus an extra block.
                floor = top - (1 if rng.random() < 0.35 else 0)
                candidates = [q for q, score in zip(candidates, scores) if score >= floor]
                qid = rng.choice(candidates)
            else:
                qid = rng.choice([q for q in range(len(KSETS)) if q not in selected])
            selected.add(qid)
            cover.update(KSETS[qid])
        if all(cover[h] >= 1 for h in range(120)):
            successes += 1
            is_decomposable = any(frozenset(selected - {q}) in exact for q in selected)
            if is_decomposable:
                decomposable += 1
            else:
                witness = {
                    "orbits": sorted(selected),
                    "multiplicity_histogram": {str(m): c for m, c in sorted(Counter(cover.values()).items())},
                    "trial": _trial,
                }
                break
    result = {
        "trials": args.trials,
        "seed": args.seed,
        "covers_found": successes,
        "decomposable_covers": decomposable,
        "witness": witness,
        "interpretation": "A non-null witness disproves the 24-exact-partition-plus-one normal form. A null result is only negative experimental evidence.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def cmd_analyze_cover(args: argparse.Namespace) -> None:
    """Analyse an arbitrary 25-E-orbit cover, without a partition normal form."""
    obj = json.loads(Path(args.cover).read_text(encoding="utf-8"))
    if isinstance(obj, dict) and "orbits" not in obj and "witness" in obj:
        obj = obj["witness"]
    orbit_ids = obj.get("orbits") if isinstance(obj, dict) else obj
    orbit_ids = tuple(sorted(int(q) for q in orbit_ids))
    if len(orbit_ids) != 25 or len(set(orbit_ids)) != 25:
        raise ValueError("expected 25 distinct E-orbit IDs")
    cover = Counter(h for q in orbit_ids for h in KSETS[q])
    if any(cover[h] == 0 for h in range(120)):
        raise ValueError("the 25 orbit family does not cover all hexagons")
    exact = {frozenset(row) for row in load_partitions(args.partitions)}
    removable = [q for q in orbit_ids if frozenset(set(orbit_ids) - {q}) in exact]
    result: Dict[str, object] = {
        "orbit_ids": list(orbit_ids),
        "multiplicity_histogram": {str(m): c for m, c in sorted(Counter(cover.values()).items())},
        "removable_orbits_leaving_an_exact_partition": removable,
    }
    # Skeleton is only a container for the 25 IDs here; the analysis below
    # does not assume its first 24 IDs form a partition.  The port model now
    # handles arbitrary cyclic m-way hexagon splits.
    skeleton = Skeleton(orbit_ids[:-1], orbit_ids[-1])
    _ports, successor, _lengths = w2_permutation(skeleton)
    cycle_count = len(cycle_decomposition(successor))
    if cycle_count > 20:
        result["port_lift"] = {"cycle_count": cycle_count, "verdict": "fails: c-1>19"}
    elif cycle_count == 20:
        result["port_lift"] = port_lift_dp(skeleton, args.heavy)
    else:
        result["port_lift"] = {"cycle_count": cycle_count, "verdict": "unexpected: violates five-switch lower bound"}
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def random_25_cover(rng: random.Random, by_hex: Dict[int, List[int]], slack: int = 1) -> Tuple[Set[int], Counter]:
    """One randomized greedy 25-block cover attempt (may fail to cover)."""
    selected: Set[int] = {0}
    cover: Counter = Counter(KSETS[0])
    while len(selected) < 25:
        uncovered = [h for h in range(120) if cover[h] == 0]
        if uncovered:
            h = min(uncovered, key=lambda z: sum(q not in selected for q in by_hex[z]))
            candidates = [q for q in by_hex[h] if q not in selected]
            scores = [sum(cover[z] == 0 for z in KSETS[q]) for q in candidates]
            top = max(scores)
            floor = top - (slack if rng.random() < 0.65 else 0)
            candidates = [q for q, score in zip(candidates, scores) if score >= floor]
            qid = rng.choice(candidates)
        else:
            qid = rng.choice([q for q in range(len(KSETS)) if q not in selected])
        selected.add(qid)
        cover.update(KSETS[qid])
    return selected, cover


def cmd_sample_covers(args: argparse.Namespace) -> None:
    """Experimental sampling of general 25-orbit covers and their c=20 lift."""
    exact = {frozenset(row) for row in load_partitions(args.partitions)}
    rng = random.Random(args.seed)
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    rows: List[Dict[str, object]] = []
    cycle_histogram: Counter = Counter()
    verdicts: Counter = Counter()
    for trial in range(args.trials):
        if len(rows) >= args.wanted:
            break
        selected, cover = random_25_cover(rng, by_hex, args.slack)
        if not all(cover[h] >= 1 for h in range(120)):
            continue
        orbit_ids = tuple(sorted(selected))
        decomposable = any(frozenset(selected - {q}) in exact for q in selected)
        row: Dict[str, object] = {
            "trial": trial,
            "orbits": list(orbit_ids),
            "decomposable": decomposable,
            "multiplicity_histogram": {str(m): c for m, c in sorted(Counter(cover.values()).items())},
        }
        skeleton = Skeleton(orbit_ids[:-1], orbit_ids[-1])
        _ports, successor, _lengths = w2_permutation(skeleton)
        cycle_count = len(cycle_decomposition(successor))
        row["cycle_count"] = cycle_count
        cycle_histogram[cycle_count] += 1
        if cycle_count > 20:
            row["port_lift_verdict"] = "fails: c-1>19"
        elif cycle_count == 20:
            dp = port_lift_dp(skeleton, args.heavy)
            row["port_lift"] = dp
            row["port_lift_verdict"] = "survives" if dp["min_heavy_to_cover_all_cycles"] is not None else "fails"
        else:
            row["port_lift_verdict"] = "unexpected: c<20"
        verdicts[row["port_lift_verdict"]] += 1
        rows.append(row)
    result = {
        "trials_budget": args.trials,
        "covers_sampled": len(rows),
        "seed": args.seed,
        "heavy_budget": args.heavy,
        "cycle_histogram": {str(k): v for k, v in sorted(cycle_histogram.items())},
        "verdict_histogram": dict(verdicts),
        "rows": rows,
        "interpretation": "Experimental only.  A survivor would refute this necessary-condition filter; universal failure would still require exhaustive cover enumeration or an invariant.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "covers_sampled": result["covers_sampled"],
        "cycle_histogram": result["cycle_histogram"],
        "verdict_histogram": result["verdict_histogram"],
        "output": args.output,
    }, indent=2))


def cmd_enumerate_nonpartition_covers(args: argparse.Namespace) -> None:
    """Enumerate a bounded prefix of non-decomposable 25-orbit covers.

    We fix orbit 0.  This loses no left-S6 orbit, since left S6 is transitive
    on the 144 E-orbits.  A cover which is already complete after 24 blocks
    contains an exact partition and is discarded; hence every retained leaf
    first completes the 120 hexagons at depth 25.
    """
    if args.quotient:
        cmd_enumerate_nonpartition_covers_quotient(args)
        return
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    solutions: List[Tuple[int, ...]] = []
    solution_set: Set[Tuple[int, ...]] = set()
    seen: Set[Tuple[int, ...]] = set()
    cover = [0] * 120
    for h in KSETS[0]:
        cover[h] += 1
    nodes = 0
    aborted = False

    def recurse(selected: Set[int], covered_count: int) -> None:
        nonlocal nodes, aborted
        if aborted or len(solutions) >= args.limit:
            return
        nodes += 1
        if nodes > args.node_limit:
            aborted = True
            return
        key = tuple(sorted(selected))
        if key in seen:
            return
        seen.add(key)
        depth = len(selected)
        if covered_count == 120:
            # At depth <=24 this is an exact partition plus possible extras;
            # it cannot yield a non-decomposable 25-cover.
            return
        if depth == 25:
            return
        remaining_slots = 25 - depth
        uncovered_count = 120 - covered_count
        if (uncovered_count + 4) // 5 > remaining_slots:
            return
        if 5 * depth - covered_count > 5:
            return
        uncovered = [h for h in range(120) if cover[h] == 0]
        h = min(uncovered, key=lambda z: sum(q not in selected for q in by_hex[z]))
        for qid in by_hex[h]:
            if qid in selected:
                continue
            changed: List[int] = []
            added_covered = 0
            for z in KSETS[qid]:
                if cover[z] == 0:
                    added_covered += 1
                cover[z] += 1
                changed.append(z)
            selected.add(qid)
            new_covered = covered_count + added_covered
            if len(selected) == 25 and new_covered == 120:
                solution = tuple(sorted(selected))
                if solution not in solution_set:
                    solution_set.add(solution)
                    solutions.append(solution)
            else:
                recurse(selected, new_covered)
            selected.remove(qid)
            for z in changed:
                cover[z] -= 1

    recurse({0}, len(KSETS[0]))
    result = {
        "fixed_orbit": 0,
        "solutions_found": len(solutions),
        "node_count": nodes,
        "node_limit": args.node_limit,
        "aborted_at_node_limit": aborted,
        "solutions": [list(s) for s in solutions],
        "note": "Every output is a 25-orbit cover which first completes at depth 25, hence contains no 24-orbit exact partition.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "solutions_found": result["solutions_found"],
        "node_count": nodes,
        "aborted_at_node_limit": aborted,
        "output": args.output,
    }, indent=2))


def cmd_complete_seed_cover(args: argparse.Namespace) -> None:
    """Try to extend a prescribed orbit set to a saturated 25-orbit cover.

    This is a falsification tool for proposed local obstructions.  It makes no
    symmetry or normal-form assumption and preserves the exact excess bound.
    """
    seed = tuple(sorted(int(token) for token in args.seed.split(",") if token.strip()))
    if not seed or len(seed) != len(set(seed)) or any(not 0 <= qid < len(E_REPS) for qid in seed):
        raise ValueError("--seed must be a nonempty comma-separated set of distinct E-orbit IDs")
    if len(seed) > 25:
        raise ValueError("seed has more than 25 E-orbits")
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    selected: Set[int] = set(seed)
    counts = [0] * 120
    for qid in selected:
        for h in KSETS[qid]:
            counts[h] += 1
    nodes = 0
    aborted = False
    solution: Tuple[int, ...] | None = None

    def recurse() -> None:
        nonlocal nodes, aborted, solution
        if aborted or solution is not None:
            return
        nodes += 1
        if nodes > args.node_limit:
            aborted = True
            return
        depth = len(selected)
        covered = sum(count > 0 for count in counts)
        excess = 5 * depth - covered
        if excess > 5:
            return
        if depth == 25:
            if covered == 120:
                solution = tuple(sorted(selected))
            return
        if (120 - covered + 4) // 5 > 25 - depth:
            return
        uncovered = [h for h, count in enumerate(counts) if count == 0]
        if not uncovered:
            return

        def legal(qid: int) -> bool:
            return qid not in selected and excess + sum(counts[h] > 0 for h in KSETS[qid]) <= 5

        h = min(uncovered, key=lambda z: sum(legal(qid) for qid in by_hex[z]))
        for qid in by_hex[h]:
            if not legal(qid):
                continue
            selected.add(qid)
            for z in KSETS[qid]:
                counts[z] += 1
            recurse()
            for z in KSETS[qid]:
                counts[z] -= 1
            selected.remove(qid)

    recurse()
    result: Dict[str, object] = {
        "seed": list(seed),
        "node_count": nodes,
        "node_limit": args.node_limit,
        "aborted_at_node_limit": aborted,
        "solution": list(solution) if solution is not None else None,
    }
    if solution is not None:
        skeleton = Skeleton(solution[:-1], solution[-1])
        _ports, successor, _lengths = w2_permutation(skeleton)
        result["ribbon"] = {
            "cycle_count": len(cycle_decomposition(successor)),
            **port_ribbon_invariants(skeleton, successor),
        }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "node_count": nodes,
        "aborted_at_node_limit": aborted,
        "found": solution is not None,
        "ribbon": result.get("ribbon"),
        "output": args.output,
    }, indent=2))


def cmd_enumerate_positive_genus_cores(args: argparse.Namespace) -> None:
    """Enumerate connected small E-orbit families with positive ribbon genus.

    The root orbit is fixed to 0 and every child is left-S6 canonicalized;
    transitivity makes this complete up to value relabeling for connected
    families.  The command is intended for the excess-five core reduction,
    hence its default maximum size is five.
    """
    if not 1 <= args.max_size <= 5:
        raise ValueError("--max-size must lie in 1..5")
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    states: Set[int] = {1}
    positive: List[int] = []
    invariants: Dict[int, Dict[str, int]] = {}
    level_counts: List[Dict[str, int]] = []
    for depth in range(1, args.max_size + 1):
        next_states: Set[int] = set()
        level_positive = 0
        for mask in states:
            ids = ids_from_mask(mask)
            data = ribbon_invariants_for_orbits(ids)
            invariants[mask] = data
            if data["ribbon_genus"] > 0:
                positive.append(mask)
                level_positive += 1
            if depth == args.max_size:
                continue
            covered = 0
            for qid in ids:
                covered |= KSET_BITSETS[qid]
            candidates: Set[int] = set()
            for h in range(120):
                if covered & (1 << h):
                    candidates.update(by_hex[h])
            for qid in candidates:
                if mask & (1 << qid):
                    continue
                child = canonical_orbit_mask(mask | (1 << qid))
                child_covered = 0
                for child_qid in iter_mask_ids(child):
                    child_covered |= KSET_BITSETS[child_qid]
                if 5 * (depth + 1) - child_covered.bit_count() <= args.max_excess:
                    next_states.add(child)
        level_counts.append({"size": depth, "connected_classes": len(states), "positive_genus_classes": level_positive})
        states = next_states

    minimal: List[int] = []
    for mask in positive:
        ids = ids_from_mask(mask)
        has_positive_proper_subset = False
        for size in range(1, len(ids)):
            for subset in combinations(ids, size):
                if ribbon_invariants_for_orbits(subset)["ribbon_genus"] > 0:
                    has_positive_proper_subset = True
                    break
            if has_positive_proper_subset:
                break
        if not has_positive_proper_subset:
            minimal.append(mask)
    result = {
        "root_orbit": 0,
        "max_size": args.max_size,
        "max_excess": args.max_excess,
        "level_counts": level_counts,
        "positive_genus_classes": [
            {"orbits": list(ids_from_mask(mask)), **invariants[mask]}
            for mask in positive
        ],
        "minimal_positive_genus_classes": [
            {"orbits": list(ids_from_mask(mask)), **invariants[mask]}
            for mask in minimal
        ],
        "note": "Complete up to left-S6 for connected families within the stated size/excess bounds.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "level_counts": level_counts,
        "positive_genus_classes": len(positive),
        "minimal_positive_genus_classes": len(minimal),
        "output": args.output,
    }, indent=2))


def cmd_enumerate_triple_hex_seeds(args: argparse.Namespace) -> None:
    """Classify three E-orbits meeting one hexagon under left S6.

    A saturated cover with a hexagon of multiplicity at least three contains
    one such seed.  The excess filter is monotone under extension.
    """
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    raw: Set[Tuple[int, ...]] = set()
    classes: Dict[Tuple[int, ...], List[Tuple[int, ...]]] = defaultdict(list)
    for qids in by_hex.values():
        for triple in combinations(qids, 3):
            triple = tuple(sorted(triple))
            covered = 0
            for qid in triple:
                covered |= KSET_BITSETS[qid]
            if 15 - covered.bit_count() > args.max_excess:
                continue
            if triple in raw:
                continue
            raw.add(triple)
            canonical = ids_from_mask(canonical_orbit_mask(sum(1 << qid for qid in triple)))
            classes[canonical].append(triple)
    serialised = []
    for representative, members in sorted(classes.items()):
        serialised.append({
            "orbits": list(representative),
            "raw_members": len(members),
            **ribbon_invariants_for_orbits(representative),
        })
    result = {
        "max_excess": args.max_excess,
        "raw_triples": len(raw),
        "left_s6_classes": serialised,
        "note": "Complete for triples sharing a rotation hexagon within the stated excess bound.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "raw_triples": len(raw),
        "left_s6_classes": len(serialised),
        "representatives": [entry["orbits"] for entry in serialised],
        "output": args.output,
    }, indent=2))


@lru_cache(maxsize=1)
def left_s6_bit_images() -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(1 << image for image in action) for action in left_s6_e_actions())


@lru_cache(maxsize=1)
def left_s6_actions_to_orbit_zero() -> Tuple[Tuple[int, ...], ...]:
    """For each source orbit q, the five left-S6 actions sending q to 0."""
    buckets: List[List[int]] = [[] for _ in E_REPS]
    for index, action in enumerate(left_s6_e_actions()):
        for qid, image in enumerate(action):
            if image == 0:
                buckets[qid].append(index)
    assert all(len(bucket) == 5 for bucket in buckets)
    return tuple(tuple(bucket) for bucket in buckets)


def transform_orbit_mask(mask: int, image_bits: Tuple[int, ...]) -> int:
    transformed = 0
    remaining = mask
    while remaining:
        low = remaining & -remaining
        qid = low.bit_length() - 1
        transformed |= image_bits[qid]
        remaining -= low
    return transformed


def iter_mask_ids(mask: int) -> Iterable[int]:
    """Yield the occupied orbit indices of ``mask`` in increasing order."""
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask -= low


def lex_mask_less(left: int, right: int) -> bool:
    """Whether the increasing index-list of ``left`` is lexicographically smaller.

    All masks compared here have the same Hamming weight.  Thus the first
    occupied bit on which they differ decides lexicographic order: the mask
    containing that smaller index is the smaller index-list.  This avoids
    constructing a 25-tuple for every candidate group image.
    """
    difference = left ^ right
    if not difference:
        return False
    first = difference & -difference
    return bool(left & first)


@lru_cache(maxsize=250_000)
def canonical_orbit_mask(mask: int) -> int:
    """Lexicographic left-S6 canonical image of a nonempty orbit set.

    A lex-minimal image necessarily contains orbit 0: some selected orbit can
    be sent to 0 by transitivity.  Hence it suffices to inspect the 5d group
    elements sending one of the d selected orbits to 0, rather than all 720.
    """
    if not mask:
        return 0
    actions_to_zero = left_s6_actions_to_orbit_zero()
    image_bits = left_s6_bit_images()
    best_mask: int | None = None
    for qid in iter_mask_ids(mask):
        for action_index in actions_to_zero[qid]:
            candidate = transform_orbit_mask(mask, image_bits[action_index])
            if best_mask is None or lex_mask_less(candidate, best_mask):
                best_mask = candidate
    assert best_mask is not None
    return best_mask


def ids_from_mask(mask: int) -> Tuple[int, ...]:
    return tuple(iter_mask_ids(mask))


@lru_cache(maxsize=500_000)
def forest_cover_state(mask: int) -> Dict[str, object]:
    """Exact collision data for a partial family of E-orbits.

    The returned state is the concrete version of

        (C, H_double, G_col).

    It is reconstructed from ``C`` rather than incrementally transported
    because every accepted child is immediately replaced by a left-S6
    canonical image.  Reconstruction is only 5|C| incidence operations, and
    prevents a subtle but serious error: carrying labels from a pre-canonical
    child into its canonical image.

    ``collision_is_forest`` means that the orbit multigraph whose edges are
    the currently double-covered hexagons has no loop, parallel-edge cycle,
    or ordinary cycle.  A triple is reported separately, since it is not a
    collision-graph edge at all.
    """
    ids = ids_from_mask(mask)
    first_owner = [-1] * 120
    second_owner = [-1] * 120
    covered_bits = 0
    triples: List[Tuple[int, int, int, int]] = []
    for qid in ids:
        for h in KSETS[qid]:
            covered_bits |= 1 << h
            if first_owner[h] < 0:
                first_owner[h] = qid
            elif second_owner[h] < 0:
                second_owner[h] = qid
            else:
                triples.append((h, first_owner[h], second_owner[h], qid))

    doubles = tuple(
        (h, first_owner[h], second_owner[h])
        for h in range(120)
        if second_owner[h] >= 0
    )
    parent = {qid: qid for qid in ids}

    def find(qid: int) -> int:
        while parent[qid] != qid:
            parent[qid] = parent[parent[qid]]
            qid = parent[qid]
        return qid

    collision_cycle = False
    for _h, left, right in doubles:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            collision_cycle = True
        else:
            parent[root_left] = root_right
    components: Dict[int, List[int]] = defaultdict(list)
    for qid in ids:
        components[find(qid)].append(qid)
    component_partition = tuple(sorted(tuple(sorted(part)) for part in components.values()))
    covered_count = covered_bits.bit_count()
    excess = 5 * len(ids) - covered_count
    return {
        "orbit_ids": ids,
        "depth": len(ids),
        "covered_bits": covered_bits,
        "covered_count": covered_count,
        "excess": excess,
        "double_hexagons": doubles,
        "triple_witnesses": tuple(triples),
        "collision_edge_count": len(doubles),
        "collision_is_forest": not collision_cycle,
        "collision_components": component_partition,
    }


def forest_state_is_admissible(state: Dict[str, object]) -> bool:
    """Necessary, monotone conditions for a target saturated forest cover."""
    if state["triple_witnesses"]:
        return False
    if int(state["excess"]) > 5:
        return False
    if int(state["collision_edge_count"]) > 5:
        return False
    return bool(state["collision_is_forest"])


def forest_child_candidates(mask: int, state: Dict[str, object], by_hex: Dict[int, List[int]]) -> List[int]:
    """Choose the canonical-augmentation branching column.

    If all 120 hexagons are already covered at depth 24, this returns every
    remaining orbit.  That is the indispensable exact-partition-plus-one
    positive-control branch.  Otherwise it returns all orbits through one
    least-constrained uncovered hexagon, as in Algorithm X.
    """
    depth = int(state["depth"])
    covered_bits = int(state["covered_bits"])
    if covered_bits.bit_count() == 120:
        if depth == 24:
            return [qid for qid in range(len(E_REPS)) if not (mask & (1 << qid))]
        return []
    uncovered = [h for h in range(120) if not (covered_bits & (1 << h))]
    h = min(uncovered, key=lambda z: sum(not (mask & (1 << qid)) for qid in by_hex[z]))
    return [qid for qid in by_hex[h] if not (mask & (1 << qid))]


def skeleton_from_orbit_ids(orbit_ids: Sequence[int]) -> Skeleton:
    ids = tuple(sorted(orbit_ids))
    if len(ids) != 25 or len(set(ids)) != 25:
        raise ValueError("a port-lift skeleton requires exactly 25 distinct E-orbits")
    return Skeleton(ids[:-1], ids[-1])


def serialise_perm(word: Perm) -> List[int]:
    return list(word)


def forest_leaf_certificate(mask: int) -> Dict[str, object]:
    """Full reproducible certificate for one canonical saturated forest cover."""
    state = forest_cover_state(mask)
    ids = tuple(state["orbit_ids"])
    if mask != canonical_orbit_mask(mask):
        raise AssertionError("forest leaf is not left-S6 canonical")
    if len(ids) != 25 or int(state["covered_count"]) != 120 or int(state["excess"]) != 5:
        raise AssertionError("not a saturated 25-orbit cover")
    if not forest_state_is_admissible(state) or len(state["double_hexagons"]) != 5:
        raise AssertionError("not a multiplicity-two forest cover")
    if incidence_beta_for_orbits(ids) != 0:
        raise AssertionError("collision forest and incidence beta disagree")
    skeleton = skeleton_from_orbit_ids(ids)
    ports, successor, _lengths = w2_permutation(skeleton)
    cycles = cycle_decomposition(successor)
    ribbon = port_ribbon_invariants(skeleton, successor)
    if ribbon["ribbon_beta1"] != 0 or ribbon["ribbon_genus"] != 0:
        raise AssertionError("forest leaf violates the certified genus-zero reduction")
    if len(cycles) != 20:
        raise AssertionError("forest leaf must have exactly twenty f-cycles")

    dp_at_three = port_lift_dp(skeleton, 3)
    lift_budgets: List[Dict[str, object]] = []
    for summary in dp_at_three["budget_summaries"]:
        heavy = int(summary["heavy_budget"])
        complete = summary["min_heavy_to_cover_all_cycles"] is not None
        lift_budgets.append({
            "heavy_budget": heavy,
            "complete_lift_exists": complete,
            "failure_cause": (
                None if complete else
                "no lifted port path reaches all "
                f"{dp_at_three['cycle_count']} f-cycles within heavy budget {heavy}; "
                f"maximum reached is {summary['max_cycles_reached']}"
            ),
            "exact_reachability": summary,
        })

    # A 24-subset that already covers everything identifies the known
    # exact-partition-plus-one positive-control family.  Its presence is
    # recorded, never silently discarded.
    exact_partition_deletion = None
    for qid in ids:
        substate = forest_cover_state(mask ^ (1 << qid))
        if int(substate["covered_count"]) == 120:
            exact_partition_deletion = qid
            break
    code_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "canonical_cover_representative": list(ids),
        "cover_sha256": stable_sha256(list(ids)),
        "cover_kind": (
            "exact_partition_plus_one" if exact_partition_deletion is not None
            else "nondecomposable_first_full_at_depth_25"
        ),
        "exact_partition_deletion_orbit": exact_partition_deletion,
        "double_hexagons": [
            {"hexagon_id": h, "orbits": [left, right]}
            for h, left, right in state["double_hexagons"]
        ],
        "collision_forest": {
            "edges": [
                {"hexagon_id": h, "orbits": [left, right]}
                for h, left, right in state["double_hexagons"]
            ],
            "component_partition": [list(component) for component in state["collision_components"]],
        },
        "f_definition": "f = rho E = deterministic weight-two port successor",
        "f_cycle_decomposition": {
            "cycle_count": len(cycles),
            "cycle_lengths": [len(cycle) for cycle in cycles],
            "cycles": [[serialise_perm(port) for port in cycle] for cycle in cycles],
        },
        "port_lift_H_0_to_3": lift_budgets,
        "port_lift_common_diagnostics_at_H_3": {
            key: dp_at_three[key]
            for key in (
                "transition_counts", "cycle_transition_arc_count",
                "cycle_transition_scc_sizes", "cycle_transition_weak_component_sizes",
            )
        },
        "ribbon": ribbon,
        "code_sha256": code_sha,
    }


def cmd_forest_depth_seeds(args: argparse.Namespace) -> None:
    """List the canonical partial states at a requested depth.

    These states partition the canonical-augmentation recursion only after
    the final cover classes are deduplicated: a final class can be reachable
    from more than one seed because canonicalization happens after every
    child.  The command is for complete branch accounting, not a claim of a
    disjoint decomposition of final cover classes.
    """
    if not 1 <= args.depth <= 24:
        raise ValueError("--depth must lie in 1..24")
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    current: Set[int] = {0}
    for depth in range(args.depth):
        next_states: Set[int] = set()
        for mask in current:
            state = forest_cover_state(mask)
            if not forest_state_is_admissible(state):
                continue
            for qid in forest_child_candidates(mask, state, by_hex):
                child = canonical_orbit_mask(mask | (1 << qid))
                child_state = forest_cover_state(child)
                if forest_state_is_admissible(child_state):
                    next_states.add(child)
        current = next_states
    result = {
        "depth": args.depth,
        "canonical_seeds": [list(ids_from_mask(mask)) for mask in sorted(current, key=ids_from_mask)],
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "note": "Every seed is a canonical state satisfying the forest invariant. Run enumerate-forest-covers once per seed with --node-limit 0 for complete branch logs.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"depth": args.depth, "seed_count": len(current), "seeds": result["canonical_seeds"], "output": args.output}, indent=2))


def cmd_enumerate_forest_covers(args: argparse.Namespace) -> None:
    """Enumerate saturated multiplicity-two collision-forest covers up to S6.

    This is the F=5, D=N=0 incidence search, before the port-lift test.  The
    forest condition is kept at *every* partial state.  The only symmetry
    reduction is safe canonical augmentation: every candidate child is mapped
    to its left-S6 canonical image and canonical masks are memoized.

    A strict McKay-style ``parent(child)==state`` test is deliberately *not*
    used with least-uncovered-hexagon branching: that combination can reject
    the sole construction order of an extendible cover.  The accompanying
    proof document explains why canonical-child-plus-memoization is complete.
    """
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    seed = 0
    if args.seed:
        parsed = tuple(sorted(int(token) for token in args.seed.split(",") if token.strip()))
        if not parsed or len(parsed) != len(set(parsed)) or any(not 0 <= qid < len(E_REPS) for qid in parsed):
            raise ValueError("--seed must be a nonempty comma-separated set of distinct E-orbit IDs")
        seed = sum(1 << qid for qid in parsed)
        if canonical_orbit_mask(seed) != seed:
            raise ValueError("--seed must already be the left-S6 canonical representative")

    seen: Set[int] = set()
    leaves: List[int] = []
    leaf_set: Set[int] = set()
    prune_counts: Counter[str] = Counter()
    nodes = 0
    aborted = False

    def recurse(mask: int) -> None:
        nonlocal nodes, aborted
        if aborted or (args.limit and len(leaves) >= args.limit):
            return
        nodes += 1
        if args.node_limit and nodes > args.node_limit:
            aborted = True
            return
        if mask in seen:
            prune_counts["seen_canonical_state"] += 1
            return
        if mask != canonical_orbit_mask(mask):
            raise AssertionError("only canonical states may enter the recursion")
        seen.add(mask)
        state = forest_cover_state(mask)
        if state["triple_witnesses"]:
            prune_counts["triple_hexagon"] += 1
            return
        if int(state["excess"]) > 5:
            prune_counts["excess_above_five"] += 1
            return
        if int(state["collision_edge_count"]) > 5:
            prune_counts["more_than_five_collision_edges"] += 1
            return
        if not bool(state["collision_is_forest"]):
            prune_counts["collision_cycle"] += 1
            return
        depth = int(state["depth"])
        covered = int(state["covered_count"])
        if depth == 25:
            if covered == 120 and int(state["excess"]) == 5:
                if mask not in leaf_set:
                    leaf_set.add(mask)
                    leaves.append(mask)
            else:
                prune_counts["depth_25_not_saturated"] += 1
            return
        if covered == 120:
            if depth != 24:
                prune_counts["premature_full_cover"] += 1
                return
            # Exact-partition-plus-one is a positive-control subfamily of the
            # saturated forest covers, and must be extended rather than lost.
        else:
            remaining_slots = 25 - depth
            uncovered = 120 - covered
            if (uncovered + 4) // 5 > remaining_slots:
                prune_counts["remaining_capacity"] += 1
                return
        if depth >= 25:
            return
        for qid in forest_child_candidates(mask, state, by_hex):
            child = canonical_orbit_mask(mask | (1 << qid))
            recurse(child)

    recurse(seed)
    certificates = [forest_leaf_certificate(mask) for mask in sorted(leaves, key=ids_from_mask)]
    result = {
        "search": "forest-only canonical augmentation",
        "canonical_augmentation": "canonical child plus memoization; no unsafe strict parent test",
        "seed": list(ids_from_mask(seed)),
        "node_count": nodes,
        "node_limit": args.node_limit,
        "aborted_at_node_limit": aborted,
        "completed": not aborted and not args.limit,
        "leaf_count": len(certificates),
        "prune_counts": dict(sorted(prune_counts.items())),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "certificates": certificates,
        "scope": "All enumerated objects are 25-E-orbit saturated covers with no triple hexagon and a collision forest. Port-lift failure is a necessary-condition certificate, not yet a full walk obstruction.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "seed": result["seed"],
        "node_count": nodes,
        "aborted_at_node_limit": aborted,
        "completed": result["completed"],
        "leaf_count": len(certificates),
        "prune_counts": result["prune_counts"],
        "output": args.output,
    }, indent=2))


def cmd_merge_forest_certificates(args: argparse.Namespace) -> None:
    """Deduplicate completed depth-split forest runs and regenerate certificates."""
    masks: Set[int] = set()
    source_summaries: List[Dict[str, object]] = []
    for path in args.runs:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        if obj.get("aborted_at_node_limit") or not obj.get("completed"):
            raise ValueError(f"refusing incomplete branch output: {path}")
        certs = obj.get("certificates", [])
        source_summaries.append({"path": path, "leaf_count": len(certs), "seed": obj.get("seed")})
        for cert in certs:
            ids = tuple(int(qid) for qid in cert["canonical_cover_representative"])
            mask = sum(1 << qid for qid in ids)
            if canonical_orbit_mask(mask) != mask:
                raise AssertionError(f"noncanonical certificate in {path}")
            masks.add(mask)
    certificates = [forest_leaf_certificate(mask) for mask in sorted(masks, key=ids_from_mask)]
    result = {
        "merge": "deduplicated canonical forest-cover certificates",
        "source_runs": source_summaries,
        "unique_leaf_count": len(certificates),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "certificates": certificates,
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"unique_leaf_count": len(certificates), "output": args.output}, indent=2))


def cmd_enumerate_nonpartition_covers_quotient(args: argparse.Namespace) -> None:
    """Sound isomorph-free version of the non-partition cover search.

    A child is never discarded merely for being non-canonical.  It is mapped
    to its full left-S6 canonical representative before recursing.  If a
    complete cover extends a current state, the same group element transports
    the unchosen part of that cover, so the canonical child is still
    extendible.  This is the key distinction from unsafe depth-wise
    lexicographic pruning.
    """
    by_hex: Dict[int, List[int]] = defaultdict(list)
    for qid, ks in enumerate(KSETS):
        for h in ks:
            by_hex[h].append(qid)
    seen: Set[int] = set()
    solutions: List[int] = []
    nodes = 0
    aborted = False

    def coverage(mask: int) -> Tuple[int, int]:
        """Union of covered hexagons and its cardinality.

        Multiplicities are unnecessary in this branch: the total excess is
        exactly `5*depth - covered_count`, so a 120-bit union replaces a
        120-entry count vector at every canonical node.
        """
        covered = 0
        for qid in iter_mask_ids(mask):
            covered |= KSET_BITSETS[qid]
        return covered, covered.bit_count()

    def recurse(mask: int) -> None:
        nonlocal nodes, aborted
        if aborted or len(solutions) >= args.limit:
            return
        nodes += 1
        if nodes > args.node_limit:
            aborted = True
            return
        if mask in seen:
            return
        seen.add(mask)
        depth = mask.bit_count()
        covered_bits, covered_count = coverage(mask)
        if args.forest_only and incidence_beta_for_orbits(ids_from_mask(mask)) > 0:
            return
        if depth == 25:
            if covered_count == 120:
                solutions.append(mask)
            return
        if covered_count == 120:
            # A depth-24 completion is an exact partition; adding another
            # orbit would be decomposable, not a target leaf.
            return
        remaining_slots = 25 - depth
        uncovered_count = 120 - covered_count
        if (uncovered_count + 4) // 5 > remaining_slots:
            return
        if 5 * depth - covered_count > 5:
            return
        uncovered = [h for h in range(120) if not (covered_bits & (1 << h))]
        h = min(uncovered, key=lambda z: sum(not (mask & (1 << q)) for q in by_hex[z]))
        for qid in by_hex[h]:
            if mask & (1 << qid):
                continue
            child = canonical_orbit_mask(mask | (1 << qid))
            recurse(child)

    seed = 0
    if args.seed:
        ids = tuple(sorted(int(token) for token in args.seed.split(",") if token.strip()))
        if not ids or len(ids) != len(set(ids)) or any(not 0 <= qid < len(E_REPS) for qid in ids):
            raise ValueError("--seed must be a nonempty comma-separated set of E-orbit IDs")
        seed = sum(1 << qid for qid in ids)
        if canonical_orbit_mask(seed) != seed:
            raise ValueError("--seed must already be the left-S6 canonical representative")
    recurse(seed)
    result = {
        "quotient_mode": "full left-S6 canonical augmentation",
        "seed": list(ids_from_mask(seed)),
        "forest_only": args.forest_only,
        "solutions_found": len(solutions),
        "node_count": nodes,
        "node_limit": args.node_limit,
        "aborted_at_node_limit": aborted,
        "solutions": [list(ids_from_mask(mask)) for mask in solutions],
        "note": "Every output is one left-S6 orbit representative of a non-decomposable 25-orbit cover, provided the search reaches completion.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "quotient_mode": result["quotient_mode"],
        "solutions_found": result["solutions_found"],
        "node_count": nodes,
        "aborted_at_node_limit": aborted,
        "output": args.output,
    }, indent=2))


def load_cover_list(path: str) -> List[Tuple[int, ...]]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = obj["solutions"] if isinstance(obj, dict) and "solutions" in obj else obj
    covers = [tuple(sorted(int(q) for q in row)) for row in rows]
    if any(len(c) != 25 or len(set(c)) != 25 for c in covers):
        raise ValueError("cover list contains a non-25-element row")
    return covers


def canonical_cover(cover: Tuple[int, ...]) -> Tuple[int, ...]:
    return min(tuple(sorted(action[q] for q in cover)) for action in left_s6_e_actions())


def cmd_classify_covers(args: argparse.Namespace) -> None:
    covers = load_cover_list(args.covers)
    classes: Dict[Tuple[int, ...], List[int]] = defaultdict(list)
    for index, cover in enumerate(covers):
        classes[canonical_cover(cover)].append(index)
    serialised = [
        {
            "representative_orbits": list(cover),
            "members_in_input": len(members),
            "first_input_index": members[0],
        }
        for cover, members in sorted(classes.items())
    ]
    result = {
        "input_covers": len(covers),
        "left_s6_orbit_classes_in_input": len(serialised),
        "classes": serialised,
        "note": "A quotient only of the supplied list.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "input_covers": result["input_covers"],
        "left_s6_orbit_classes_in_input": result["left_s6_orbit_classes_in_input"],
        "output": args.output,
    }, indent=2))


def cmd_merge_cover_lists(args: argparse.Namespace) -> None:
    """Merge split quotient searches, removing cross-branch duplicates."""
    raw_count = 0
    classes: Set[Tuple[int, ...]] = set()
    for path in args.covers:
        covers = load_cover_list(path)
        raw_count += len(covers)
        classes.update(canonical_cover(cover) for cover in covers)
    result = {
        "input_files": args.covers,
        "raw_cover_count": raw_count,
        "left_s6_orbit_classes": len(classes),
        "solutions": [list(cover) for cover in sorted(classes)],
        "note": "A merge of finite, possibly incomplete split searches; it makes no completeness claim.",
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "raw_cover_count": raw_count,
        "left_s6_orbit_classes": len(classes),
        "output": args.output,
    }, indent=2))


def cmd_lift_cover_classes(args: argparse.Namespace) -> None:
    covers = load_cover_list(args.covers)
    classes = json.loads(Path(args.classes).read_text(encoding="utf-8"))["classes"]
    if args.limit is not None:
        classes = classes[: args.limit]
    rows: List[Dict[str, object]] = []
    summary: Counter = Counter()
    for class_index, meta in enumerate(classes):
        cover = covers[int(meta["first_input_index"])]
        skeleton = Skeleton(cover[:-1], cover[-1])
        ports, successor, _lengths = w2_permutation(skeleton)
        c = len(cycle_decomposition(successor))
        ribbon = port_ribbon_invariants(skeleton, successor)
        if c > 20:
            result: Dict[str, object] = {"cycle_count": c, "verdict": "fails: c-1>19", **ribbon}
        elif c == 20:
            dp = port_lift_dp(skeleton, args.heavy)
            result = {**dp, "verdict": "survives" if dp["min_heavy_to_cover_all_cycles"] is not None else "fails"}
        else:
            result = {"cycle_count": c, "verdict": "unexpected c<20", **ribbon}
        summary[result["verdict"]] += 1
        rows.append({
            "class_index": class_index,
            "members_in_input": meta["members_in_input"],
            "cover": list(cover),
            **result,
        })
    output = {
        "classes_scanned": len(classes),
        "heavy_budget": args.heavy,
        "summary": dict(summary),
        "rows": rows,
    }
    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"classes_scanned": len(classes), "summary": dict(summary), "output": args.output}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("basic", help="verify finite group conventions and tail counts")
    p.set_defaults(func=cmd_basic)
    p = sub.add_parser("find-partition", help="find one or more 24-E-orbit exact partitions")
    p.add_argument("--limit", type=int, default=1)
    p.add_argument("--output")
    p.set_defaults(func=cmd_find_partition)
    p = sub.add_parser("scan-extra", help="scan all 25th E-orbits over one exact partition")
    p.add_argument("partition", help="JSON from find-partition or a JSON list of 24 orbit IDs")
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--extra", type=int, action="append", help="restrict scan to this 25th E-orbit ID (repeatable)")
    p.add_argument("--lift", action="store_true", help="run the exponential port-lift DP for c=20 skeletons")
    p.add_argument("--output")
    p.set_defaults(func=cmd_scan_extra)
    p = sub.add_parser("scan-partitions", help="survey w=2 cycle counts over a finite list of partitions")
    p.add_argument("partitions", help="JSON emitted by find-partition")
    p.add_argument("--limit", type=int)
    p.add_argument("--indices", help="comma-separated source indices, scanned in the given order")
    p.add_argument("--output")
    p.set_defaults(func=cmd_scan_partitions)
    p = sub.add_parser("lift-candidate", help="run port-lift DP for one partition/extra pair")
    p.add_argument("partitions", help="JSON emitted by find-partition")
    p.add_argument("partition_index", type=int)
    p.add_argument("extra_orbit", type=int)
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--output")
    p.set_defaults(func=cmd_lift_candidate)
    p = sub.add_parser("classify-c20", help="quotient sampled c=20 skeletons by the genuine left S6 action")
    p.add_argument("partitions", help="JSON emitted by find-partition")
    p.add_argument("survey", help="JSON emitted by scan-partitions")
    p.add_argument("--output")
    p.set_defaults(func=cmd_classify_c20)
    p = sub.add_parser("classify-partitions", help="quotient a finite partition list by left S6")
    p.add_argument("partitions", help="JSON emitted by find-partition")
    p.add_argument("--limit", type=int)
    p.add_argument("--output")
    p.set_defaults(func=cmd_classify_partitions)
    p = sub.add_parser("verify-word", help="verify an explicit no-repeat n=6 superpermutation word")
    p.add_argument("word", help="text file containing exactly six digit symbols (whitespace is ignored)")
    p.add_argument("--output")
    p.set_defaults(func=cmd_verify_word)
    p = sub.add_parser("generate-standard", help="generate the classical recursive standard superpermutation")
    p.add_argument("n", type=int)
    p.add_argument("--output")
    p.set_defaults(func=cmd_generate_standard)
    p = sub.add_parser("lift-classes", help="port-lift all representatives from classify-c20")
    p.add_argument("partitions", help="JSON emitted by find-partition")
    p.add_argument("classes", help="JSON emitted by classify-c20")
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--limit", type=int)
    p.add_argument("--output")
    p.set_defaults(func=cmd_lift_classes)
    p = sub.add_parser("random-cover", help="experimental search for non-decomposable 25-orbit covers")
    p.add_argument("partitions", help="complete exact-partition JSON from find-partition")
    p.add_argument("--trials", type=int, default=10000)
    p.add_argument("--seed", type=int, default=20260722)
    p.add_argument("--output")
    p.set_defaults(func=cmd_random_cover)
    p = sub.add_parser("analyze-cover", help="analyse a general 25-E-orbit hexagon cover")
    p.add_argument("partitions", help="complete exact-partition JSON from find-partition")
    p.add_argument("cover", help="JSON list of 25 IDs or a random-cover witness JSON")
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--output")
    p.set_defaults(func=cmd_analyze_cover)
    p = sub.add_parser("sample-covers", help="experimental sample of general 25-orbit covers")
    p.add_argument("partitions", help="complete exact-partition JSON from find-partition")
    p.add_argument("--wanted", type=int, default=50)
    p.add_argument("--trials", type=int, default=100000)
    p.add_argument("--seed", type=int, default=20260722)
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--slack", type=int, default=1, help="greedy new-coverage slack; higher values sample more overlap")
    p.add_argument("--output")
    p.set_defaults(func=cmd_sample_covers)
    p = sub.add_parser("enumerate-nonpartition-covers", help="bounded exact search for non-partition 25-orbit covers")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--node-limit", type=int, default=1_000_000)
    p.add_argument("--quotient", action="store_true", help="use sound full-left-S6 canonical augmentation")
    p.add_argument("--forest-only", action="store_true", help="prune partial incidence graphs with positive cycle rank")
    p.add_argument("--seed", help="canonical comma-separated orbit IDs at which to start quotient search")
    p.add_argument("--output")
    p.set_defaults(func=cmd_enumerate_nonpartition_covers)
    p = sub.add_parser("forest-depth-seeds", help="emit canonical forest-only augmentation states at a fixed depth")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--output")
    p.set_defaults(func=cmd_forest_depth_seeds)
    p = sub.add_parser("enumerate-forest-covers", help="complete forest-only saturated-cover enumeration with lift certificates")
    p.add_argument("--seed", help="canonical comma-separated orbit IDs at which to start")
    p.add_argument("--node-limit", type=int, default=0, help="0 means no node limit")
    p.add_argument("--limit", type=int, default=0, help="0 means no leaf limit")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_enumerate_forest_covers)
    p = sub.add_parser("merge-forest-certificates", help="merge completed depth-split forest-only enumeration runs")
    p.add_argument("runs", nargs="+", help="completed JSON outputs from enumerate-forest-covers")
    p.add_argument("--output", required=True)
    p.set_defaults(func=cmd_merge_forest_certificates)
    p = sub.add_parser("complete-seed-cover", help="try to extend a prescribed orbit set to a saturated 25-orbit cover")
    p.add_argument("--seed", required=True, help="comma-separated distinct E-orbit IDs; no symmetry assumption")
    p.add_argument("--node-limit", type=int, default=1_000_000)
    p.add_argument("--output")
    p.set_defaults(func=cmd_complete_seed_cover)
    p = sub.add_parser("enumerate-positive-genus-cores", help="enumerate connected small positive-genus E-orbit cores")
    p.add_argument("--max-size", type=int, default=5)
    p.add_argument("--max-excess", type=int, default=5)
    p.add_argument("--output")
    p.set_defaults(func=cmd_enumerate_positive_genus_cores)
    p = sub.add_parser("enumerate-triple-hex-seeds", help="classify low-excess triples meeting one hexagon")
    p.add_argument("--max-excess", type=int, default=5)
    p.add_argument("--output")
    p.set_defaults(func=cmd_enumerate_triple_hex_seeds)
    p = sub.add_parser("classify-covers", help="quotient a finite 25-orbit cover list by left S6")
    p.add_argument("covers", help="JSON emitted by enumerate-nonpartition-covers")
    p.add_argument("--output")
    p.set_defaults(func=cmd_classify_covers)
    p = sub.add_parser("merge-cover-lists", help="merge split finite cover lists and deduplicate by left S6")
    p.add_argument("covers", nargs="+", help="JSON cover lists emitted by quotient search")
    p.add_argument("--output")
    p.set_defaults(func=cmd_merge_cover_lists)
    p = sub.add_parser("lift-cover-classes", help="run general port-lift on cover-class representatives")
    p.add_argument("covers", help="JSON emitted by enumerate-nonpartition-covers")
    p.add_argument("classes", help="JSON emitted by classify-covers")
    p.add_argument("--heavy", type=int, default=3)
    p.add_argument("--limit", type=int)
    p.add_argument("--output")
    p.set_defaults(func=cmd_lift_cover_classes)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
