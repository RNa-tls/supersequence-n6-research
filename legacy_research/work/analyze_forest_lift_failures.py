"""Read-only structural analysis of completed forest-cover certificates.

Scope
-----
This program reads only completed ``forest_branch_0_2.json`` and
``forest_branch_0_3.json`` certificates.  It neither enumerates covers nor
edits any branch output, runner, or generator.  The exact port-lift DP is not
reimplemented here: its serialized H=0,...,3 summaries are treated as the
authoritative reachability results.  The only group machinery reused from the
main program is the existing port-transition API (``w2_permutation`` and
``deep_edges``), used to form a deliberately weaker phase-aware diagnostic
graph.

The diagnostic graph has states (f-cycle, forced exit port, heavy spent).
It omits the DP's visited-cycle mask, so it can expose local transport and
SCC structure but cannot certify or refute a no-revisit port lift by itself.
Every graph construction is checked against the certificate's H=3 collapsed
cycle-transition diagnostics.

Run from the repository root:

    & $py work/analyze_forest_lift_failures.py

Outputs are written under ``outputs/`` and record this source SHA-256 plus
the SHA-256 values of both read-only inputs.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
INPUT_NAMES = ("forest_branch_0_2.json", "forest_branch_0_3.json")
CORE_PATH = ROOT / "work" / "superperm_port_lift.py"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_core() -> Any:
    spec = importlib.util.spec_from_file_location("forest_port_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_completed_branch(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("completed", "node_limit", "seed", "certificates", "code_sha256")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{path.name}: missing top-level keys {missing}")
    if data["completed"] is not True or data["node_limit"] != 0:
        raise ValueError(f"{path.name}: not an unlimited completed branch")
    if not isinstance(data["certificates"], list):
        raise ValueError(f"{path.name}: certificates is not a list")
    differing_certificate_sha = [
        cert.get("cover_sha256", "<missing>")
        for cert in data["certificates"]
        if cert.get("code_sha256") != data["code_sha256"]
    ]
    if differing_certificate_sha:
        raise ValueError(f"{path.name}: certificate code SHA mismatch")
    return data


def first_empty_layer(layer_counts: Sequence[int]) -> int | None:
    """Return one-based cycle-cardinality of first empty DP layer, if any."""
    for cardinality, count in enumerate(layer_counts, start=1):
        if count == 0:
            return cardinality
    return None


def canonical_tree_adjacency(vertices: Sequence[int], edges: Sequence[tuple[int, int]]) -> str:
    """Exact small-tree topology code, independent of orbit labels.

    The collision forest has only five edges, so a component has at most six
    vertices.  Exhausting at most 6! labelings is inexpensive and avoids a
    degree-sequence-only ambiguity.
    """
    vertices = tuple(vertices)
    edge_set = {frozenset(edge) for edge in edges}
    best: tuple[int, ...] | None = None
    for ordering in itertools.permutations(vertices):
        bits = tuple(
            int(frozenset((ordering[i], ordering[j])) in edge_set)
            for i in range(len(ordering))
            for j in range(i + 1, len(ordering))
        )
        if best is None or bits < best:
            best = bits
    return "".join(map(str, best or ()))


def classify_tree(vertex_count: int, degrees: Sequence[int]) -> str:
    if vertex_count == 1:
        return "isolated"
    maximum = max(degrees)
    if maximum <= 2:
        return "path"
    if maximum == vertex_count - 1:
        return "star"
    return "mixed"


def forest_features(cert: dict[str, Any]) -> tuple[dict[str, Any], dict[int, int], list[dict[str, Any]]]:
    """Collision-forest features and maps from orbit/edge to component."""
    components = [tuple(component) for component in cert["collision_forest"]["component_partition"]]
    edge_rows = cert["collision_forest"]["edges"]
    edges = [tuple(row["orbits"]) for row in edge_rows]
    orbit_component: dict[int, int] = {}
    component_rows: list[dict[str, Any]] = []
    edge_component: list[int] = []
    for component_index, component in enumerate(components):
        for orbit in component:
            if orbit in orbit_component:
                raise AssertionError("orbit occurs in more than one forest component")
            orbit_component[orbit] = component_index
        local_edges = [edge for edge in edges if edge[0] in component and edge[1] in component]
        degrees = Counter(orbit for edge in local_edges for orbit in edge)
        degree_sequence = tuple(sorted(degrees.get(orbit, 0) for orbit in component))
        component_rows.append({
            "orbits": list(component),
            "size": len(component),
            "edge_count": len(local_edges),
            "degree_sequence": list(degree_sequence),
            "max_degree": max(degree_sequence),
            "tree_type": classify_tree(len(component), degree_sequence),
            "topology_code": canonical_tree_adjacency(component, local_edges),
        })
    for edge in edges:
        left = orbit_component[edge[0]]
        right = orbit_component[edge[1]]
        if left != right:
            raise AssertionError("collision edge crosses a recorded forest component")
        edge_component.append(left)
    nonisolated = [row for row in component_rows if row["edge_count"]]
    component_partition = tuple(sorted((row["size"] for row in component_rows), reverse=True))
    topology_signature = tuple(sorted(
        (row["size"], tuple(row["degree_sequence"]), row["topology_code"])
        for row in component_rows
    ))
    return ({
        "component_size_partition": list(component_partition),
        "isolated_component_count": sum(row["size"] == 1 for row in component_rows),
        "edge_component_count": len(nonisolated),
        "edge_distribution_among_components": sorted(row["edge_count"] for row in nonisolated),
        "max_tree_degree": max(row["max_degree"] for row in component_rows),
        "tree_type_counts": dict(sorted(Counter(row["tree_type"] for row in component_rows).items())),
        "component_rows": component_rows,
        "topology_signature": [list(item) for item in topology_signature],
    }, orbit_component, [{"edge": list(edge), "component": comp} for edge, comp in zip(edges, edge_component)])


def edge_automorphism_orders(edges: Sequence[tuple[int, int]]) -> list[tuple[int, ...]]:
    """All collision-edge relabelings preserving the forest line graph.

    There are exactly five collision edges, so trying all 5! orders is both
    exact and clearer than relying on a graph-library hash.  The minimum line
    graph encoding makes the resulting incidence fingerprint independent of
    the certificate's edge order.
    """
    count = len(edges)
    adjacent = [[False] * count for _ in range(count)]
    for i, left in enumerate(edges):
        for j, right in enumerate(edges):
            if i != j:
                adjacent[i][j] = bool(set(left) & set(right))
    encodings: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for ordering in itertools.permutations(range(count)):
        code = tuple(
            int(adjacent[ordering[i]][ordering[j]])
            for i in range(count)
            for j in range(i + 1, count)
        )
        encodings.append((code, ordering))
    minimum = min(code for code, _ordering in encodings)
    return [ordering for code, ordering in encodings if code == minimum]


def dp_features(cert: dict[str, Any]) -> dict[str, Any]:
    levels = cert["port_lift_H_0_to_3"]
    if len(levels) != 4:
        raise ValueError("certificate does not contain exactly H=0,1,2,3 summaries")
    out = []
    for expected_budget, item in enumerate(levels):
        exact = item["exact_reachability"]
        if item["heavy_budget"] != expected_budget or exact["heavy_budget"] != expected_budget:
            raise AssertionError("inconsistent serialized heavy budget")
        layers = list(exact["layer_state_counts"])
        out.append({
            "heavy_budget": expected_budget,
            "complete_lift_exists": item["complete_lift_exists"],
            "max_cycles_reached": exact["max_cycles_reached"],
            "dp_states": exact["dp_states"],
            "layer_state_counts": layers,
            "layer_cycle_mask_counts": list(exact["layer_cycle_mask_counts"]),
            "first_empty_layer": first_empty_layer(layers),
        })
    h3 = out[3]
    return {
        "by_heavy_budget": out,
        "h3_profile": {
            "max_cycles_reached": h3["max_cycles_reached"],
            "dp_states": h3["dp_states"],
            "first_empty_layer": h3["first_empty_layer"],
            "layer_state_counts": h3["layer_state_counts"],
        },
    }


def kosaraju(vertices: Iterable[Any], arcs: Iterable[tuple[Any, Any]]) -> list[list[Any]]:
    """Iterative SCC decomposition for a small, JSON-friendly diagnostic graph."""
    vertices = list(vertices)
    forward: dict[Any, list[Any]] = {vertex: [] for vertex in vertices}
    backward: dict[Any, list[Any]] = {vertex: [] for vertex in vertices}
    for left, right in arcs:
        forward.setdefault(left, []).append(right)
        backward.setdefault(right, []).append(left)
    seen: set[Any] = set()
    finish: list[Any] = []
    for root in vertices:
        if root in seen:
            continue
        seen.add(root)
        stack: list[tuple[Any, Iterator[Any]]] = [(root, iter(forward.get(root, ())))]
        while stack:
            node, successors = stack[-1]
            try:
                nxt = next(successors)
            except StopIteration:
                finish.append(node)
                stack.pop()
                continue
            if nxt not in seen:
                seen.add(nxt)
                stack.append((nxt, iter(forward.get(nxt, ()))))
    seen.clear()
    result: list[list[Any]] = []
    for root in reversed(finish):
        if root in seen:
            continue
        seen.add(root)
        component: list[Any] = []
        stack = [root]
        while stack:
            node = stack.pop()
            component.append(node)
            for nxt in backward.get(node, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def component_cycle_signature(
    cycle_lengths: Sequence[int], edge_hits: Sequence[Sequence[int]], edge_orders: Sequence[tuple[int, ...]]
) -> tuple[Any, ...]:
    """Unlabelled cycle--collision-edge incidence fingerprint.

    A row records its f-cycle length and which of the five collision edges it
    meets.  We minimize that multiset over every forest-line-graph edge
    automorphism.  Together with the exact tree topology code this is a much
    stronger invariant than a component-size partition or a length multiset.
    """
    candidates: list[tuple[Any, ...]] = []
    for ordering in edge_orders:
        rows = tuple(sorted(
            (cycle_lengths[cid], tuple(edge_hits[cid][edge] for edge in ordering))
            for cid in range(len(cycle_lengths))
        ))
        candidates.append(rows)
    return min(candidates)


def lifted_diagnostic(core: Any, cert: dict[str, Any], orbit_component: dict[int, int]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct the phase-aware but mask-free diagnostic graph.

    Returns a compact diagnostic record and auxiliary information needed by
    the potential search.  The exact DP remains the certificate data.
    """
    orbit_ids = tuple(cert["canonical_cover_representative"])
    skeleton = core.Skeleton(orbit_ids[:-1], orbit_ids[-1])
    ports, successor, lengths = core.w2_permutation(skeleton)
    cycles = core.cycle_decomposition(successor)
    certificate_cycles = tuple(tuple(tuple(word) for word in cycle) for cycle in cert["f_cycle_decomposition"]["cycles"])
    if tuple(cycles) != certificate_cycles:
        raise AssertionError("reconstructed f-cycle decomposition differs from certificate")
    cycle_of = {port: cid for cid, cycle in enumerate(cycles) for port in cycle}
    inverse_successor = {target: source for source, target in successor.items()}
    port_index = {port: index for index, port in enumerate(ports)}
    orbit_of_port = {
        port: orbit_id
        for orbit_id in orbit_ids
        for port in core.ports_of_e_orbit(core.E_REPS[orbit_id])
    }
    if set(orbit_of_port) != set(ports):
        raise AssertionError("port/orbit reconstruction mismatch")
    candidates = core.deep_edges(ports, lengths, set(ports))

    # States use forced exit port, matching the exact DP's ``(mask, u)`` port
    # coordinate.  A deep target is f(next_exit), hence next_exit=f^{-1}(target).
    states = [(cycle_of[port], port, heavy) for port in ports for heavy in range(4)]
    arcs: list[tuple[tuple[int, Any, int], tuple[int, Any, int], int, int]] = []
    collapsed_h3: set[tuple[int, int]] = set()
    transition_by_weight: Counter[int] = Counter()
    transition_by_extra: Counter[int] = Counter()
    zero_outdegree: dict[Any, int] = {}
    for port in ports:
        zero_outdegree[port] = sum(extra == 0 for _target, extra, _weight, _pi in candidates.get(port, ()))
        for target, extra, weight, _pi in candidates.get(port, ()):
            next_port = inverse_successor[target]
            source_cycle = cycle_of[port]
            target_cycle = cycle_of[next_port]
            collapsed_h3.add((source_cycle, target_cycle))
            transition_by_weight[weight] += 1
            transition_by_extra[extra] += 1
            for heavy in range(4 - extra):
                arcs.append(((source_cycle, port, heavy), (target_cycle, next_port, heavy + extra), extra, weight))

    common = cert["port_lift_common_diagnostics_at_H_3"]
    if len(collapsed_h3) != common["cycle_transition_arc_count"]:
        raise AssertionError("diagnostic collapsed cycle-arc count disagrees with certificate")
    core_scc_sizes = core.strongly_connected_component_sizes(len(cycles), collapsed_h3)
    if core_scc_sizes != common["cycle_transition_scc_sizes"]:
        raise AssertionError("diagnostic collapsed SCC sizes disagree with certificate")
    core_weak_sizes = core.weak_component_sizes(len(cycles), collapsed_h3)
    if core_weak_sizes != common["cycle_transition_weak_component_sizes"]:
        raise AssertionError("diagnostic collapsed weak components disagree with certificate")

    adjacency: dict[tuple[int, Any, int], list[tuple[int, Any, int]]] = defaultdict(list)
    for source, target, _extra, _weight in arcs:
        adjacency[source].append(target)
    starts = {(cycle_of[port], port, 0) for port in ports}
    reachable = set(starts)
    queue: deque[tuple[int, Any, int]] = deque(starts)
    while queue:
        source = queue.popleft()
        for target in adjacency.get(source, ()):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    reachable_arcs = [(source, target) for source, target, _extra, _weight in arcs if source in reachable and target in reachable]
    sccs = kosaraju(reachable, reachable_arcs)
    scc_index = {node: index for index, component in enumerate(sccs) for node in component}
    scc_outgoing: list[set[int]] = [set() for _ in sccs]
    for source, target in reachable_arcs:
        left, right = scc_index[source], scc_index[target]
        if left != right:
            scc_outgoing[left].add(right)
    terminal = [index for index, out in enumerate(scc_outgoing) if not out]
    terminal_cycle_coverages = sorted(
        len({node[0] for node in sccs[index]}) for index in terminal
    )
    scc_cycle_coverages = sorted(len({node[0] for node in component}) for component in sccs)

    per_budget_scc: dict[str, Any] = {}
    for budget in range(4):
        cycle_arcs = {
            (cycle_of[port], cycle_of[inverse_successor[target]])
            for port, options in candidates.items()
            for target, extra, _weight, _pi in options
            if extra <= budget
        }
        per_budget_scc[str(budget)] = {
            "cycle_arc_count": len(cycle_arcs),
            "cycle_scc_sizes": core.strongly_connected_component_sizes(len(cycles), cycle_arcs),
            "cycle_weak_component_sizes": core.weak_component_sizes(len(cycles), cycle_arcs),
        }

    component_size = {orbit: len(cert["collision_forest"]["component_partition"][component]) for orbit, component in orbit_component.items()}
    component_degree: dict[int, int] = Counter(orbit for edge in cert["collision_forest"]["edges"] for orbit in edge["orbits"])
    auxiliary = {
        "all_transition_feature_deltas": [],
        "lifted_state_features": {},
    }
    for cycle, port, heavy in states:
        orbit = orbit_of_port[port]
        auxiliary["lifted_state_features"][(cycle, port, heavy)] = (
            heavy,
            len(cycles[cycle]),
            component_size[orbit],
            component_degree.get(orbit, 0),
            zero_outdegree[port],
        )
    for source, target, _extra, _weight in arcs:
        left = auxiliary["lifted_state_features"][source]
        right = auxiliary["lifted_state_features"][target]
        auxiliary["all_transition_feature_deltas"].append(tuple(b - a for a, b in zip(left, right)))

    record = {
        "state_model": "(f_cycle, forced_exit_port, heavy_spent); a diagnostic relaxation without visited-cycle mask",
        "local_transition_api_assertion": {
            "cycle_arc_count_matches_certificate_H3": True,
            "cycle_scc_sizes_match_certificate_H3": True,
            "cycle_weak_component_sizes_match_certificate_H3": True,
        },
        "node_count": len(states),
        "arc_count": len(arcs),
        "reachable_node_count_from_all_H0_starts": len(reachable),
        "reachable_arc_count": len(reachable_arcs),
        "transition_count_by_weight": {str(key): value for key, value in sorted(transition_by_weight.items())},
        "transition_count_by_heavy_increment": {str(key): value for key, value in sorted(transition_by_extra.items())},
        "reachable_scc_count": len(sccs),
        "reachable_scc_size_multiset": sorted(len(component) for component in sccs),
        "reachable_scc_cycle_coverage_multiset": scc_cycle_coverages,
        "terminal_scc_count": len(terminal),
        "terminal_scc_cycle_coverage_multiset": terminal_cycle_coverages,
        "per_budget_collapsed_cycle_graph": per_budget_scc,
        "cut_claim": "No mask-free graph cut is asserted: the exact obstruction is no-revisit DP state dependent.",
        "common_bottleneck_entry_phase": None,
        "common_bottleneck_entry_phase_reason": "Certificates serialize counts, not final DP states; the mask-free graph cannot identify a common terminal DP exit/entry phase.",
    }
    return record, auxiliary


