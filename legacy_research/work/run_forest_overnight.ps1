<#
Long-running supervisor for the five depth-2 forest-cover branches.

It never kills or restarts an existing forest enumeration.  Existing commands
are adopted by their exact `--seed` / `--output` command-line pair.  A branch
which exits without a valid `completed: true` JSON is recorded as failed and
is deliberately not retried automatically.

The supervisor itself requests ES_SYSTEM_REQUIRED, but not
ES_DISPLAY_REQUIRED: the display may turn off while Windows is kept awake.
#>
[CmdletBinding()]
param(
    [int]$MaxConcurrent = 2,
    [int]$PollSeconds = 120,
    [switch]$Once
)

$ErrorActionPreference = 'Stop'
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Workspace = Split-Path -Parent $ScriptRoot
$Outputs = Join-Path $Workspace 'outputs'
$Python = 'C:\Users\parks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Engine = Join-Path $Workspace 'work\superperm_port_lift.py'
$Verifier = Join-Path $Workspace 'work\verify_forest_certificates.py'
$StatusJson = Join-Path $Outputs 'forest_overnight_status.json'
$StatusMd = Join-Path $Outputs 'FOREST_OVERNIGHT_STATUS.md'
$RunnerLog = Join-Path $Outputs 'forest_overnight_runner.log'
$RunnerSha = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()

if (-not (Test-Path -LiteralPath $Python)) { throw "Python runtime not found: $Python" }
if (-not (Test-Path -LiteralPath $Engine)) { throw "Engine not found: $Engine" }
New-Item -ItemType Directory -Force -Path $Outputs | Out-Null

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ForestPower {
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern uint SetThreadExecutionState(uint esFlags);
}
'@
$ES_CONTINUOUS = [uint32]2147483648
$ES_SYSTEM_REQUIRED = [uint32]1
$KeepSystemAwake = [uint32]2147483649
[void][ForestPower]::SetThreadExecutionState($KeepSystemAwake)

$Seeds = @('0,2', '0,3', '0,7', '0,15', '0,27')

function Timestamp { (Get-Date).ToString('o') }

function Write-RunnerLog([string]$Message) {
    "$(Timestamp) $Message" | Add-Content -LiteralPath $RunnerLog -Encoding utf8
}

function Write-AtomicJson([object]$Object, [string]$Path) {
    $temp = "$Path.tmp"
    $Object | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $temp -Encoding utf8
    Move-Item -LiteralPath $temp -Destination $Path -Force
}

function Get-OutputStem([string]$Seed) {
    "forest_branch_0_$($Seed.Split(',')[1])"
}

function Get-BranchPaths([string]$Seed) {
    $stem = Get-OutputStem $Seed
    [pscustomobject]@{
        Stem = $stem
        Json = Join-Path $Outputs "$stem.json"
        Stdout = Join-Path $Outputs "$stem.stdout.log"
        Stderr = Join-Path $Outputs "$stem.stderr.log"
        Incidence = Join-Path $Outputs "$stem.incidence_verified.json"
        Full = Join-Path $Outputs "$stem.fully_verified.json"
        VerifyStdout = Join-Path $Outputs "$stem.verify.stdout.log"
        VerifyStderr = Join-Path $Outputs "$stem.verify.stderr.log"
    }
}

function Get-ForestProcess([string]$Seed) {
    $escapedSeed = [regex]::Escape($Seed)
    $matches = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
        $_.CommandLine -match 'superperm_port_lift\.py\s+enumerate-forest-covers' -and
        $_.CommandLine -match "--seed\s+$escapedSeed(\s|$)"
    })
    if ($matches.Count -gt 1) { throw "Duplicate live forest processes for seed $Seed" }
    if ($matches.Count -eq 0) { return $null }
    $record = $matches[0]
    $process = Get-Process -Id $record.ProcessId -ErrorAction Stop
    [pscustomobject]@{
        PID = [int]$record.ProcessId
        CommandLine = $record.CommandLine
        StartTime = $process.StartTime.ToString('o')
        CPU = [math]::Round($process.CPU, 2)
        WorkingSetMB = [math]::Round($process.WorkingSet64 / 1MB, 1)
        Priority = $process.PriorityClass.ToString()
    }
}

