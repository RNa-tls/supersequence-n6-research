#!/usr/bin/env python3
"""Round 168 phases 0-2 -- revalidate the round-167 target before generating.

Nothing here trusts a prose summary or a stored count.  The 190-cell set is
recovered from the artifact, the rule system is rebuilt from the two bridge
theorems, and the four claims round 168 depends on are re-checked:

  1. every one of the 190 witness rows validates -- dropping that one cell
     from the universe leaves that row not strictly closed;
  2. the 190 cells together close all 180 exposed rows;
  3. therefore removing any single cell breaks a required closure, so the set
     is necessary as well as sufficient;
  4. the free/derived layer -- what the current proof system already gives
     without generating anything -- is reconstructed and measured.

If any of this fails, round 168 would be generating against a stale target and
must not start.
"""
from __future__ import annotations
import gzip, hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r163" / "src"))
sys.path.insert(0, str(ROOT / "r166" / "src"))
import hidden163 as H                                             # noqa: E402
import extree_basis_verify as V                                   # noqa: E402

HEX = 120
GOOD = ("EXACT_CERTIFIED", "UPPER_CERTIFIED")
OLD_BATCHES = ("r164/certs/extree_prefix_164.txt.gz",
               "r166/certs/extree_batch2_166.txt.gz",
               "r166/certs/extree_batch3_166.txt.gz")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def parse(s):
    return tuple(int(x) for x in s.split("|"))


def cellstr(K):
    return "|".join(map(str, K))


class System:
    """base facts + granted certificates, closed under the bridge rules."""

    def __init__(self):
        H.load()
        self.chain_tab, self.piece_tab = dict(H.CERT), dict(H.PCERT)
        tg = json.loads((ROOT / "r164" / "certs" / "targets_164.json").read_text())
        vg = json.loads((ROOT / "r164" / "certs"
                         / "verifygen_164.json").read_text())
        done = {parse(s) for s
                in vg["targets_upper_certified_by_two_validators"]}
        self.single_chain = {tuple(c) for c in tg["CHAIN_SINGLE_IMPL"]
                             if tuple(c) not in done}
        self.single_piece = {tuple(c) for c in tg["PIECE_SINGLE_IMPL"]
                             if tuple(c) not in done}
        self.dual_chain = {k: v for k, v in self.chain_tab.items()
                           if k not in self.single_chain}
        self.dual_piece = {k: v for k, v in self.piece_tab.items()
                           if k not in self.single_piece}
        self.groups = {}
        for t in (0, 1, 2, 3, 4):
            g = defaultdict(list)
            for r in H.rows(t):
                g[tuple(r[c] for c in H.COORD)].append(r)
            self.groups[t] = dict(g)

    def value_of(self, K):
        if K in self.chain_tab:
            return self.chain_tab[K]
        if K[2:] == (0, 0, 0, 0):
            return self.piece_tab.get((K[0], K[1], 0, 0))
        return None

    def apply(self, granted, values=None):
        chain = dict(self.dual_chain)
        for K in granted:
            v = (values or {}).get(K, self.value_of(K))
            if v is not None:
                chain[K] = min(v, chain.get(K, 10 ** 9))
        Z = {}
        for K, v in chain.items():                         # (BRIDGE-EQ), ->
            if K[2:] == (0, 0, 0, 0):
                Z[K[:2]] = min(v, Z.get(K[:2], 10 ** 9))
        for (b, d, fp, lp), v in self.dual_piece.items():  # (BRIDGE-EQ), <-
            if (fp, lp) == (0, 0):
                Z[(b, d)] = min(v, Z.get((b, d), 10 ** 9))
        cert = {K: v for K, v in chain.items()
                if v < HEX + K[2] + K[3] + K[4]}
        for (b, d), v in Z.items():
            K = (b, d, 0, 0, 0, 0)
            if v < HEX and v < cert.get(K, 10 ** 9):
                cert[K] = v
        pcert = dict(self.dual_piece)
        for (b, d), v in Z.items():                        # (BRIDGE-LE)
            if v >= HEX:
                continue
            for fp in (0, 1):
                for lp in (0, 1):
                    if v < pcert.get((b, d, fp, lp), HEX):
                        pcert[(b, d, fp, lp)] = v
        H.CERT.clear(); H.CERT.update(cert)
        H.PCERT.clear(); H.PCERT.update({p: v for p, v in pcert.items()
                                         if v < HEX})
        H.best.cache_clear()
        return cert, pcert

    def full(self):
        H.CERT.clear(); H.CERT.update(self.chain_tab)
        H.PCERT.clear(); H.PCERT.update(self.piece_tab)
        H.best.cache_clear()

    def verdicts(self, keys=None):
        out = {}
        for t, g in self.groups.items():
            for k, variants in g.items():
                if keys is not None and (t, k) not in keys:
                    continue
                req, b = H.bounds(variants)
                out[(t, k)] = ("STRICTLY_CLOSED" if b and min(b.values()) < req
                               else ("EQUALITY" if b and min(b.values()) == req
                                     else "SURVIVING"))
        return out


