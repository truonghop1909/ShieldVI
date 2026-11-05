$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$artifactRoot=(Resolve-Path (Join-Path $projectRoot 'reports/task_rollout_20261104')).Path
$pointer=Join-Path $artifactRoot 'ACTIVE_DEMO.json'
if (-not (Test-Path -LiteralPath $pointer)) { Write-Output 'No interactive demo is registered.'; exit 0 }
$record=Get-Content -LiteralPath $pointer -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $record.running) { Write-Output 'Interactive demo already stopped.'; exit 0 }
$demoRoot=(Resolve-Path -LiteralPath $record.root).Path
if ((Split-Path -Parent $demoRoot) -ne $artifactRoot -or (Split-Path -Leaf $demoRoot) -notmatch '^demo_[a-f0-9]{16}$') { throw 'Refusing a stop path outside the owned demo directory.' }
Set-Content -LiteralPath (Join-Path $demoRoot 'stop.request') -Value 'Operator requested stop; retain data.' -Encoding UTF8
Write-Output 'Stop requested. The owning launcher will stop its processes and retain demo data.'
