#!/usr/bin/env python3
"""Round 162 Phase 20 -- downstream search for the fixed-representative step.

The corollary of H.fixedrep is a WLOG: a lower bound proved for every FIXED
representative is a lower bound for every cover.  That is sound only if the
downstream argument

  (D1) never assumes anything about W* STRONGER than Lemma 5,
  (D2) never quietly performs a SECOND normalisation on top of it,
  (D3) never carries a coordinate computed BEFORE normalisation into a
       statement about the normalised word,
  (D4) never assumes the fixed representative is UNIQUE.

Each of the four is turned into a mechanical check over the file set the
final theorem path actually reaches (`where` fields of the repaired DAG plus
the transitive closure of in-repository imports).  Regex hits are evidence,
not verdicts: every hit is emitted with file:line so the audit document can
adjudicate it.  D1 and D4 additionally get a positive test -- D1 by running
the audited splicing analyser on real fixed representatives, D4 by exhibiting
distinct fixed representatives of equal length.
"""
from __future__ import annotations
import json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DAG = ROOT / "r162" / "certs" / "dag_162.json"
sys.path.insert(0, str(HERE))
import fixedrep162 as F                                           # noqa: E402

# This round's own artefacts NAME the patterns being searched for, so a
# keyword scan would flag them as findings.  Excluded, and the exclusion is
# recorded in the certificate.
SELF = ("r162/", "research/RR_L6_H_FIXEDREP_AUDIT.md")

# (D1) how downstream code spells "W is a fixed representative"
FIXED_PRED = {
    "gap_equals_omega": r"(?:!=|==)\s*omega\(",
    "phrase_not_a_fixed_representative": r"not a fixed representative",
    "calls_fixed_representative": r"\bfixed_representative\s*\(",
}
# (D2) markers of a second normalisation (relabelling / lexicographic choice)
SECOND_NORM = {
    "relabel": r"\brelabel\w*\b",
    "wlog": r"\bWLOG\b|\bwlog\b|without loss of generality",
    "lexicographic": r"\blexicograph\w*",
    "assume_start": r"assume[sd]?\s+(?:that\s+)?W\s+starts",
    "rotate_word": r"\brotate_word\b|\bcyclic(?:ally)?\s+rotat",
}
# (D4) markers of an assumed-unique / canonical representative
UNIQUENESS = {
    "unique": r"\bunique(?:ly|ness)?\b",
    "canonical": r"\bcanonical\b",
    "the_normal_form": r"\bnormal form\b",
    "korean_unique": r"유일",
    "korean_canonical": r"정준",
}
# (D3) entry points that produce proof coordinates from a word
COORD_CALL = r"\b(structure|analyse|analyze|coordinates|build)\s*\(\s*([A-Za-z_][\w\[\]\.]*)"
NORMALISED_ARGS = {"Ws", "wf", "ws", "W_fixed", "wfix", "Wstar", "W_star"}


def is_self(p):
    rel = str(p.relative_to(ROOT))
    return any(rel.startswith(x) or rel == x for x in SELF)


def repo_files():
    out = []
    for suf in ("*.py", "*.md"):
        for p in ROOT.rglob(suf):
            if ".git" not in p.parts:
                out.append(p)
    return out


def where_paths(dag):
    out = []
    for nid, v in dag["nodes"].items():
        for tok in re.split(r"[;,]", v.get("where", "")):
            m = re.match(r"([\w./-]+\.(?:py|md|json|txt))", tok.strip())
            if m:
                out.append((nid, m.group(1)))
    return out


def imports_of(path):
    if path.suffix != ".py":
        return set()
    txt = path.read_text(errors="ignore")
    return (set(re.findall(r"^\s*import\s+([\w_]+)", txt, re.M)) |
            set(re.findall(r"^\s*from\s+([\w_]+)\s+import", txt, re.M)))


def reachable(files, dag):
    bymod = {}
    for p in files:
        if p.suffix == ".py":
            bymod.setdefault(p.stem, []).append(p)
    seeds, missing = [], []
    for nid, rel in where_paths(dag):
        q = ROOT / rel
        (seeds if q.exists() else missing).append(q if q.exists()
                                                  else (nid, rel))
    for rel in ("r152/src/rows152.py", "r152/src/checker152.py",
                "r153/src/dag153.py", "r153/src/theorem153.py",
                "src/l6_proof_145.py"):
        q = ROOT / rel
        if q.exists():
            seeds.append(q)
    reach, stack = set(), list(seeds)
    while stack:
        p = stack.pop()
        if p in reach:
            continue
        reach.add(p)
        for m in imports_of(p):
            for q in bymod.get(m, []):
                if q not in reach:
                    stack.append(q)
    return reach, missing


