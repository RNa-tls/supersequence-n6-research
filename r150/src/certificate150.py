"""Tiny rejection certificate verifier. No histogram sorting or production code.
Soundness is the Token-Touched-Orbit theorem in r150/PROOF.md.
This API is prospective; old capacity runs did not emit per-prune certificates.
"""
def verify_rejection(masks, current, tok, dmax, lam, m=5):
    if not (isinstance(tok,int) and tok>=0 and isinstance(dmax,int) and dmax>=0):return False
    if not (0<=current<len(masks) and masks[current]):return False
    if not all(isinstance(x,int) and 0<=x<(1<<m) for x in masks):return False
    if not (isinstance(lam,int) and 0<=lam<=m-1):return False
    bound=sum(min(m-x.bit_count(),lam) for j,x in enumerate(masks) if x and j!=current)-tok*lam
    return bound>dmax