function Get-Json([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json) }
    catch { return $null }
}

function Invoke-Logged([string[]]$CommandArguments, [string]$Stdout, [string]$Stderr) {
    & $Python @CommandArguments 1>> $Stdout 2>> $Stderr
    return $LASTEXITCODE
}

function Test-BranchJson([string]$Seed, [string]$JsonPath) {
    $obj = Get-Json $JsonPath
    if ($null -eq $obj) { return [pscustomobject]@{Valid=$false;Reason='JSON parse failed or missing';Object=$null} }
    $expected = $Seed.Split(',') | ForEach-Object {[int]$_}
    $actual = @($obj.seed | ForEach-Object {[int]$_})
    $required = @('node_count','prune_counts','certificates','code_sha256','completed','node_limit')
    foreach($field in $required) {
        if ($null -eq $obj.$field) { return [pscustomobject]@{Valid=$false;Reason="missing $field";Object=$obj} }
    }
    if (@(Compare-Object $expected $actual).Count -ne 0) { return [pscustomobject]@{Valid=$false;Reason='seed mismatch';Object=$obj} }
    if ([int64]$obj.node_limit -ne 0) { return [pscustomobject]@{Valid=$false;Reason='node_limit is not zero';Object=$obj} }
    if (-not [bool]$obj.completed -or [bool]$obj.aborted_at_node_limit) { return [pscustomobject]@{Valid=$false;Reason='branch JSON is not completed';Object=$obj} }
    return [pscustomobject]@{Valid=$true;Reason='ok';Object=$obj}
}

function Invoke-Verification([string]$Seed, $Paths) {
    $basic = Test-BranchJson $Seed $Paths.Json
    if (-not $basic.Valid) { return [pscustomobject]@{Incidence=$false;Full=$false;Reason=$basic.Reason} }
    if (-not (Test-Path -LiteralPath $Paths.Incidence)) {
        $exit = Invoke-Logged -CommandArguments @($Verifier, $Paths.Json, '--skip-dp-replay', '--output', $Paths.Incidence) -Stdout $Paths.VerifyStdout -Stderr $Paths.VerifyStderr
        if ($exit -ne 0) { return [pscustomobject]@{Incidence=$false;Full=$false;Reason="incidence verifier exit $exit"} }
    }
    $incidence = Get-Json $Paths.Incidence
    if ($null -eq $incidence -or [int]$incidence.certificates_verified -ne @($basic.Object.certificates).Count) {
        return [pscustomobject]@{Incidence=$false;Full=$false;Reason='invalid incidence verifier output'}
    }
    if (-not (Test-Path -LiteralPath $Paths.Full)) {
        $exit = Invoke-Logged -CommandArguments @($Verifier, $Paths.Json, '--output', $Paths.Full) -Stdout $Paths.VerifyStdout -Stderr $Paths.VerifyStderr
        if ($exit -ne 0) { return [pscustomobject]@{Incidence=$true;Full=$false;Reason="full verifier exit $exit"} }
    }
    $full = Get-Json $Paths.Full
    if ($null -eq $full -or [int]$full.certificates_verified -ne @($basic.Object.certificates).Count -or -not [bool]$full.dp_replayed) {
        return [pscustomobject]@{Incidence=$true;Full=$false;Reason='invalid full verifier output'}
    }
    return [pscustomobject]@{Incidence=$true;Full=$true;Reason='ok'}
}

