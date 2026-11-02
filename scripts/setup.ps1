# One-command setup for this project on Windows. Safe to re-run: every step
# checks first and skips what's already done.
#
#   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -SkipReason
#   powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Test
param(
  [switch] $SkipReason,   # don't install or join Reason Network
  [switch] $Test          # run all test suites at the end
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path', 'User')
}
function Have([string] $cmd) { [bool] (Get-Command $cmd -ErrorAction SilentlyContinue) }
function Step([string] $msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. Tools
foreach ($tool in @(@('git', 'Git.Git'), @('gh', 'GitHub.cli'), @('uv', 'astral-sh.uv'))) {
  if (Have $tool[0]) { Write-Host "    $($tool[0]) found"; continue }
  Step "Installing $($tool[0])"
  winget install --id $tool[1] -e --silent --accept-source-agreements --accept-package-agreements
  Refresh-Path
}

# 2. Python dependencies
Step 'uv sync'
uv sync

# 3. MCP servers for this project (local scope, private to you)
$existing = (cmd /c "claude mcp list 2>nul") -join "`n"
if ($existing -notmatch '(?m)^career-copilot:') {
  Step 'Registering career-copilot (local stdio)'
  cmd /c "claude mcp add career-copilot -- uv run --directory `"$root`" app.py --stdio"
}
if ($existing -notmatch '(?m)^reason:') {
  Step 'Registering reason (remote HTTP; authenticate later via /mcp)'
  cmd /c "claude mcp add --transport http reason https://mcp.reasonmachines.com/mcp"
}

# 4. Reason Network (lets Muse and other agents reach Claude Code here)
if (-not $SkipReason) {
  Refresh-Path
  if (-not (Have 'reason')) {
    Step 'Installing Reason CLI and joining Reason Network (browser sign-in)'
    powershell -c "irm https://reasonmachines.com/network/install.ps1 | iex"
  } else {
    Step 'Reason CLI found; checking network status'
    reason network
  }
}

# 5. Tests
if ($Test) {
  foreach ($t in 'tests/test_knowledge.py', 'tests/test_poc.py', 'tests/test_features.py', 'tests/test_http.py', 'tests/test_soul.py') {
    Step "uv run $t"
    uv run $t
    if ($LASTEXITCODE) { throw "$t failed" }
  }
}

Write-Host ''
Write-Host 'Setup complete. Next: /mcp -> reason -> Authenticate, then start a new Claude Code session.' -ForegroundColor Green
