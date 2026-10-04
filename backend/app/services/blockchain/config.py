"""
Hyperledger Fabric Service Configuration (Phase 6).
Configures network channel, chaincode identifiers, and secure ledger storage paths.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LEDGER_STORAGE_DIR = BASE_DIR / "data" / "blockchain_ledger"
LEDGER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

FABRIC_NETWORK_NAME = os.getenv("FABRIC_NETWORK_NAME", "government-document-integrity-network")
FABRIC_CHANNEL_NAME = os.getenv("FABRIC_CHANNEL_NAME", "integritychannel")
FABRIC_CHAINCODE_NAME = os.getenv("FABRIC_CHAINCODE_NAME", "documentintegrity")
FABRIC_PEER_ENDPOINT = os.getenv("FABRIC_PEER_ENDPOINT", "localhost:7051")
FABRIC_MSPID = os.getenv("FABRIC_MSPID", "Org1MSP")
FABRIC_TIMEOUT_SECONDS = float(os.getenv("FABRIC_TIMEOUT_SECONDS", "10.0"))
