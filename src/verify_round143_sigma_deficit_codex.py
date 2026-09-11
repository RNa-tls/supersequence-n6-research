"""Local symbolic checks and bounded controls for the hand sigma-deficit lemma.

No capacity search, no compilation, and no literal-cover realizability claim.
"""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def E(v):
    return v[1:-1] + v[:1] + v[-1:]


def sigma(v):
    return v[1:] + v[:1]


def sigma_inv(v):
    return v[-1:] + v[:-1]


def Epower(v, k):
    for _ in range(k % 5):
        v = E(v)
    return v


def hx(v):
    return min(v[k:] + v[:k] for k in range(6))


def qkey(v):
    return min(Epower(v, k) for k in range(5))


def literal_targets(v):
    # A full pass appends the first five symbols. Its endpoint is the
    # final six-symbol window; append either tail order across a w2 gap.
    end = (v + v[:5])[-6:]
    return end[2:] + end[1] + end[0], end[2:] + end[:2]


def runs(lengths, start="012345", literal=False):
    result = []
    v = start
    for r in lengths:
        block = []
        for _ in range(r):
            block.append(v)
            v = literal_targets(v)[0] if literal else E(v)
        result.append(block)
        v = literal_targets(block[-1])[1] if literal else sigma(block[-1])
    return result


def audit(lengths):
    blocks = runs(lengths)
    assert blocks == runs(lengths, literal=True)
    visited_ports, visited_hexes, opened_q = set(), set(), set()
    b = 0
    violations = []
    for j, block in enumerate(blocks):
        orbit = qkey(block[0])
        b += int(j > 0 and orbit in opened_q)
        opened_q.add(orbit)
        for i, v in enumerate(block):
            if v in visited_ports:
                violations.append("repeated-entry-port")
            if hx(v) in visited_hexes and not (j > 0 and i == 0):
                violations.append("non-sigma-entry-into-old-hex")
            if j > 0 and i == 0:
                assert v == sigma(blocks[j - 1][-1])
                assert hx(v) == hx(blocks[j - 1][-1])
            visited_ports.add(v)
            visited_hexes.add(hx(v))
    P = sum(lengths)
    A = len(lengths) - 1
    D = 5 * len(opened_q) - P
    delta = sum(5 - r for r in lengths)
    assert delta == D + 5 * b
    valid = not violations
    if valid:
        assert D >= 0 and delta >= A
    return dict(lengths=list(lengths), valid=valid, A=A, b=b, D=D,
                Delta=delta, violations=sorted(set(violations)))