def scan(reach, pats):
    """file:line evidence for each pattern, on the theorem path only."""
    hits = {}
    for p in sorted(reach, key=lambda x: str(x)):
        if is_self(p):
            continue
        rel = str(p.relative_to(ROOT))
        for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            for name, rx in pats.items():
                if re.search(rx, line):
                    hits.setdefault(name, []).append(
                        dict(at=f"{rel}:{i}", text=line.strip()[:110]))
    return hits


# --------------------------------------------------------------- D1 positive
def d1_positive(limit6=3):
    """Run the AUDITED splicing analyser on real fixed representatives.

    If any downstream step demanded more than Lemma 5 gives, a genuine fixed
    representative would trip it.  l6_splicing_145.analyse is pure in W.
    """
    sys.path.insert(0, str(ROOT / "src"))
    import l6_splicing_145 as SP                                  # noqa: E402
    out, bad = [], []
    W6 = (ROOT / "data" / "verified_872_witness.txt").read_text().strip()
    rng = __import__("random").Random(20162)
    words = [(6, "123456", W6)]
    for _ in range(limit6 - 1):
        V, wid = F.inflate(W6, 6, rng)
        if F.is_cover(V, 6, "123456") and wid:
            words.append((6, "123456", V))
    sys.path.insert(0, str(ROOT / "r156" / "src"))
    import run156 as R                                            # noqa: E402
    words.append((4, "1234", R.W4))
    for n, alpha, W in words:
        Ws, _lens, _steps, b = F.iterate(W, n, alpha)
        if b:
            bad.append(dict(n=n, stage="normalisation", why=[str(x) for x in b]))
            continue
        # analyse() returns a DICT: nfail is the true count, failures is the
        # first 8 of them, ok is nfail == 0.
        res = SP.analyse(Ws, n)
        shown = [f[0] if isinstance(f, (list, tuple)) else str(f)
                 for f in res.get("failures", [])]
        notfixed = [x for x in shown if "fixed representative" in x]
        out.append(dict(n=n, input_len=len(W), fixed_len=len(Ws),
                        splicing_nfail=res.get("nfail"),
                        splicing_ok=res.get("ok"),
                        failures_shown=shown,
                        not_a_fixed_representative=len(notfixed),
                        MASTER_holds=res.get("MASTER_holds"),
                        FO_holds=res.get("FO_holds")))
        if res.get("nfail") or notfixed:
            bad.append(dict(n=n, stage="splicing", nfail=res.get("nfail"),
                            why=shown[:8]))
    return out, bad


# --------------------------------------------------------------- D3 positive
def d3_positive():
    """The literal corpora fed to un-enforcing entry points are already fixed.

    `extract()` (src/l6_extraction_145.py) is the one coordinate entry point on
    the path that does NOT re-check the hypothesis; it inherits it from its
    caller.  Its call sites feed three literal corpora.  Check each word really
    is a fixed point of Phi, so the inherited hypothesis actually holds.
    """
    out = []
    W4 = "123412314231243121342132413214321"
    corpora = [("n4_optimum", 4, "1234", [W4])]
    p5 = ROOT / "outputs" / "rr_nr6_n5_minima_142.json"
    if p5.exists():
        raw = json.loads(p5.read_text())
        w5 = sorted({e["word"] for e in raw
                     if isinstance(e, dict) and "word" in e})
        corpora.append(("n5_minima", 5, "01234", w5))
    p6 = ROOT / "data" / "verified_872_witness.txt"
    if p6.exists():
        corpora.append(("n6_witness_872", 6, "123456",
                        [p6.read_text().strip()]))
    bad = []
    for tag, n, alpha, words in corpora:
        nfix = 0
        for w in words:
            a = alpha if set(alpha) == set(w) else "".join(sorted(set(w)))
            if F.is_cover(w, n, a) and F.Phi(w, n) == w and F.trim(w, n) == w:
                nfix += 1
            else:
                bad.append(dict(corpus=tag, length=len(w)))
        out.append(dict(corpus=tag, n=n, words=len(words),
                        already_fixed=nfix,
                        all_already_fixed=nfix == len(words)))
    return out, bad


# --------------------------------------------------------------- D4 positive
def d4_positive(n=3, L=9):
    """Exhibit DISTINCT fixed representatives of the same n and length."""
    alpha = "".join(str(i + 1) for i in range(n))
    reps, count = set(), 0
    stack = [""]
    while stack:
        w = stack.pop()
        if len(w) == L:
            if F.is_cover(w, n, alpha):
                count += 1
                Ws, _l, _s, b = F.iterate(w, n, alpha)
                if not b:
                    reps.add(Ws)
            continue
        for c in alpha:
            stack.append(w + c)
    same_len = sorted(r for r in reps if len(r) == L)
    return dict(n=n, word_length=L, covers=count,
                distinct_fixed_representatives=len(reps),
                distinct_of_that_length=len(same_len),
                examples=same_len[:4],
                uniqueness_is_false=len(same_len) > 1)


