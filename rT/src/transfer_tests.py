#!/usr/bin/env python3
"""Round T -- which run-level facts behind the Round R/S theorems hold on a family of closed trails.
Runs = class visits with their entry permutation; W[x, y] = 8 - overlap(last perm of x, first perm of y).
usage: transfer_tests.py (old FAMILY.json | new SEL TSV BASE) OUT.json"""
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model, slice_structure as SS
a = sys.argv[1:]; outp = a[-1]
if a[0] == "old":
    fam = json.load(open(a[1])); cyc = [SS.expand(t["versions"][0]) for t in fam["trails"]]
else: cyc = model.load(*a[1:4])
ent = []; tr = []; idx = []; cnat = []; tlen = []
for t, c in enumerate(cyc):
    rs = model.runs_of(c); d = c + c; tlen.append(len(rs))
    for i, r in enumerate(rs): ent.append([int(ch) for ch in d[r[0]:r[0] + 8]]); tr.append(t); idx.append(i); cnat.append(r[2])
S = np.array(ent, np.int64); n = len(S); tr = np.array(tr); idx = np.array(idx); cnat = np.array(cnat); tofs = np.concatenate([[0], np.cumsum(tlen)])
X = np.concatenate([S[:, 7:], S[:, :7]], 1); W = np.full((n, n), 8, np.int8)
for k in range(7, 0, -1):                                   # overlap 8 - k ... written as weight k: last(x)[k:] == first(y)[:8-k]
    A = (X[:, k:] * (8 ** np.arange(8 - k))).sum(1); B = (S[:, :8 - k] * (8 ** np.arange(8 - k))).sum(1)
    o = np.argsort(B, kind="stable"); Bs = B[o]; lo = np.searchsorted(Bs, A, "left"); hi = np.searchsorted(Bs, A, "right")
    for i in np.nonzero(hi > lo)[0]: W[i, o[lo[i]:hi[i]]] = k
np.fill_diagonal(W, 8)
succ = np.array([tofs[tr[i]] + (idx[i] + 1) % tlen[tr[i]] for i in range(n)]); pred = np.empty(n, np.int64); pred[succ] = np.arange(n)
c_in = cnat[pred]                                            # weight of the natural link INTO each run
natural = np.zeros((n, n), bool); natural[np.arange(n), succ] = True
assert (W[np.arange(n), succ] == cnat).all()
same = tr[:, None] == tr[None, :]
res = dict(runs=n, trails=len(cyc), natural_w2=int((cnat == 2).sum()), natural_w3=int((cnat == 3).sum()), Q=int((cnat == 3).sum()) - 720)
res["weight1_links_between_distinct_runs"] = int((W == 1).sum())
nn2 = (W == 2) & ~natural; xs, ys = np.nonzero(nn2)
# wrap: y is a chain start (c_in = 3), x is the 7th run of the chain starting at y, the chain being 7 runs linked by weight 2
def chain_from(y):
    out = [y]
    while cnat[out[-1]] == 2 and len(out) < 8: out.append(succ[out[-1]])
    return out
wr = 0; other = []
for x, y in zip(xs, ys):
    ch = chain_from(y)
    if c_in[y] == 3 and len(ch) == 7 and ch[-1] == x and cnat[x] == 3: wr += 1
    else: other.append((int(x), int(y)))
complete = [y for y in range(n) if c_in[y] == 3 and len(chain_from(y)) == 7 and cnat[chain_from(y)[-1]] == 3]
res["non_natural_w2_links"] = dict(total=int(nn2.sum()), wraps=wr, complete_chains=len(complete), other=len(other), other_same_trail=sum(1 for x, y in other if tr[x] == tr[y]), other_cross_trail=sum(1 for x, y in other if tr[x] != tr[y]),
    other_examples=[dict(x_trail=int(tr[x]), x_run=int(idx[x]), y_trail=int(tr[y]), y_run=int(idx[y]), c_in_y=int(c_in[y]), c_out_x=int(cnat[x])) for x, y in other[:6]],
    other_by_c=dict(collections.Counter("cin%d_cout%d_%s" % (c_in[y], cnat[x], "same" if tr[x] == tr[y] else "cross") for x, y in other)))
E = W.astype(np.int16) - c_in[None, :] - 1                   # e(x -> y) = w - c(y) - 1
ec = E[~same]; res["cross_trail_e"] = dict(min=int(ec.min()), zeros=int((ec == 0).sum()), negative=int((ec < 0).sum()), histogram={str(k): int((ec == k).sum()) for k in range(int(ec.min()), 5)})
Ep = (W.astype(np.int16) - c_in[None, :])[same & ~natural & ~np.eye(n, dtype=bool)]
res["same_trail_jump_Eprime"] = dict(min=int(Ep.min()), histogram={str(k): int((Ep == k).sum()) for k in range(int(Ep.min()), 5)})
m3 = (W == 3) & same & ~natural & (c_in[None, :] == 2); res["same_trail_w3_into_mid_run"] = int(m3.sum())
c3 = (W == 3) & ~same; res["cross_trail_w3_links"] = dict(total=int(c3.sum()), into_chain_start=int((c3 & (c_in[None, :] == 3)).sum()), into_mid_run=int((c3 & (c_in[None, :] == 2)).sum()), from_chain_end=int((c3 & (cnat[:, None] == 3)).sum()))
# skip weight law: k consecutive complete chains, w(run before, run after) = 3 + k
law = collections.Counter(); bad = 0
cs = set(complete)
for y in complete:
    q = pred[y]; cur = y; k = 0
    while cur in cs and k < 8:
        k += 1; nx = succ[chain_from(cur)[-1]]
        if nx == q or nx == y: break
        wgt = int(W[q, nx]); law[(k, wgt)] += 1; bad += (wgt != 3 + k) if k <= 4 else 0
        cur = nx
res["skip_weight_law"] = dict(counts={"k%d_w%d" % k: v for k, v in sorted(law.items())}, violations_k_le_4=int(bad))
# Monge four-point inequality on random quadruples, and on natural links exhaustively against random (a, y)
rng = np.random.default_rng(2026); viol = 0; tested = 0
for _ in range(40):
    aa = rng.integers(0, n, 200000); yy = rng.integers(0, n, 200000); u = rng.integers(0, n, 200000); b = pred[u] if _ % 2 == 0 else rng.integers(0, n, 200000)
    hyp = (W[b, u] <= W[aa, u]) & (W[b, u] <= W[b, yy]); tested += int(hyp.sum()); viol += int((hyp & (W[aa, yy].astype(int) + W[b, u] > W[aa, u].astype(int) + W[b, yy])).sum())
res["monge_sample"] = dict(quadruples_with_hypothesis=tested, violations=viol)
res["weight_histogram_all_pairs"] = {str(k): int((W == k).sum()) for k in range(1, 9)}
json.dump(res, open(outp, "w"), indent=1); print(json.dumps(res, indent=0)[:3000])
np.save(os.path.splitext(outp)[0] + "_W.npy", W) if "--saveW" in a else None
