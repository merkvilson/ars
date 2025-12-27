param(
  [string]$PythonVersion = "3.12.8",
  [ValidateSet("amd64", "win32")][string]$Arch = "amd64"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$embedDir = Join-Path $root "python_embeded"
$downloadsDir = Join-Path $PSScriptRoot "_downloads"
$zipName = "python-$PythonVersion-embed-$Arch.zip"
$zipPath = Join-Path $downloadsDir $zipName
$pyUrl = "https://www.python.org/ftp/python/$PythonVersion/$zipName"
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = Join-Path $embedDir "get-pip.py"
$reqPath = Join-Path $root "util_functions\requirements.txt"

New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null

Write-Host "[1/5] Downloading Python embed: $pyUrl" -ForegroundColor Cyan
Invoke-WebRequest -Uri $pyUrl -OutFile $zipPath

if (Test-Path $embedDir) {
  Write-Host "[2/5] Removing existing $embedDir" -ForegroundColor Cyan
  Remove-Item -Recurse -Force $embedDir
}

Write-Host "[2/5] Extracting to $embedDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $embedDir | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $embedDir -Force

$pth = Get-ChildItem -Path $embedDir -Filter "python*._pth" | Select-Object -First 1
if (-not $pth) {
  throw "Could not find python*._pth in $embedDir"
}

Write-Host "[3/5] Configuring $($pth.Name) (enable site-packages)" -ForegroundColor Cyan
$lines = Get-Content -LiteralPath $pth.FullName

# Ensure we can import packages installed into Lib\site-packages
if (-not ($lines | Where-Object { $_ -eq "Lib\\site-packages" })) {
  $lines += "Lib\\site-packages"
}

# Ensure the project root (one level above python_embeded) is on sys.path
if (-not ($lines | Where-Object { $_ -eq ".." })) {
  $lines += ".."
}

# Keep python_embeded itself on sys.path (useful for local zips/dlls)
if (-not ($lines | Where-Object { $_ -eq "." })) {
  $lines += "."
}

# Enable standard site initialization (required for site-packages)
$lines = $lines | ForEach-Object {
  if ($_ -match "^#\s*import\s+site\s*$") { "import site" } else { $_ }
}

Set-Content -LiteralPath $pth.FullName -Value $lines -Encoding ASCII

Write-Host "[4/5] Bootstrapping pip" -ForegroundColor Cyan
Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath

$pyExe = Join-Path $embedDir "python.exe"
if (-not (Test-Path $pyExe)) {
  throw "python.exe not found in $embedDir"
}

& $pyExe $getPipPath

Write-Host "[5/5] Installing requirements into python_embeded" -ForegroundColor Cyan
if (-not (Test-Path $reqPath)) {
  throw "requirements.txt not found at $reqPath"
}

& $pyExe -m pip install --upgrade pip
& $pyExe -m pip install -r $reqPath --progress-bar off

Write-Host "Done. Portable Python is in: $embedDir" -ForegroundColor Green
Write-Host "Run with: portable\\run_ars_portable.bat" -ForegroundColor Green
