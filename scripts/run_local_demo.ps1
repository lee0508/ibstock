$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $projectRoot 'backend'

Set-Location $projectRoot

Write-Host '[1/4] preprocess'
python -X utf8 scripts\preprocess.py

Write-Host '[2/4] init_db'
python -X utf8 scripts\init_db.py

Write-Host '[3/4] build_index'
python -X utf8 scripts\build_index.py

Write-Host '[4/4] start web server'
Write-Host 'Open: http://127.0.0.1:8081/frontend/index.html'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8081
