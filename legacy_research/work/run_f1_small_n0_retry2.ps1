<#
Resume the exact F=1,H=0,N=0 search from the last *committed* retry-1
checkpoint.  The source and its backup are read-only evidence.  This one-shot
supervisor never restarts a failed child and uses fresh output paths.
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
$wrapper = Join-Path $PSScriptRoot 'run_with_atomic_replace_retry.py'
$verifier = Join-Path $PSScriptRoot 'verify_partial_f1_certificates.py'

$source = Join-Path $outputs 'f1_small_n0.committed_resume.checkpoint.json'
$sourceTmp = Join-Path $outputs 'f1_small_n0.committed_resume.checkpoint.json.tmp'
$sourceSha = '5fc78a33465b86131ac99d8851bfd7cb827318eba8ee12575c100b43bacced8a'
$backup = Join-Path $outputs 'f1_small_n0.committed_resume.checkpoint.5fc78a33465b861.backup.json'

$checkpoint = Join-Path $outputs 'f1_small_n0.retry2.checkpoint.json'
$result = Join-Path $outputs 'f1_small_n0_retry2_search.json'
$stdout = Join-Path $outputs 'f1_small_n0_retry2.stdout.log'
$stderr = Join-Path $outputs 'f1_small_n0_retry2.stderr.log'
$events = Join-Path $outputs 'f1_small_n0_retry2.events.jsonl'
$status = Join-Path $outputs 'f1_small_n0_retry2_status.json'
$structural = Join-Path $outputs 'f1_small_n0_retry2_structural_verified.json'
$literal = Join-Path $outputs 'f1_small_n0_retry2_literal_replay_verified.json'

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Write-JsonAtomic([string]$Path, [object]$Data) {
    $temporary = "$Path.tmp"
    $Data | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $temporary -Encoding UTF8
    for ($attempt = 0; $attempt -le 120; ++$attempt) {
        try { Move-Item -LiteralPath $temporary -Destination $Path -Force; return }
        catch { if ($attempt -eq 120) { throw }; Start-Sleep -Milliseconds 500 }
    }
}
function Append-Event([hashtable]$Data) { $Data.timestamp=(Get-Date).ToString('o'); ($Data|ConvertTo-Json -Depth 10 -Compress)|Add-Content -LiteralPath $events -Encoding UTF8 }
function Read-CheckpointSummary([string]$Path) {
    $data = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    [ordered]@{ schema=$data.schema; macro_sha256=$data.macro_sha256; engine_sha256=$data.engine_sha256; core_sha256=$data.core_sha256; config=$data.config; expanded=[int64]$data.stats.expanded; accepted=[int64]$data.stats.accepted; frontier=@($data.frontier).Count; terminal_certificates=@($data.stats.terminal_certificates).Count; success_certificates=@($data.stats.success_certificates).Count; prunes=$data.stats.prunes }
}
function Observe-Checkpoint([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return @{exists=$false} }
    try { $item=Get-Item -LiteralPath $Path; return @{exists=$true;parse_ok=$true;size_bytes=$item.Length;last_write=$item.LastWriteTime.ToString('o');summary=(Read-CheckpointSummary $Path)} }
    catch { return @{exists=$true;parse_ok=$false;read_error=$_.Exception.Message} }
}

try {
    foreach($p in @($Python,$macro,$engine,$core,$wrapper,$verifier,$source)) { if(-not(Test-Path -LiteralPath $p)){throw "required path missing: $p"} }
    if ((Get-Sha256 $source) -ne $sourceSha) { throw 'retry-1 committed checkpoint SHA mismatch' }
    if (-not(Test-Path -LiteralPath $backup)) { Copy-Item -LiteralPath $source -Destination $backup -ErrorAction Stop; (Get-Item -LiteralPath $backup).IsReadOnly=$true }
    if ((Get-Sha256 $backup) -ne $sourceSha) { throw 'retry-1 immutable backup SHA mismatch' }
    $summary=Read-CheckpointSummary $source
    if($summary.schema -ne 'partial-f1-macro-checkpoint-v1'){throw 'unexpected checkpoint schema'}
    if($summary.macro_sha256 -ne (Get-Sha256 $macro) -or $summary.engine_sha256 -ne (Get-Sha256 $engine) -or $summary.core_sha256 -ne (Get-Sha256 $core)){throw 'checkpoint engine SHA mismatch'}
    if($summary.expanded -ne 36250 -or $summary.accepted -ne 114182 -or $summary.frontier -ne 77932){throw 'retry-1 checkpoint counters differ from audited source'}
    $cfg=$summary.config
    if($cfg.name -ne 'small_F1_H0_N0' -or $cfg.n_limit -ne 0 -or $null -ne $cfg.max_macro_depth -or $cfg.node_limit -ne 0 -or $cfg.memory_limit_bytes -ne 0 -or -not $cfg.canonical_children){throw 'checkpoint config is not unbounded N=0'}
    if((Test-Path -LiteralPath $checkpoint) -or (Test-Path -LiteralPath $result)){throw 'retry2 artifact already exists; refusing overwrite'}
} catch {
    Write-JsonAtomic $status @{schema='partial-f1-n0-retry2-v1';state='resume validation failed; no search started';timestamp=(Get-Date).ToString('o');error=$_.Exception.Message;resume_source=$source}
    exit 2
}

