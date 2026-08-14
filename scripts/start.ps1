param(
    [switch]$SkipInstall,
    [string]$EnvFile,
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "python")) {
    throw "python 명령을 찾을 수 없습니다."
}

if (-not (Test-CommandExists "npm")) {
    throw "npm 명령을 찾을 수 없습니다."
}

$NpmCommand = (Get-Command "npm.cmd" -ErrorAction SilentlyContinue)?.Source
if (-not $NpmCommand) {
    $NpmCommand = (Get-Command "npm" -ErrorAction Stop).Source
}

if ($EnvFile) {
    if (-not (Test-Path $EnvFile)) {
        throw "지정한 .env 파일을 찾을 수 없습니다: $EnvFile"
    }
    $env:NEIS_ENV_FILE = (Resolve-Path $EnvFile).Path
}

if (-not $env:VITE_API_BASE_URL) {
    $env:VITE_API_BASE_URL = "http://${BackendHost}:${BackendPort}"
}

if (-not $env:BACKEND_ALLOWED_ORIGINS) {
    $env:BACKEND_ALLOWED_ORIGINS = "http://localhost:${FrontendPort},http://127.0.0.1:${FrontendPort}"
}

if (-not $SkipInstall) {
    Push-Location $BackendDir
    python -m pip install -e ".[dev]"
    Pop-Location

    Push-Location $FrontendDir
    if (Test-Path "package-lock.json") {
        npm ci
    } else {
        npm install
    }
    Pop-Location
}

$BackendArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--reload",
    "--app-dir", "src",
    "--host", $BackendHost,
    "--port", "$BackendPort"
)

$FrontendArgs = @(
    "run", "dev", "--",
    "--host", $FrontendHost,
    "--port", "$FrontendPort"
)

$BackendProcess = Start-Process -FilePath "python" -ArgumentList $BackendArgs -WorkingDirectory $BackendDir -PassThru -NoNewWindow
$FrontendProcess = Start-Process -FilePath $NpmCommand -ArgumentList $FrontendArgs -WorkingDirectory $FrontendDir -PassThru -NoNewWindow

try {
    Write-Host "Backend:  http://${BackendHost}:${BackendPort}"
    Write-Host "Frontend: http://${FrontendHost}:${FrontendPort}"
    Write-Host "종료하려면 Ctrl+C를 누르세요."

    while (-not $BackendProcess.HasExited -and -not $FrontendProcess.HasExited) {
        Start-Sleep -Seconds 1
    }

    if ($BackendProcess.HasExited) {
        throw "백엔드 프로세스가 종료되었습니다. ExitCode=$($BackendProcess.ExitCode)"
    }

    if ($FrontendProcess.HasExited) {
        throw "프론트엔드 프로세스가 종료되었습니다. ExitCode=$($FrontendProcess.ExitCode)"
    }
}
finally {
    foreach ($Process in @($FrontendProcess, $BackendProcess)) {
        if ($Process -and -not $Process.HasExited) {
            Stop-Process -Id $Process.Id
        }
    }
}
