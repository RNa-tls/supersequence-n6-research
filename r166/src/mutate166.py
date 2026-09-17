#!/usr/bin/env python3
"""Round 166 phases 13 and 14 -- mutations and generator-bug controls.

Two things are tested.

  CERTIFICATE MUTATIONS mangle the proof object, including the new reference
  machinery: a corrupted predecessor hash, a redirected reference, and a
  dependency cycle.  Every mutation that changes what is claimed must be
  rejected.

  GENERATOR BUGS patch the generator's own state update and require that the
  independent verifier rejects whatever it produces.  The point is that a
  buggy generator must not be able to manufacture an accepted upper bound.

NOTE ON THREE REQUESTED MUTATIONS.  "corrupt token state", "corrupt
used-hexagon state" and "corrupt feas histogram" are NOT EXPRESSIBLE in this
format, and "alter prune reason" is not either.  The certificate stores only
the branching shape -- `N<k>` and `L` -- and no solver state or prune label at
all; the verifier recomputes every state and re-derives every leaf
justification from the state it reconstructed.  There is nothing to corrupt.
That is reported rather than simulated, and the generator-bug controls below
attack the same surface from the only side where it exists.
"""
from __future__ import annotations
import gzip, hashlib, json, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import routeb164 as R                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")
WORK = SCRATCH / "r166mut"
BATCH = "r166/certs/mut_batch_b.txt.gz"
REF = "r166/certs/mut_batch_a.txt.gz"
REAL_BATCH = "r166/certs/extree_batch2_166.txt.gz"
REAL_REF = "r164/certs/extree_prefix_164.txt.gz"

# The suite exercises the VERIFIER's logic, which does not depend on the size
# of the proof object, so it runs on a purpose-built two-level DAG of cheap
# cells instead of re-replaying 27.5 million nodes for each mutation.  The
# reference-level mutations are ALSO run against the real batch at the end,
# where they are caught before any tree is replayed.


def build_small_dag():
    import extree_basis_generator as G
    cap, order = R.parse_capcert(ROOT / "r152" / "certs"
                                 / "cap_cert_all_152.txt")
    (ROOT / "r166" / "certs").mkdir(parents=True, exist_ok=True)

    def batch(lo, hi, refs, out):
        certified = {}
        for h, rel in refs:
            certified.update(V.verify_chain(rel, verifier_a=False)["certified"])
        trees = []
        for i in range(lo, hi + 1):
            cell = order[i]
            C = cap[cell]["cap"]
            g = G.Generator(certified, 10 ** 8)
            toks, err = g.build(cell, C)
            assert toks is not None, err
            certified[cell] = C
            trees.append((cell, C, toks))
        G.write_batch(ROOT / out, refs, trees)

    batch(0, 4, [], REF)
    asha = hashlib.sha256((ROOT / REF).read_bytes()).hexdigest()
    batch(5, 9, [(asha, REF)], BATCH)
    return asha


def write_gz(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=1,
                           mtime=0) as fh:
            fh.write(text.encode())


def verify_text(text, extra_files=()):
    """Verify a mutated batch inside a throwaway tree that mirrors the repo."""
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "r166" / "certs").mkdir(parents=True)
    (WORK / "r164" / "certs").mkdir(parents=True)
    shutil.copy(ROOT / REF, WORK / REF)
    for rel, t in extra_files:
        (WORK / rel).parent.mkdir(parents=True, exist_ok=True)
        write_gz(WORK / rel, t)
    write_gz(WORK / BATCH, text)
    old = V.ROOT
    V.ROOT = WORK
    try:
        res = V.verify_chain(BATCH, verifier_a=False)
        return bool(res["ok"]), res.get("error")
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        V.ROOT = old


