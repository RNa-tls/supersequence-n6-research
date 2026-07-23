param(
    [int]$WaitForPid,
    [string]$Python = 'C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outputs = Join-Path $root 'outputs'
$macro = Join-Path $PSScriptRoot 'superperm_partial_f1_macro.py'
$checkpoint = Join-Path $outputs 'f1_small_n0.checkpoint.json'
$result = Join-Path $outputs 'f1_small_n0_search.json'
$stdout = Join-Path $outputs 'f1_small_n0.stdout.log'
$stderr = Join-Path $outputs 'f1_small_n0.stderr.log'
$status = Join-Path $outputs 'f1_small_n0_runner_status.json'

function Write-Status([hashtable]$Data) {
    $tmp = "$status.tmp"
    $Data | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $status -Force
}

Write-Status @{
    schema = 'partial-f1-small-n0-runner-v1'; state = 'waiting_for_profile';
    wait_for_pid = $WaitForPid; started_at = (Get-Date).ToString('o');
    command = @($Python, $macro, 'enumerate', '--subcase', 'N0', '--unbounded', '--node-limit', '0', '--memory-limit-mib', '0', '--checkpoint', $checkpoint, '--checkpoint-every', '250', '--output', $result)
}

if ($WaitForPid -gt 0) {
    try { Wait-Process -Id $WaitForPid -ErrorAction Stop } catch { }
}

$started = Get-Date
Write-Status @{
    schema = 'partial-f1-small-n0-runner-v1'; state = 'running';
    wait_for_pid = $WaitForPid; started_at = $started.ToString('o');
    checkpoint = $checkpoint; result = $result; stdout = $stdout; stderr = $stderr;
    command = @($Python, $macro, 'enumerate', '--subcase', 'N0', '--unbounded', '--node-limit', '0', '--memory-limit-mib', '0', '--checkpoint', $checkpoint, '--checkpoint-every', '250', '--output', $result)
}

& $Python $macro enumerate --subcase N0 --unbounded --node-limit 0 --memory-limit-mib 0 --checkpoint $checkpoint --checkpoint-every 250 --output $result 1>> $stdout 2>> $stderr
$code = $LASTEXITCODE
$completed = $false
$parse_ok = $false
if (Test-Path -LiteralPath $result) {
    try {
        $data = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
        $parse_ok = $true
        $completed = [bool]$data.completed
    } catch { }
}
Write-Status @{
    schema = 'partial-f1-small-n0-runner-v1';
    state = if ($code -eq 0 -and $completed) {'completed'} else {'stopped_or_incomplete'};
    started_at = $started.ToString('o'); ended_at = (Get-Date).ToString('o');
    exit_code = $code; result_parse_ok = $parse_ok; result_completed = $completed;
    checkpoint = $checkpoint; result = $result; stdout = $stdout; stderr = $stderr;
}
exit $code