def all_feature_deltas(covers: Sequence[dict[str, Any]]) -> set[tuple[int, ...]]:
    deltas: set[tuple[int, ...]] = set()
    for cover in covers:
        deltas.update(tuple(delta) for delta in cover.pop("_potential_deltas"))
    return deltas


def potential_search(deltas: set[tuple[int, ...]]) -> dict[str, Any]:
    """Small, explicitly non-theorem search for a static lifted-state potential.

    Features are (heavy spent, cycle length, collision-tree size, orbit
    degree, zero-heavy outdegree).  We look for a nonconstant bounded linear
    potential nonincreasing on every diagnostic arc and strictly decreasing
    on each positive-heavy arc.  The budget-only potential -heavy is excluded
    as tautological.  This is intentionally a very narrow diagnostic test.
    """
    ordered = sorted(deltas)
    positive = [delta for delta in ordered if delta[0] > 0]
    found: list[tuple[int, ...]] = []
    tested = 0
    for coeffs in itertools.product(range(-3, 4), repeat=5):
        if not any(coeffs) or all(value == 0 for value in coeffs[1:]):
            continue
        tested += 1
        if all(sum(a * b for a, b in zip(coeffs, delta)) <= 0 for delta in ordered):
            if positive and all(sum(a * b for a, b in zip(coeffs, delta)) < 0 for delta in positive):
                found.append(coeffs)
                if len(found) >= 10:
                    break
    return {
        "features": ["heavy_spent", "f_cycle_length", "collision_tree_size", "collision_orbit_degree", "zero_heavy_deep_outdegree"],
        "coefficient_domain": [-3, 3],
        "distinct_transition_delta_vectors": len(ordered),
        "nontrivial_coefficients_tested": tested,
        "criterion": "nonincreasing on every diagnostic arc and strictly decreasing on every positive-heavy diagnostic arc; budget-only multiples are excluded",
        "solutions_first_10": [list(row) for row in found],
        "interpretation": "Exploratory only.  The diagnostic graph omits the no-revisit mask, so this cannot establish the port-lift obstruction.",
    }