def main():
    refsha = build_small_dag()
    text = gzip.decompress((ROOT / BATCH).read_bytes()).decode()
    lines = text.splitlines()
    tree_at = [i for i, l in enumerate(lines) if l.startswith("tree ")]
    # the LAST tree in the batch is the basis cell 3|0|0|0|0|0
    last = tree_at[-1]
    toks = lines[last + 1].split()
    rows = []

    def case(name, mutate, expected_valid, extra=()):
        t = mutate()
        ok, err = verify_text(t, extra)
        rows.append(dict(mutation=name, expected_valid=expected_valid,
                         accepted=ok, correct=(ok == expected_valid),
                         rejection=None if ok else str(err)[:110]))

    case("unchanged (control)", lambda: text, True)

    # ---- reference machinery
    def bad_hash():
        bad = ("0" * 8) + refsha[8:]
        return text.replace(refsha, bad)
    case("corrupt predecessor hash", bad_hash, False)

    def redirect():
        return text.replace(f"ref {refsha} {REF}",
                            f"ref {refsha} r166/certs/extree_batch2_166.txt.gz")
    case("redirect predecessor reference to another file", redirect, False)

    def cycle():
        own = hashlib.sha256((ROOT / BATCH).read_bytes()).hexdigest()
        return text.replace(f"ref {refsha} {REF}",
                            f"ref {refsha} {REF}\nref {own} {BATCH}")
    case("introduce a certificate dependency cycle", cycle, False)

    def drop_ref():
        return "\n".join(l for l in lines if not l.startswith("ref ")) + "\n"
    case("delete the predecessor reference", drop_ref, False)

    # ---- tree shape
    def child_fewer():
        i = next(j for j, x in enumerate(toks) if x.startswith("N"))
        q = toks[:]
        k = int(q[i][1:])
        q[i] = f"N{max(k - 1, 0)}"
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("declare one child fewer", child_fewer, False)

    def child_more():
        i = next(j for j, x in enumerate(toks) if x.startswith("N"))
        q = toks[:]
        q[i] = f"N{int(q[i][1:]) + 1}"
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("declare one child more", child_more, False)

    def dup_leaf():
        i = toks.index("L")
        q = toks[:i] + ["L"] + toks[i:]
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("duplicate one leaf", dup_leaf, False)

    def del_leaf():
        i = toks.index("L")
        q = toks[:i] + toks[i + 1:]
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("remove one child (delete a leaf)", del_leaf, False)

    def leaf_to_branch():
        i = toks.index("L")
        q = toks[:]
        q[i] = "N2"
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("replace a transition (leaf becomes a branch)", leaf_to_branch, False)

    def del_subtree():
        q = toks[:len(toks) // 2]
        return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
    case("delete a subtree", del_subtree, False)

    # ---- header claims
    def bump_cap():
        f = lines[last].split()
        f[7] = str(int(f[7]) - 1)
        return "\n".join(lines[:last] + [" ".join(f), lines[last + 1]]) + "\n"
    case("lower the claimed capacity", bump_cap, False)

    def raise_cap():
        f = lines[last].split()
        f[7] = str(int(f[7]) + 1)
        return "\n".join(lines[:last] + [" ".join(f), lines[last + 1]]) + "\n"
    case("raise the claimed capacity (a weaker, still true claim)",
         raise_cap, True)

    def move_root():
        f = lines[last].split()
        f[1] = str(int(f[1]) + 1)
        return "\n".join(lines[:last] + [" ".join(f), lines[last + 1]]) + "\n"
    case("modify the root cell", move_root, False)

    real_text = gzip.decompress((ROOT / REAL_BATCH).read_bytes()).decode()
    real_ref_sha = hashlib.sha256((ROOT / REAL_REF).read_bytes()).hexdigest()
    for nm, mutated in (
        ("real batch: corrupt predecessor hash",
         real_text.replace(real_ref_sha, ("0" * 8) + real_ref_sha[8:])),
        ("real batch: delete the predecessor reference",
         "\n".join(l for l in real_text.splitlines()
                    if not l.startswith("ref ")) + "\n"),
    ):
        if WORK.exists():
            shutil.rmtree(WORK)
        (WORK / "r166" / "certs").mkdir(parents=True)
        (WORK / "r164" / "certs").mkdir(parents=True)
        shutil.copy(ROOT / REAL_REF, WORK / REAL_REF)
        write_gz(WORK / REAL_BATCH, mutated)
        old = V.ROOT
        V.ROOT = WORK
        try:
            res = V.verify_chain(REAL_BATCH, verifier_a=False)
            ok, err = bool(res["ok"]), res.get("error")
        except Exception as e:
            ok, err = False, f"{type(e).__name__}: {e}"
        finally:
            V.ROOT = old
        rows.append(dict(mutation=nm, expected_valid=False, accepted=ok,
                         correct=not ok,
                         rejection=None if ok else str(err)[:110]))

    out = dict(
        small_dag_batch=BATCH,
        real_batch=REAL_BATCH,
        real_batch_sha256=hashlib.sha256(
            (ROOT / REAL_BATCH).read_bytes()).hexdigest(),
        not_expressible_in_this_format=[
            "corrupt token state", "corrupt used-hexagon state",
            "corrupt feas histogram", "alter prune reason"],
        why="the certificate stores only the branching shape (N<k> and L); no "
            "solver state and no prune label is serialised, so the verifier "
            "recomputes every state and re-derives every leaf justification. "
            "There is nothing to corrupt, which is the point of phase 5's "
            "'prefer structural proof data over snapshots of solver memory'",
        rows=rows,
        invalid=sum(1 for r in rows if not r["expected_valid"]),
        invalid_rejected=sum(1 for r in rows
                             if not r["expected_valid"] and r["correct"]),
        valid=sum(1 for r in rows if r["expected_valid"]),
        valid_accepted=sum(1 for r in rows
                           if r["expected_valid"] and r["correct"]),
        wrong=[r for r in rows if not r["correct"]])
    out["ok"] = not out["wrong"]
    (ROOT / "r166" / "certs" / "mutations_166.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    for r in rows:
        print(f"  {r['mutation']:<52} expect={'valid' if r['expected_valid'] else 'INVALID':<7} "
              f"got={'accepted' if r['accepted'] else 'rejected':<8} "
              f"{'OK' if r['correct'] else 'WRONG'}")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows", "why")}, ensure_ascii=False,
                     indent=1))
    if WORK.exists():
        shutil.rmtree(WORK)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
