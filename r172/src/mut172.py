#!/usr/bin/env python3
"""Round 172 (EXPERIMENTAL) -- mutation suite for the R1 architecture.

Every mutant proof object must be REJECTED by verifier A4 and verifier B4
(and, for format mutants, by the unchanged Round-168 verifiers).  Positive
controls must be ACCEPTED.  Two layers:

  layer T (text):   a valid R1 file is edited (annotation, header, hashes, leaf
                    kind, format line).
  layer G (search): a MUTANT generator prunes with a deliberately wrong R1 rule
                    and writes either
                      faithful -- the annotation its wrong rule computed, or
                      honest   -- the true annotation (so the verifier must
                                  reject on the inequality, not on the
                                  annotation mismatch).
                    A generator mutant counts only if it is EXERCISED: its tree
                    differs from the correct tree for the same input.
                    Mutants that can only make the rule MORE conservative
                    (extra branches in a max) cannot produce an unsound leaf;
                    for those the honest variant is expected to be accepted and
                    that is reported, not hidden.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r172" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import fixtures172 as FX                                          # noqa: E402
import gen172 as X                                                # noqa: E402
import verifyA172 as VA                                           # noqa: E402
import verifyB172 as VB                                           # noqa: E402
import trust172                                                   # noqa: E402
import verifyA168 as A3                                           # noqa: E402
import verify168 as B3                                            # noqa: E402

DIR = "r172/certs/mut/"
OUT = "r172/certs/mutation_suite_R1.json"
CELLS = [((1, 2, 0, 0, 0, 0), 48), ((1, 4, 0, 0, 0, 0), 61),
         ((1, 2, 1, 0, 0, 0), 48), ((1, 1, 0, 0, 0, 0), 35),
         ((1, 3, 1, 0, 0, 0), 48), ((2, 2, 0, 0, 0, 0), 63),
         ((1, 6, 1, 0, 0, 0), 111)]


def run_a4(rel):
    try:
        r = VA.verify(rel, log=lambda *_a, **_k: None)
        return bool(r["ok"]), r.get("error") or (r.get("rows") or [{}])[-1].get("detail")
    except SystemExit as e:
        return False, f"SystemExit: {e}"


def run_b4(rel):
    B3.verify_any.__defaults__  # noqa: B018  (no cache across calls)
    r = VB.verify_any4(rel)
    return bool(r["ok"]), r.get("error")


def run_a3(rel):
    try:
        r = A3.verify(rel, log=lambda *_a, **_k: None)
        return bool(r["ok"]), r.get("error") or (r.get("rows") or [{}])[-1].get("detail")
    except SystemExit as e:
        return False, f"SystemExit: {e}"


def run_b3(rel):
    try:
        r = B3.verify_any(rel)
        return bool(r["ok"]), r.get("error")
    except (AssertionError, ValueError, IndexError) as e:
        return False, f"{type(e).__name__}: {e}"


def read(rel):
    return gzip.decompress((ROOT / rel).read_bytes()).decode()


def write(rel, text):
    X.write_gz(ROOT / rel, text)


# ------------------------------------------------------------ G mutants
class Mutant(X.Engine172):
    """Wrong R1 decision; `variant` chooses the annotation written."""
    kind = "base"

    def __init__(self, deps, cap, variant):
        super().__init__(deps, cap, "r1")
        self.variant = variant
        self.diverged = 0          # pruning decisions that differ from R1
        self.annot_div = 0         # written S annotations that differ from R1

    def wrong_branches(self, tok, d0, a, bb, e, h):
        raise NotImplementedError

    def wrong_closes(self, br, ports, target):
        return not br or ports + max(x for _r, x in br) - 1 < target

    def r1_decide(self, tok, d0, a, bb, e, h, ports, target):
        good = self.r1_branches(tok, d0, a, bb, e, h)
        bad = self.wrong_branches(tok, d0, a, bb, e, h)
        closes = self.wrong_closes(bad, ports, target)
        truth = not good or ports + max(x for _r, x in good) - 1 < target
        if closes != truth:
            self.diverged += 1
        annot = bad if self.variant == "faithful" else good
        if closes and annot != good:
            self.annot_div += 1
        return closes, annot, good


def mk(name, conservative, branches=None, closes=None):
    cls = type("M_" + name, (Mutant,), dict(kind=name))
    if branches:
        cls.wrong_branches = branches
    else:
        cls.wrong_branches = lambda self, *k: self.r1_branches(*k)
    if closes:
        cls.wrong_closes = closes
    cls.conservative = conservative
    return cls


def _drop_argmax(self, tok, d0, *res):
    br = self.r1_branches(tok, d0, *res)
    if len(br) < 2:
        return br
    top = max(br, key=lambda x: x[1])
    return [x for x in br if x != top]


def _gt0(self, tok, d0, *res):
    return [(r, self.ub(tok - r, d0 + 5 * r, *res))
            for r in range(tok + 1) if d0 + 5 * r > 0]


def _r_gt_t(self, tok, d0, *res):
    return [(r, self.ub(tok - r, d0 + 5 * r, *res))
            for r in range(tok + 2) if d0 + 5 * r >= 0]


def _neg(self, tok, d0, *res):
    return [(r, self.ub(tok - r, d0 + 5 * r, *res)) for r in range(tok + 1)]


def _wrong_tr(self, tok, d0, *res):
    return [(r, self.ub(tok - r - 1, d0 + 5 * r, *res))
            for r in range(tok + 1) if d0 + 5 * r >= 0]


def _wrong_d(self, tok, d0, *res):
    return [(r, self.ub(tok - r, d0 + 5 * r - 1, *res))
            for r in range(tok + 1) if d0 + 5 * r >= 0]


def _stronger(self, tok, d0, *res):
    return [(r, u - 3) for r, u in self.r1_branches(tok, d0, *res)]


FAKE = {(0, 6, 0, 0, 0, 0): 20, (0, 4, 0, 0, 0, 0): 20, (0, 2, 0, 0, 0, 0): 20,
        (1, 1, 0, 0, 0, 0): 20, (0, 8, 1, 0, 0, 0): 20}


def _nonpred(self, tok, d0, a, bb, e, h):
    """branch values from a cell table containing NON-predecessor cells"""
    out = []
    for r in range(tok + 1):
        if d0 + 5 * r >= 0:
            best = self.ub(tok - r, d0 + 5 * r, a, bb, e, h)
            for (kb, kd, ka, kbb, ke, kh), c in FAKE.items():
                if (kb >= tok - r and kd >= d0 + 5 * r and ka >= a and kbb >= bb
                        and ke >= e and kh >= h and c < best):
                    best = c
            out.append((r, best))
    return out


def _fab_empty_br(self, tok, d0, *res):
    return []


def _fab_empty_closes(self, br, ports, target):
    return True


def _m_minus_2(self, br, ports, target):
    return not br or ports + max(x for _r, x in br) - 2 < target


def _j_plus_2(self, br, ports, target):
    return not br or ports + max(x for _r, x in br) - 1 < target + 1


GEN_MUTANTS = [
    mk("dropped_r_branch", False, _drop_argmax),
    mk("fabricated_empty_live", False, _fab_empty_br, _fab_empty_closes),
    mk("gt0_instead_of_ge0", False, _gt0),
    mk("r_greater_than_t_admitted", True, _r_gt_t),
    mk("negative_d0_plus_5r_admitted", True, _neg),
    mk("wrong_t_minus_r", False, _wrong_tr),
    mk("wrong_d0_plus_5r", False, _wrong_d),
    mk("non_predecessor_certificate", False, _nonpred),
    mk("stronger_unsupported_branch_bound", False, _stronger),
    mk("off_by_one_m_minus_1", False, closes=_m_minus_2),
    mk("off_by_one_J_plus_1", False, closes=_j_plus_2),
]


def gen_layer(results, flush):
    """A variant is EXERCISED once the wrong rule changed a pruning decision,
    or (faithful only) wrote an annotation that differs from the true one.
    Expected outcome:
      non-conservative mutant          -> REJECT (both variants)
      conservative, honest             -> ACCEPT (fewer prunes, sound tree)
      conservative, faithful           -> REJECT iff it wrote a wrong annotation
    """
    for M in GEN_MUTANTS:
        for variant in ("faithful", "honest"):
            row = None
            for cell, J in CELLS:
                refs, dep = FX.reduced(cell)
                cert = {k: v[0] for k, v in dep.items()}
                m = M(cert, 5_000_000, variant)
                toks, err = m.build(cell, J)
                if not (m.diverged or (variant == "faithful" and m.annot_div)):
                    continue
                if toks is None:
                    continue                      # exercised but did not finish
                rel = DIR + f"G_{M.kind}_{variant}_" + "_".join(map(str, cell)) + ".extree4.txt.gz"
                X.write_batch4(ROOT / rel, refs, FX.E.deps_list(dep),
                               [(cell, J, " ".join(toks))])
                a_ok, a_err = run_a4(rel)
                b_ok, b_err = run_b4(rel)
                if not M.conservative:
                    expect_accept = False
                elif variant == "honest":
                    expect_accept = True
                else:
                    expect_accept = m.annot_div == 0
                row = dict(mutation=M.kind, layer="G", variant=variant,
                           cell="|".join(map(str, cell)), J=J, path=rel,
                           conservative=M.conservative,
                           decisions_diverged=m.diverged,
                           annotations_diverged=m.annot_div,
                           A4_accepts=a_ok, B4_accepts=b_ok,
                           A4_error=(a_err or "")[:200], B4_error=(b_err or "")[:200],
                           expected="ACCEPT" if expect_accept else "REJECT",
                           passed=(a_ok and b_ok) if expect_accept
                           else (not a_ok and not b_ok))
                break
            if row is None:
                row = dict(mutation=M.kind, layer="G", variant=variant,
                           outcome="NOT_EXERCISED_ON_ANY_FIXTURE",
                           conservative=M.conservative, passed=False)
            results.append(row)
            flush()
            print(f"  G {M.kind:<36} {variant:<9} {row.get('cell', '-'):>12} "
                  f"div={row.get('decisions_diverged', '-')}/{row.get('annotations_diverged', '-')} "
                  f"A4={row.get('A4_accepts', '-')} B4={row.get('B4_accepts', '-')} "
                  f"expect={row.get('expected', '-')} {row.get('outcome', '')} "
                  f"{'PASS' if row['passed'] else 'FAIL'}", flush=True)


# ------------------------------------------------------------ T mutants
def first_token(text, pred):
    lines = text.split("\n")
    for li, ln in enumerate(lines):
        if ln.startswith(("rule", "ref", "dep", "tree", "L6-", "#")) or (
                not ln.startswith("S:") and " S:" not in ln):
            continue
        toks = ln.split(" ")
        for ti, tk in enumerate(toks):
            if tk.startswith("S:") and pred(tk):
                return lines, li, toks, ti
    return None


def replace_token(text, pred, fn):
    hit = first_token(text, pred)
    if not hit:
        return None
    lines, li, toks, ti = hit
    toks[ti] = fn(toks[ti])
    lines[li] = " ".join(toks)
    return "\n".join(lines)


def parse_s(tk):
    _s, d0, rest = tk.split(":")
    br = [] if rest == "-" else [tuple(map(int, x.split("="))) for x in rest.split(",")]
    return int(d0), br


def fmt_s(d0, br):
    return X.s_token(d0, br)


def text_layer(results, base_rel):
    base = read(base_rel)
    muts = []

    def add(name, text, verifiers=("A4", "B4")):
        muts.append((name, text, verifiers))

    add("dropped_r_branch", replace_token(
        base, lambda t: len(parse_s(t)[1]) >= 2,
        lambda t: fmt_s(parse_s(t)[0], parse_s(t)[1][1:])))
    add("fabricated_empty_live", replace_token(
        base, lambda t: parse_s(t)[1], lambda t: fmt_s(parse_s(t)[0], [])))
    add("gt0_zero_branch_dropped", replace_token(
        base, lambda t: any(parse_s(t)[0] + 5 * r == 0 for r, _u in parse_s(t)[1]),
        lambda t: fmt_s(parse_s(t)[0], [(r, u) for r, u in parse_s(t)[1]
                                         if parse_s(t)[0] + 5 * r > 0])))
    add("r_greater_than_t_added", replace_token(
        base, lambda t: parse_s(t)[1],
        lambda t: fmt_s(parse_s(t)[0], parse_s(t)[1] + [(parse_s(t)[1][-1][0] + 1, parse_s(t)[1][-1][1])])))
    add("negative_branch_added", replace_token(
        base, lambda t: parse_s(t)[0] < 0 and parse_s(t)[1],
        lambda t: fmt_s(parse_s(t)[0], [(0, parse_s(t)[1][0][1])] + parse_s(t)[1])))
    add("wrong_t_minus_r_value", replace_token(
        base, lambda t: parse_s(t)[1],
        lambda t: fmt_s(parse_s(t)[0], [(r + 1, u) for r, u in parse_s(t)[1]])))
    add("wrong_d0", replace_token(
        base, lambda t: parse_s(t)[1],
        lambda t: fmt_s(parse_s(t)[0] - 1, parse_s(t)[1])))
    add("stronger_unsupported_branch_bound", replace_token(
        base, lambda t: parse_s(t)[1],
        lambda t: fmt_s(parse_s(t)[0], [(r, u - 1) for r, u in parse_s(t)[1]])))
    add("old_leaf_interpreted_as_R1 (S replaced by L)", replace_token(
        base, lambda t: True, lambda t: "L"))
    # header / DAG mutations
    lines = base.split("\n")
    ri = next(i for i, ln in enumerate(lines) if ln.startswith("ref "))
    f = lines[ri].split()
    f[1] = ("0" if f[1][0] != "0" else "1") + f[1][1:]
    add("altered_predecessor_container_hash", "\n".join(lines[:ri] + [" ".join(f)] + lines[ri + 1:]))
    f = lines[ri].split()
    f[2] = ("0" if f[2][0] != "0" else "1") + f[2][1:]
    add("altered_predecessor_plain_hash", "\n".join(lines[:ri] + [" ".join(f)] + lines[ri + 1:]))
    di = next(i for i, ln in enumerate(lines) if ln.startswith("dep "))
    f = lines[di].split()
    add("dep_claims_stronger_cap_than_predecessor",
        "\n".join(lines[:di] + [" ".join(f[:7] + [str(int(f[7]) - 1)] + f[8:])] + lines[di + 1:]))
    fake = ["dep", "0", "4", "0", "0", "0", "0", "20", f[8], f[9]]
    add("non_predecessor_certificate_dep", "\n".join(lines[:di] + [" ".join(fake)] + lines[di:]))
    add("R1_leaf_placed_in_EXTREE-3", "\n".join(["L6-EXTREE-3"] + lines[2:]),
        ("A4", "B4", "A3", "B3"))
    add("missing_rule_declaration", "\n".join([lines[0]] + lines[2:]))
    add("wrong_rule_declaration", "\n".join([lines[0], lines[1].replace("v1", "v2")] + lines[2:]))
    for name, text, vs in muts:
        if text is None:
            results.append(dict(mutation=name, layer="T", outcome="NO_SUITABLE_TOKEN",
                                base=base_rel, passed=False))
            print(f"  T {name:<44} no suitable token in base", flush=True)
            continue
        rel = DIR + "T_" + name.split(" ")[0] + ".txt.gz"
        write(rel, text)
        got = {}
        for v in vs:
            ok, err = dict(A4=run_a4, B4=run_b4, A3=run_a3, B3=run_b3)[v](rel)
            got[v] = dict(accepts=ok, error=(err or "")[:200])
        passed = all(not g["accepts"] for g in got.values())
        results.append(dict(mutation=name, layer="T", base=base_rel, path=rel,
                            verifiers=got, expected="REJECT", passed=passed))
        print(f"  T {name:<44} " + " ".join(f"{v}={'acc' if g['accepts'] else 'REJ'}"
                                            for v, g in got.items())
              + f"  {'PASS' if passed else 'FAIL'}", flush=True)


def positive(results, r1_rel, old_rel):
    rows = []
    for v, fn in (("A4", run_a4), ("B4", run_b4)):
        ok, err = fn(r1_rel)
        rows.append((f"R1 tree with R1-only leaves accepted under EXTREE-4 by {v}", ok, err))
    for v, fn in (("A3", run_a3), ("B3", run_b3)):
        # the same token stream declared as the old format must be refused
        text = read(r1_rel).split("\n")
        rel = DIR + "P_r1_tokens_as_old_format.txt.gz"
        write(rel, "\n".join(["L6-EXTREE-3"] + text[2:]))
        ok, err = fn(rel)
        rows.append((f"same R1-only leaves refused under old format by {v}", not ok, err))
    for v, fn in (("A4", run_a4), ("B4", run_b4), ("A3", run_a3), ("B3", run_b3)):
        ok, err = fn(old_rel)
        rows.append((f"old-format tree accepted by {v} (old semantics)", ok, err))
    # conservativity at object level: the old tree's tokens, declared EXTREE-4
    text = read(old_rel).split("\n")
    rel = DIR + "P_old_tokens_as_extree4.txt.gz"
    write(rel, "\n".join(["L6-EXTREE-4", X.RULE_LINE] + text[1:]))
    for v, fn in (("A4", run_a4), ("B4", run_b4)):
        ok, err = fn(rel)
        rows.append((f"old L-only tree re-declared EXTREE-4 accepted by {v}", ok, err))
    for name, ok, err in rows:
        results.append(dict(mutation=name, layer="POSITIVE_CONTROL",
                            passed=bool(ok), error=None if ok else (err or "")[:200]))
        print(f"  + {name:<64} {'PASS' if ok else 'FAIL'}", flush=True)


def main():
    trust172.setup()
    (ROOT / DIR).mkdir(parents=True, exist_ok=True)
    results = []

    def flush(final=False):
        out = dict(title="R1 mutation suite (EXPERIMENTAL)",
                   complete=final,
                   verifier_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                    for p in ("r172/src/verifyA172.py",
                                              "r172/src/verifyB172.py",
                                              "r172/src/gen172.py",
                                              "r172/src/mut172.py")},
                   total=len(results), passed=sum(r["passed"] for r in results),
                   all_passed=all(r["passed"] for r in results), results=results)
        (ROOT / OUT).write_text(json.dumps(out, indent=1) + "\n")
        return out

    base_r1 = "r172/certs/test/1_4_0_0_0_0_J61_r1.extree4.txt.gz"
    base_old = "r172/certs/test/1_2_0_0_0_0_J48_old.extree3.txt.gz"
    print("positive controls", flush=True)
    positive(results, base_r1, base_old)
    flush()
    print("text-layer mutants", flush=True)
    text_layer(results, base_r1)
    flush()
    print("generator-layer mutants", flush=True)
    gen_layer(results, flush)
    out = flush(final=True)
    print(f"mutation suite: {out['passed']}/{out['total']} passed", flush=True)
    return 0 if out["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