function Get-LastLines([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    return @(Get-Content -LiteralPath $Path -Tail 100 -ErrorAction SilentlyContinue)
}

function Start-ForestBranch([string]$Seed, $Paths) {
    $arguments = @('work\superperm_port_lift.py','enumerate-forest-covers','--seed',$Seed,'--node-limit','0','--output',"outputs\$($Paths.Stem).json")
    $process = Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $Workspace -WindowStyle Hidden -RedirectStandardOutput $Paths.Stdout -RedirectStandardError $Paths.Stderr -PassThru
    try { $process.PriorityClass = 'BelowNormal' } catch { Write-RunnerLog "seed ${Seed}: priority change failed: $($_.Exception.Message)" }
    Write-RunnerLog "started seed ${Seed} pid $($process.Id): $Python $($arguments -join ' ')"
    return $process.Id
}

function Get-BranchRecord([string]$Seed) {
    $paths = Get-BranchPaths $Seed
    $live = Get-ForestProcess $Seed
    $basic = Test-BranchJson $Seed $paths.Json
    $priorStatus = Get-Json $StatusJson
    $priorBranch = if($priorStatus) { @($priorStatus.branches | Where-Object {$_.seed -eq $Seed}) | Select-Object -First 1 } else { $null }
    $verification = $null
    $state = 'queued'
    $reason = $null
    if ($live) {
        $state = 'running'
        $reason = 'live process'
    } elseif ($basic.Valid) {
        $verification = Invoke-Verification $Seed $paths
        $state = if ($verification.Full) {'verified'} else {'verification_failed'}
        $reason = $verification.Reason
    } elseif (Test-Path -LiteralPath $paths.Json) {
        $state = 'failed'
        $reason = $basic.Reason
    } elseif ($priorBranch -and $priorBranch.state -in @('running','failed','verification_failed')) {
        $state = 'failed'
        $reason = 'previous live process vanished without a valid completed JSON; automatic restart is disabled'
    }
    [pscustomobject]@{
        seed=$Seed; state=$state; reason=$reason; live=$live; paths=$paths; basic=$basic; verification=$verification
    }
}

function Write-Status([object[]]$Records) {
    $os = Get-CimInstance Win32_OperatingSystem
    $battery = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue
    $rows = foreach($record in $Records) {
        $obj = $record.basic.Object
        [ordered]@{
            seed=$record.seed; state=$record.state; reason=$record.reason
            pid=if($record.live){$record.live.PID}else{$null}
            command=if($record.live){$record.live.CommandLine}else{$null}
            start_time=if($record.live){$record.live.StartTime}else{$null}
            cpu_seconds=if($record.live){$record.live.CPU}else{$null}
            working_set_mb=if($record.live){$record.live.WorkingSetMB}else{$null}
            priority=if($record.live){$record.live.Priority}else{$null}
            node_count=if($obj){$obj.node_count}else{$null}
            prune_counts=if($obj){$obj.prune_counts}else{$null}
            certificate_count=if($obj){@($obj.certificates).Count}else{$null}
            branch_code_sha256=if($obj){$obj.code_sha256}else{$null}
            completed=if($obj){$obj.completed}else{$false}
            incidence_verified=if($record.verification){$record.verification.Incidence}else{$false}
            dp_replay_verified=if($record.verification){$record.verification.Full}else{$false}
            last_heartbeat_at=if($record.live){Timestamp}else{$null}
            checkpoint_supported=$false
            resume_command=("& '"+$Python+"' work\\superperm_port_lift.py enumerate-forest-covers --seed "+$record.seed+" --node-limit 0 --output outputs\\"+$record.paths.Stem+".json")
            output_json=$record.paths.Json; stdout_log=$record.paths.Stdout; stderr_log=$record.paths.Stderr
            last_stdout=Get-LastLines $record.paths.Stdout; last_stderr=Get-LastLines $record.paths.Stderr
        }
    }
    $status = [ordered]@{
        updated_at=Timestamp; runner_sha256=$RunnerSha; runner=$PSCommandPath
        max_concurrent=$MaxConcurrent; poll_seconds=$PollSeconds
        machine=[ordered]@{logical_processors=(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum; physical_memory_gb=[math]::Round($os.TotalVisibleMemorySize/1MB,1); free_memory_gb=[math]::Round($os.FreePhysicalMemory/1MB,1); battery_present=[bool]$battery; battery_status=if($battery){$battery.BatteryStatus}else{$null}; charge_percent=if($battery){$battery.EstimatedChargeRemaining}else{$null}; ac_online=if($battery){$battery.BatteryStatus -in 2,6,7,8,9,11}else{$null}; sleep_prevention='ES_SYSTEM_REQUIRED only; display is not held awake'}
        branches=$rows
        final_merge_permitted=(@($rows | Where-Object {$_.state -ne 'verified'}).Count -eq 0)
    }
    Write-AtomicJson $status $StatusJson
    $lines = @('# Forest overnight status', '', "Updated: $($status.updated_at)", "Runner SHA-256: $RunnerSha", '', '| seed | state | PID | CPU s | working set MB | nodes | certificates | incidence | DP replay |', '|---|---|---:|---:|---:|---:|---:|---|---|')
    $pipe = [string][char]124
    foreach($row in $rows) {
        $lines += ($pipe+' '+$row.seed+' '+$pipe+' '+$row.state+' '+$pipe+' '+$row.pid+' '+$pipe+' '+$row.cpu_seconds+' '+$pipe+' '+$row.working_set_mb+' '+$pipe+' '+$row.node_count+' '+$pipe+' '+$row.certificate_count+' '+$pipe+' '+$row.incidence_verified+' '+$pipe+' '+$row.dp_replay_verified+' '+$pipe)
    }
    $lines += '', "Final merge permitted: **$($status.final_merge_permitted)**", '', 'A running branch has no safe checkpoint/resume artifact in the current enumerator; its heartbeat records CPU/memory/time only.  A process that exits without `completed: true` is recorded as failed and is not automatically restarted.', '', 'The machine-readable JSON contains the exact restart command for every branch.'
    $lines | Set-Content -LiteralPath $StatusMd -Encoding utf8
}

function Try-FinalMerge([object[]]$Records) {
    if (@($Records | Where-Object {$_.state -ne 'verified'}).Count -ne 0) { return }
    $target = Join-Path $Outputs 'forest_all_classes.json'
    if (-not (Test-Path -LiteralPath $target)) {
        $inputs = foreach($record in $Records) { "outputs\$($record.paths.Stem).json" }
        $stdout = Join-Path $Outputs 'forest_merge.stdout.log'; $stderr = Join-Path $Outputs 'forest_merge.stderr.log'
        $mergeArgs = @('work\superperm_port_lift.py','merge-forest-certificates')
        $mergeArgs += $inputs
        $mergeArgs += @('--output','outputs\forest_all_classes.json')
        $exit = Invoke-Logged -CommandArguments $mergeArgs -Stdout $stdout -Stderr $stderr
        if ($exit -ne 0) { Write-RunnerLog "final merge failed with exit $exit"; return }
        Write-RunnerLog "final merge completed"
    }
    $incidencePath = Join-Path $Outputs 'forest_all_classes.incidence_verified.json'
    $fullPath = Join-Path $Outputs 'forest_all_classes.fully_verified.json'
    $verifyOut = Join-Path $Outputs 'forest_all_classes.verify.stdout.log'
    $verifyErr = Join-Path $Outputs 'forest_all_classes.verify.stderr.log'
    if (-not (Test-Path -LiteralPath $incidencePath)) {
        $exit = Invoke-Logged -CommandArguments @($Verifier,$target,'--skip-dp-replay','--output',$incidencePath) -Stdout $verifyOut -Stderr $verifyErr
        if ($exit -ne 0) { Write-RunnerLog "merged incidence verification failed with exit $exit"; return }
    }
    if (-not (Test-Path -LiteralPath $fullPath)) {
        $exit = Invoke-Logged -CommandArguments @($Verifier,$target,'--output',$fullPath) -Stdout $verifyOut -Stderr $verifyErr
        if ($exit -ne 0) { Write-RunnerLog "merged DP replay failed with exit $exit"; return }
    }
    $merged = Get-Json $target
    $sourceRaw = ($Records | ForEach-Object {@($_.basic.Object.certificates).Count} | Measure-Object -Sum).Sum
    $certs = @($merged.certificates)
    $componentHistogram = @{}
    $cycleHistogram = @{}
    $liftHistogram = @{'H0_complete'=0;'H1_complete'=0;'H2_complete'=0;'H3_complete'=0}
    $h3Max = @(); $h3FirstZero = @(); $h3Unreachable = @()
    foreach($cert in $certs) {
        $componentKey = ((@($cert.collision_forest.component_partition) | ForEach-Object {@($_).Count} | Sort-Object) -join '+')
        if(-not $componentHistogram.ContainsKey($componentKey)){$componentHistogram[$componentKey]=0}; $componentHistogram[$componentKey]++
        $cycleKey = ((@($cert.f_cycle_decomposition.cycle_lengths) | Sort-Object) -join '+')
        if(-not $cycleHistogram.ContainsKey($cycleKey)){$cycleHistogram[$cycleKey]=0}; $cycleHistogram[$cycleKey]++
        foreach($entry in @($cert.port_lift_H_0_to_3)) { if($entry.complete_lift_exists){$liftHistogram['H'+$entry.heavy_budget+'_complete']++} }
        $h3 = @($cert.port_lift_H_0_to_3 | Where-Object {$_.heavy_budget -eq 3})[0].exact_reachability
        $h3Max += [int]$h3.max_cycles_reached; $h3Unreachable += (20-[int]$h3.max_cycles_reached)
        $zero = @($h3.layer_state_counts | ForEach-Object -Begin {$index=0} -Process {$index++; if($_ -eq 0){$index}} | Where-Object {$_}) | Select-Object -First 1
        $h3FirstZero += if($zero){$zero}else{0}
    }
    $statistics = [ordered]@{
        generated_at=Timestamp; runner_sha256=$RunnerSha; merged_code_sha256=$merged.code_sha256
        total_raw_leaf_count=$sourceRaw; total_canonical_class_count=@($certs).Count
        exact_partition_plus_one_class_count=@($certs | Where-Object {$_.cover_kind -eq 'exact_partition_plus_one'}).Count
        nonpartition_class_count=@($certs | Where-Object {$_.cover_kind -eq 'nondecomposable_first_full_at_depth_25'}).Count
        collision_component_size_partition_histogram=$componentHistogram
        f_cycle_length_multiset_histogram=$cycleHistogram
        complete_lift_histogram=$liftHistogram
        h3_max_reachable_cycle_histogram=($h3Max | Group-Object | ForEach-Object {[ordered]@{value=[int]$_.Name;count=$_.Count}})
        h3_first_empty_layer_histogram=($h3FirstZero | Group-Object | ForEach-Object {[ordered]@{value=[int]$_.Name;count=$_.Count}})
        h3_unreachable_cycle_lower_bound_histogram=($h3Unreachable | Group-Object | ForEach-Object {[ordered]@{value=[int]$_.Name;count=$_.Count}})
        exhaustive_port_lift_failure_H_le_3=(@($liftHistogram.Values | Where-Object {$_ -ne 0}).Count -eq 0)
    }
    Write-AtomicJson $statistics (Join-Path $Outputs 'forest_all_statistics.json')
    Write-RunnerLog "merged verification and statistics completed"
}

Write-RunnerLog "runner started; SHA=$RunnerSha; maxConcurrent=$MaxConcurrent"
try {
    while ($true) {
        $records = @($Seeds | ForEach-Object { Get-BranchRecord $_ })
        $running = @($records | Where-Object {$_.state -eq 'running'}).Count
        $queued = @($records | Where-Object {$_.state -eq 'queued'} | Sort-Object {[array]::IndexOf($Seeds, $_.seed)})
        while ($running -lt $MaxConcurrent -and $queued.Count -gt 0) {
            $next = $queued[0]
            Start-ForestBranch $next.seed $next.paths | Out-Null
            $running += 1
            $queued = @($queued | Select-Object -Skip 1)
        }
        $records = @($Seeds | ForEach-Object { Get-BranchRecord $_ })
        Write-Status $records
        Try-FinalMerge $records
        if ($Once) { break }
        [void][ForestPower]::SetThreadExecutionState($KeepSystemAwake)
        Start-Sleep -Seconds $PollSeconds
    }
} finally {
    [void][ForestPower]::SetThreadExecutionState($ES_CONTINUOUS)
    Write-RunnerLog "runner stopped"
}
