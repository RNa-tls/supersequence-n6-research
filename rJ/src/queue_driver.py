#!/usr/bin/env python3
"""Work-queue driver for certified subtree runs (chainset_bc.py) with nested delegation.

Keeps W producer processes busy.  A job is a delegated leaf (initial fixings) of the top certificate
or of a finished subtree certificate.  Each job runs with a wall-clock limit; on the limit the producer
delegates its open nodes (DELEGATE_ON_TIMEOUT), and those become new jobs.  Stops at the first
INCUMBENT (a route of weight <= T-1) and reports it.  The certificates are verified afterwards by
composite_check.py / chainset_check2.py, never by this driver.

Initial fixings are passed through a file (INIT_FIX=@file): with node reduced-cost fixing they can
exceed the 128 KB limit of a single environment string.  Producer processes that are already running
for a job (e.g. after a driver restart) are adopted and waited for, never launched twice.

usage: queue_driver.py WORD T TOPCERT WORKERS JOB_SECONDS [EXTRA_ENV=VAL ...]
Job files: <TOP base>_sub_<id>.json, nested: <parent base>_<id>.json  (+ .json.log, .stdout, .initfix.json)"""
import sys, os, json, time, subprocess, gzip

def jload(p):
    return json.load(gzip.open(p, "rt") if p.endswith(".gz") else open(p))

def running_producers():
    """{cert path: pid} of chainset_bc.py processes currently alive"""
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit(): continue
        try: args = open(f"/proc/{d}/cmdline", "rb").read().split(b"\0")
        except OSError: continue
        args = [a.decode(errors="replace") for a in args if a]
        for i, a in enumerate(args):
            if a.endswith("chainset_bc.py") and i + 3 < len(args):
                out[args[i + 3]] = int(d)
    return out

def alive(pid):
    try: os.kill(pid, 0); return True
    except OSError: return False

def main():
    word, T, top, W, TL = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    extra = dict(kv.split("=", 1) for kv in sys.argv[6:])
    here = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
    base = top[:-len(".json")]
    state_f = base + ".queue.jsonl"
    def log(**kw):
        kw["t"] = time.strftime("%H:%M:%S")
        with open(state_f, "a") as f: f.write(json.dumps(kw) + "\n")
    def done_file(name):
        return os.path.exists(name) or os.path.exists(name + ".gz")
    def children_of(name):
        fr = json.load(open(name + ".frontier.json"))["frontier"]
        return [(name[:-len(".json")] + f"_{f['id']}.json", f["fix"], name) for f in fr]
    adopted = running_producers()
    todo = [(f"{base}_sub_{fr['id']}.json", fr["fix"], top) for fr in json.load(open(top + ".frontier.json"))["frontier"]]
    pending = []; running = {}
    while todo:
        name, fix, pool = todo.pop(0)
        if name in adopted and alive(adopted[name]):
            running[adopted[name]] = (None, name, fix, pool, time.time(), None); continue
        if done_file(name):
            C = jload(name if os.path.exists(name) else name + ".gz")
            if C.get("incumbent"): log(event="INCUMBENT_FOUND", job=name); print("INCUMBENT in", name); return
            if C.get("frontier"): todo.extend(children_of(name))
            continue
        pending.append((name, fix, pool))
    log(event="start", pending=len(pending), adopted=len(running), workers=W, job_seconds=TL)
    def finished(name, ok, t0):
        if not ok or not os.path.exists(name):
            log(event="FAILED", job=name); return True
        C = jload(name)
        if C.get("incumbent"):
            log(event="INCUMBENT_FOUND", job=name, incumbent=C["incumbent"][0]); print("INCUMBENT in", name)
            return False
        if C.get("frontier"):
            ch = children_of(name); pending.extend(ch)
            log(event="timeout_split", job=name, new_jobs=len(ch), sec=round(time.time() - t0))
        else:
            log(event="closed", job=name, nodes=len(C["nodes"]), sec=round(time.time() - t0))
        return True
    while pending or running:
        while pending and len(running) < W:
            name, fix, pool = pending.pop(0)
            fixf = name[:-len(".json")] + ".initfix.json"
            json.dump(fix, open(fixf, "w"))
            env = dict(os.environ, INIT_FIX="@" + fixf, GLOBAL_FIX0=top, INIT_POOL=pool, DELEGATE_ON_TIMEOUT="1", **extra)
            out = open(name[:-len(".json")] + ".stdout", "w")
            p = subprocess.Popen([PY, "-I", os.path.join(here, "chainset_bc.py"), word, T, name, str(TL)], env=env, stdout=out, stderr=subprocess.STDOUT)
            running[p.pid] = (p, name, fix, pool, time.time(), out)
            log(event="launch", job=name, nfix=len(fix), running=len(running), pending=len(pending))
        time.sleep(5)
        for pid in list(running):
            p, name, fix, pool, t0, out = running[pid]
            if p is None:                                   # adopted process
                if alive(pid): continue
                del running[pid]; ok = True
            else:
                if p.poll() is None: continue
                out.close(); del running[pid]; ok = (p.returncode == 0)
            if not finished(name, ok, t0):
                for q in running.values():
                    if q[0] is not None: q[0].kill()
                return
    log(event="queue_empty")
    print("queue empty")

if __name__ == "__main__":
    main()