def audit_literal_extension(saved):
    n, word = saved["n"], saved["word"]
    symbols = set(map(str, range(n)))
    first, seen = [], set()
    for at in range(len(word) - n + 1):
        port = word[at:at+n]
        if set(port) == symbols and port not in seen:
            first.append((at, port))
            seen.add(port)
    groups = []
    for j, item in enumerate(first):
        if not j or item[0] != first[j-1][0] + 1:
            groups.append([])
        groups[-1].append(item)
    ports = [group[0][1] for group in groups]
    assert len(ports) == len(set(ports))
    which = {port: j for j, port in enumerate(ports)}
    hexa = lambda port: min(port[k:] + port[:k] for k in range(n))
    edges = {}
    for j in range(len(groups)-1):
        position, literal_source = groups[j][-1]
        source = which[sigma(literal_source)]
        target = j+1
        weight = groups[target][0][0] - position
        kind = "OTHER"
        if weight == 2:
            kind = "E" if E(ports[source]) == ports[target] else "A"
            if kind == "A":
                assert sigma(ports[source]) == ports[target]
        elif weight == 3 and hexa(ports[source]) == hexa(ports[target]):
            kind = "B"
            assert sigma(sigma(ports[source])) == ports[target]
        elif weight >= 4:
            kind = "HEAVY"
        assert source not in edges
        edges[source] = (target, kind)

    all_vertices = set(range(len(ports)))
    incoming = {target for target, _ in edges.values()}
    assert len(incoming) == len(edges)
    components, visited = [], set()
    # The unique open component precedes the cycles.
    for start in sorted(all_vertices-incoming) + sorted(all_vertices):
        if start in visited:
            continue
        component, current = [], start
        while current not in visited:
            component.append(current)
            visited.add(current)
            if current not in edges:
                break
            current = edges[current][0]
        components.append(component)
    assert len(components) == saved["K"]
    pure = [component for component in components[1:]
            if all(edges[v][1] == "E" for v in component)]
    assert len(pure) == saved["c"]
    removed = set(sum(pure, []))
    keep = all_vertices-removed
    cuts = {v for v in keep if v in edges and edges[v][1] == "HEAVY"}
    cycle_openings = set()
    for component in components[1:]:
        if component in pure or cuts.intersection(component):
            continue
        opening = min(v for v in component if edges[v][1] != "E")
        cycle_openings.add(opening)
        cuts.add(opening)
    x = sum(edges[v][1] == "A" for v in cycle_openings)
    y = sum(edges[v][1] == "B" for v in cycle_openings)
    d = saved["K"]-1-saved["c"]
    assert x+y <= len(cycle_openings) <= d
    retained = {v: e for v, e in edges.items() if v in keep and v not in cuts}
    incoming = {target for target, _ in retained.values()}
    paths = []
    for start in sorted(keep-incoming):
        path, current = [], start
        while True:
            path.append(current)
            if current not in retained:
                break
            current = retained[current][0]
        paths.append(path)
    assert set(sum(paths, [])) == keep
    assert sum(map(len, paths)) == len(keep)
    Aret = sum(kind == "A" for _, kind in retained.values())
    Bret = sum(kind == "B" for _, kind in retained.values())
    assert Aret == saved["D2"]-x
    assert Bret == saved["D3_same"]-y
    delta, bad = 0, 0
    for path in paths:
        blocks = []
        for v in path:
            if not blocks or retained[blocks[-1][-1]][1] != "E":
                blocks.append([])
            blocks[-1].append(v)
        assert all(1 <= len(block) <= n-1 for block in blocks)
        delta += sum(n-1-len(block) for block in blocks)
        clusters = []
        for block in blocks:
            if not clusters or retained[clusters[-1][-1][-1]][1] != "A":
                clusters.append([])
            clusters[-1].append(block)
        bad_targets = set()
        for cluster in clusters:
            full = [j for j, block in enumerate(cluster) if len(block) == n-1]
            for left, right in zip(full, full[1:]):
                if all(len(block) == n-2 for block in cluster[left+1:right]):
                    source = cluster[left][0]
                    target = cluster[right][-1]
                    assert hexa(ports[source]) == hexa(ports[target])
                    assert retained[cluster[right][-2]][1] == "E"
                    assert target not in bad_targets
                    bad_targets.add(target)
        bad += len(bad_targets)
        old_hex_entries, local_seen = set(), set()
        for v in path:
            if hexa(ports[v]) in local_seen:
                old_hex_entries.add(v)
            local_seen.add(hexa(ports[v]))
        same_targets = {retained[v][0] for v in path if v in retained
                        and retained[v][1] in ("A", "B")}
        assert not (bad_targets & same_targets)
        assert bad_targets | same_targets <= old_hex_entries
    repeat = sum(len(path)-len({hexa(ports[v]) for v in path}) for path in paths)
    original_repeat = sum(len(comp)-len({hexa(ports[v]) for v in comp})
                          for comp in components)
    assert original_repeat == saved["R_int"]
    assert Aret+Bret+bad <= repeat <= original_repeat
    assert delta >= Aret-bad
    assert delta == (n-1)*saved["k"]-saved["G"]+(n-1)*saved["Bstar"]
    assert original_repeat <= saved["D2"]+saved["Z"]-d
    sharp_bound = saved["D2"]-saved["Z"]+d-2*x-y+saved["D3_same"]
    uniform_bound = saved["D2"]-saved["Z"]-d+saved["D3_same"]
    assert delta >= sharp_bound >= uniform_bound
    return dict(n=n, word_sha256=hashlib.sha256(word.encode()).hexdigest(),
                A=saved["D2"], Qs=saved["D3_same"], Z=saved["Z"], d=d,
                x=x, y=y, bad=bad, Delta=delta, R_int=original_repeat,
                path_repeat=repeat, sharp_bound=sharp_bound,
                uniform_bound=uniform_bound)