def certified_cells(batches):
    """cells already carried by verified exhaustion certificates."""
    out = {}
    for rel in batches:
        text = gzip.decompress((ROOT / rel).read_bytes()).decode()
        for cell, capv, _toks in V.parse_batch(text)[1]:
            out[tuple(cell)] = capv
    return out


def main():
    S = System()
    src = json.loads((ROOT / "r167" / "certs"
                      / "row_optimum_167.json").read_text())
    oc = json.loads((ROOT / "r167" / "certs"
                     / "optimality_certificate_167.json").read_text())
    assert src["ok"] and oc["ok"]
    U = {parse(c) for c in src["universe"]["cells"]}
    OPT = {parse(c) for c in src["optimum"]["cells"]}
    wit = src["optimum"]["witness_rows"]

    # ---------- the exposed rows, re-derived from the tables
    S.full()
    base = S.verdicts()
    S.apply(set())
    empty = S.verdicts()
    EX = sorted(k for k in base if base[k] == "STRICTLY_CLOSED"
                and empty[k] != "STRICTLY_CLOSED")
    tally_full = Counter(base.values())

    # ---------- claim 2: the 190 close everything exposed
    S.apply(OPT)
    got = S.verdicts(set(EX))
    open_opt = sorted(k for k in EX if got[k] != "STRICTLY_CLOSED")

    # ---------- claim 1/3: each witness row opens when its cell is dropped
    bad = []
    for K in sorted(OPT):
        w = wit[cellstr(K)]
        key = (w["layer"] - 867, tuple(w["row"][c] for c in H.COORD))
        if key[1] not in S.groups[key[0]]:
            bad.append(dict(cell=cellstr(K), error="row outside the row space"))
            continue
        S.apply(U - {K})
        if S.verdicts({key})[key] == "STRICTLY_CLOSED":
            bad.append(dict(cell=cellstr(K), error="witness row still closed"))

    # ---------- phase 2: everything free, before generating anything
    DONE = certified_cells(OLD_BATCHES)
    S.apply(set(DONE))
    cert, pcert = S.apply(set(DONE))
    free = S.verdicts(set(EX))
    closed_now = [k for k in EX if free[k] == "STRICTLY_CLOSED"]
    bridged_piece = sorted(
        cellstr(p) for p in pcert
        if p not in S.dual_piece and (p[0], p[1], 0, 0, 0, 0) in DONE)
    other_piece = sorted(
        cellstr(p) for p in pcert
        if p not in S.dual_piece and (p[0], p[1], 0, 0, 0, 0) not in DONE)
    free_chain = sorted(cellstr(K) for K in cert
                        if K not in S.dual_chain and K not in DONE)

    out = dict(
        head_inputs={p: sha(p) for p in
                     ("r167/certs/row_optimum_167.json",
                      "r167/certs/optimality_certificate_167.json",
                      "r167/certs/round168_plan_167.json",
                      "r152/certs/verify_all_c152.json",
                      "r152/certs/verify_piece_c152.json",
                      "r163/src/hidden163.py") + OLD_BATCHES},
        baseline=dict(rows=len(base), tally=dict(tally_full),
                      reproduces_round_152=(tally_full["STRICTLY_CLOSED"] == 1607
                                            and tally_full["EQUALITY"] == 2)),
        target=dict(
            direct_certificates_required=len(OPT),
            is_190=len(OPT) == 190,
            exposed_rows=len(EX), is_180=len(EX) == 180,
            universe=len(U)),
        claim_sufficient=dict(rows_left_open=len(open_opt), ok=not open_opt),
        claim_necessary=dict(checked=len(OPT), failures=bad, ok=not bad),
        free_layer=dict(
            extree_certified_cells=len(DONE),
            extree_cells_inside_the_target=len(set(DONE) & OPT),
            extree_cells_outside_the_target=len(set(DONE) - OPT),
            dual_route_chain_cells=len(S.dual_chain),
            dual_route_piece_cells=len(S.dual_piece),
            bridge_derived_piece_cells=len(bridged_piece),
            other_derived_piece_cells=len(other_piece),
            bridge_derived_chain_cells=len(free_chain),
            exposed_rows_closed_for_free=len(closed_now),
            exposed_rows_still_open=len(EX) - len(closed_now)),
        remaining=dict(
            count=len(OPT - set(DONE)),
            cells=sorted(cellstr(K) for K in OPT - set(DONE))),
        exposed_rows=[[k[0], list(k[1])] for k in EX],
        optimum=sorted(cellstr(K) for K in OPT),
        universe_cells=sorted(cellstr(K) for K in U),
    )
    out["ok"] = (out["baseline"]["reproduces_round_152"]
                 and out["target"]["is_190"] and out["target"]["is_180"]
                 and out["claim_sufficient"]["ok"]
                 and out["claim_necessary"]["ok"])
    (ROOT / "r168" / "certs" / "state_168.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    show = {k: v for k, v in out.items()
            if k not in ("head_inputs", "exposed_rows", "optimum",
                         "universe_cells")}
    show["remaining"] = dict(count=show["remaining"]["count"])
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