def main():
    t0 = time.time()
    dag = json.loads(DAG.read_text())["dag"]
    files = repo_files()
    reach, missing = reachable(files, dag)

    d1_hits = scan(reach, FIXED_PRED)
    d2_hits = scan(reach, SECOND_NORM)
    d4_hits = scan(reach, UNIQUENESS)

    # D3: every call site of a coordinate-producing entry point on the path.
    # Three evidence labels per site, no verdicts:
    #   enclosing_def / arg_is_parameter  -- the hypothesis is inherited
    #   normalised_earlier_in_file        -- the file normalises first
    #   callee_enforces_fixedness         -- the callee CHECKS gap == omega
    # Comment tails are stripped first (a prose "structure (S3)" is not a call).
    enforcers = set()
    for p in sorted(reach, key=lambda x: str(x)):
        if p.suffix == ".py" and "not a fixed representative" in \
                p.read_text(errors="ignore"):
            enforcers.add(p.stem)
    calls = []
    for p in sorted(reach, key=lambda x: str(x)):
        if is_self(p) or p.suffix != ".py":
            continue
        rel = str(p.relative_to(ROOT))
        lines = p.read_text(errors="ignore").splitlines()
        norm_lines = [i for i, l in enumerate(lines, 1)
                      if re.search(r"=\s*fixed_representative\s*\(|"
                                   r"=\s*[A-Za-z_]*\.?iterate\s*\(", l)]
        cur_def, cur_params = None, set()
        for i, line in enumerate(lines, 1):
            code = line.split("#", 1)[0]
            m = re.match(r"\s*def\s+(\w+)\s*\(([^)]*)", code)
            if m:
                cur_def = m.group(1)
                cur_params = {x.split("=")[0].strip()
                              for x in m.group(2).split(",") if x.strip()}
                continue
            for m in re.finditer(COORD_CALL, code):
                fn, arg = m.group(1), m.group(2)
                calls.append(dict(
                    at=f"{rel}:{i}", fn=fn, arg=arg,
                    enclosing_def=cur_def,
                    arg_is_parameter=arg in cur_params,
                    normalised_name=arg in NORMALISED_ARGS,
                    normalised_earlier_in_file=any(j < i for j in norm_lines),
                    callee_enforces_fixedness=(fn == "analyse"
                                               and bool(enforcers)),
                    text=line.strip()[:110]))

    # the Phi NAME COLLISION: a different Phi (a capacity potential) lives in
    # the search branch.  Recorded so the two are never conflated.
    collide = []
    for p in files:
        if is_self(p):
            continue
        txt = p.read_text(errors="ignore")
        if re.search(r"Phi\(S", txt) or re.search(r"phi_definition", txt):
            collide.append(str(p.relative_to(ROOT)))

    d1_runs, d1_bad = d1_positive()
    d3_runs, d3_bad = d3_positive()
    d4 = d4_positive()

    out = dict(
        seconds=round(time.time() - t0, 1),
        dag_source=str(DAG.relative_to(ROOT)),
        self_references_excluded=list(SELF),
        theorem_path_files=len(reach),
        where_paths_missing=[list(x) for x in missing],
        D1_fixedness_predicates=d1_hits,
        D1_distinct_predicate_forms=sorted(d1_hits),
        D1_positive_runs=d1_runs,
        D1_failures=d1_bad,
        D2_second_normalisation_hits=d2_hits,
        D3_coordinate_call_sites=calls,
        D3_entry_points_not_enforcing=sorted(
            {c["at"] for c in calls if not c["callee_enforces_fixedness"]}),
        D3_positive=d3_runs,
        D3_failures=d3_bad,
        D4_uniqueness_hits=d4_hits,
        D4_positive=d4,
        phi_name_collision=sorted(collide),
    )
    out["ok"] = (not d1_bad and not d3_bad
                 and all(r["all_already_fixed"] for r in d3_runs)
                 and out["D1_positive_runs"] != []
                 and d4["uniqueness_is_false"]
                 and all(r["not_a_fixed_representative"] == 0
                         for r in d1_runs))
    (ROOT / "r162" / "certs" / "downstream_162.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in
                      ("seconds", "theorem_path_files",
                       "D1_distinct_predicate_forms",
                       "D1_failures", "D3_entry_points_not_enforcing",
                       "D3_positive", "D3_failures", "D4_positive", "ok")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