def main():
    propagation_checks = 0
    forbidden_checks = 0
    for symbols in itertools.permutations("012345"):
        v = "".join(symbols)
        assert literal_targets(v) == (E(v), sigma(v))
        assert Epower(sigma(v), 4) == sigma_inv(E(v))
        assert Epower(sigma(Epower(v, 4)), 4) == sigma_inv(v)
        assert Epower(sigma(Epower(v, 3)), 4) == sigma_inv(Epower(v, 4))
        propagation_checks += 1
        for intermediate in range(6):
            lengths = (5,) + (4,) * intermediate + (5,)
            blocks = runs(lengths, start=v)
            assert blocks == runs(lengths, start=v, literal=True)
            final_fifth = blocks[-1][4]
            assert hx(final_fifth) == hx(v)
            assert final_fifth == E(blocks[-1][3])
            for block in blocks[1:-1]:
                assert len(block) == 4
                assert hx(Epower(block[0], 4)) == hx(v)
            forbidden_checks += 1

    rows = [audit(lengths) for count in range(1, 5)
            for lengths in itertools.product(range(1, 6), repeat=count)]
    assert len(rows) == 780
    sharp = [audit((5, 4)), audit((5, 3, 5))]
    assert all(r["valid"] and r["b"] == 0 and r["D"] == r["A"]
               for r in sharp)
    control_path = ROOT / "outputs/rr_round142_shadow_budget_verified_codex.json"
    saved_controls = json.loads(control_path.read_text())
    extension_controls = [audit_literal_extension(row) for row in saved_controls["rows"]]
    proof = ROOT / "research/RR_ROUND143_SIGMA_DEFICIT_CODEX.md"
    output = dict(
        schema="round143-sigma-deficit-hand-lemma-checks-v1",
        theorem="D + 5*b >= A under the explicitly stated SIGMA path rules",
        local_renamings=propagation_checks,
        forbidden_pattern_checks=forbidden_checks,
        forbidden_pattern_intermediate_fours=list(range(6)),
        bounded_template_max_runs=4,
        bounded_template_count=len(rows),
        bounded_valid_templates=sum(r["valid"] for r in rows),
        sharp_controls=sharp,
        extension_control_count=len(extension_controls),
        extension_controls=extension_controls,
        extension_input_sha256=hashlib.sha256(control_path.read_bytes()).hexdigest(),
        all_bounded_valid_templates_obey_lemma=True,
        independent_literal_endpoint_match=True,
        completed=True,
        capped=False,
        scope="Local identities exhaustive over all 720 renamings; templates "
              "bounded. The unrestricted theorem is proved by induction in "
              "the accompanying hand proof, not by these controls. No global "
              "capacity or cover closure is claimed.",
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        hand_proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
        bounded_templates=rows,
    )
    destination = ROOT / "outputs/rr_round143_sigma_deficit_codex.json"
    destination.write_text(json.dumps(output, indent=2) + "\n", newline="\n")
    print(json.dumps({key: output[key] for key in (
        "local_renamings", "forbidden_pattern_checks", "bounded_template_count",
        "bounded_valid_templates", "extension_control_count", "completed", "capped")}))


if __name__ == "__main__":
    main()
