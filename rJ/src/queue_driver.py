#!/usr/bin/env python3
"""Work-queue driver for certified subtree runs (chainset_bc.py) with nested delegation.

Keeps W producer processes busy.  A job is a delegated leaf (initial fixings) of the top certificate
or of a finished subtree certificate.  Each job runs with a wall-clock limit; on the limit the producer
delegates its open nodes (DELEGATE_ON_TIMEOUT), and those become new jobs.  Stops at the first
INCUMBENT (a route of weight <= T-1) and reports it.  The certificates are verified afterwards by
composite_check.py / chainset_check2.py, never by this driver.

usage: queue_driver.py WORD T TOPCERT WORKERS JOB_SECONDS [EXTRA_ENV=VAL ...]
Job files: <TOP base>_sub_<id>.json, nested: <parent base>_<id>.json  (+ .json.log, .stdout)"""
import sys, os, json, time, subprocess, gzip

def jload(p):
    return json.load(gzip.open(p, "rt") if p.endswith(".gz") else open(p))

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
    pending = []
    for fr in json.load(open(top + ".frontier.json"))["frontier"]:
        pending.append((f"{base}_sub_{fr['id']}.json", fr["fix"], top))
    # resume: jobs whose certificate exists are expanded (their own frontier) instead of rerun
    expanded = []
    while pending:
        name, fix, pool = pending.pop(0)
        if done_file(name):
            C = jload(name if os.path.exists(name) else name + ".gz")
            if C.get("incumbent"): log(event="INCUMBENT_FOUND", job=name); print("INCUMBENT in", name); return
            if C.get("frontier"):
                fr = json.load(open(name + ".frontier.json"))["frontier"]
                for f in fr: pending.append((name[:-len(".json")] + f"_{f['id']}.json", f["fix"], name))
            continue
        expanded.append((name, fix, pool))
    pending = expanded
    log(event="start", pending=len(pending), workers=W, job_seconds=TL)
    running = {}
    while pending or running:
        while pending and len(running) < W:
            name, fix, pool = pending.pop(0)
            env = dict(os.environ, INIT_FIX=json.dumps(fix).replace(" ", ""), GLOBAL_FIX0=top, INIT_POOL=pool, DELEGATE_ON_TIMEOUT="1", **extra)
            out = open(name[:-len(".json")] + ".stdout", "w")
            p = subprocess.Popen([PY, "-I", os.path.join(here, "chainset_bc.py"), word, T, name, str(TL)], env=env, stdout=out, stderr=subprocess.STDOUT)
            running[p.pid] = (p, name, fix, pool, time.time(), out)
            log(event="launch", job=name, nfix=len(fix), running=len(running), pending=len(pending))
        time.sleep(5)
        for pid in list(running):
            p, name, fix, pool, t0, out = running[pid]
            if p.poll() is None: continue
            out.close(); del running[pid]
            if p.returncode != 0 or not os.path.exists(name):
                log(event="FAILED", job=name, rc=p.returncode); continue
            C = jload(name)
            if C.get("incumbent"):
                log(event="INCUMBENT_FOUND", job=name, incumbent=C["incumbent"][0])
                print("INCUMBENT in", name)
                for q in running.values(): q[0].kill()
                return
            if C.get("frontier"):
                fr = json.load(open(name + ".frontier.json"))["frontier"]
                for f in fr: pending.append((name[:-len(".json")] + f"_{f['id']}.json", f["fix"], name))
                log(event="timeout_split", job=name, new_jobs=len(fr), sec=round(time.time() - t0))
            else:
                log(event="closed", job=name, nodes=len(C["nodes"]), sec=round(time.time() - t0))
    log(event="queue_empty")
    print("queue empty")

if __name__ == "__main__":
    main()
