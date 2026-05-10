$ErrorActionPreference = 'Stop'

$ollamaPath = 'C:\Users\leedh\AppData\Local\Programs\Ollama\ollama.exe'

if (-not (Test-Path $ollamaPath)) {
    throw "Ollama executable not found: $ollamaPath"
}

Write-Host 'Starting Ollama local server on http://127.0.0.1:11434'
& $ollamaPath serve
