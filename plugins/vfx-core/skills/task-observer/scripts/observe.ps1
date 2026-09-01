# task-observer helper - PowerShell port of observe.sh. Same subcommands, same
# output lines, so a skill instruction written for one works for the other.
#
#   observe.ps1 status [-Json]   one-screen state of the observation log
#   observe.ps1 init             create the workspace layout (only when status reports MISSING)
#   observe.ps1 scan             print the frontmatter header of every active observation
#   observe.ps1 next-id          allocate the next observation id (updates archive/.id-floor)
#   observe.ps1 archive          move resolved observations (resolved before today) to archive/
#
# -Json wraps the status lines as a Qwen Code SessionStart hook response
# ({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":...}}).
#
# Runs under Windows PowerShell 5.1 and pwsh 7 (no ternary, no ??, no -Depth
# assumptions beyond 5.0). ASCII only. Writes files UTF-8 WITHOUT BOM.
#
# Workspace resolution, in order:
#   1. TASK_OBSERVER_WS environment variable; the token {user} becomes the
#      current username, so a team can share one value such as
#      <team share>/skill-observations/{user}.
#   2. Default: $HOME\.claude\skill-observations
# Never the current working directory.
#
# Fail-soft rule: if the PARENT of the workspace does not exist (a share that
# is not mounted) the helper reports UNREACHABLE and exits 0 without creating
# anything. A second log is never created somewhere else.

[CmdletBinding()]
param(
    [Parameter(Position = 0)][string]$Command = "status",
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$me = $MyInvocation.MyCommand.Path
$user = if ($env:USERNAME) { $env:USERNAME } elseif ($env:USER) { $env:USER } else { "user" }
$ws = if ($env:TASK_OBSERVER_WS) { $env:TASK_OBSERVER_WS } else { Join-Path $HOME ".claude\skill-observations" }
$ws = $ws.Replace("{user}", $user).TrimEnd("/", "\")
$log = Join-Path $ws "observation-log"
$arch = Join-Path $log "archive"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-NoBom([string]$path, [string]$text) {
    [System.IO.File]::WriteAllText($path, $text, $utf8)
}

# Frontmatter block of one file (between the first two --- lines), as one string.
function Get-Header([string]$path) {
    $lines = [System.IO.File]::ReadAllLines($path)
    if ($lines.Count -eq 0 -or $lines[0].TrimEnd() -ne "---") { return "" }
    $out = New-Object System.Collections.Generic.List[string]
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].TrimEnd() -eq "---") { break }
        $out.Add($lines[$i])
    }
    return ($out -join "`n")
}

# Scalar field value, brackets and trailing comments stripped.
function Get-Field([string]$header, [string]$key) {
    foreach ($l in ($header -split "`n")) {
        if ($l -match ("^" + [regex]::Escape($key) + ":\s*(.*)$")) {
            $v = $Matches[1]
            $v = $v -replace '^\[', '' -replace '\]$', '' -replace '#.*$', ''
            return $v.Trim()
        }
    }
    return ""
}

function Test-SkillExists([string]$n) {
    if (Test-Path (Join-Path ".claude\skills" $n)) { return $true }
    if (Test-Path (Join-Path $HOME ".claude\skills\$n")) { return $true }
    $plug = Join-Path $HOME ".claude\plugins"
    if (Test-Path $plug) {
        $hit = Get-ChildItem $plug -Directory -Recurse -Depth 7 -Filter $n -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "skills" } | Select-Object -First 1
        if ($hit) { return $true }
    }
    return $false
}

function Test-Reachable { return (Test-Path (Split-Path -Parent $ws)) }

function Get-ActiveFiles {
    if (-not (Test-Path $log)) { return @() }
    return @(Get-ChildItem $log -File -Filter "*.md" | Sort-Object Name)
}

function Emit([string[]]$lines, [int]$code) {
    if ($Json) {
        $obj = @{ hookSpecificOutput = @{ hookEventName = "SessionStart"; additionalContext = ($lines -join "`n") } }
        Write-Output ($obj | ConvertTo-Json -Compress -Depth 4)
    } else {
        foreach ($l in $lines) { Write-Output $l }
    }
    exit $code
}

