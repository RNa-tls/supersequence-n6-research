#!/usr/bin/env python3
"""Round 152 -- cross-check the checker's catalogue against round 147's.

This is a CROSS-CHECK, not a dependency: the checkers build their own catalogue
and never read r147/src/catalogue147.h.  If the two disagree that is a finding,
and it is better to learn it here than to have two rounds quietly disagree.

Phases and orbit ids are only defined up to a relabelling of the classes and, in
the phase case, up to the choice of representative, so those are compared as
PARTITIONS and as phase DIFFERENCES along tau, not as raw numbers.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r152" / "src"))
import checker152 as CK                                            # noqa: E402

H = (ROOT / "r147" / "src" / "catalogue147.h").read_text()


def arr(name):
    m = re.search(r"\b" + name + r"\[\] = \{([^}]*)\}", H)
    if not m:
        raise SystemExit(f"{name} not found in catalogue147.h")
    return [int(x) for x in m.group(1).split(",") if x.strip()]


def partition(lst):
    """A class labelling, up to renaming of the labels."""
    seen, out = {}, []
    for x in lst:
        out.append(seen.setdefault(x, len(seen)))
    return out


def main():
    r = {}
    hex2, orb2, ph2 = arr("HEX2"), arr("ORB2"), arr("PH2")
    free2, da2, db2 = arr("FREE2"), arr("DA2"), arr("DB2")
    paid2, poff = arr("PAID2"), None
    hv2, hvc2, hvoff2 = arr("HV2"), arr("HVC2"), arr("HVOFF2")

    r["hexagon_partition"] = partition(hex2) == partition(CK.HEX)
    r["orbit_partition"] = partition(orb2) == partition(CK.ORB)
    # phases: compare the step taken by tau, which is representative-free
    ok = True
    for i, p in enumerate(CK.PERMS):
        j = CK.IDX[CK._tau(p)]
        if (CK.PHASE[j] - CK.PHASE[i]) % 5 != (ph2[j] - ph2[i]) % 5:
            ok = False
            break
    r["phase_steps_along_tau"] = ok
    r["free_edges"] = free2 == CK.FREE
    r["dirtyA_edges"] = da2 == CK.DA
    r["dirtyB_edges"] = db2 == CK.DB

    # PAID2 is flat with a stride of 5 per word (each word has exactly five)
    r["paid_count"] = len(paid2) == 5 * CK.N
    r["paid_edges"] = all(sorted(paid2[5 * v:5 * v + 5]) == sorted(CK.PAID[v])
                          for v in range(CK.N)) if r["paid_count"] else False
    r["heavy_edges"] = all(
        sorted(zip(hv2[hvoff2[v]:hvoff2[v + 1]], hvc2[hvoff2[v]:hvoff2[v + 1]]))
        == sorted(CK.HEAVY[v]) for v in range(CK.N))
    r["heavy_total"] = len(hv2)
    r["agree"] = all(v for k, v in r.items() if isinstance(v, bool))
    out = ROOT / "r152" / "certs" / "catalogue_crosscheck_152.json"
    out.write_text(json.dumps(r, indent=1) + "\n")
    print(json.dumps(r, indent=1))
    return 0 if r["agree"] else 1


if __name__ == "__main__":
    sys.exit(main())
