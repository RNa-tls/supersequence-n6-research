#!/usr/bin/env python3
"""Round 163 -- current-DAG hand-proof inventory (phases 0, 1, 6, 7, 13).

Nothing here proves a theorem.  It reconstructs, from the repository alone,
which DAG file is authoritative, what is on the theorem path, which nodes are
hand proofs, what each one's provenance actually points at, and whether the
whole path walks from the leaves to T.eq872 without an unresolved source.
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HAND = "AUDITED_HAND_PROOF"


def sha(p):
    q = ROOT / p
    return hashlib.sha256(q.read_bytes()).hexdigest() if q.exists() else None


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


# ---------------------------------------------------------------- phase 0
def lineage():
    """Walk `supersedes` back from every dag_*.json and check the hash chain."""
    files = sorted(str(p.relative_to(ROOT))
                   for p in ROOT.glob("r1*/certs/dag_*.json"))
    meta = {}
    for rel in files:
        d = json.loads((ROOT / rel).read_text())
        meta[rel] = dict(sha256=sha(rel), supersedes=d.get("supersedes"),
                         source_sha256=d.get("source_sha256"),
                         nodes=len(d.get("dag", {}).get("nodes", {})))
    superseded = {v["supersedes"] for v in meta.values() if v["supersedes"]}
    # r147..r152 predate the `supersedes` convention, so "not superseded by
    # name" does not make them heads.  The authoritative file is the highest
    # round number; the chain check below is what actually validates it.
    no_field = [f for f in files if meta[f]["supersedes"] is None]
    heads = [f for f in files if f not in superseded]
    rank = lambda f: int(re.match(r"r(\d+)", f).group(1))
    auth = max(files, key=rank) if files else None
    chain, broken, cur = [], [], auth
    # follow the head back to the root, verifying each source hash
    while cur:
        chain.append(cur)
        prev = meta[cur]["supersedes"]
        if not prev:
            break
        if prev not in meta:
            broken.append(dict(at=cur, missing=prev))
            break
        if meta[cur]["source_sha256"] != meta[prev]["sha256"]:
            broken.append(dict(at=cur, expected=meta[cur]["source_sha256"],
                               actual=meta[prev]["sha256"]))
        cur = prev
    # rounds that produced artefacts but no DAG revision
    rounds = sorted({p.name for p in ROOT.glob("r1*") if p.is_dir()})
    with_dag = {rel.split("/")[0] for rel in files}
    return dict(all_dag_files=meta, heads=heads,
                predate_supersedes_convention=no_field,
                authoritative=auth,
                chain_root=chain[-1] if chain else None,
                chain_newest_first=chain, chain_breaks=broken,
                rounds_with_artefacts=rounds,
                rounds_without_a_dag_revision=[r for r in rounds
                                               if r not in with_dag])


# ---------------------------------------------------------------- phase 1
def closure(nodes, start, forward):
    """Reachable set from `start` following deps (forward=False) or rdeps."""
    seen, stack = set(), [start]
    while stack:
        x = stack.pop()
        for y in forward.get(x, ()) if forward else ():
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def node_table(dag):
    nodes = dag["nodes"]
    rdeps = {k: [] for k in nodes}
    for k, v in nodes.items():
        for d in v.get("deps", []):
            rdeps.setdefault(d, []).append(k)

    def trans_down(start):
        seen, stack = set(), [start]
        while stack:
            x = stack.pop()
            for y in rdeps.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen

    def trans_up(start):
        seen, stack = set(), [start]
        while stack:
            x = stack.pop()
            for y in nodes.get(x, {}).get("deps", ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen

    on_path = trans_up(dag["top"]) | {dag["top"]}
    out = {}
    for k, v in nodes.items():
        out[k] = dict(status=v.get("status"), what=v.get("what"),
                      where=v.get("where"),
                      derived_from=v.get("derived_from"),
                      deps=v.get("deps", []),
                      direct_dependents=sorted(rdeps.get(k, [])),
                      transitive_dependents=len(trans_down(k)),
                      on_theorem_path=k in on_path)
    return out, sorted(on_path)


# ---------------------------------------------------------------- phase 6
DOC_RE = r"[\w./-]+\.(?:py|md|json|txt|exe)"


def provenance(table):
    rows = {}
    for k, v in table.items():
        if v["status"] != HAND:
            continue
        w = v["where"] or ""
        paths = re.findall(DOC_RE, w)
        exists = {p: (ROOT / p).exists() for p in paths}
        df = v["derived_from"] or ""
        dfp = re.findall(DOC_RE, df)
        dfx = {p: (ROOT / p).exists() for p in dfp}
        # does the cited document look like it states this node's claim?
        mentions = {}
        for p, ok in exists.items():
            if not ok or not p.endswith((".md", ".py")):
                continue
            txt = (ROOT / p).read_text(errors="ignore")
            mentions[p] = dict(names_node=k in txt,
                               size=len(txt.splitlines()))
        rows[k] = dict(
            where=w, where_paths=exists,
            where_is_prose_only=(paths == []),
            where_all_exist=all(exists.values()) and bool(exists),
            derived_from_present=bool(v["derived_from"]),
            derived_from_paths=dfx,
            derived_from_all_exist=all(dfx.values()) if dfx else None,
            what_is_placeholder=len((v["what"] or "").split()) <= 4,
            cited_docs=mentions)
    return rows


# ---------------------------------------------------------------- phase 7
def deps_semantics(table):
    """Is `deps: []` on hand-proof leaves a convention or an omission?"""
    hand = {k: v for k, v in table.items() if v["status"] == HAND}
    empty = [k for k, v in hand.items() if not v["deps"]]
    # mathematical dependencies asserted in prose (derived_from / what)
    NODE_RE = r"\b([HACEXTW]\.[a-z0-9]+)\b"
    prose = {}
    for k, v in hand.items():
        txt = f"{v['what']} {v['derived_from']}"
        named = sorted({m for m in re.findall(NODE_RE, txt) if m != k})
        prose[k] = named
    return dict(hand_nodes=len(hand), hand_with_empty_deps=sorted(empty),
                all_hand_leaves_are_empty=len(empty) == len(hand),
                prose_dependencies=prose,
                nodes_whose_prose_names_a_dependency=sorted(
                    k for k, v in prose.items() if v))


# ---------------------------------------------------------------- phase 13
def walk(dag, table):
    """Topological walk from sources to the top, labelling every source."""
    nodes = dag["nodes"]
    order, seen = [], set()

    def visit(x):
        if x in seen:
            return
        seen.add(x)
        for d in nodes[x].get("deps", []):
            visit(d)
        order.append(x)
    visit(dag["top"])
    sources = [k for k in order if not nodes[k].get("deps")]
    labels = {k: nodes[k]["status"] for k in sources}
    bad = {k: s for k, s in labels.items()
           if s not in ("EXPLICIT_WITNESS", "PROVEN_ANALYTIC",
                        "CERTIFIED_MACHINE", HAND)}
    edges = []
    for k in order:
        for d in nodes[k].get("deps", []):
            edges.append(dict(frm=d, to=k, to_status=nodes[k]["status"]))
    forbidden = [k for k, v in nodes.items()
                 if v["status"] in ("UNKNOWN", "RETRACTED", "FORBIDDEN",
                                    "UNRESOLVED", "UNKNOWN_CAP")]
    return dict(topological_order=order, edge_count=len(edges),
                sources=sources, source_labels=labels,
                sources_with_a_bad_label=bad,
                forbidden_or_unresolved_nodes=forbidden,
                top=dag["top"],
                dag_claims_theorem_path_clean=dag.get("theorem_path_clean"))


def main():
    lin = lineage()
    auth = lin["authoritative"]
    assert auth, f"no single authoritative DAG: {lin['heads']}"
    dag = json.loads((ROOT / auth).read_text())["dag"]
    table, on_path = node_table(dag)
    out = dict(
        branch=git("rev-parse", "--abbrev-ref", "HEAD"),
        head=git("rev-parse", "HEAD"),
        git_dirty=bool(git("status", "--porcelain")),
        dag_path=auth, dag_sha256=sha(auth),
        node_count=len(table),
        theorem_path_node_count=len(on_path),
        theorem_path_nodes=on_path,
        off_path_nodes=sorted(k for k in table
                              if not table[k]["on_theorem_path"]),
        status_counts={s: sum(1 for v in table.values()
                              if v["status"] == s)
                       for s in sorted({v["status"]
                                        for v in table.values()})},
        hand_proof_nodes=sorted(k for k, v in table.items()
                                if v["status"] == HAND),
        lineage=lin, nodes=table,
        provenance=provenance(table),
        deps_semantics=deps_semantics(table),
        walk=walk(dag, table))
    out["ok"] = (out["node_count"] == out["theorem_path_node_count"]
                 and not out["walk"]["sources_with_a_bad_label"]
                 and not out["walk"]["forbidden_or_unresolved_nodes"]
                 and not lin["chain_breaks"])
    (ROOT / "r163" / "certs" / "inventory_163.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    brief = {k: out[k] for k in ("branch", "head", "dag_path", "dag_sha256",
                                 "node_count", "theorem_path_node_count",
                                 "status_counts", "hand_proof_nodes",
                                 "off_path_nodes", "ok")}
    brief["chain"] = lin["chain_newest_first"]
    brief["chain_breaks"] = lin["chain_breaks"]
    brief["rounds_without_a_dag_revision"] = lin["rounds_without_a_dag_revision"]
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
