$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host '[1/1] preflight checks'
python -X utf8 scripts\preflight_check.py --ollama-host http://127.0.0.1:11434
