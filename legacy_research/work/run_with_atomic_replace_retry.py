#!/usr/bin/env python3
"""Run a Python program while retrying transient Windows ``os.replace`` locks.

This is intentionally an execution wrapper, not a modification of the search
engine.  The macro engine continues to hash to the SHA stored in an existing
checkpoint.  Only atomic checkpoint replacement is retried after a sharing or
antivirus lock; all other exceptions are propagated unchanged.
"""

from __future__ import annotations

import argparse
import errno
import os
import runpy
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace-retries", type=int, default=120)
    parser.add_argument("--replace-delay-seconds", type=float, default=0.5)
    parser.add_argument("program")
    parser.add_argument("program_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.replace_retries < 0 or args.replace_delay_seconds < 0:
        raise ValueError("retry count and delay must be nonnegative")

    real_replace = os.replace

    def retrying_replace(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
        # WinError 5 is the observed failure.  Sharing violations also occur
        # transiently on NTFS, so retry only those explicitly identified cases.
        retryable = {5, 32, 33}
        for attempt in range(args.replace_retries + 1):
            try:
                real_replace(source, destination)
                return
            except PermissionError as exc:
                winerror = getattr(exc, "winerror", None)
                if winerror not in retryable or attempt == args.replace_retries:
                    raise
            except OSError as exc:
                winerror = getattr(exc, "winerror", None)
                if (winerror not in retryable and exc.errno not in (errno.EACCES, errno.EBUSY)) or attempt == args.replace_retries:
                    raise
            time.sleep(args.replace_delay_seconds)

    # ``import os`` in the target returns this same module object.
    os.replace = retrying_replace  # type: ignore[assignment]
    sys.argv = [args.program, *args.program_args]
    runpy.run_path(args.program, run_name="__main__")


if __name__ == "__main__":
    main()
