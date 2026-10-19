$ErrorActionPreference = 'Stop'
$labPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $labPython)) {
    throw 'Local environment missing. Follow docs/document-lab.md to install lab_requirements.txt.'
}
$labUrl = 'http://127.0.0.1:8910/'
try {
    $health = Invoke-WebRequest -Uri ($labUrl + 'api/summary') -UseBasicParsing -TimeoutSec 5
    $alreadyRunning = ($health.StatusCode -eq 200)
} catch { $alreadyRunning = $false }
if (-not $alreadyRunning) {
    $labSource = Join-Path $PSScriptRoot 'document_lab.py'
    Start-Process -FilePath $labPython -ArgumentList @(('"' + $labSource + '"'), 'serve', '--port', '8910') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 500
        try { Invoke-WebRequest -Uri ($labUrl + 'api/summary') -UseBasicParsing -TimeoutSec 2 | Out-Null; break } catch { }
    }
}
Start-Process $labUrl
