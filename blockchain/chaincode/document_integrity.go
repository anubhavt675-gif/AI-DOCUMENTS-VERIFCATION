package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// DocumentContract provides functions for managing immutable document fingerprints
type DocumentContract struct {
	contractapi.Contract
}

// DocumentRecord defines the on-chain metadata structure.
// NOTE: Full document content is NEVER stored on the blockchain.
type DocumentRecord struct {
	DocumentID       string `json:"document_id"`
	DocumentHash     string `json:"document_hash"`
	HashAlgorithm    string `json:"hash_algorithm"`
	IPFSCID          string `json:"ipfs_cid"`
	RegisteredAt     string `json:"registered_at"`
	IssuerReference  string `json:"issuer_reference"`
	DocumentVersion  string `json:"document_version"`
	Status           string `json:"status"`
	TxID             string `json:"tx_id"`
}

// DocumentHistoryEntry captures state changes across the document lifecycle
type DocumentHistoryEntry struct {
	TxID      string          `json:"tx_id"`
	Timestamp string          `json:"timestamp"`
	IsDelete  bool            `json:"is_delete"`
	Value     *DocumentRecord `json:"value"`
}

// InitLedger adds initial test state or logs readiness
func (c *DocumentContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	fmt.Println("DocumentIntegrity contract initialized.")
	return nil
}

// RegisterDocument registers a new document fingerprint and IPFS CID on-chain
func (c *DocumentContract) RegisterDocument(
	ctx contractapi.TransactionContextInterface,
	documentID string,
	documentHash string,
	hashAlgorithm string,
	ipfsCID string,
	documentVersion string,
	issuerReference string,
) (*DocumentRecord, error) {
	if documentID == "" || documentHash == "" || ipfsCID == "" {
		return nil, fmt.Errorf("document_id, document_hash, and ipfs_cid must not be empty")
	}

	exists, err := c.DocumentExists(ctx, documentID)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, fmt.Errorf("document with ID %s is already registered on blockchain", documentID)
	}

	txID := ctx.GetStub().GetTxID()
	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	var registeredAt string
	if err == nil && txTimestamp != nil {
		registeredAt = time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)
	} else {
		registeredAt = time.Now().UTC().Format(time.RFC3339)
	}

	if hashAlgorithm == "" {
		hashAlgorithm = "SHA-256"
	}
	if documentVersion == "" {
		documentVersion = "1.0"
	}

	record := DocumentRecord{
		DocumentID:      documentID,
		DocumentHash:    documentHash,
		HashAlgorithm:   hashAlgorithm,
		IPFSCID:         ipfsCID,
		RegisteredAt:    registeredAt,
		IssuerReference: issuerReference,
		DocumentVersion: documentVersion,
		Status:          "REGISTERED",
		TxID:            txID,
	}

	recordBytes, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize record: %v", err)
	}

	err = ctx.GetStub().PutState(documentID, recordBytes)
	if err != nil {
		return nil, fmt.Errorf("failed to put state to ledger: %v", err)
	}

	return &record, nil
}

// GetDocument retrieves the registered record for a document ID
func (c *DocumentContract) GetDocument(
	ctx contractapi.TransactionContextInterface,
	documentID string,
) (*DocumentRecord, error) {
	recordBytes, err := ctx.GetStub().GetState(documentID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from ledger: %v", err)
	}
	if recordBytes == nil {
		return nil, fmt.Errorf("document record with ID %s does not exist", documentID)
	}

	var record DocumentRecord
	err = json.Unmarshal(recordBytes, &record)
	if err != nil {
		return nil, fmt.Errorf("failed to deserialize record: %v", err)
	}

	return &record, nil
}

// VerifyDocument compares current SHA-256 against on-chain registered hash
func (c *DocumentContract) VerifyDocument(
	ctx contractapi.TransactionContextInterface,
	documentID string,
	currentHash string,
) (bool, error) {
	record, err := c.GetDocument(ctx, documentID)
	if err != nil {
		return false, err
	}
	return record.DocumentHash == currentHash, nil
}

// DocumentExists checks whether a document key exists on the ledger
func (c *DocumentContract) DocumentExists(
	ctx contractapi.TransactionContextInterface,
	documentID string,
) (bool, error) {
	recordBytes, err := ctx.GetStub().GetState(documentID)
	if err != nil {
		return false, fmt.Errorf("failed to read ledger state: %v", err)
	}
	return recordBytes != nil, nil
}

// GetDocumentHistory returns the full blockchain audit trail for a document
func (c *DocumentContract) GetDocumentHistory(
	ctx contractapi.TransactionContextInterface,
	documentID string,
) ([]DocumentHistoryEntry, error) {
	iterator, err := ctx.GetStub().GetHistoryForKey(documentID)
	if err != nil {
		return nil, fmt.Errorf("failed to get history for key %s: %v", documentID, err)
	}
	defer iterator.Close()

	var history []DocumentHistoryEntry
	for iterator.HasNext() {
		modification, err := iterator.Next()
		if err != nil {
			return nil, err
		}

		var record *DocumentRecord
		if !modification.IsDelete && len(modification.Value) > 0 {
			var r DocumentRecord
			if err := json.Unmarshal(modification.Value, &r); err == nil {
				record = &r
			}
		}

		entry := DocumentHistoryEntry{
			TxID:      modification.TxId,
			Timestamp: time.Unix(modification.Timestamp.Seconds, int64(modification.Timestamp.Nanos)).UTC().Format(time.RFC3339),
			IsDelete:  modification.IsDelete,
			Value:     record,
		}
		history = append(history, entry)
	}

	return history, nil
}

func main() {
	cc, err := contractapi.NewChaincode(&DocumentContract{})
	if err != nil {
		panic(fmt.Sprintf("Error creating DocumentContract chaincode: %v", err))
	}

	if err := cc.Start(); err != nil {
		panic(fmt.Sprintf("Error starting DocumentContract chaincode: %v", err))
	}
}
