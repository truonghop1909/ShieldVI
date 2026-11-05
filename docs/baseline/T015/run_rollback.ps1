# Fast code rollback using preserved source; does not overwrite/migrate any file.
# Stop the current AI server first. Keep worker/AI shared token in environment.
$rollbackRepo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../../ShieldVI_V3_Hybrid_Review')).Path
$rollbackSource = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'rollback-source')).Path
$rollbackPython = Join-Path $rollbackRepo '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $rollbackPython)) { throw 'AI Python environment is missing' }
if (-not $env:MODEL_PATH) {
    $env:MODEL_PATH = (Resolve-Path -LiteralPath (Join-Path $rollbackRepo 'models/visobert_head_refined')).Path
}
if (-not [IO.Path]::IsPathRooted($env:MODEL_PATH)) {
    $env:MODEL_PATH = [IO.Path]::GetFullPath((Join-Path $rollbackRepo $env:MODEL_PATH))
}
if (-not $env:REVIEW_DB_PATH) { $env:REVIEW_DB_PATH = Join-Path $rollbackRepo 'shieldvi_reviews.sqlite3' }
if (-not $env:DB_PATH) { $env:DB_PATH = Join-Path $rollbackRepo 'moderation_summaries.sqlite3' }
Push-Location -LiteralPath $rollbackRepo
try {
    & $rollbackPython -m uvicorn app.main:app --app-dir $rollbackSource --host 127.0.0.1 --port 8000 --no-proxy-headers
} finally {
    Pop-Location
}