def make_cover_record(core: Any, cert: dict[str, Any]) -> dict[str, Any]:
    forest, orbit_component, edge_components = forest_features(cert)
    orbit_ids = tuple(cert["canonical_cover_representative"])
    skeleton = core.Skeleton(orbit_ids[:-1], orbit_ids[-1])
    ports, successor, _lengths = core.w2_permutation(skeleton)
    cycles = core.cycle_decomposition(successor)
    cycle_lengths = tuple(sorted(len(cycle) for cycle in cycles))
    if list(cycle_lengths) != sorted(cert["f_cycle_decomposition"]["cycle_lengths"]):
        raise AssertionError("cycle length multiset mismatch")
    orbit_of_port = {
        port: orbit_id
        for orbit_id in orbit_ids
        for port in core.ports_of_e_orbit(core.E_REPS[orbit_id])
    }
    edges = [tuple(row["orbits"]) for row in cert["collision_forest"]["edges"]]
    edge_hits: list[list[int]] = []
    for cycle in cycles:
        used_orbits = {orbit_of_port[port] for port in cycle}
        edge_hits.append([int(bool(used_orbits & set(edge))) for edge in edges])
    edge_orders = edge_automorphism_orders(edges)
    incidence_signature = component_cycle_signature([len(cycle) for cycle in cycles], edge_hits, edge_orders)
    component_cycle_counts = []
    for component_index, component in enumerate(forest["component_rows"]):
        edge_indices = [index for index, item in enumerate(edge_components) if item["component"] == component_index]
        component_cycle_counts.append(sum(any(edge_hits[cid][edge] for edge in edge_indices) for cid in range(len(cycles))))
    cycle_edge_counts = [sum(row) for row in edge_hits]
    dp = dp_features(cert)
    diagnostic, auxiliary = lifted_diagnostic(core, cert, orbit_component)
    return {
        "cover_sha256": cert["cover_sha256"],
        "cover_kind": cert["cover_kind"],
        "canonical_cover_representative": list(orbit_ids),
        "double_hexagons": cert["double_hexagons"],
        "collision_forest": forest,
        "collision_edge_component_map": edge_components,
        "f_cycle": {
            "cycle_count": len(cycles),
            "cycle_length_multiset": list(cycle_lengths),
            "min_cycle_length": min(cycle_lengths),
            "max_cycle_length": max(cycle_lengths),
            "cycle_length_counts": {str(length): count for length, count in sorted(Counter(cycle_lengths).items())},
            "collision_edges_met_by_each_cycle": cycle_edge_counts,
            "f_cycles_meeting_each_collision_edge": [sum(row[edge] for row in edge_hits) for edge in range(len(edges))],
            "f_cycles_meeting_each_collision_component": component_cycle_counts,
            "cycle_collision_edge_incidence_rows": ["".join(map(str, row)) for row in edge_hits],
            "unlabelled_cycle_collision_incidence_signature": [
                [length, "".join(map(str, bits))] for length, bits in incidence_signature
            ],
        },
        "port_lift_dp": dp,
        "lifted_transition_diagnostic": diagnostic,
        "_forest_partition_key": tuple(forest["component_size_partition"]),
        "_cycle_lengths_key": cycle_lengths,
        "_combined_key": (
            tuple((int(item[0]), tuple(item[1]), item[2]) for item in forest["topology_signature"]),
            incidence_signature,
        ),
        "_h3_profile_key": (
            dp["h3_profile"]["max_cycles_reached"],
            dp["h3_profile"]["first_empty_layer"],
            tuple(dp["h3_profile"]["layer_state_counts"]),
        ),
        "_potential_deltas": auxiliary["all_transition_feature_deltas"],
        "_f_cycles": [[list(port) for port in cycle] for cycle in cycles],
        "_deep_transition_summary": diagnostic["transition_count_by_weight"],
    }


