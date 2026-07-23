<#
Resume the selected F=1,H=0,N=0 macro search from the *committed* checkpoint.

This is deliberately a one-shot supervisor: it never restarts a failed child,
never uses the uncommitted .tmp checkpoint as input, and writes only new output
and checkpoint paths.  The source checkpoints are read-only evidence.
#>

[CmdletBinding()]
param(
    [string]$Python = 'C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [int]$PollSeconds = 60
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$outputs = Join-Path $root 'outputs'
$macro = Join-Path $PSScriptRoot 'superperm_partial_f1_macro.py'
$engine = Join-Path $PSScriptRoot 'superperm_partial_f1.py'
$core = Join-Path $PSScriptRoot 'superperm_port_lift.py'
$verifier = Join-Path $PSScriptRoot 'verify_partial_f1_certificates.py'

# Immutable evidence and the sole resume source.
$committed = Join-Path $outputs 'f1_small_n0.checkpoint.json'
$uncommittedTmp = Join-Path $outputs 'f1_small_n0.checkpoint.json.tmp'
$committedBackup = Join-Path $outputs 'f1_small_n0.checkpoint.committed.0ca3f3530e78a115.backup.json'
$tmpBackup = Join-Path $outputs 'f1_small_n0.checkpoint.tmp.6b5db667b1f4faca.backup.json'

# All mutable artifacts of this run have distinct names.
$runCheckpoint = Join-Path $outputs 'f1_small_n0.committed_resume.checkpoint.json'
$result = Join-Path $outputs 'f1_small_n0_committed_resume_search.json'
$stdout = Join-Path $outputs 'f1_small_n0_committed_resume.stdout.log'
$stderr = Join-Path $outputs 'f1_small_n0_committed_resume.stderr.log'
$events = Join-Path $outputs 'f1_small_n0_committed_resume.events.jsonl'
$status = Join-Path $outputs 'f1_small_n0_committed_resume_status.json'
$finalMarkdown = Join-Path $outputs 'F1_N0_COMMITTED_RESUME_FINAL_STATUS.md'
$structuralVerification = Join-Path $outputs 'f1_small_n0_committed_resume_structural_verified.json'
$literalVerification = Join-Path $outputs 'f1_small_n0_committed_resume_literal_replay_verified.json'

$expected = @{
    checkpoint_sha256 = '0ca3f3530e78a115ba8443cde2df4d496a07d64711a101e4e1ca56913ccf3a9f'
    tmp_sha256 = '6b5db667b1f4facaaed4259a118751d344ef32d03f618c26e6e0e398ff25a42c'
    macro_sha256 = 'b02d3985d3672c24efdc197777cc25080fc9cb3846545db240ceacd649485049'
    engine_sha256 = '9196dcc17b3081aeb777001a1c5366e787fe15c1dad0614ec760953b785801a8'
    core_sha256 = '18f75735b08fc061765e33cc661a084c8735e433e80ee8035a163b113ee39d60'
    expanded = 25000
    accepted = 79683
    frontier = 54683
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-JsonAtomic([string]$Path, [object]$Data) {
    $temporary = "$Path.tmp"
    $Data | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Append-Event([hashtable]$Data) {
    $Data.timestamp = (Get-Date).ToString('o')
    ($Data | ConvertTo-Json -Depth 10 -Compress) | Add-Content -LiteralPath $events -Encoding UTF8
}

function Read-CheckpointSummary([string]$Path) {
    $data = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    return [ordered]@{
        schema = $data.schema
        macro_sha256 = $data.macro_sha256
        engine_sha256 = $data.engine_sha256
        core_sha256 = $data.core_sha256
        config = $data.config
        expanded = [int64]$data.stats.expanded
        accepted = [int64]$data.stats.accepted
        frontier = @($data.frontier).Count
        terminal_certificates = @($data.stats.terminal_certificates).Count
        success_certificates = @($data.stats.success_certificates).Count
        prunes = $data.stats.prunes
    }
}

function Get-CheckpointObservation([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return @{ exists = $false } }
    try {
        $item = Get-Item -LiteralPath $Path
        $summary = Read-CheckpointSummary $Path
        return @{ exists = $true; parse_ok = $true; size_bytes = $item.Length; last_write = $item.LastWriteTime.ToString('o'); summary = $summary }
    } catch {
        return @{ exists = $true; parse_ok = $false; read_error = $_.Exception.Message }
    }
}

function Assert-ResumePreflight {
    foreach ($path in @($committed, $uncommittedTmp, $committedBackup, $tmpBackup, $macro, $engine, $core, $verifier, $Python)) {
        if (-not (Test-Path -LiteralPath $path)) { throw "required path missing: $path" }
    }
    if ((Get-Sha256 $committed) -ne $expected.checkpoint_sha256) { throw 'committed checkpoint SHA mismatch' }
    if ((Get-Sha256 $uncommittedTmp) -ne $expected.tmp_sha256) { throw 'uncommitted checkpoint SHA mismatch' }
    if ((Get-Sha256 $committedBackup) -ne $expected.checkpoint_sha256) { throw 'committed backup SHA mismatch' }
    if ((Get-Sha256 $tmpBackup) -ne $expected.tmp_sha256) { throw 'tmp backup SHA mismatch' }
    if ((Get-Sha256 $macro) -ne $expected.macro_sha256) { throw 'macro engine SHA mismatch' }
    if ((Get-Sha256 $engine) -ne $expected.engine_sha256) { throw 'exact engine SHA mismatch' }
    if ((Get-Sha256 $core) -ne $expected.core_sha256) { throw 'exact engine SHA mismatch' }

    $summary = Read-CheckpointSummary $committed
    if ($summary.schema -ne 'partial-f1-macro-checkpoint-v1') { throw 'unexpected committed checkpoint schema' }
    if ($summary.macro_sha256 -ne $expected.macro_sha256 -or $summary.engine_sha256 -ne $expected.engine_sha256 -or $summary.core_sha256 -ne $expected.core_sha256) {
        throw 'checkpoint-internal engine SHA mismatch'
    }
    if ($summary.expanded -ne $expected.expanded -or $summary.accepted -ne $expected.accepted -or $summary.frontier -ne $expected.frontier) {
        throw "committed counters differ: expanded=$($summary.expanded), accepted=$($summary.accepted), frontier=$($summary.frontier)"
    }
    $config = $summary.config
    if ($config.name -ne 'small_F1_H0_N0' -or $config.n_limit -ne 0 -or $null -ne $config.max_macro_depth -or $config.node_limit -ne 0 -or $config.memory_limit_bytes -ne 0 -or -not $config.canonical_children) {
        throw 'committed checkpoint search config does not match the unbounded N=0 target'
    }
    return $summary
}

function Write-FinalMarkdown([hashtable]$Data) {
    $state = [string]$Data.state
    $body = @(
        '# F=1, H=0, N=0 committed-checkpoint resume',
        '',
        "Status: ``$state``.",
        '',
        'Scope: this runner concerns only the NR6/exact-state subcase `F=1, H=0, N=0`.  It makes no claim about `N>0`, other F slabs, or the full superpermutation lower bound.',
        '',
        '```json',
        ($Data | ConvertTo-Json -Depth 16),
        '```'
    ) -join [Environment]::NewLine
    Set-Content -LiteralPath $finalMarkdown -Value $body -Encoding UTF8
}

try {
    $preflight = Assert-ResumePreflight
} catch {
    $failure = @{
        schema = 'partial-f1-n0-committed-resume-v1'
        state = 'resume validation failed; no search started'
        timestamp = (Get-Date).ToString('o')
        error = $_.Exception.Message
        resume_source = $committed
        uncommitted_tmp_comparison_only = $uncommittedTmp
    }
    Write-JsonAtomic $status $failure
    Write-FinalMarkdown $failure
    exit 2
}

$preflightRecord = @{
    schema = 'partial-f1-n0-committed-resume-preflight-v1'
    state = 'validated'
    validated_at = (Get-Date).ToString('o')
    resume_source = $committed
    uncommitted_tmp_comparison_only = $uncommittedTmp
    committed_summary = $preflight
    immutable_backups = @(
        @{ path = $committedBackup; sha256 = Get-Sha256 $committedBackup; size_bytes = (Get-Item -LiteralPath $committedBackup).Length; last_write = (Get-Item -LiteralPath $committedBackup).LastWriteTime.ToString('o') },
        @{ path = $tmpBackup; sha256 = Get-Sha256 $tmpBackup; size_bytes = (Get-Item -LiteralPath $tmpBackup).Length; last_write = (Get-Item -LiteralPath $tmpBackup).LastWriteTime.ToString('o') }
    )
    code_sha256 = @{ macro = Get-Sha256 $macro; engine = Get-Sha256 $engine; core = Get-Sha256 $core; verifier = Get-Sha256 $verifier }
    new_artifacts = @{ checkpoint = $runCheckpoint; result = $result; stdout = $stdout; stderr = $stderr; events = $events; status = $status }
}
Write-JsonAtomic (Join-Path $outputs 'f1_n0_committed_resume_preflight.json') $preflightRecord

if ((Test-Path -LiteralPath $runCheckpoint) -or (Test-Path -LiteralPath $result)) {
    throw "refusing to overwrite mutable resume artifact: checkpoint=$runCheckpoint result=$result"
}

$command = @($macro, 'enumerate', '--subcase', 'N0', '--unbounded', '--node-limit', '0', '--memory-limit-mib', '0', '--checkpoint', $runCheckpoint, '--checkpoint-every', '250', '--resume', $committed, '--output', $result)
$started = Get-Date
$initialStatus = @{
    schema = 'partial-f1-n0-committed-resume-v1'
    state = 'N=0 exhaustive search resumed from committed checkpoint'
    started_at = $started.ToString('o')
    process_id = $null
    resume_source = $committed
    uncommitted_tmp_comparison_only = $uncommittedTmp
    committed_summary = $preflight
    command = @($Python) + $command
    node_limit = 0
    memory_limit_mib = 0
    run_checkpoint = $runCheckpoint
    result = $result
    stdout = $stdout
    stderr = $stderr
    events = $events
}
Write-JsonAtomic $status $initialStatus
Append-Event @{ event = 'preflight_passed'; resume_source = $committed; expanded = $preflight.expanded; accepted = $preflight.accepted; frontier = $preflight.frontier }

$child = Start-Process -FilePath $Python -ArgumentList $command -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$initialStatus.process_id = $child.Id
Write-JsonAtomic $status $initialStatus
Append-Event @{ event = 'child_started'; process_id = $child.Id }

while (-not $child.HasExited) {
    Start-Sleep -Seconds $PollSeconds
    try { $child.Refresh() } catch { }
    $processObservation = $null
    try {
        $proc = Get-Process -Id $child.Id -ErrorAction Stop
        $processObservation = @{ cpu_seconds = [math]::Round($proc.CPU, 3); working_set_bytes = [int64]$proc.WorkingSet64; private_memory_bytes = [int64]$proc.PrivateMemorySize64; start_time = $proc.StartTime.ToString('o') }
    } catch { $processObservation = @{ unavailable = $true } }
    $checkpointObservation = Get-CheckpointObservation $runCheckpoint
    $heartbeat = @{
        schema = 'partial-f1-n0-committed-resume-v1'
        state = 'N=0 exhaustive search resumed from committed checkpoint'
        started_at = $started.ToString('o')
        observed_at = (Get-Date).ToString('o')
        process_id = $child.Id
        process = $processObservation
        checkpoint = $checkpointObservation
        resume_source = $committed
        uncommitted_tmp_comparison_only = $uncommittedTmp
        node_limit = 0
        memory_limit_mib = 0
        command = @($Python) + $command
    }
    Write-JsonAtomic $status $heartbeat
    Append-Event @{ event = 'heartbeat'; process_id = $child.Id; process = $processObservation; checkpoint = $checkpointObservation }
}

$exitCode = $child.ExitCode
$ended = Get-Date
$resultData = $null
$resultParseError = $null
if (Test-Path -LiteralPath $result) {
    try { $resultData = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json } catch { $resultParseError = $_.Exception.Message }
}
$runCheckpointObservation = Get-CheckpointObservation $runCheckpoint

if ($exitCode -eq 0 -and $null -ne $resultData -and [bool]$resultData.completed) {
    & $Python $verifier $result --output $structuralVerification 1>> $stdout 2>> $stderr
    $structuralExit = $LASTEXITCODE
    & $Python $verifier $result --full-terminal-replay --output $literalVerification 1>> $stdout 2>> $stderr
    $literalExit = $LASTEXITCODE
    $structuralData = $null; $literalData = $null
    try { $structuralData = Get-Content -LiteralPath $structuralVerification -Raw | ConvertFrom-Json } catch { }
    try { $literalData = Get-Content -LiteralPath $literalVerification -Raw | ConvertFrom-Json } catch { }
    $verified = $structuralExit -eq 0 -and $literalExit -eq 0 -and $null -ne $structuralData -and $null -ne $literalData -and [bool]$structuralData.passed -and [bool]$literalData.passed
    $finalState = if ($verified) { 'N=0 exhaustive search completed and verified' } else { 'output inconsistency; no conclusion permitted' }
    $final = @{
        schema = 'partial-f1-n0-committed-resume-v1'; state = $finalState
        started_at = $started.ToString('o'); ended_at = $ended.ToString('o'); exit_code = $exitCode
        result = @{ path = $result; parse_ok = $true; sha256 = Get-Sha256 $result; completed = [bool]$resultData.completed; stats = $resultData.stats }
        structural_verification = @{ path = $structuralVerification; exit_code = $structuralExit; report = $structuralData }
        literal_replay_verification = @{ path = $literalVerification; exit_code = $literalExit; report = $literalData }
        run_checkpoint = $runCheckpointObservation
        resume_source = $committed; uncommitted_tmp_comparison_only = $uncommittedTmp
    }
} else {
    $resumable = $runCheckpointObservation.exists -and $runCheckpointObservation.parse_ok -and $runCheckpointObservation.summary.macro_sha256 -eq $expected.macro_sha256 -and $runCheckpointObservation.summary.engine_sha256 -eq $expected.engine_sha256 -and $runCheckpointObservation.summary.core_sha256 -eq $expected.core_sha256
    $finalState = if ($resumable) { 'N=0 search interrupted again; resumable checkpoint verified' } else { 'output inconsistency; no conclusion permitted' }
    $final = @{
        schema = 'partial-f1-n0-committed-resume-v1'; state = $finalState
        started_at = $started.ToString('o'); ended_at = $ended.ToString('o'); exit_code = $exitCode
        result = @{ path = $result; exists = (Test-Path -LiteralPath $result); parse_error = $resultParseError; completed = if ($null -ne $resultData) {[bool]$resultData.completed} else {$false} }
        run_checkpoint = $runCheckpointObservation
        resume_source = $committed; uncommitted_tmp_comparison_only = $uncommittedTmp
        automatic_restart = $false
        next_step = 'Do not restart automatically.  Preserve this new checkpoint and validate it before any future resume.'
    }
}
Write-JsonAtomic $status $final
Write-FinalMarkdown $final
Append-Event @{ event = 'child_ended'; exit_code = $exitCode; state = $final.state }
exit $exitCode