switch ($Command) {

    "status" {
        $out = New-Object System.Collections.Generic.List[string]
        $out.Add("task-observer: helper $me")
        if (-not (Test-Reachable)) {
            $out.Add("task-observer: workspace UNREACHABLE - parent of $ws does not exist (share not mounted?). Skip logging this session; do NOT create a log elsewhere.")
            Emit $out 0
        }
        if (-not (Test-Path $log)) {
            $out.Add("task-observer: workspace MISSING at $ws - run '$me init' once, then re-run status.")
            Emit $out 0
        }
        $files = Get-ActiveFiles
        $n = $files.Count; $parsed = 0; $open = 0; $parked = 0; $nosib = 0
        $targets = New-Object System.Collections.Generic.List[string]
        foreach ($f in $files) {
            $hdr = Get-Header $f.FullName
            if (-not $hdr) { continue }
            $parsed++
            $st = Get-Field $hdr "status"; if (-not $st) { $st = "open" }
            if ($st -eq "open") {
                $open++
                if (-not (Get-Field $hdr "siblings_checked")) { $nosib++ }
                foreach ($s in ((Get-Field $hdr "skill") -split ",")) { if ($s.Trim()) { $targets.Add($s.Trim()) } }
            } elseif ($st -eq "parked") { $parked++ }
        }
        if ($n -gt 0 -and $parsed -eq 0) {
            $out.Add("task-observer: SCAN BROKEN - $n files present, 0 headers parsed. Fix before logging.")
            Emit $out 1
        }
        $lastPath = Join-Path $ws "last-review-date.txt"
        $last = if (Test-Path $lastPath) { (Get-Content $lastPath -Raw).Trim() } else { "missing" }
        $ageDays = $null
        if ($last -ne "never" -and $last -ne "missing") {
            try { $ageDays = [int]((Get-Date).Date - [datetime]::ParseExact($last, "yyyy-MM-dd", $null)).TotalDays } catch { $ageDays = $null }
        }
        $updRoot = Join-Path $ws "skill-updates"
        $staged = if (Test-Path $updRoot) { @(Get-ChildItem $updRoot -Directory).Count } else { 0 }
        $missing = @()
        foreach ($s in ($targets | Sort-Object -Unique)) { if (-not (Test-SkillExists $s)) { $missing += $s } }
        $ageTxt = if ($null -ne $ageDays) { " (${ageDays}d ago)" } else { "" }
        $out.Add("task-observer: workspace $ws")
        $out.Add("task-observer: $open open, $parked parked, $n active files; last review: $last$ageTxt; staged update dirs: $staged")
        if ($nosib -gt 0) { $out.Add("task-observer: $nosib open observation(s) logged WITHOUT a sibling check") }
        if ($missing.Count -gt 0) { $out.Add("task-observer: open observations target skills that do not resolve here: " + ($missing -join " ")) }
        if ($open -gt 0) {
            if ($last -eq "never" -or $last -eq "missing") {
                $out.Add("task-observer: backlog has NEVER been reviewed - offer the review in one line, do not gate the task on it")
            } elseif ($null -ne $ageDays -and $ageDays -ge 7) {
                $out.Add("task-observer: last review is 7+ days old with open observations - offer the review in one line")
            }
        }
        Emit $out 0
    }

    "init" {
        if (-not (Test-Reachable)) {
            Write-Output "task-observer: cannot init - parent of $ws does not exist. Mount the share or fix TASK_OBSERVER_WS."; exit 1
        }
        if (Test-Path $log) { Write-Output "task-observer: workspace already exists at $ws"; exit 0 }
        New-Item -ItemType Directory -Force -Path $arch | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $ws "skill-updates") | Out-Null
        $floor = Join-Path $arch ".id-floor"
        if (-not (Test-Path $floor)) { Write-NoBom $floor "0`n" }
        $lastPath = Join-Path $ws "last-review-date.txt"
        if (-not (Test-Path $lastPath)) { Write-NoBom $lastPath "never`n" }
        $chk = Join-Path $ws "checkpoints.log"
        if (-not (Test-Path $chk)) { Write-NoBom $chk "" }
        $ccp = Join-Path $ws "cross-cutting-principles.md"
        if (-not (Test-Path $ccp)) {
            Write-NoBom $ccp (@(
                "# Cross-Cutting Principles", "",
                "Principles that apply to all skills. Read as a mandatory checklist during any",
                "skill creation, regeneration or staged update. Added by reviews.", "",
                "---", "", "## Active Principles", "",
                "(none yet - a review adds entries in the form below)", "",
                "### N. Principle title",
                "**Added:** YYYY-MM-DD (source)",
                "**Applies to:** all skills | all public skills | skills that ...",
                "**Requirement:** what it requires",
                "**Propagation:** immediate | opportunistic",
                "**Status:** active", ""
            ) -join "`n")
        }
        $fam = Join-Path $ws "skill-families.md"
        if (-not (Test-Path $fam)) {
            Write-NoBom $fam (@(
                "# Skill families", "",
                "Families of sibling skills (same methodology for different tools, same",
                "structure for different subjects). The sibling check resolves every",
                "observation target against this file. Add a family the first time an",
                "observation would apply to more than one member.", "",
                "## family-name",
                "**Members:** skill-a, skill-b",
                "**Coherence model:** synced-duplicates | shared-core",
                "**Shared:** what every member should carry",
                "**Member-specific:** what legitimately differs, and why", ""
            ) -join "`n")
        }
        foreach ($p in @($floor, $lastPath, $ccp, $fam)) {
            if (-not (Test-Path $p) -or (Get-Item $p).Length -eq 0) { Write-Output "task-observer: init INCOMPLETE - $p missing or empty"; exit 1 }
        }
        Write-Output "task-observer: workspace created at $ws"; exit 0
    }

    "scan" {
        if (-not (Test-Reachable) -or -not (Test-Path $log)) { Write-Output "task-observer: workspace unavailable at $ws"; exit 1 }
        $files = Get-ActiveFiles; $n = $files.Count; $parsed = 0
        foreach ($f in $files) {
            $hdr = Get-Header $f.FullName
            if ($hdr) { $parsed++ }
            Write-Output $f.Name; Write-Output $hdr; Write-Output "---"
        }
        if ($n -gt 0 -and $parsed -eq 0) { Write-Output "SCAN COMMAND BROKEN - $n files present, 0 headers parsed"; exit 1 }
        Write-Output "scanned $parsed of $n files"; exit 0
    }

    "next-id" {
        if (-not (Test-Reachable) -or -not (Test-Path $arch)) {
            Write-Output "ID COMMAND BROKEN - workspace unavailable at $ws (run init, or the share is unreachable)"; exit 1
        }
        $nums = @()
        foreach ($d in @($log, $arch)) {
            foreach ($it in (Get-ChildItem $d -ErrorAction SilentlyContinue)) {
                if ($it.Name -match '^(\d+)') { $nums += [int]$Matches[1] }
            }
        }
        $floor = Join-Path $arch ".id-floor"
        if (Test-Path $floor) {
            $fv = (Get-Content $floor -Raw).Trim()
            if ($fv -match '^\d+$') { $nums += [int]$fv }
        }
        $hi = 0
        if ($nums.Count -gt 0) { $hi = ($nums | Measure-Object -Maximum).Maximum }
        if ($hi -eq 0 -and (Get-ActiveFiles).Count -gt 0) {
            Write-Output "ID COMMAND BROKEN - log is non-empty but no ids extracted"; exit 1
        }
        $next = [int]$hi + 1
        Write-NoBom $floor "$next`n"
        Write-Output ("{0:D4}" -f $next); exit 0
    }

    "archive" {
        if (-not (Test-Reachable) -or -not (Test-Path $log)) { Write-Output "task-observer: workspace unavailable at $ws"; exit 1 }
        New-Item -ItemType Directory -Force -Path $arch | Out-Null
        $today = (Get-Date).ToString("yyyy-MM-dd"); $moved = 0
        foreach ($f in (Get-ActiveFiles)) {
            $hdr = Get-Header $f.FullName
            $st = Get-Field $hdr "status"
            if ($st -notin @("actioned", "declined", "superseded")) { continue }
            $rd = Get-Field $hdr "resolved"
            if (-not $rd) {
                Write-Output "no resolved: date on $($f.Name) - set it to today ($today) and archive tomorrow"; continue
            }
            # ISO dates compare ordinally; archive only if strictly before today.
            if ([string]::CompareOrdinal($rd, $today) -lt 0) {
                Move-Item $f.FullName (Join-Path $arch $f.Name)
                $moved++; Write-Output "archived $($f.Name)"
            }
        }
        Write-Output "archived $moved file(s)"; exit 0
    }

    default { Write-Output "usage: observe.ps1 {status|init|scan|next-id|archive} [-Json]"; exit 2 }
}