def group_records(records: Sequence[dict[str, Any]], key_fn: Any) -> dict[Any, list[dict[str, Any]]]:
    result: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        result[key_fn(record)].append(record)
    return result


def counterexample_for(groups: dict[Any, list[dict[str, Any]]], profile_key: Any, *, include_combined: bool = False) -> dict[str, Any] | None:
    choices = []
    for key, rows in groups.items():
        by_profile = group_records(rows, profile_key)
        if len(by_profile) < 2:
            continue
        profiles = sorted(by_profile, key=repr)
        left = min(by_profile[profiles[0]], key=lambda row: row["cover_sha256"])
        right = min(by_profile[profiles[1]], key=lambda row: row["cover_sha256"])
        choices.append((len(rows), repr(key), left, right))
    if not choices:
        return None
    _size, _key_text, left, right = min(choices, key=lambda item: (item[0], item[1], item[2]["cover_sha256"], item[3]["cover_sha256"]))
    result = {
        "left_cover_sha256": left["cover_sha256"],
        "right_cover_sha256": right["cover_sha256"],
        "shared_feature": {
            "forest_partition": left["collision_forest"]["component_size_partition"],
            "cycle_lengths": left["f_cycle"]["cycle_length_multiset"],
        },
        "left_h3_profile": left["port_lift_dp"]["h3_profile"],
        "right_h3_profile": right["port_lift_dp"]["h3_profile"],
    }
    if include_combined:
        result["shared_combined_fingerprint"] = {
            "forest_topology_signature": left["collision_forest"]["topology_signature"],
            "unlabelled_cycle_collision_edge_incidence_signature": left["f_cycle"]["unlabelled_cycle_collision_incidence_signature"],
        }
    return result


