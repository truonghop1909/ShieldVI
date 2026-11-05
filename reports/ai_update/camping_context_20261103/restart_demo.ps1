$ErrorActionPreference = 'Stop'
$demoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$demoPriorPath = Join-Path $demoRoot 'reports/demo/restart_20261103_164006/server_state.json'
$demoPrior = Get-Content -LiteralPath $demoPriorPath -Raw -Encoding UTF8 | ConvertFrom-Json
$demoNewStatePath = Join-Path $PSScriptRoot 'demo_after_server_state.json'
if (Test-Path -LiteralPath $demoNewStatePath) { throw 'Do not overwrite an already restarted session' }
foreach ($demoItem in $demoPrior) {
    $demoProcess = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $demoItem.server_process_id)
    if (-not $demoProcess -or $demoProcess.ParentProcessId -ne $demoItem.process_id -or
        -not $demoProcess.CommandLine.Contains((Join-Path $demoRoot 'services/moderation-ai').Replace('/','\')) -or
        $demoProcess.CommandLine -notmatch ('--port\s+' + $demoItem.port + '(?:\s|$)')) { throw 'Demo process ownership mismatch; no process stopped' }
    if ((Get-FileHash -LiteralPath (Join-Path $demoItem.model_path 'model.safetensors') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $demoItem.model_sha256) { throw 'Model integrity mismatch' }
}
$demoStatic = Join-Path $demoRoot 'services/moderation-ai/app/static'
$demoBuild = Join-Path $PSScriptRoot 'dashboard_build'
$demoBackup = Join-Path $PSScriptRoot 'before_static'
New-Item -ItemType Directory -Path $demoBackup -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $demoStatic 'index.html') -Destination (Join-Path $demoBackup 'index.html')
# Keep previous hashed assets to support already-open browser tabs. New index last.
foreach ($demoAsset in Get-ChildItem -LiteralPath (Join-Path $demoBuild 'assets') -File) {
    Copy-Item -LiteralPath $demoAsset.FullName -Destination (Join-Path $demoStatic ('assets/' + $demoAsset.Name)) -Force
}
Copy-Item -LiteralPath (Join-Path $demoBuild 'index.html') -Destination (Join-Path $demoStatic 'index.html') -Force
$env:STORE_SUMMARIES = '0'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$demoStarted = @()
foreach ($demoItem in $demoPrior) {
    Stop-Process -Id $demoItem.server_process_id -Force
    $env:MODEL_PATH = $demoItem.model_path
    $demoOut = Join-Path $PSScriptRoot ($demoItem.name + '.stdout.log')
    $demoErr = Join-Path $PSScriptRoot ($demoItem.name + '.stderr.log')
    $demoProcess = Start-Process -FilePath (Join-Path $demoRoot '.venv/Scripts/python.exe') -ArgumentList @('-m','uvicorn','app.main:app','--app-dir',(Join-Path $demoRoot 'services/moderation-ai'),'--host','127.0.0.1','--port',([string]$demoItem.port),'--no-proxy-headers') -WorkingDirectory $demoRoot -WindowStyle Hidden -RedirectStandardOutput $demoOut -RedirectStandardError $demoErr -PassThru
    $demoStarted += [pscustomobject]@{ name = $demoItem.name; port = $demoItem.port; process_id = $demoProcess.Id; model_path = $demoItem.model_path; model_sha256 = $demoItem.model_sha256; approved_default = $demoItem.approved_default; status = 'STARTING'; stdout = $demoOut; stderr = $demoErr }
    $demoStarted | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $demoNewStatePath -Encoding UTF8
}
$demoStarted | Select-Object name,port,process_id,status | ConvertTo-Json -Compress
