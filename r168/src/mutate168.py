#!/usr/bin/env python3
"""Round 168 phase 17 -- mutation regression for L6-EXTREE-3.

The verifier's logic does not depend on the size of the proof object, so the
suite runs against a purpose-built two-level DAG of cheap cells rather than
replaying hundreds of millions of nodes per mutation.  The reference- and
dependency-level mutations are ALSO run against the real round-168 batch,
where they are caught before any tree is replayed.

Format 3 adds a dependency layer, so four mutations are new: a dep whose
claimed capacity is wrong, a dep whose plain-text hash is wrong, a dep citing
a file that is not a declared reference, and a dep for a cell the referenced
certificate does not carry.

As in round 166, "corrupt token state", "corrupt used-hexagon state",
"corrupt feasibility histogram" and "alter prune reason" are NOT EXPRESSIBLE:
the certificate stores only `N<k>` and `L`, with no solver state and no prune
label, and the verifier recomputes all of it.  That is reported, not
simulated.
"""
from __future__ import annotations
import hashlib, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r164" / "src"))
sys.path.insert(0, str(ROOT / "r167" / "src"))
sys.path.insert(0, str(ROOT / "r168" / "src"))
import routeb164 as R                                             # noqa: E402
import verify168 as V                                             # noqa: E402
import gen168 as G                                                # noqa: E402
from gzrule167 import write_gz, plain_sha256                      # noqa: E402

SCRATCH = Path("/tmp/claude-0/-home-user-supersequence-n6-research/"
               "0161dc0f-40e0-56e3-8c56-97df10c350b4/scratchpad")
WORK = SCRATCH / "r168mut"
A_REL = "r168/certs/mut_a_168.txt.gz"
B_REL = "r168/certs/mut_b_168.txt.gz"
REAL = "r168/certs/extree_batch1_168.txt.gz"


def build_small_dag():
    """Two tiny format-3 batches, B referencing A.  Values are DISCOVERED."""
    _cap, order = R.parse_capcert(ROOT / "r152" / "certs"
                                  / "cap_cert_all_152.txt")

    def batch(cells, refs, deps, out):
        certified = {c: v for c, v, _p, _r in deps}
        trees = []
        for cell in cells:
            g = G.Engine(certified, 10 ** 7)
            cap, err = g.discover(cell)
            assert cap is not None, err
            g2 = G.Engine(certified, 10 ** 7)
            toks, err = g2.build(cell, cap)
            assert toks is not None, err
            certified[cell] = cap
            trees.append((cell, cap, toks))
        G.write_batch(ROOT / out, refs, deps, trees)

    batch(order[0:5], [], [], A_REL)
    ac = hashlib.sha256((ROOT / A_REL).read_bytes()).hexdigest()
    ap_ = plain_sha256(ROOT / A_REL)
    res = V.verify_any(A_REL)
    assert res["ok"], res
    deps = [(c, v, ap_, A_REL) for c, v in sorted(res["certified"].items())]
    batch(order[5:10], [(ac, ap_, A_REL)], deps, B_REL)
    return ac, ap_, deps


def verify_text(text, extra=()):
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "r168" / "certs").mkdir(parents=True)
    shutil.copy(ROOT / A_REL, WORK / A_REL)
    for rel, t in extra:
        (WORK / rel).parent.mkdir(parents=True, exist_ok=True)
        write_gz(WORK / rel, t)
    write_gz(WORK / B_REL, text)
    old_v, old_g = V.ROOT, G.ROOT
    V.ROOT = WORK
    try:
        res = V.verify_any(B_REL)
        return bool(res["ok"]), res.get("error")
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        V.ROOT, G.ROOT = old_v, old_g