def candidate_lemmas(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """At most three explicitly finite, falsifiable lemma candidates.

    They are deliberately labelled as finite-data statements rather than
    promoted to theorems: the remaining branches have not completed.
    """
    partition_groups = group_records(records, lambda row: row["_forest_partition_key"])
    candidates = [{
        "statement": "For every C in the completed canonical SHA union B_02 union B_03, an H<=3 exact port-lift does not visit all 20 f-cycles.",
        "tested_cover_count": len(records),
        "counterexamples": 0,
        "observed_H3_maximum": max(row["port_lift_dp"]["h3_profile"]["max_cycles_reached"] for row in records),
        "needed_state_information": "Exact DP state (visited-cycle mask, forced exit port); certificate stores layer counts but not terminal states.",
        "proof_status": "Finite computation for this duplicated two-branch union only; not a theorem about all forest covers.",
    }]
    for partition, rows in sorted(partition_groups.items(), key=lambda item: (-len(item[1]), repr(item[0])))[:2]:
        candidates.append({
            "statement": f"For every C in the current union with collision component partition {list(partition)}, an H<=3 exact port-lift reaches at most {max(row['port_lift_dp']['h3_profile']['max_cycles_reached'] for row in rows)} f-cycles.",
            "tested_cover_count": len(rows),
            "counterexamples": 0,
            "observed_H3_maximum": max(row["port_lift_dp"]["h3_profile"]["max_cycles_reached"] for row in rows),
            "needed_state_information": "Exact DP state (visited-cycle mask, forced exit port), plus phase-level transport not retained by forest partition alone.",
            "proof_status": "No counterexample in this finite input union; partition alone is not sufficient to determine the full H=3 profile.",
        })
    return candidates


def strict_and_coarse_archetypes(records: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    strict_groups = group_records(records, lambda row: (
        row["_h3_profile_key"], row["_forest_partition_key"], row["_cycle_lengths_key"]
    ))
    coarse_groups = group_records(records, lambda row: (
        row["port_lift_dp"]["h3_profile"]["max_cycles_reached"],
        row["port_lift_dp"]["h3_profile"]["first_empty_layer"],
        row["_forest_partition_key"],
        row["_cycle_lengths_key"],
    ))
    def score(row: dict[str, Any]) -> tuple[Any, ...]:
        h3 = row["port_lift_dp"]["h3_profile"]
        return (h3["dp_states"], max(row["collision_forest"]["component_size_partition"]), h3["first_empty_layer"] or 99, row["cover_sha256"])
    strict_rows = []
    for key, rows in sorted(strict_groups.items(), key=lambda item: (repr(item[0]), min(row["cover_sha256"] for row in item[1]))):
        representative = min(rows, key=score)
        strict_rows.append({
            "count": len(rows),
            "representative_cover_sha256": representative["cover_sha256"],
            "h3_profile": representative["port_lift_dp"]["h3_profile"],
            "forest_partition": representative["collision_forest"]["component_size_partition"],
            "cycle_lengths": representative["f_cycle"]["cycle_length_multiset"],
            "cover_sha256s": sorted(row["cover_sha256"] for row in rows),
        })
    coarse_rows = []
    for key, rows in sorted(coarse_groups.items(), key=lambda item: (repr(item[0]), min(row["cover_sha256"] for row in item[1]))):
        representative = min(rows, key=score)
        h3_profiles = Counter(stable_json(row["port_lift_dp"]["h3_profile"]) for row in rows)
        coarse_rows.append({
            "count": len(rows),
            "representative_cover_sha256": representative["cover_sha256"],
            "h3_max_cycles_reached": representative["port_lift_dp"]["h3_profile"]["max_cycles_reached"],
            "first_empty_layer": representative["port_lift_dp"]["h3_profile"]["first_empty_layer"],
            "forest_partition": representative["collision_forest"]["component_size_partition"],
            "cycle_lengths": representative["f_cycle"]["cycle_length_multiset"],
            "distinct_full_H3_layer_profiles": len(h3_profiles),
            "cover_sha256s": sorted(row["cover_sha256"] for row in rows),
        })
    return strict_rows, coarse_rows


def failure_certificate(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "cover_sha256": record["cover_sha256"],
        "cover_kind": record["cover_kind"],
        "orbit_ids": record["canonical_cover_representative"],
        "double_hexagons": record["double_hexagons"],
        "collision_forest": record["collision_forest"],
        "f_cycle_lengths": record["f_cycle"]["cycle_length_multiset"],
        "f_cycles_port_words": record["_f_cycles"],
        "allowed_lifted_transition_summary": record["_deep_transition_summary"],
        "lifted_transition_diagnostic": record["lifted_transition_diagnostic"],
        "H3_layer_state_counts": record["port_lift_dp"]["h3_profile"]["layer_state_counts"],
        "exact_failure_stage": {
            "max_cycles_reached": record["port_lift_dp"]["h3_profile"]["max_cycles_reached"],
            "first_empty_layer": record["port_lift_dp"]["h3_profile"]["first_empty_layer"],
            "complete_lift_exists": record["port_lift_dp"]["by_heavy_budget"][3]["complete_lift_exists"],
        },
    }


def markdown_table(rows: Sequence[Sequence[Any]], headers: Sequence[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def write_reports(
    metadata: dict[str, Any], overlap: dict[str, Any], records: list[dict[str, Any]],
    tests: dict[str, Any], potential: dict[str, Any], strict: list[dict[str, Any]], coarse: list[dict[str, Any]],
    lemma_candidates: list[dict[str, Any]],
) -> None:
    public_records = []
    for row in records:
        public_records.append({key: value for key, value in row.items() if not key.startswith("_")})
    main_json = {
        "metadata": metadata,
        "branch_overlap": overlap,
        "unique_canonical_cover_count": len(records),
        "certificate_features": public_records,
        "determinacy_tests": tests,
        "potential_search": potential,
        "candidate_lemmas": lemma_candidates,
        "scope": "Only completed branches 0,2 and 0,3 were read.  The phase-aware lifted graph is diagnostic and omits the exact DP visited-cycle mask.",
    }
    (OUTPUTS / "forest_branch_overlap_analysis.json").write_text(json.dumps(main_json, indent=2, ensure_ascii=False), encoding="utf-8")

    h3_distribution = Counter(row["port_lift_dp"]["h3_profile"]["max_cycles_reached"] for row in records)
    lines = [
        "# Forest branch overlap and port-lift failure analysis",
        "",
        "## Scope and reproducibility",
        "",
        "This is a read-only analysis of the two already completed, independently verified branch files. It does not touch the supervisor, running branches, enumerator, generator, or existing branch JSON.",
        "",
        f"- Analysis code SHA-256: `{metadata['analysis_code_sha256']}`",
        f"- Core transition code SHA-256: `{metadata['core_code_sha256']}`",
        f"- Input `0,2` SHA-256: `{metadata['input_sha256']['forest_branch_0_2.json']}`",
        f"- Input `0,3` SHA-256: `{metadata['input_sha256']['forest_branch_0_3.json']}`",
        "",
        "## Branch overlap",
        "",
        markdown_table([
            ("0,2", overlap["branch_certificate_counts"]["0,2"], overlap["branch_unique_cover_counts"]["0,2"]),
            ("0,3", overlap["branch_certificate_counts"]["0,3"], overlap["branch_unique_cover_counts"]["0,3"]),
        ], ("branch seed", "raw certificates", "unique cover SHA-256")),
        "",
        f"The SHA sets are exactly equal: intersection = {overlap['intersection_size']}, union = {overlap['union_size']}. Every shared SHA has byte-for-byte identical serialized certificate content after parsed JSON comparison: {overlap['serialized_certificate_differences']} differences.",
        "",
        "This is not reported as an enumerator error. Canonical-child augmentation plus memoization removes repetitions within a branch, but the completed depth-2 branches maintain separate memo tables. Hence different seeds can re-enter the same canonical descendants. The matching count 326 is therefore explained by cross-seed duplication of the same canonical set, not treated as evidence for 652 classes or as coincidence.",
        "",
        "## Exact DP facts from certificates",
        "",
        markdown_table([(key, value) for key, value in sorted(h3_distribution.items())], ("H=3 maximum f-cycles reached", "covers")),
        "",
        "All 326 canonical covers have `complete_lift_exists=false` for each recorded budget H=0,1,2,3. These are certificate facts, not extrapolations to unfinished branches or to other (F,D,N) slabs.",
        "",
        "## Structural tests",
        "",
        f"- A. Forest component-size partition determines H=3 `max_cycles_reached`: **{tests['A_partition_determines_h3_max_cycles']}**.",
        f"- B. f-cycle length multiset determines H=3 failure profile: **{tests['B_cycle_lengths_determine_h3_profile']}**.",
        f"- C. The implemented unlabeled forest-topology + cycle-length + collision-edge-incidence fingerprint determines H=3 profile in this data: **{tests['C_combined_fingerprint_determines_h3_profile']}**.",
        "",
        "For A--C, `false` means the report JSON contains a lexicographically selected counterexample pair; `true` would mean only no counterexample in this 326-cover union, not a theorem.",
        "",
        "The C counterexample fixes the full implemented unlabeled fingerprint, yet has a different H=3 layer-state-count profile. Thus the fingerprint is insufficient for exact DP-profile prediction in this finite data. The missing information is port-level phase/deep-tail transport; this is a computed counterexample to sufficiency of the stated fingerprint, not a general theorem about every possible structural invariant.",
        "",
        "## Phase-aware lifted diagnostic graph",
        "",
        "For each cover, the analysis reused the main program's `w2_permutation` and `deep_edges` APIs to construct states `(f-cycle, forced exit port, heavy spent)`. Its reconstructed H=3 collapsed cycle-arc count, SCC sizes, and weak-component sizes were asserted equal to the certificate diagnostics for all covers. The graph deliberately omits the exact DP visited-cycle mask. It is therefore useful for local transport/SCC diagnostics but cannot itself prove the no-revisit obstruction; no mask-free cut or common terminal entry phase is claimed.",
        "",
        "## Bounded potential search",
        "",
        "The JSON records a deliberately limited coefficient search on five static diagnostic-state features. It is exploratory only, excludes the tautological budget-only potential, and is not a proof because the graph has forgotten the visited-cycle mask.",
        "",
        "## Candidate lemmas (explicitly not yet theorems)",
        "",
    ]
    for candidate in lemma_candidates:
        lines.extend([
            f"> {candidate['statement']}",
            "",
            f"Tested covers: {candidate['tested_cover_count']}; counterexamples: {candidate['counterexamples']}; observed H=3 maximum: {candidate['observed_H3_maximum']}.  ",
            f"Status: {candidate['proof_status']}",
            "",
        ])
    lines.extend([
        "## Failure archetypes",
        "",
        f"Using the requested strict H=3 layer-state-count profile together with the other minimum fields gives {len(strict)} groups over {len(records)} covers. If this equals 326, the strict profile is too fine to compress the data: it should not be represented as a falsely small number of identical archetypes. A coarser grouping by H=3 maximum, first empty layer, forest partition, and f-cycle multiset gives {len(coarse)} diagnostic groups; its representatives and the strict groups are in `forest_failure_archetypes.json`.",
        "",
        "## Epistemic status",
        "",
        "- **Computed exactly for this input union:** branch overlap; all stored DP profiles; all reconstructed local-transition/SCC consistency assertions; all stated fingerprints and counterexample pairs.",
        "- **No-counterexample claims:** only where explicitly labelled as such in the JSON, and only for these 326 canonical covers (not 652 independent covers).",
        "- **Not established here:** a proof for all five branches, a full port-lift obstruction beyond the certificate's stated relaxation, the other F<5 slabs, removal of NR6, or `L_6 >= 872`.",
    ])
    (OUTPUTS / "FOREST_BRANCH_OVERLAP_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    coarse_by_sha = {row["representative_cover_sha256"]: row for row in coarse}
    records_by_sha = {row["cover_sha256"]: row for row in records}
    certificates = [failure_certificate(records_by_sha[sha]) for sha in sorted(coarse_by_sha)]
    archetype_json = {
        "metadata": metadata,
        "strict_requested_groups": strict,
        "coarse_diagnostic_groups": coarse,
        "minimal_failure_certificates_one_per_coarse_group": certificates,
        "candidate_lemmas": lemma_candidates,
        "important_limit": "The exact DP state is (visited-cycle mask, forced exit port).  Certificate serialization does not include terminal states or unreachable cycle identities, so this file does not invent them.",
    }
    (OUTPUTS / "forest_failure_archetypes.json").write_text(json.dumps(archetype_json, indent=2, ensure_ascii=False), encoding="utf-8")

    rows = []
    for group in coarse:
        rows.append((group["count"], group["h3_max_cycles_reached"], group["first_empty_layer"], ",".join(map(str, group["forest_partition"])), group["representative_cover_sha256"][:16]))
    md = [
        "# Minimal forest port-lift failure certificates",
        "",
        "Each row below selects the smallest H=3 reachable-state representative of a coarse diagnostic group. Full reproducible data, including 25 orbit IDs, five double hexagons, collision forest, f-cycle port words, H=3 layer counts, and phase-aware transition summary are in `forest_failure_archetypes.json`.",
        "",
        f"Analysis SHA-256: `{metadata['analysis_code_sha256']}`  ",
        f"Input SHA-256 (`0,2`): `{metadata['input_sha256']['forest_branch_0_2.json']}`  ",
        f"Input SHA-256 (`0,3`): `{metadata['input_sha256']['forest_branch_0_3.json']}`",
        "",
        markdown_table(rows, ("covers", "H3 max", "first empty layer", "forest component partition", "representative SHA prefix")),
        "",
        "The strict requested grouping (which also fixes the complete H=3 layer-state-count profile) is retained separately in JSON. If it yields singleton groups, that is a finding about the heterogeneity of exact DP state counts rather than permission to collapse them.",
        "",
        "The allowed transition data are summarized by weight in the certificates to avoid implying that a mask-free graph gives the exact no-revisit DP path. The exact failure stage reported for each representative is its serialized H=3 first empty layer and maximum reached cycle cardinality.",
    ]
    (OUTPUTS / "FOREST_FAILURE_ARCHETYPES.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    inputs = [OUTPUTS / name for name in INPUT_NAMES]
    if any(not path.exists() for path in inputs):
        raise FileNotFoundError("both completed branch JSON files are required")
    branches = [load_completed_branch(path) for path in inputs]
    by_sha = []
    for branch in branches:
        mapping = {cert["cover_sha256"]: cert for cert in branch["certificates"]}
        if len(mapping) != len(branch["certificates"]):
            raise AssertionError("duplicate cover SHA inside a completed branch")
        by_sha.append(mapping)
    left, right = by_sha
    shared = set(left) & set(right)
    serialized_differences = []
    for sha in sorted(shared):
        if stable_json(left[sha]) != stable_json(right[sha]):
            serialized_differences.append({
                "cover_sha256": sha,
                "different_fields": sorted(set(left[sha]) | set(right[sha])),
            })
    overlap = {
        "branch_certificate_counts": {"0,2": len(branches[0]["certificates"]), "0,3": len(branches[1]["certificates"])},
        "branch_unique_cover_counts": {"0,2": len(left), "0,3": len(right)},
        "sets_exactly_equal": set(left) == set(right),
        "intersection_size": len(shared),
        "union_size": len(set(left) | set(right)),
        "serialized_certificate_differences": len(serialized_differences),
        "serialized_certificate_difference_details": serialized_differences,
        "interpretation": "Cross-depth-seed duplication is expected because canonical-child memoization is branch-local; it is not an enumerator error.",
    }
    if not overlap["sets_exactly_equal"] or serialized_differences:
        raise AssertionError("this analysis expects the observed completed-branch overlap; inspect branch output")

    core = load_core()
    records = [make_cover_record(core, left[sha]) for sha in sorted(left)]
    deltas = all_feature_deltas(records)
    potential = potential_search(deltas)
    partition_groups = group_records(records, lambda row: row["_forest_partition_key"])
    cycle_groups = group_records(records, lambda row: row["_cycle_lengths_key"])
    combined_groups = group_records(records, lambda row: row["_combined_key"])
    tests = {
        "A_partition_determines_h3_max_cycles": all(
            len({row["port_lift_dp"]["h3_profile"]["max_cycles_reached"] for row in rows}) == 1
            for rows in partition_groups.values()
        ),
        "A_counterexample": counterexample_for(
            partition_groups, lambda row: row["port_lift_dp"]["h3_profile"]["max_cycles_reached"]
        ),
        "B_cycle_lengths_determine_h3_profile": all(len(group_records(rows, lambda row: row["_h3_profile_key"])) == 1 for rows in cycle_groups.values()),
        "B_counterexample": counterexample_for(cycle_groups, lambda row: row["_h3_profile_key"]),
        "C_combined_fingerprint_determines_h3_profile": all(len(group_records(rows, lambda row: row["_h3_profile_key"])) == 1 for rows in combined_groups.values()),
        "C_counterexample": counterexample_for(combined_groups, lambda row: row["_h3_profile_key"], include_combined=True),
        "partition_group_count": len(partition_groups),
        "cycle_length_group_count": len(cycle_groups),
        "combined_fingerprint_group_count": len(combined_groups),
        "combined_fingerprint_definition": "unlabelled exact collision-tree topology plus f-cycle lengths plus cycle-by-five-collision-edge incidence, minimized over all forest-line-graph edge automorphisms",
    }
    strict, coarse = strict_and_coarse_archetypes(records)
    lemma_candidates = candidate_lemmas(records)
    metadata = {
        "analysis_code": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
        "analysis_code_sha256": sha256_file(Path(__file__)),
        "core_code": str(CORE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "core_code_sha256": sha256_file(CORE_PATH),
        "input_sha256": {path.name: sha256_file(path) for path in inputs},
        "input_branch_code_sha256": {"0,2": branches[0]["code_sha256"], "0,3": branches[1]["code_sha256"]},
        "input_branch_seeds": {"0,2": branches[0]["seed"], "0,3": branches[1]["seed"]},
        "analysis_memory_policy": "serial read-only analysis of two completed JSON files; no enumeration and no multiprocessing",
    }
    write_reports(metadata, overlap, records, tests, potential, strict, coarse, lemma_candidates)
    print(json.dumps({
        "unique_canonical_covers": len(records),
        "sets_exactly_equal": overlap["sets_exactly_equal"],
        "H3_max_distribution": dict(sorted(Counter(row["port_lift_dp"]["h3_profile"]["max_cycles_reached"] for row in records).items())),
        "strict_archetype_count": len(strict),
        "coarse_archetype_count": len(coarse),
        "partition_determines_max_cycles": tests["A_partition_determines_h3_max_cycles"],
        "cycle_lengths_determine_profile": tests["B_cycle_lengths_determine_h3_profile"],
        "combined_fingerprint_determines_profile": tests["C_combined_fingerprint_determines_h3_profile"],
        "potential_solutions": len(potential["solutions_first_10"]),
    }, indent=2))


if __name__ == "__main__":
    main()
