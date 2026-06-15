$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ImageName = "pm-mvp:dev"
$ContainerName = "pm-mvp"
$Port = if ($env:PORT) { $env:PORT } else { "8000" }
$EnvFile = Join-Path $RootDir ".env"

if (-not (Test-Path $EnvFile)) {
  Write-Error "Missing .env at $EnvFile"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker is required but was not found in PATH."
}

docker info | Out-Null

$portBusy = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portBusy) {
  Write-Error "Port $Port is already in use."
}

Write-Host "Building image $ImageName..."
docker build -t $ImageName $RootDir | Out-Null

docker rm -f $ContainerName | Out-Null 2>$null

Write-Host "Starting container $ContainerName on port $Port..."
docker run -d --name $ContainerName --env-file $EnvFile -p "${Port}:8000" $ImageName | Out-Null

Write-Host "Waiting for service readiness..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    Invoke-RestMethod "http://127.0.0.1:$Port/health" | Out-Null
    $ready = $true
    break
  } catch {
    Start-Sleep -Seconds 1
  }
}

if (-not $ready) {
  docker logs $ContainerName
  Write-Error "Service failed to become ready."
}

$health = Invoke-RestMethod "http://127.0.0.1:$Port/health" | ConvertTo-Json -Compress
$hello = Invoke-RestMethod "http://127.0.0.1:$Port/api/hello" | ConvertTo-Json -Compress
Write-Host "Container is ready."
Write-Host "Health: $health"
Write-Host "API:    $hello"
Write-Host "Open http://127.0.0.1:$Port/"
