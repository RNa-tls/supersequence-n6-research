# Proposed macro-engine memory instrumentation repair

## Status

**Proposal only.** The active `F=1,H=0,N=0` process was not touched, and this
document does not modify its macro engine, checkpoint, supervisor, or
finalizer.  Apply the change only after that process has stopped and its
checkpoint/output SHA relationship has been archived.

## Observed defect

`work/superperm_partial_f1_macro.py::_working_set_bytes` currently calls
`GetProcessMemoryInfo` without declaring `ctypes` argument and return types.
On 64-bit Windows, the default `ctypes` conversion is not a safe declaration
for a process HANDLE and pointer-valued argument.  Any resulting exception or
false return is caught by a blanket `except`, silently producing `0`.

That explains the profile's internal `peak_working_set_bytes: 0` even though
external read-only `Get-Process -Id <python PID>` samples observed nonzero
working sets.

## Minimal proposed diff — do not apply while PID 4448 runs

```diff
 def _working_set_bytes() -> int:
-    try:
-        import ctypes
+    try:
+        import ctypes
+        from ctypes import wintypes
         class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
             _fields_ = [ ... unchanged fields ... ]
         counters = PROCESS_MEMORY_COUNTERS_EX()
         counters.cb = ctypes.sizeof(counters)
-        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
-            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
-        )
+        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
+        get_current_process.restype = wintypes.HANDLE
+        get_process_memory = ctypes.windll.psapi.GetProcessMemoryInfo
+        get_process_memory.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
+        get_process_memory.restype = wintypes.BOOL
+        ok = get_process_memory(get_current_process(), ctypes.byref(counters), counters.cb)
         return int(counters.WorkingSetSize) if ok else 0
     except Exception:
         return 0
```

This is the same ABI pattern already used by
`work/analyze_partial_f1_profiles.py::working_set_bytes`.

## Correct measurement scopes

| quantity | owner | source |
|---|---|---|
| exact-search working set | Python enumerator child | `GetProcessMemoryInfo(GetCurrentProcess())` inside the engine |
| runner/finalizer working set | PowerShell parent processes | separate external process samples, never mixed into the enumerator peak |
| checkpoint serialization peak | Python enumerator child | same internal sampler before and after atomic checkpoint write |

The output must label these separately.  A parent's PowerShell working set is
not evidence about the child search's working set.

## Atomic checkpoint rule

At every checkpoint boundary:

1. sample `current_working_set_bytes`;
2. set `max_working_set_bytes = max(previous_peak, current)` in `stats`;
3. construct the complete checkpoint payload in memory;
4. write `<checkpoint>.tmp`, flush/close it, then `os.replace` it atomically.

The existing `write_json_atomic` already supplies step 4.  The proposed
change affects only numerical instrumentation in `stats`, not states,
transitions, pruning, canonicalization, or checkpoint schema.

## Why the mathematical computation is unchanged

Working-set values are neither read by the unbounded selected run (its memory
limit is zero) nor used in any transition or pruning predicate.  After the
active run ends, changing this function necessarily changes the engine SHA,
so old checkpoints must remain archived and must not be resumed with the new
engine.  The patch is therefore an operational measurement repair, not a
change to the finite state graph or any mathematical conclusion.
