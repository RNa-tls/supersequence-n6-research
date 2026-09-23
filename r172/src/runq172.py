#!/usr/bin/env python3
"""Run exp172.py argument lists (one JSON list per line) with N workers; no shell."""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def one(args):
    with open(ROOT / "r172/logs/final/runs.log", "a") as log:
        return subprocess.run([sys.executable, str(ROOT / "r172/src/exp172.py"), *args],
                              cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode


if __name__ == "__main__":
    q = [json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
    with ThreadPoolExecutor(int(sys.argv[2])) as ex:
        print(list(ex.map(one, q)))
