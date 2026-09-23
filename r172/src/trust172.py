"""Round 172 (EXPERIMENTAL) -- the verifier-B trust table, set up exactly as the
Round 171 bulk pipeline does (no new trust is created here):

  verify168.load_trust()                    Round 166-170 pinned reports
  production_j171.environment()             Round 171 dual-verified batches
  bulk_j171.initial()                       the accepted helper decision
  bulk_j171.add_accepted(..., accepted)     bulk certificates, each with a
                                            recorded A/B per-batch agreement
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "r171" / "src"))

_done = []


def setup():
    if _done:
        return _done[0]
    import bulk_j171 as BK
    BK.B.load_trust()
    f, refs, dep, env, backed = BK.initial()
    m = BK.load(BK.MAN)
    refs2, dep2 = BK.add_accepted(refs, m["accepted"])
    _done.append(dict(trusted=len(BK.B.TRUST), accepted=len(m["accepted"])))
    return _done[0]