$command=@($wrapper,'--replace-retries','240','--replace-delay-seconds','0.5',$macro,'enumerate','--subcase','N0','--unbounded','--node-limit','0','--memory-limit-mib','0','--checkpoint',$checkpoint,'--checkpoint-every','250','--resume',$source,'--output',$result)
$started=Get-Date
$base=@{schema='partial-f1-n0-retry2-v1';state='N=0 exhaustive search resumed from retry-1 committed checkpoint';started_at=$started.ToString('o');resume_source=$source;resume_source_sha256=$sourceSha;immutable_backup=$backup;source_tmp_comparison_only=$sourceTmp;source_summary=$summary;command=@($Python)+$command;node_limit=0;memory_limit_mib=0;checkpoint=$checkpoint;result=$result;stdout=$stdout;stderr=$stderr;events=$events;wrapper_sha256=(Get-Sha256 $wrapper);macro_sha256=(Get-Sha256 $macro);engine_sha256=(Get-Sha256 $engine);core_sha256=(Get-Sha256 $core)}
Write-JsonAtomic $status $base; Append-Event @{event='preflight_passed';source_sha256=$sourceSha;source_summary=$summary}
$child=Start-Process -FilePath $Python -ArgumentList $command -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
$base.process_id=$child.Id; Write-JsonAtomic $status $base; Append-Event @{event='child_started';process_id=$child.Id}
while(-not $child.HasExited){
    Start-Sleep -Seconds $PollSeconds; try{$child.Refresh()}catch{}
    try{$proc=Get-Process -Id $child.Id -ErrorAction Stop;$po=@{cpu_seconds=[math]::Round($proc.CPU,3);working_set_bytes=[int64]$proc.WorkingSet64;private_memory_bytes=[int64]$proc.PrivateMemorySize64;start_time=$proc.StartTime.ToString('o')}}catch{$po=@{unavailable=$true}}
    $beat=$base.Clone();$beat.observed_at=(Get-Date).ToString('o');$beat.process=$po;$beat.checkpoint_observation=Observe-Checkpoint $checkpoint;Write-JsonAtomic $status $beat;Append-Event @{event='heartbeat';process=$po;checkpoint=$beat.checkpoint_observation}
}
$exit=$child.ExitCode;$ended=Get-Date;$resultData=$null;$parseError=$null;if(Test-Path -LiteralPath $result){try{$resultData=Get-Content -LiteralPath $result -Raw|ConvertFrom-Json}catch{$parseError=$_.Exception.Message}}
$finish=$base.Clone();$finish.ended_at=$ended.ToString('o');$finish.exit_code=$exit;$finish.run_checkpoint=Observe-Checkpoint $checkpoint;$finish.result=@{exists=(Test-Path -LiteralPath $result);parse_error=$parseError}
if($exit -eq 0 -and $null -ne $resultData -and [bool]$resultData.completed){
    & $Python $verifier $result --output $structural 1>>$stdout 2>>$stderr;$se=$LASTEXITCODE
    & $Python $verifier $result --full-terminal-replay --output $literal 1>>$stdout 2>>$stderr;$le=$LASTEXITCODE
    $sd=$null;$ld=$null;try{$sd=Get-Content $structural -Raw|ConvertFrom-Json}catch{};try{$ld=Get-Content $literal -Raw|ConvertFrom-Json}catch{}
    $ok=$se -eq 0 -and $le -eq 0 -and $null -ne $sd -and $null -ne $ld -and [bool]$sd.passed -and [bool]$ld.passed;$finish.structural_verification=@{exit_code=$se;report=$sd};$finish.literal_replay_verification=@{exit_code=$le;report=$ld};$finish.state=if($ok){'N=0 exhaustive search completed and verified'}else{'output inconsistency; no conclusion permitted'}
}else{$finish.state='N=0 search interrupted again; resumable checkpoint verified'}
Write-JsonAtomic $status $finish;Append-Event @{event='child_finished';exit_code=$exit;state=$finish.state;checkpoint=$finish.run_checkpoint}
