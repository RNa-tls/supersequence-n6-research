"""Independent finite audit of chronological J/topology identities.

No continuation search.  The abstract domain is all permutations of sizes
1..8; the literal domain is the already preserved, complete Round-140 NR4
corpus.  Its exit-window parser is an explicitly hashed dependency, not the
Round-140 producer's parse/support/splice implementation.

The hand proof is not inferred from the finite domain: for each non-dummy
beta circuit choose its minimum m and the incoming predecessor v.  Then
beta(v)=m<=v, so nu(m-1)=v>m-1.  Distinct circuits charge distinct ascents;
a pure-free circuit charges a free ascent.  Thus K-1<=F and c<=F-a.
"""

import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from verify_round140_g3_codex import data_word


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = [
    "src/verify_round141_j_topology_codex.py",
    "src/verify_round140_g3_codex.py",
]
INPUT_PATH = "outputs/rr_round140_nr4_codex.json"
OUTPUT_PATH = "outputs/rr_round141_j_topology_verified_codex.json"
CROSSING_WORD = "012301203102130210312013201023103210"
SHARP_WORD = "012310213012023120312301320130210321023"


def digest_json(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def permutation_cycles(nu):
    assert sorted(nu) == list(range(len(nu)))
    unseen = set(range(len(nu)))
    answer = []
    while unseen:
        start = value = min(unseen)
        cycle = []
        while value in unseen:
            unseen.remove(value)
            cycle.append(value)
            value = nu[value]
        assert value == start
        answer.append(cycle)
    return answer


def orbit(word):
    first = word[:-1]
    return min(first[i:] + first[:i] + word[-1:] for i in range(len(first)))


def audit_permutation(nu):
    """Check the charge map directly, rather than importing support()."""
    nu = tuple(nu)
    cycles = permutation_cycles(nu)
    size = len(nu)
    extended = nu + (size,)
    inverse = {target: source for source, target in enumerate(extended)}
    beta = tuple((inverse[v] + 1) % (size + 1) for v in range(size + 1))
    beta_cycles = permutation_cycles(beta)
    G = size - len(cycles)
    ascents = {i for i, target in enumerate(nu) if i < target}
    F = len(ascents)
    J = G - F
    K = len(beta_cycles)
    assert G + 1 - K >= 0 and (G + 1 - K) % 2 == 0
    genus = (G + 1 - K) // 2
    charged = []
    for cycle in beta_cycles:
        if size in cycle:
            continue
        minimum = min(cycle)
        predecessor = next(v for v in cycle if beta[v] == minimum)
        assert 0 < minimum <= predecessor < size
        source = minimum - 1
        assert nu[source] == predecessor and source in ascents
        charged.append(source)
    assert len(charged) == len(set(charged)) == K - 1
    assert K - 1 <= F and 0 <= J <= 2 * genus
    sorted_cycles = True
    for cycle in cycles:
        if len(cycle) == 1:
            continue
        ordered = sorted(cycle)
        successor = dict(zip(ordered, ordered[1:] + ordered[:1]))
        increasing_order = all(nu[v] == successor[v] for v in cycle)
        descents = sum(nu[v] < v for v in cycle)
        assert descents >= 1 and (descents == 1) == increasing_order
        sorted_cycles = sorted_cycles and increasing_order
    assert (J == 0) == sorted_cycles
    return dict(
        G=G, F=F, J=J, K=K, g=genus,
        charged_ascents=charged, nu_cycles=cycles, beta_cycles=beta_cycles,
    )


def crossing_pair(cycles):
    for first, second in itertools.combinations(cycles, 2):
        for a, c in itertools.combinations(sorted(first), 2):
            for b, d in itertools.combinations(sorted(second), 2):
                if a < b < c < d or b < a < d < c:
                    return dict(cycles=[first, second], endpoints=[a, b, c, d])
    return None


def audit_word(word, n=4):
    """Use independent R140 exit-window replay, then rederive event counts."""
    parsed = data_word(word, n)
    entries = parsed["entries"]
    entry_index = {entry: i for i, entry in enumerate(entries)}
    # The full-exit mapping determines each old joint's original endpoint.
    literal = tuple(map(int, word))
    positions = [i for i in range(len(literal) - n + 1)
                 if set(literal[i:i+n]) == set(range(n))]
    windows = [literal[i:i+n] for i in positions]
    groups = []
    for i, window in enumerate(windows):
        if i == 0 or positions[i] != positions[i-1] + 1:
            groups.append([])
        groups[-1].append(window)
    assert [group[0] for group in groups] == entries
    nu = tuple(entry_index[group[-1][1:] + group[-1][:1]] for group in groups)
    topology = audit_permutation(nu)
    assert (topology["K"], topology["G"], topology["F"]) == (
        parsed["K"], parsed["metrics"]["G"], parsed["metrics"]["F"],
    )
    qs = [orbit(entry) for entry in entries]
    weights = []
    for i in range(len(entries) - 1):
        target, weight = parsed["successor"][entries[nu[i]]]
        assert target == entries[i+1]
        weights.append(weight)
    free = {i for i, weight in enumerate(weights)
            if weight == 2 and qs[i] != qs[i+1]}
    ascents = {i for i, target in enumerate(nu) if i < target}
    ordinary = {i+1 for i in free if nu[i] < i}
    repeats = {i for i in range(1, len(entries))
               if qs[i] != qs[i-1] and qs[i] in qs[:i]}
    assert ordinary <= repeats
    a = len(ascents - free)
    eta = len(repeats - ordinary)
    x = sum(weight >= 3 and qs[i] == qs[i+1]
            for i, weight in enumerate(weights))
    S = sum(weight >= 3 for weight in weights)
    assert (a, eta, x, S) == tuple(parsed["metrics"][k] for k in ("a", "eta", "x", "S"))
    pure_charges = []
    for circuit in parsed["pure"]:
        indices = {entry_index[v] for v in circuit}
        minimum = min(indices)
        source = minimum - 1
        assert source >= 0 and source in ascents & free
        predecessor = entries[nu[source]]
        assert predecessor in circuit
        assert parsed["successor"][predecessor] == (entries[minimum], 2)
        pure_charges.append(source)
    c = len(parsed["pure"])
    assert len(set(pure_charges)) == c
    G, F, J, K, g = (topology[k] for k in ("G", "F", "J", "K", "g"))
    omega = F - a - c
    z = G - c
    d = K - 1 - c
    assert omega >= 0 and d >= 0 and c <= F - a
    assert z == J + a + omega == 2 * g + d
    assert parsed["R"] <= 2 * g
    local_freeblock_budget = S + 1 - len(set(qs)) + c
    assert local_freeblock_budget == eta + x - omega >= 0
    return dict(
        word=word, n=n, length=len(word), nu=list(nu),
        G=G, F=F, J=J, K=K, g=g, R=parsed["R"], c=c,
        a=a, eta=eta, x=x, omega=omega, z=z, d=d,
        exact_freeblock_budget=local_freeblock_budget,
        pure_cycle_charge_origins=pure_charges,
        crossing=crossing_pair(topology["nu_cycles"]),
    )


def committed_inputs():
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    committed, runtime = {}, {}
    for name in SOURCE_PATHS + [INPUT_PATH]:
        raw = subprocess.check_output(["git", "-C", str(ROOT), "show", head + ":" + name])
        committed[name] = hashlib.sha256(raw).hexdigest()
        runtime[name] = sha(ROOT / name)
        # Historical parser bytes can be CRLF while the committed canonical
        # blob is LF. Preserve both hashes; reject every non-newline change.
        assert raw.replace(b'\r\n',b'\n') == (ROOT/name).read_bytes().replace(b'\r\n',b'\n'), "Uncommitted or altered audit input: " + name
    return head, committed, runtime


def main():
    assert sys.flags.optimize == 0, "Assertions must be enabled for certificate verification"
    started = time.perf_counter()
    head, committed, runtime = committed_inputs()
    by_size = Counter()
    abstract_histogram = Counter()
    abstract_digest = hashlib.sha256()
    for size in range(1, 9):
        for nu in itertools.permutations(range(size)):
            row = audit_permutation(nu)
            by_size[size] += 1
            abstract_histogram[(row["J"], row["g"])] += 1
            abstract_digest.update((digest_json(dict(nu=nu, audit=row)) + "\n").encode())
    assert sum(by_size.values()) == 46233 == sum(math.factorial(n) for n in range(1, 9))
    archive = json.loads((ROOT / INPUT_PATH).read_text())
    assert archive["summary"]["capped"] is False
    words = archive["words"]
    assert len(words) == len(set(words)) == archive["summary"]["walks"] == 29255
    literal_histogram = Counter()
    literal_digest = hashlib.sha256()
    fixtures = {}
    for word in words:
        row = audit_word(word)
        literal_histogram[(row["G"], row["J"], row["omega"])] += 1
        literal_digest.update((digest_json(row) + "\n").encode())
        if word in (CROSSING_WORD, SHARP_WORD):
            fixtures[word] = row
    crossing = fixtures[CROSSING_WORD]
    assert crossing["J"] == crossing["a"] == 0 and crossing["g"] == 1 and crossing["crossing"]
    sharp = fixtures[SHARP_WORD]
    assert sharp["G"] == 5 and sharp["J"] == sharp["z"] == 2
    assert sharp["a"] == sharp["eta"] == sharp["omega"] == 0 and sharp["c"] == 3
    result = dict(
        schema="codex/round141-j-topology-independent/1",
        verified=True, completed=True, status="COMPLETE_FINITE_AUDIT", capped=False,
        node_limit=None, continuation_search=False,
        scope="All abstract supports size1..8 and the preserved complete normalized NR4 length<=39 corpus; not an NR6 search",
        hand_proof_dependency="Distinct beta circuits charge distinct chronological ascents; pure-free circuits charge free ascents",
        exact_identities=["K-1<=F", "J<=2g", "c<=F-a", "omega=F-a-c>=0",
                          "z=J+a+omega=2g+d", "sum(b_j)+s=eta+x-omega>=0"],
        dependency_role={SOURCE_PATHS[1]: "Independent Round140 literal exit-window parser, not producer parse/support/splice"},
        abstract_permutations=sum(by_size.values()), abstract_count_by_size=dict(by_size),
        abstract_J_genus_histogram={str(k): v for k, v in sorted(abstract_histogram.items())},
        abstract_transcript_sha256=abstract_digest.hexdigest(),
        nr4_words=len(words), literal_G_J_omega_histogram={str(k): v for k, v in sorted(literal_histogram.items())},
        literal_transcript_sha256=literal_digest.hexdigest(),
        counterexamples={"J0_does_not_imply_noncrossing_or_genus_zero": crossing},
        sharpness_controls={"z_equals_positive_J": sharp},
        nodes=dict(abstract_supports=sum(by_size.values()), literal_words=len(words)),
        commit=head, committed_sha256=committed, runtime_sha256=runtime,
        newline_only_runtime_differences=[p for p in committed if committed[p]!=runtime[p]],
        argv=sys.argv, python_executable=sys.executable, python_executable_sha256=sha(sys.executable),
        python_version=platform.python_version(), seconds=time.perf_counter()-started,
    )
    result["mathematical_digest"] = digest_json({k: v for k, v in result.items()
                                                if k not in ("commit", "committed_sha256", "runtime_sha256", "argv",
                                                             "python_executable", "python_executable_sha256", "python_version", "seconds")})
    (ROOT / OUTPUT_PATH).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(verified=True, abstract_permutations=sum(by_size.values()), nr4_words=len(words),
                          output=OUTPUT_PATH, seconds=result["seconds"])))


if __name__ == "__main__":
    main()
