$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Url = "http://127.0.0.1:8765"
$LogDir = Join-Path $AppRoot "logs"
$BackendLog = Join-Path $LogDir "desktop_backend.log"
$BackendErr = Join-Path $LogDir "desktop_backend_error.log"
$PythonCandidates = @(
  "python",
  "C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-AppReady {
  try {
    $response = Invoke-WebRequest -Uri "$Url/api/project" -UseBasicParsing -TimeoutSec 1
    return ($response.StatusCode -eq 200)
  } catch {
    return $false
  }
}

if (-not (Test-AppReady)) {
  $python = $null
  foreach ($candidate in $PythonCandidates) {
    try {
      $cmd = Get-Command $candidate -ErrorAction Stop
      $python = $cmd.Source
      break
    } catch {}
  }
  if (-not $python) {
    throw "Python was not found. Install Python or edit SlopeGuard_AI_Desktop.ps1 and set the Python path."
  }
  "Starting SlopeGuard AI backend with $python at $(Get-Date)" | Out-File -FilePath $BackendLog -Encoding utf8
  Start-Process -FilePath $python -ArgumentList "backend\server.py" -WorkingDirectory $AppRoot -WindowStyle Hidden -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErr
}

for ($i = 0; $i -lt 60; $i++) {
  if (Test-AppReady) { break }
  Start-Sleep -Milliseconds 500
}

if (-not (Test-AppReady)) {
  Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'SlopeGuard AI backend did not start. Check these logs:'; Write-Host '$BackendLog'; Write-Host '$BackendErr'; if (Test-Path '$BackendLog') { Get-Content '$BackendLog' }; if (Test-Path '$BackendErr') { Get-Content '$BackendErr' }"
  throw "SlopeGuard AI backend did not start. See $BackendLog and $BackendErr"
}

$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) {
  $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
}

$chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"

if (Test-Path $edge) {
  Start-Process -FilePath $edge -ArgumentList "--app=$Url", "--window-size=1400,900", "--user-data-dir=$AppRoot\desktop_profile"
} elseif (Test-Path $chrome) {
  Start-Process -FilePath $chrome -ArgumentList "--app=$Url", "--window-size=1400,900", "--user-data-dir=$AppRoot\desktop_profile"
} else {
  Start-Process $Url
}
