# Hyperledger Fabric Development Network Bootstrap Script (PowerShell)
Write-Host "=== Starting Hyperledger Fabric Development Network ===" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\..\network"

docker compose -f docker-compose-fabric.yaml down -v
docker compose -f docker-compose-fabric.yaml up -d

Write-Host "Fabric containers launched successfully." -ForegroundColor Green
docker ps --filter "network=fabric-integrity-net"
