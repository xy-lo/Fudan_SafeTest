$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectDir = $PSScriptRoot
Set-Location $projectDir

$pythonExecutable = $null
$pythonPrefix = @()

if ($env:SAFETEST_PYTHON) {
    $pythonExecutable = $env:SAFETEST_PYTHON
}
elseif (Get-Command "py.exe" -ErrorAction SilentlyContinue) {
    $pythonExecutable = "py.exe"
    $pythonPrefix = @("-3")
}
elseif (Get-Command "python3.exe" -ErrorAction SilentlyContinue) {
    $pythonExecutable = "python3.exe"
}
elseif (Get-Command "python.exe" -ErrorAction SilentlyContinue) {
    $pythonExecutable = "python.exe"
}
else {
    throw "未找到 Python 3.9+。请从 https://www.python.org/downloads/ 安装后重试。"
}

function Invoke-BootstrapPython {
    param([string[]]$Arguments)
    $allArguments = @($script:pythonPrefix) + $Arguments
    & $script:pythonExecutable @allArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python 命令执行失败，退出码：$LASTEXITCODE"
    }
}

Invoke-BootstrapPython @(
    "-c",
    "import sys; raise SystemExit(sys.version_info < (3, 9))"
)

$venvDir = Join-Path $projectDir ".venv-windows"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "首次运行：正在创建独立 Python 环境……"
    Invoke-BootstrapPython @("-m", "venv", $venvDir)
}

$requirementsPath = Join-Path $projectDir "requirements.txt"
$markerPath = Join-Path $venvDir ".requirements.sha256"
$requirementsHash = (Get-FileHash -Algorithm SHA256 $requirementsPath).Hash.ToLowerInvariant()
$installedHash = ""
if (Test-Path $markerPath) {
    $installedHash = (Get-Content -Raw $markerPath).Trim()
}

if ($requirementsHash -ne $installedHash) {
    Write-Host "正在安装/更新依赖（仅首次或依赖变化时执行）……"
    & $venvPython -m pip install --upgrade "pip<26"
    if ($LASTEXITCODE -ne 0) {
        throw "pip 更新失败，退出码：$LASTEXITCODE"
    }
    & $venvPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "依赖安装失败，退出码：$LASTEXITCODE"
    }
    [System.IO.File]::WriteAllText($markerPath, $requirementsHash)
}

if (-not (Test-Path "environment.py")) {
    Copy-Item "environment_template.py" "environment.py"
}

& $venvPython "main.py" @args
exit $LASTEXITCODE
