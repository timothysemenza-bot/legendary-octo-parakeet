param(
    [ValidateSet("faster-whisper","whisper")]
    [string]$Engine = "faster-whisper"
)

$ErrorActionPreference = "Stop"

function Ensure-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $py) {
        throw "Python is not installed or not on PATH."
    }
    return $py.Source
}

$pythonExe = Ensure-Python

Write-Output ("Using Python: {0}" -f $pythonExe)
& python -m pip --version | Out-Null

Write-Output "Upgrading pip/setuptools/wheel..."
& python -m pip install --upgrade pip setuptools wheel

if ($Engine -eq "faster-whisper") {
    Write-Output "Installing faster-whisper..."
    & python -m pip install --upgrade faster-whisper
    $result = & python -c "import importlib.util; print('ok' if importlib.util.find_spec('faster_whisper') is not None else 'missing')"
    if ($result -notcontains "ok") {
        throw "faster-whisper install verification failed."
    }
    Write-Output "Installed and verified faster-whisper."
} else {
    Write-Output "Installing openai-whisper..."
    & python -m pip install --upgrade openai-whisper
    $result = & python -c "import importlib.util; print('ok' if importlib.util.find_spec('whisper') is not None else 'missing')"
    if ($result -notcontains "ok") {
        throw "openai-whisper install verification failed."
    }
    Write-Output "Installed and verified openai-whisper."
}

Write-Output ("Transcription engine ready: {0}" -f $Engine)
