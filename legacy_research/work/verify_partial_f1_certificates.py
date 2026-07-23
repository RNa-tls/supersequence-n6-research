#!/usr/bin/env python3
"""Read-only verifier for partial-F=1 macro-search result files.

The verifier does not enumerate new states.  It validates serialized terminal
and success-state data, then literally replays every supplied representative
macro path through the exact state engine.  It rejects a result whose macro or
exact-engine SHA does not match the code used for verification.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
MACRO_PATH = HERE.with_name("superperm_partial_f1_macro.py")
SPEC = importlib.util.spec_from_file_location("partial_f1_macro_for_verifier", MACRO_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MACRO_PATH}")
macro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = macro
SPEC.loader.exec_module(macro)
exact = macro.exact


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CODE_SHA256 = sha256_file(HERE)


def config_from_result(data: Mapping[str, object]) -> macro.AreaAConfig:
    config = data["config"]
    if not isinstance(config, Mapping):
        raise ValueError("missing config")
    return macro.AreaAConfig(int(config["n_limit"]), str(config["name"]))


def verify(path: Path, full_terminal_replay: bool) -> Dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "partial-f1-macro-search-v1":
        raise ValueError("unrecognized search result schema")
    expected = (macro.CODE_SHA256, macro.ENGINE_SHA256, macro.CORE_SHA256)
    observed = (data.get("macro_sha256"), data.get("engine_sha256"), data.get("core_sha256"))
    if observed != expected:
        raise ValueError("search-result code SHA mismatch; refuse verification")
    config = config_from_result(data)
    stats = data.get("stats")
    if not isinstance(stats, Mapping):
        raise ValueError("missing stats")

    terminal_checked = 0
    terminal_replayed = 0
    for cert in stats.get("terminal_certificates", []):
        if not isinstance(cert, Mapping):
            raise ValueError("malformed terminal certificate")
        state = exact.state_from_json(cert["state"])
        if macro.stable_hash(state) != cert.get("state_hash"):
            raise AssertionError("terminal state hash mismatch")
        if list(macro.state_coordinate(state)) != list(cert.get("coordinate", [])):
            raise AssertionError("terminal coordinate mismatch")
        if macro.area_a_final(state, config):
            raise AssertionError("successful state cannot be serialized as dead")
        terminal_checked += 1
        if full_terminal_replay and cert.get("path"):
            replay = macro.replay_macro_path(cert["path"])
            if replay.stable_key() != state.stable_key():
                raise AssertionError("terminal representative path does not replay")
            terminal_replayed += 1

    success_checked = 0
    for cert in stats.get("success_certificates", []):
        if not isinstance(cert, Mapping):
            raise ValueError("malformed success certificate")
        state = exact.state_from_json(cert["state"])
        replay = macro.replay_macro_path(cert["path"])
        final_rotation = int(cert.get("final_rotation_length", 0))
        for _ in range(final_rotation):
            step = exact.extend(replay, macro.W1)
            if step is None:
                raise AssertionError("success final rotation suffix collides")
            replay = step.state
        if replay.stable_key() != state.stable_key():
            raise AssertionError("success representative path does not replay")
        if not macro.area_a_final(state, config):
            raise AssertionError("claimed success does not meet exact Area-A target")
        success_checked += 1

    return {
        "schema": "partial-f1-certificate-verification-v1",
        "verifier_sha256": CODE_SHA256,
        "macro_sha256": macro.CODE_SHA256,
        "engine_sha256": macro.ENGINE_SHA256,
        "core_sha256": macro.CORE_SHA256,
        "input": str(path),
        "input_sha256": sha256_file(path),
        "config": {"name": config.name, "n_limit": config.n_limit},
        "terminal_certificates_checked": terminal_checked,
        "terminal_paths_replayed": terminal_replayed,
        "success_certificates_checked_and_literally_replayed": success_checked,
        "completed_input": bool(data.get("completed")),
        "passed": True,
        "scope": "read-only certificate consistency and literal-path replay; not an independent enumeration",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--full-terminal-replay", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(Path(args.input), args.full_terminal_replay)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
