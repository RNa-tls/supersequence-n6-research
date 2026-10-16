"""Round N (section 13) -- exact re-solve of one 46185 window with a larger WMAX.
usage (from the repo root): window_resolve.py K I WMAX[,WMAX2] TIME_LIMIT [out.json]"""
import sys, json, time
sys.path.insert(0, 'rN/src')
import rl_window as RW
fam = json.load(open('rM/certs/family_46187.json'))
st = RW.word_runs('rL/records/superperm8_46185.txt'); where, cyc = RW.family_index(fam)
pos, pcs, vsel = RW.pieces_of(st, where, cyc)
tw = [RW.wt(RW.last(a), b) for a, b in zip(st, st[1:])]
k, i = int(sys.argv[1]), int(sys.argv[2])
blk = pcs[i:i + k]; trails = [pos[b[0]][0] for b in blk]
lo = blk[0][0]; hi = blk[-1][-1]
src = st[lo - 1]; snk = st[hi + 1]
cur = sum(w - 2 for w in tw[lo - 1:hi + 1])
print('trails', trails, 'current', cur, 'runs lo..hi', lo, hi, flush=True)
for wmax in [int(x) for x in sys.argv[3].split(",")]:
    t0 = time.time()
    r = RW.solve_window(fam, trails, src, snk, wmax=wmax, time_limit=float(sys.argv[4]), threads=2)
    print(json.dumps(dict(wmax=wmax, opt=r.get('obj'), bound=r.get('bound'), status=r['status'], complete=r.get('complete'), else_arcs=r.get('else_arcs'), sec=r['sec'])), flush=True)
    if r.get('complete'):
        json.dump(dict(trails=trails, lo=lo, hi=hi, wmax=wmax, obj=r['obj'], path=[list(p) for p in r['path']], versions=r['versions']), open(sys.argv[5] if len(sys.argv) > 5 else 'win_%d_%d_w%d.json' % (k, i, wmax), 'w'))
        break
