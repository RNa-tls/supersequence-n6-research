#!/usr/bin/env python3
"""Independent incidence/f-cycle verifier for forest-cover certificates.

This script intentionally reconstructs the finite S6 incidence system instead
of importing the forest generator.  It verifies canonicality, coverage,
multiplicity-two, the collision forest, and the serialized f=rho E cycle
decomposition.  For the exponential port-lift table it invokes the shared
DP implementation only as a final replay check; the finite incidence and
cycle calculations are an independent code path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from itertools import permutations
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


N = 6
Perm = Tuple[int, ...]
IDENTITY: Perm = tuple(range(N))
SIGMA: Perm = (1, 2, 3, 4, 5, 0)
TAU: Perm = (2, 3, 4, 5, 1, 0)
E: Perm = (1, 2, 3, 4, 0, 5)
WORDS = tuple(permutations(range(N)))


def compose(g: Perm, h: Perm) -> Perm:
    return tuple(g[h[i]] for i in range(N))


def power(g: Perm, exponent: int) -> Perm:
    answer = IDENTITY
    while exponent:
        if exponent & 1:
            answer = compose(answer, g)
        g = compose(g, g)
        exponent >>= 1
    return answer


def cyclic_orbit(seed: Perm, generator: Perm) -> Tuple[Perm, ...]:
    answer: List[Perm] = []
    word = seed
    while word not in answer:
        answer.append(word)
        word = compose(word, generator)
    return tuple(answer)


def canonical_rotation(word: Perm) -> Perm:
    return min(cyclic_orbit(word, SIGMA))


def canonical_e(word: Perm) -> Perm:
    return min(cyclic_orbit(word, E))


ROT_REPS = tuple(sorted({canonical_rotation(word) for word in WORDS}))
ROT_ID = {word: index for index, word in enumerate(ROT_REPS)}
E_REPS = tuple(sorted({canonical_e(word) for word in WORDS}))
E_ID = {word: index for index, word in enumerate(E_REPS)}


def hexagon_id(word: Perm) -> int:
    return ROT_ID[canonical_rotation(word)]


KSETS = tuple(tuple(hexagon_id(port) for port in cyclic_orbit(q, E)) for q in E_REPS)


def left_action_on_orbits(value_permutation: Perm) -> Tuple[int, ...]:
    return tuple(E_ID[canonical_e(tuple(value_permutation[x] for x in q))] for q in E_REPS)


LEFT_ACTIONS = tuple(left_action_on_orbits(value_perm) for value_perm in permutations(range(N)))


def canonical_cover(ids: Sequence[int]) -> Tuple[int, ...]:
    return min(tuple(sorted(action[qid] for qid in ids)) for action in LEFT_ACTIONS)


def rotation_distance(source: Perm, target: Perm) -> int:
    for distance in range(N):
        if compose(source, power(SIGMA, distance)) == target:
            return distance
    raise AssertionError("ports must lie in the same rotation hexagon")


def successor_and_cycles(ids: Sequence[int]) -> List[Tuple[Perm, ...]]:
    ports: List[Perm] = []
    by_hex: Dict[int, List[Perm]] = defaultdict(list)
    for qid in ids:
        for port in cyclic_orbit(E_REPS[qid], E):
            ports.append(port)
            by_hex[hexagon_id(port)].append(port)
    assert len(ports) == 125 and len(set(ports)) == 125
    successor: Dict[Perm, Perm] = {}
    for h, members in by_hex.items():
        cyclic = sorted((rotation_distance(ROT_REPS[h], port), port) for port in members)
        for index, (position, port) in enumerate(cyclic):
            next_position, _ = cyclic[(index + 1) % len(cyclic)]
            length = (next_position - position) % N or N
            endpoint = compose(port, power(SIGMA, length - 1))
            successor[port] = compose(endpoint, TAU)
    assert set(successor) == set(ports)
    assert set(successor.values()) == set(ports)
    unseen = set(ports)
    cycles: List[Tuple[Perm, ...]] = []
    while unseen:
        start = min(unseen)
        cycle: List[Perm] = []
        current = start
        while current not in cycle:
            cycle.append(current)
            unseen.remove(current)
            current = successor[current]
        assert current == start
        cycles.append(tuple(cycle))
    return cycles


def collision_data(ids: Sequence[int]) -> Tuple[List[Tuple[int, int, int]], bool]:
    owners: List[List[int]] = [[] for _ in range(120)]
    for qid in ids:
        for h in KSETS[qid]:
            owners[h].append(qid)
    if any(len(row) not in (1, 2) for row in owners):
        raise AssertionError("cover is not multiplicity two")
    doubles = [(h, row[0], row[1]) for h, row in enumerate(owners) if len(row) == 2]
    parent = {qid: qid for qid in ids}

    def find(qid: int) -> int:
        while parent[qid] != qid:
            parent[qid] = parent[parent[qid]]
            qid = parent[qid]
        return qid

    forest = True
    for _h, left, right in doubles:
        left, right = find(left), find(right)
        if left == right:
            forest = False
        else:
            parent[left] = right
    return doubles, forest


def verify_certificate(cert: Dict[str, object], replay_dp: bool) -> Dict[str, object]:
    ids = tuple(int(qid) for qid in cert["canonical_cover_representative"])
    if len(ids) != 25 or len(set(ids)) != 25:
        raise AssertionError("not 25 distinct orbit IDs")
    if ids != canonical_cover(ids):
        raise AssertionError("cover is not the left-S6 canonical representative")
    if cert["cover_sha256"] != hashlib.sha256(
        json.dumps(list(ids), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest():
        raise AssertionError("cover SHA mismatch")
    counts = [0] * 120
    for qid in ids:
        for h in KSETS[qid]:
            counts[h] += 1
    if sorted(counts) != [1] * 115 + [2] * 5:
        raise AssertionError("coverage is not 115 single plus 5 double")
    doubles, forest = collision_data(ids)
    if not forest or len(doubles) != 5:
        raise AssertionError("collision graph is not a five-edge forest")
    serial_doubles = [
        (int(row["hexagon_id"]), int(row["orbits"][0]), int(row["orbits"][1]))
        for row in cert["double_hexagons"]
    ]
    if doubles != serial_doubles:
        raise AssertionError("serialized double-hexagon list differs")
    cycles = successor_and_cycles(ids)
    serial_cycles = [tuple(tuple(port) for port in cycle) for cycle in cert["f_cycle_decomposition"]["cycles"]]
    if cycles != serial_cycles:
        raise AssertionError("serialized f-cycle decomposition differs")
    if len(cycles) != 20:
        raise AssertionError("forest cover must have 20 f-cycles")
    if replay_dp:
        sys.path.insert(0, str(Path(__file__).parent))
        import superperm_port_lift as shared  # DP replay only; incidence checks above are independent.
        skeleton = shared.skeleton_from_orbit_ids(ids)
        dp = shared.port_lift_dp(skeleton, 3)
        summaries = [entry["exact_reachability"] for entry in cert["port_lift_H_0_to_3"]]
        if summaries != dp["budget_summaries"]:
            raise AssertionError("serialized exact port-lift table differs from replay")
    return {"cover_sha256": cert["cover_sha256"], "cycle_count": len(cycles), "verified": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("certificates", help="JSON from enumerate-forest-covers or merge-forest-certificates")
    parser.add_argument("--skip-dp-replay", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.loads(Path(args.certificates).read_text(encoding="utf-8"))
    rows = [verify_certificate(cert, not args.skip_dp_replay) for cert in data["certificates"]]
    result = {
        "certificates_verified": len(rows),
        "dp_replayed": not args.skip_dp_replay,
        "rows": rows,
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("certificates_verified", "dp_replayed", "verifier_sha256")}, indent=2))


if __name__ == "__main__":
    main()