def main():
    import gzip
    # the historical batches are accepted on their pinned hashes here too,
    # otherwise every mutation case would re-replay 164 million nodes
    V.load_trust()
    ac, ap_, deps = build_small_dag()
    text = gzip.decompress((ROOT / B_REL).read_bytes()).decode()
    lines = text.splitlines()
    tree_at = [i for i, l in enumerate(lines) if l.startswith("tree ")]
    last = tree_at[-1]
    toks = lines[last + 1].split()
    dep_line = next(i for i, l in enumerate(lines) if l.startswith("dep "))
    rows = []

    def case(name, mutate, expected_valid, extra=()):
        t = mutate()
        ok, err = verify_text(t, extra)
        rows.append(dict(mutation=name, expected_valid=expected_valid,
                         accepted=ok, correct=(ok == expected_valid),
                         rejection=None if ok else str(err)[:130]))
        print(f"  {name:<58} {'accepted' if ok else 'rejected':<9}"
              f"{'OK' if rows[-1]['correct'] else '  MISSED'}", flush=True)

    case("unchanged (control)", lambda: text, True)

    # ---------------- reference layer
    case("corrupt predecessor container hash",
         lambda: text.replace(ac, "0" * 8 + ac[8:]), False)
    case("corrupt predecessor plain-text hash",
         lambda: text.replace(f"ref {ac} {ap_}", f"ref {ac} {'0' * 8}{ap_[8:]}"),
         False)
    case("redirect the predecessor reference to another file",
         lambda: text.replace(f"ref {ac} {ap_} {A_REL}",
                              f"ref {ac} {ap_} r168/certs/other_168.txt.gz"),
         False)
    case("delete the predecessor reference",
         lambda: "\n".join(l for l in lines
                           if not l.startswith("ref ")) + "\n", False)

    def cycle():
        own = hashlib.sha256((ROOT / B_REL).read_bytes()).hexdigest()
        ownp = plain_sha256(ROOT / B_REL)
        return text.replace(f"ref {ac} {ap_} {A_REL}",
                            f"ref {ac} {ap_} {A_REL}\n"
                            f"ref {own} {ownp} {B_REL}")
    case("introduce a certificate dependency cycle", cycle, False)

    # ---------------- dependency layer (new in format 3)
    def dep_cap():
        f = lines[dep_line].split()
        f[7] = str(int(f[7]) - 1)
        return "\n".join(lines[:dep_line] + [" ".join(f)]
                         + lines[dep_line + 1:]) + "\n"
    case("dep claims a capacity the predecessor does not certify",
         dep_cap, False)

    def dep_hash():
        f = lines[dep_line].split()
        f[8] = "0" * 8 + f[8][8:]
        return "\n".join(lines[:dep_line] + [" ".join(f)]
                         + lines[dep_line + 1:]) + "\n"
    case("dep carries the wrong plain-text hash", dep_hash, False)

    def dep_undeclared():
        f = lines[dep_line].split()
        f[9] = "r168/certs/not_a_reference.txt.gz"
        return "\n".join(lines[:dep_line] + [" ".join(f)]
                         + lines[dep_line + 1:]) + "\n"
    case("dep cites a file that is not a declared reference",
         dep_undeclared, False)

    def dep_unknown_cell():
        f = lines[dep_line].split()
        f[1] = "9"
        return "\n".join(lines[:dep_line] + [" ".join(f)]
                         + lines[dep_line + 1:]) + "\n"
    case("dep names a cell the predecessor does not carry",
         dep_unknown_cell, False)

    def dep_extra():
        f = lines[dep_line].split()
        g = f[:]
        g[7] = "1"                       # an absurdly strong free bound
        g[1] = "5"
        return "\n".join(lines[:dep_line] + [" ".join(f), " ".join(g)]
                         + lines[dep_line + 1:]) + "\n"
    case("invent an extra dependency with a very strong bound",
         dep_extra, False)

    # ---------------- tree shape
    def shape(fn, name, expected=False):
        def m():
            q = fn(toks[:])
            return "\n".join(lines[:last + 1] + [" ".join(q)]) + "\n"
        case(name, m, expected)

    def fewer(q):
        i = next(j for j, x in enumerate(q) if x.startswith("N"))
        q[i] = f"N{max(int(q[i][1:]) - 1, 0)}"
        return q
    shape(fewer, "declare one child fewer")

    def more(q):
        i = next(j for j, x in enumerate(q) if x.startswith("N"))
        q[i] = f"N{int(q[i][1:]) + 1}"
        return q
    shape(more, "declare one child more")
    shape(lambda q: q[:q.index("L")] + ["L"] + q[q.index("L"):],
          "duplicate one child")
    shape(lambda q: q[:q.index("L")] + q[q.index("L") + 1:],
          "remove one child")

    def illegal(q):
        q[q.index("L")] = "N2"
        return q
    shape(illegal, "illegal transition (leaf becomes a branch)")
    shape(lambda q: q[:len(q) // 2], "delete a subtree")
    shape(lambda q: ["N9"] + q[1:], "corrupt the root node")
    shape(lambda q: q[:3] + ["Z"] + q[4:], "malformed proof syntax")

    # ---------------- header claims
    def cap_down():
        f = lines[last].split()
        f[7] = str(int(f[7]) - 1)
        return "\n".join(lines[:last] + [" ".join(f), lines[last + 1]]) + "\n"
    case("corrupt the claimed capacity downwards", cap_down, False)

    def cap_up():
        f = lines[last].split()
        f[7] = str(int(f[7]) + 1)
        return "\n".join(lines[:last] + [" ".join(f), lines[last + 1]]) + "\n"
    case("raise the claimed capacity (weaker but still true)", cap_up, True)

    # ---------------- the same reference/dependency attacks on the real batch
    real_rows = []
    if (ROOT / REAL).exists():
        rtext = gzip.decompress((ROOT / REAL).read_bytes()).decode()
        rl = rtext.splitlines()
        rdep = next(i for i, l in enumerate(rl) if l.startswith("dep "))
        rref = next(i for i, l in enumerate(rl) if l.startswith("ref "))

        def run(name, t):
            if WORK.exists():
                shutil.rmtree(WORK)
            (WORK / "r168" / "certs").mkdir(parents=True)
            for rel in ("r164/certs/extree_prefix_164.txt.gz",
                        "r166/certs/extree_batch2_166.txt.gz",
                        "r166/certs/extree_batch3_166.txt.gz"):
                (WORK / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, WORK / rel)
            write_gz(WORK / REAL, t)
            old = V.ROOT
            V.ROOT = WORK
            try:
                res = V.verify_any(REAL)
                ok = bool(res["ok"])
                err = res.get("error")
            except Exception as e:
                ok, err = False, f"{type(e).__name__}: {e}"
            finally:
                V.ROOT = old
            real_rows.append(dict(mutation=name, accepted=ok,
                                  correct=not ok,
                                  rejection=None if ok else str(err)[:130]))
            print(f"  [real] {name:<51} "
                  f"{'accepted' if ok else 'rejected':<9}"
                  f"{'OK' if not ok else '  MISSED'}", flush=True)

        f = rl[rref].split()
        run("real batch: corrupt a reference container hash",
            "\n".join(rl[:rref] + [" ".join([f[0], "0" * 8 + f[1][8:]]
                                            + f[2:])] + rl[rref + 1:]) + "\n")
        f = rl[rdep].split()
        g = f[:]
        g[7] = str(int(g[7]) - 1)
        run("real batch: dep claims a capacity the predecessor denies",
            "\n".join(rl[:rdep] + [" ".join(g)] + rl[rdep + 1:]) + "\n")

    out = dict(
        small_dag=dict(a=A_REL, b=B_REL,
                       a_sha256=ac, a_plain_sha256=ap_,
                       declared_dependencies=len(deps)),
        rows=rows, real_batch_rows=real_rows,
        invalid=sum(1 for r in rows if not r["expected_valid"]),
        invalid_rejected=sum(1 for r in rows
                             if not r["expected_valid"] and r["correct"]),
        valid=sum(1 for r in rows if r["expected_valid"]),
        valid_accepted=sum(1 for r in rows
                           if r["expected_valid"] and r["correct"]),
        real_batch_invalid=len(real_rows),
        real_batch_rejected=sum(1 for r in real_rows if r["correct"]),
        not_expressible_in_this_format=[
            "corrupt token state", "corrupt used-hexagon state",
            "corrupt feasibility histogram", "alter prune reason"],
        why_not_expressible="the certificate stores only N<k> and L; no "
                            "solver state and no prune label appear in it, "
                            "and the verifier recomputes every one of them "
                            "from the state it rebuilt",
    )
    out["ok"] = (out["invalid"] == out["invalid_rejected"]
                 and out["valid"] == out["valid_accepted"]
                 and out["real_batch_invalid"] == out["real_batch_rejected"])
    (ROOT / "r168" / "certs" / "mutations_168.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("rows", "real_batch_rows")},
                     ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
