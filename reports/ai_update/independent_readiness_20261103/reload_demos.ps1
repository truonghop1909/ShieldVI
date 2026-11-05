$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$prior=Get-Content -LiteralPath (Join-Path $taskRoot 'reports/ai_update/camping_context_20261103/demo_after_server_state.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$statePath=Join-Path $PSScriptRoot 'demo_server_state.json'
if(Test-Path -LiteralPath $statePath){throw 'Reload already recorded; do not overwrite'}
foreach($item in $prior){
    $owned=Get-CimInstance Win32_Process -Filter ('ProcessId = '+$item.server_process_id)
    if(-not $owned -or $owned.ParentProcessId -ne $item.process_id -or -not $owned.CommandLine.Contains((Join-Path $taskRoot 'services/moderation-ai').Replace('/','\')) -or $owned.CommandLine -notmatch ('--port\s+'+$item.port+'(?:\s|$)')){throw 'Process ownership mismatch; no process stopped'}
    if((Get-FileHash -LiteralPath (Join-Path $item.model_path 'model.safetensors') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.model_sha256){throw 'Checkpoint integrity mismatch'}
}
$env:STORE_SUMMARIES='0';$env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1';$env:OMP_NUM_THREADS='4';$env:MKL_NUM_THREADS='4';$env:PYTHONDONTWRITEBYTECODE='1'
$started=@()
foreach($item in $prior){
    Stop-Process -Id $item.server_process_id -Force
    $env:MODEL_PATH=$item.model_path
    $stdout=Join-Path $PSScriptRoot ($item.name+'.stdout.log');$stderr=Join-Path $PSScriptRoot ($item.name+'.stderr.log')
    $process=Start-Process -FilePath (Join-Path $taskRoot '.venv/Scripts/python.exe') -ArgumentList @('-m','uvicorn','app.main:app','--app-dir',(Join-Path $taskRoot 'services/moderation-ai'),'--host','127.0.0.1','--port',([string]$item.port),'--no-proxy-headers') -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $started += [pscustomobject]@{name=$item.name;port=$item.port;process_id=$process.Id;model_path=$item.model_path;model_sha256=$item.model_sha256;approved_default=$item.approved_default;status='STARTING';stdout=$stdout;stderr=$stderr}
    $started | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8
}
$started | Select-Object name,port,process_id,status | ConvertTo-Json -Compress
