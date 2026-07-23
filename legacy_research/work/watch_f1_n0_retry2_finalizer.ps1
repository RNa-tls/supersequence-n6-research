<# Passive finalizer watcher.  It never starts, stops, or resumes search. #>
[CmdletBinding()]
param([int]$PollSeconds = 120)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root 'outputs'
$py='C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$status=Join-Path $out 'f1_small_n0_retry2_status.json'
$result=Join-Path $out 'f1_small_n0_retry2_search.json'
$checkpoint=Join-Path $out 'f1_small_n0.retry2.checkpoint.json'
$finalizer=Join-Path $PSScriptRoot 'finalize_f1_n0_retry2.py'
$summary=Join-Path $out 'f1_n0_retry2_final_summary.json'
$markdown=Join-Path $out 'F1_N0_RETRY2_FINAL_STATUS.md'
$certs=Join-Path $out 'f1_n0_retry2_terminal_certificates.json'
$watch=Join-Path $out 'f1_n0_retry2_finalizer_watch.json'
while($true){
  if(Test-Path $status){
    try{$d=Get-Content $status -Raw|ConvertFrom-Json}catch{$d=$null}
    if($null -ne $d){
      if($d.state -eq 'N=0 exhaustive search completed and verified'){
        if(-not(Test-Path $result) -or -not(Test-Path $checkpoint)){throw 'completed supervisor status lacks result or checkpoint'}
        & $py $finalizer $result $checkpoint --output $summary --markdown $markdown --certificates $certs
        exit $LASTEXITCODE
      }
      if($d.state -like '*interrupted*' -or $d.state -like 'output inconsistency*' -or $d.state -like 'resume validation failed*'){
        @{schema='partial-f1-n0-retry2-finalizer-watch-v1';state='search ended without finalization';observed_state=$d.state;observed_at=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content $watch -Encoding UTF8
        exit 0
      }
    }
  }
  Start-Sleep -Seconds $PollSeconds
}
