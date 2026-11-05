param([switch]$HeadlessCheck,[switch]$InteractiveCheck,[switch]$FeedCheck,[switch]$StudioCheck,[switch]$AskPassword,[switch]$VisualAudit,[switch]$VisualCheck,[switch]$DownloadCheck)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
$previousDemoPassword=[Environment]::GetEnvironmentVariable('SHIELDVI_DEMO_PASSWORD','Process')
try {
  $socialPython=Join-Path $projectRoot 'services/social-api/.venv/Scripts/python.exe'
  $runner=Join-Path $projectRoot 'reports/task_rollout_20261104/run_browser_actual.py'
  if (-not (Test-Path -LiteralPath $socialPython)) { throw 'Social Python environment is missing.' }
  if ($AskPassword) {
    $secureDemoPassword=Read-Host 'Demo password (12-128 characters; used for all demo accounts)' -AsSecureString
    $demoPasswordBuffer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDemoPassword)
    try { $env:SHIELDVI_DEMO_PASSWORD=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($demoPasswordBuffer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($demoPasswordBuffer); $secureDemoPassword.Dispose() }
  }
  if ($DownloadCheck) { & $socialPython -X utf8 $runner --native-download-check }
  elseif ($VisualAudit) { & $socialPython -X utf8 $runner --visual-audit }
  elseif ($VisualCheck) { & $socialPython -X utf8 $runner --visual-check }
  elseif ($StudioCheck) { & $socialPython -X utf8 $runner --studio-check }
  elseif ($FeedCheck) { & $socialPython -X utf8 $runner --feed-check }
  elseif ($InteractiveCheck) { & $socialPython -X utf8 $runner --interactive-check }
  elseif ($HeadlessCheck) { & $socialPython -X utf8 $runner }
  else { & $socialPython -X utf8 $runner --interactive }
  if ($LASTEXITCODE -ne 0) { throw "Demo exited with code $LASTEXITCODE; inspect reports/task_rollout_20261104/T043 logs." }
} finally {
  if ($AskPassword) { [Environment]::SetEnvironmentVariable('SHIELDVI_DEMO_PASSWORD',$previousDemoPassword,'Process') }
  Pop-Location
}
