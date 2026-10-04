#!/usr/bin/env bash
# Hyperledger Fabric Development Network Bootstrap Script
set -e

echo "=== Starting Hyperledger Fabric Development Network ==="
cd "$(dirname "$0")/../network"

docker compose -f docker-compose-fabric.yaml down -v
docker compose -f docker-compose-fabric.yaml up -d

echo "Fabric containers launched successfully."
docker ps --filter "network=fabric-integrity-net"
