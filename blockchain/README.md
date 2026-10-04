# Hyperledger Fabric Document Integrity Network (Phase 6)

## Overview
This directory contains the Hyperledger Fabric blockchain integration infrastructure for the Official Government Document Anomaly Detection & Integrity Verification System.

The blockchain acts as an **immutable, append-only technical ledger** for document fingerprints (SHA-256) and off-chain storage references (IPFS CIDs).

### Key Architectural Rules
1. **No full documents on-chain**: Documents are stored in IPFS; only cryptographic hashes, CIDs, and audit records are recorded on Fabric.
2. **Technical evidence only**: A valid blockchain record proves technical fingerprint immutability; it does **not** independently verify the real-world legitimacy of the issuing entity.
3. **Zero fake transactions**: All transaction IDs are genuine cryptographic hashes following Hyperledger Fabric's transaction hashing specification.

## Directory Structure
- `chaincode/`: Go smart contract (`document_integrity.go`) implementing registration, state query, hash verification, and audit history.
- `network/`: `docker-compose-fabric.yaml` defining Orderer, Org1 Peer, and CLI services.
- `config/`: `connection-profile.json` detailing gRPC endpoints and channel topology.
- `scripts/`: Network startup and shutdown scripts.

## Running the Fabric Network
```bash
# In Linux/macOS
./blockchain/scripts/start-network.sh

# In Windows PowerShell
.\blockchain\scripts\start-network.ps1
```

## Chaincode Methods
- `RegisterDocument(document_id, document_hash, hash_algorithm, ipfs_cid, document_version, issuer_reference)`
- `GetDocument(document_id)`
- `VerifyDocument(document_id, current_hash)`
- `GetDocumentHistory(document_id)`
