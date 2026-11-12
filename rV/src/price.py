#!/usr/bin/env python3
"""Round V -- price selections: for every selection of IN.jsonl (field "rows") build its closed trails and run-level
arcs, then J by the exact path programme (T <= --exact trails) or by the heuristic assembler (an upper bound).
Any selection with Q + J <= --record is turned into a literal word, checked, and saved.
usage: price.py IN.jsonl OUT.jsonl WORKDIR [--exact 17] [--iters 300000] [--record 87] [--maxqt 87]"""
import sys, os, json, subprocess, hashlib, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sel_lib as SL
ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("out"); ap.add_argument("work"); ap.add_argument("--exact", type=int, default=17); ap.add_argument("--iters", type=int, default=300000)
ap.add_argument("--record", type=int, default=87); ap.add_argument("--maxqt", type=int, default=87); ap.add_argument("--tag", default="p"); ap.add_argument("--seeds", type=int, default=2)
a = ap.parse_args(); os.makedirs(a.work, exist_ok=True)
done = set()
if os.path.exists(a.out):
    for l in open(a.out): done.add(json.loads(l)["key"])
fo = open(a.out, "a")
def check_word(w):
    seen = set()
    for i in range(len(w) - 7):
        s = w[i:i + 8]
        if len(set(s)) == 8: seen.add(s)
    return len(seen) == 40320 and set(w) <= set("01234567")
for line in open(a.inp):
    d = json.loads(line); rows = {x: int(v) for x, v in d["rows"].items()}; key = hashlib.sha256(json.dumps(sorted(rows.items())).encode()).hexdigest()[:16]
    if key in done: continue
    done.add(key); sm = SL.summary(rows)
    if sm["Q"] + sm["T"] - 1 > a.maxqt: continue
    t0 = time.time(); cyc = SL.closed_trails(rows); arcs, ent = SL.arcs_of(cyc); assert len(cyc) == sm["T"], (len(cyc), sm["T"])
    ap_ = os.path.join(a.work, "%s_arcs.txt" % a.tag); SL.write_arcs(ap_, arcs); T = sm["T"]; best = None; wit = None; exact = False
    if T <= a.exact:
        r = subprocess.run([os.path.join(a.work, "path_witness"), ap_, os.path.join(a.work, "%s_pw.json" % a.tag)], capture_output=True, text=True); j = json.load(open(os.path.join(a.work, "%s_pw.json" % a.tag)))
        best = j["optimal_J"]; wit = [(e["trail"], e["start"]) for e in j["witness"]]; exact = True
    else:
        for s in range(a.seeds):
            r = subprocess.run([os.path.join(a.work, "jheur"), ap_, str(a.iters), str(s + 1), os.path.join(a.work, "%s_jh.json" % a.tag)], capture_output=True, text=True); j = json.load(open(os.path.join(a.work, "%s_jh.json" % a.tag)))
            if best is None or j["J"] < best: best = j["J"]; wit = [(e["trail"], e["start"]) for e in j["witness"]]
    res = dict(key=key, Q=sm["Q"], T=T, rowless=sm["rowless"], walk_lengths=sm["walk_lengths"], walk_trails=sm["walk_trails"], row_words=sm["row_words"], J=best, exact=exact, total=sm["Q"] + best, length=46085 + sm["Q"] + best, sec=round(time.time() - t0, 1))
    if sm["Q"] + best <= a.record + 1:
        w = SL.word_of(ent, wit); ok = check_word(w); res.update(word_length=len(w), word_ok=ok, word_sha256=hashlib.sha256((w + "\n").encode()).hexdigest())
        if ok and len(w) <= 46085 + a.record + 1:
            open(os.path.join(a.work, "word_%d_%s.txt" % (len(w), key)), "w").write(w + "\n"); json.dump(dict(rows=rows, witness=wit), open(os.path.join(a.work, "word_%d_%s.json" % (len(w), key)), "w"))
            print("*** WORD of length", len(w), "saved, key", key, flush=True)
    fo.write(json.dumps(res) + "\n"); fo.flush()
    print("Q", res["Q"], "T", T, "J", best, "exact" if exact else "heur", "Q+J", res["total"], "length", res["length"], "walks", sm["walk_lengths"], "rowless", sm["rowless"], "%.0fs" % res["sec"], flush=True)
