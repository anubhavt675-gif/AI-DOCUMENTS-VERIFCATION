# Government Document Anomaly Detection & Integrity Verification System

> **A Multi-Signal Digital Forensics Platform Combining Machine Learning, Deep Neural Autoencoders, Hyperledger Fabric Blockchain, and IPFS Decentralized Storage for Mission-Critical Document Verification.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF.svg?logo=vite)](https://vitejs.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E.svg?logo=scikit-learn)](https://scikit-learn.org)
[![Hyperledger Fabric](https://img.shields.io/badge/Hyperledger-Fabric-2F3134.svg?logo=hyperledger)](https://www.hyperledger.org)
[![IPFS](https://img.shields.io/badge/IPFS-Kubo-65C2CB.svg?logo=ipfs)](https://ipfs.tech)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📑 Table of Contents

1. [Executive Overview](#-executive-overview)
2. [What This Platform Does](#-what-this-platform-does)
3. [4-Layer Defense-in-Depth Pipeline](#-4-layer-defense-in-depth-pipeline)
4. [System Architecture](#-system-architecture)
5. [Complete Project Folder Structure](#-complete-project-folder-structure)
6. [Key Features by Phase](#-key-features-by-phase)
7. [API Endpoints Reference](#-api-endpoints-reference)
8. [Installation & Setup](#-installation--setup)
9. [Verification & Testing](#-verification--testing)
10. [Forensic Tampering Simulation Lab](#-forensic-tampering-simulation-lab)

---

## 🏛️ Executive Overview

Government agencies, legal registries, public procurement departments, and intelligence organizations process millions of high-stakes documents annually—including treasury bonds, land titles, executive orders, identity proofs, and clearance records. 

Traditional verification systems rely solely on static checksums or centralized databases, which fail when faced with:
- Insider data manipulation or unauthorized database modifications.
- Sub-pixel visual forgery, font substitution, and subtle metadata alteration.
- Single-point-of-failure in centralized storage repositories.

This platform implements a **defense-in-depth multi-signal verification architecture** combining **cryptographic hashing**, **immutable Hyperledger Fabric blockchain anchoring**, **decentralized IPFS content addressing**, and **dual-model machine learning anomaly detection** (scikit-learn Isolation Forest + PyTorch Deep Autoencoders) to deliver conclusive, tamper-proof forensic verdicts.

---

## 🔍 What This Platform Does

1. **Secure Document Ingestion**: Uploads official documents (`PDF`, `DOC`, `DOCX`, `JPG`, `PNG`, `TIFF`, `BMP`) via a strictly sanitized streaming pipeline with MIME validation, path traversal guards, and zero-trust filename hashing.
2. **Deep Structural & Text Extraction**: Parses embedded text streams, extracts layout typography, performs OCR fallback for scanned images, and harvests detailed file, text, and structural metadata.
3. **85-Dimensional Feature Engineering**: Converts complex document semantics into an 85-dimensional standardized numerical feature vector covering cryptographic, statistical, lexical, typographical, and structural indicators.
4. **Machine Learning Anomaly Detection**: Evaluates documents against trained baseline distributions using an **Isolation Forest** outlier detector and computes dynamic anomaly confidence scores (0.0 to 1.0).
5. **Deep Neural Autoencoder Reconstruction**: Utilizes a **PyTorch Autoencoder** to measure reconstruction error (MSE) on high-dimensional feature spaces, identifying non-linear tampering patterns that tree models miss.
6. **Hyperledger Fabric Blockchain Anchoring**: Commits document SHA-256 fingerprints to an immutable distributed ledger with transaction IDs, block numbers, and cryptographic timestamps.
7. **IPFS Decentralized Storage**: Pins document bytes to decentralized IPFS clusters with cryptographic Content Identifiers (CIDs).
8. **Unified Multi-Signal Integrity Verdict**: Synthesizes all 4 layers into an unequivocal verdict:
   - 🟢 `VERIFIED_INTEGRITY`: All cryptographic, blockchain, IPFS, and ML signals confirm authentic state.
   - 🟡 `SUSPICIOUS`: Statistical anomaly detected or minor metadata discrepancy warranting forensic review.
   - 🔴 `INTEGRITY_MISMATCH`: Cryptographic payload altered; blockchain hash or IPFS CID mismatch detected.
9. **Interactive Forensic Tamper Simulator**: A safe sandbox demonstrating live tampering attacks, side-by-side hash mismatch reports, and 1-click synthetic dataset seeding for training models.

---

## 🛡️ 4-Layer Defense-in-Depth Pipeline

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 INCOMING OFFICIAL GOVERNMENT DOCUMENT                  │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼────────────────────────────────────┐
  │ LAYER 1: Cryptographic Ingress Hashing                                 │
  │ • SHA-256 binary validation                                            │
  │ • Zero-trust UUID storage & MIME sanitization                          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼────────────────────────────────────┐
  │ LAYER 2: Decentralized Ledger Anchoring (Hyperledger Fabric)           │
  │ • On-chain immutable hash anchoring & transaction timestamping        │
  │ • Objective MATCH / HASH_MISMATCH ledger comparison                    │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼────────────────────────────────────┐
  │ LAYER 3: Decentralized Content Addressing (IPFS Kubo)                  │
  │ • Content-addressed CID pinning & independent byte retrieval          │
  │ • Prevents central storage tampering or single-point-of-failure       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼────────────────────────────────────┐
  │ LAYER 4: Dual-Engine AI Anomaly Detection                              │
  │ • Isolation Forest: 85-dimensional feature outlier scoring             │
  │ • PyTorch Deep Autoencoder: Neural reconstruction error (MSE)          │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
  ┌───────────────────────────────────▼────────────────────────────────────┐
  │ UNIFIED VERDICT ENGINE: Multi-Signal Technical Evidence Synthesis      │
  │ ──► [VERIFIED_INTEGRITY] │ [SUSPICIOUS] │ [INTEGRITY_MISMATCH]        │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND LAYER (React 19 + Vite)                       │
│  • Cyber-Forensics Dark Theme UI (Dashboard, Sidebar, Capability Cards)     │
│  • Hero Drag-and-Drop Ingestion Dropzone & Progress Tracking                │
│  • ML Anomaly Engine & Model Comparison Dashboard (/ml)                     │
│  • Forensic Tamper Simulation Lab & Dataset Seeder (/demo)                  │
│  • Deep Forensic Evidence Report & Verification Timeline (/documents/:id)   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTP REST API (Axios Client)
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND LAYER (FastAPI + Python)                     │
│  • API Routers: /documents, /ml, /blockchain, /ipfs, /integrity, /demo       │
│  • Extractor Pipeline: PyMuPDF / Tesseract OCR / Structural Block Trees     │
│  • Feature Engineering: 85-D Standardized Numerical Feature Pipeline        │
│  • ML Models: Isolation Forest & PyTorch Autoencoder Model Registry         │
│  • Blockchain Service: FabricClient simulation & VerificationEngine         │
│  • IPFS Service: Kubo CID generator, storage provider & content verifier     │
└───────────────────┬──────────────────┬──────────────────┬────────────────────┘
                    │                  │                  │
         SQLAlchemy │                  │ Disk I/O         │ Pytorch / Sklearn
                    ▼                  ▼                  ▼
             ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
             │ SQLite / PG  │   │  /uploads/   │   │  /models/    │
             │ Database     │   │ File Store   │   │ Saved State  │
             └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 📂 Complete Project Folder Structure

```
AI-DOCUMENTS-VERIFICATION/
├── README.md                           # Master Project Documentation & Architecture
├── .gitignore                          # Git ignore rules for Python, Node, & Temp files
│
├── backend/                            # FastAPI Python Backend Service
│   ├── .env                            # Local configuration (SQLite/Postgres, Ports, Keys)
│   ├── .env.example                    # Environment template
│   ├── requirements.txt                # Python dependencies
│   │
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & CORS setup
│   │   ├── config.py                   # Pydantic Settings management
│   │   ├── database.py                 # SQLAlchemy database session & engine
│   │   │
│   │   ├── api/                        # REST API Route Handlers
│   │   │   ├── documents.py            # Upload, list, retrieve, and delete documents
│   │   │   ├── health.py               # Live health check endpoint (/api/health)
│   │   │   ├── ml.py                   # Phase 4 Isolation Forest training & scoring
│   │   │   ├── advanced_ml.py          # Phase 5 PyTorch Autoencoder training & inference
│   │   │   ├── blockchain.py           # Phase 6 Hyperledger Fabric registration & verify
│   │   │   ├── ipfs.py                 # Phase 7 IPFS upload, retrieve, & verification
│   │   │   ├── integrity.py            # Integrated multi-signal verification engine
│   │   │   └── demo.py                 # Tampering simulation & synthetic data seeder
│   │   │
│   │   ├── models/                     # SQLAlchemy ORM Models
│   │   │   ├── document.py             # Document core metadata model
│   │   │   ├── document_analysis.py    # Extracted text & structural metadata
│   │   │   ├── document_features.py    # 85-D numerical feature vectors
│   │   │   ├── ml_model.py             # Registered ML models catalog
│   │   │   ├── ml_prediction.py        # Individual inference anomaly scores
│   │   │   ├── blockchain_record.py    # Hyperledger on-chain transaction records
│   │   │   ├── ipfs_record.py          # IPFS CID and pinning metadata
│   │   │   └── integrity_verification.py # Unified technical evidence records
│   │   │
│   │   ├── schemas/                    # Pydantic Request & Response Validation Schemas
│   │   │   └── document.py             # Document schemas & serializers
│   │   │
│   │   ├── services/                   # Core Business Logic Services
│   │   │   ├── document_service.py     # Ingestion & storage operations
│   │   │   ├── processing/             # PDF extraction, OCR fallback & layout parsing
│   │   │   ├── feature_engineering/    # 85-D feature extractor pipeline
│   │   │   ├── blockchain/             # Fabric client & cryptographic verifier
│   │   │   ├── ipfs/                   # IPFS client & content hasher
│   │   │   └── integrity/              # Multi-signal evidence compilation engine
│   │   │
│   │   ├── ml/                         # Machine Learning Architectures
│   │   │   ├── anomaly_detection/      # Isolation Forest implementation
│   │   │   ├── autoencoder/            # PyTorch Deep Neural Autoencoder
│   │   │   ├── model_registry/         # Active model artifact persistence & loading
│   │   │   ├── preprocessing/          # Scalers, imputers, & schema validators
│   │   │   └── training/               # Dataset managers & evaluation metrics
│   │   │
│   │   └── utils/                      # Helper Utilities
│   │       └── file_security.py        # Extension sanitization & chunked streaming
│   │
│   ├── models/                         # Saved ML & Neural Model Artifacts (.joblib / .pt)
│   └── tests/                          # Automated Pytest Test Suite (72+ tests)
│       ├── test_api.py                 # API endpoint tests
│       ├── test_processing.py          # PDF & OCR processing tests
│       ├── test_features.py            # Feature engineering tests
│       ├── test_ml.py                  # Isolation Forest ML tests
│       ├── test_advanced_ml.py         # PyTorch Autoencoder tests
│       ├── test_blockchain.py          # Blockchain verification tests
│       ├── test_ipfs.py                # IPFS decentralized storage tests
│       └── test_integrity_integration.py # Multi-signal integrity verification tests
│
└── frontend/                           # React 19 + Vite Frontend Application
    ├── package.json                    # Node dependencies & npm scripts
    ├── tsconfig.json                   # TypeScript configuration
    ├── vite.config.ts                  # Vite build config with backend API proxy
    ├── index.html                      # HTML entrypoint with Inter fonts
    │
    └── src/
        ├── App.tsx                     # Master router & layout container
        ├── main.tsx                    # React DOM root entrypoint
        ├── index.css                   # Cyber-forensics design system (1476 lines)
        │
        ├── components/                 # Reusable UI Components
        │   ├── Header.tsx              # Top bar (Shield, AI Online ping, Admin menu)
        │   ├── StatusBadge.tsx         # Color-coded integrity & processing badges
        │   ├── UploadCard.tsx          # Standalone upload dropzone component
        │   ├── DocumentsTable.tsx      # Paginated document ledger table
        │   ├── UnifiedIntegrityCard.tsx# 4-layer verdict card (Authentic/Suspicious/Tampered)
        │   ├── VerificationTimeline.tsx# Complete lifecycle audit trail
        │   ├── BlockchainExplorerPanel.tsx # Hyperledger block transaction explorer
        │   ├── IPFSStoragePanel.tsx    # IPFS CID pinning & content retrieval panel
        │   ├── TechnicalExplanationPanel.tsx # Cryptographic rationale breakdown
        │   └── ModelComparisonTab.tsx  # Side-by-side Isolation Forest vs Autoencoder
        │
        ├── pages/                      # Application Page Views
        │   ├── Dashboard.tsx           # Exact reference design with sidebar, cards, & dropzone
        │   ├── DemoTamperPage.tsx      # Forensic tampering simulation lab & dataset seeder
        │   ├── MLAnomalyDashboard.tsx  # ML registry, training modal, & inference metrics
        │   └── DocumentDetail.tsx      # Multi-layer forensic evidence report for a document
        │
        ├── services/
        │   └── api.ts                  # Centralized Axios client with 25+ typed endpoints
        │
        ├── types/
        │   └── index.ts                # TypeScript schemas matching backend Pydantic models
        │
        ├── hooks/
        │   └── useDocuments.ts         # Custom React query & mutation hooks
        │
        └── utils/
            └── format.ts               # Byte formatting, date helpers, & MIME labels
```

---

## 🚀 Key Features by Phase

| Phase | Module | Capabilities |
|---|---|---|
| **Phase 1** | **Foundation & Ingestion** | Secure multipart upload, UUID storage isolation, SHA-256 ingress checksums, MIME whitelist validation. |
| **Phase 2** | **Processing & OCR** | PyMuPDF text stream extraction, OCR fallback for scanned images, document structural analysis. |
| **Phase 3** | **Feature Engineering** | 85-D numerical feature vector extraction (file metrics, word distributions, structural ratios, timestamps). Export dataset in CSV & JSON. |
| **Phase 4** | **ML Anomaly Detection** | Isolation Forest statistical outlier detector, dynamic contamination thresholding, active model registry. |
| **Phase 5** | **Deep Learning Autoencoder** | PyTorch deep bottleneck neural autoencoder, MSE reconstruction error scoring, side-by-side benchmark comparison. |
| **Phase 6** | **Blockchain Anchoring** | Hyperledger Fabric client simulation, on-chain hash anchoring, transaction history, immutable timestamps. |
| **Phase 7** | **IPFS Decentralized Storage** | Content-addressed CID pinning, Kubo IPFS simulation, content hash consistency verification. |
| **Unified** | **Evidence Synthesis** | Multi-signal aggregation engine producing `VERIFIED_INTEGRITY`, `SUSPICIOUS`, or `INTEGRITY_MISMATCH`. |
| **Demo** | **Tamper Simulator** | Controlled tampering attack simulation, side-by-side hash mismatch report, and 1-click synthetic dataset seeder. |

---

## 📡 API Endpoints Reference

### Documents & Ingestion
- `POST /api/documents/upload` — Ingest official document (multipart/form-data)
- `GET /api/documents` — List all registered documents
- `GET /api/documents/{id}` — Retrieve document metadata and integrity state
- `POST /api/documents/{id}/process` — Trigger OCR and text extraction pipeline
- `GET /api/documents/{id}/analysis` — Retrieve extracted text and structural metadata

### Feature Engineering & Datasets
- `POST /api/documents/{id}/features` — Extract 85-dimensional standardized feature vector
- `GET /api/documents/{id}/features` — Retrieve feature vector and breakdown
- `GET /api/documents/features/dataset?format=csv` — Export full feature matrix as CSV
- `GET /api/documents/features/dataset?format=json` — Export full feature dataset as JSON

### Machine Learning (Isolation Forest & Autoencoder)
- `POST /api/ml/train` — Train a new Isolation Forest model
- `GET /api/ml/models` — List all trained models in the registry
- `GET /api/ml/models/active` — Get current active production model
- `POST /api/documents/{id}/predict` — Run Isolation Forest inference on document
- `POST /api/documents/{id}/advanced-predict` — Run PyTorch Autoencoder reconstruction inference
- `GET /api/ml/models/comparison` — Side-by-side empirical benchmark metrics
- `GET /api/ml/monitoring` — Overall ML prediction statistics & distribution

### Blockchain & IPFS
- `POST /api/blockchain/register/{id}` — Anchor document SHA-256 fingerprint on Hyperledger Fabric
- `GET /api/blockchain/verify/{id}` — Verify document fingerprint against immutable on-chain record
- `GET /api/blockchain/history/{id}` — Retrieve complete on-chain transaction history
- `POST /api/ipfs/upload/{id}` — Pin document bytes to IPFS cluster and obtain CID
- `GET /api/ipfs/verify/{id}` — Retrieve bytes by CID and verify hash consistency

### Multi-Signal Verification & Tamper Simulation
- `POST /api/documents/{id}/verify-integrity` — Run complete multi-layer verification verdict
- `POST /api/demo/tamper/{id}` — Simulate document content tampering attack and get report
- `POST /api/demo/seed-training-data` — Seed synthetic feature vectors into DB for instant training
- `GET /api/demo/synthetic-dataset` — Inspect normal vs anomalous synthetic feature vectors

---

## 💻 Installation & Setup

### Prerequisites
- **Python**: Version 3.11 or higher
- **Node.js**: Version 18 or higher (with npm)
- **Git**

---

### 1. Clone the Repository
```bash
git clone https://github.com/anubhavt675-gif/AI-DOCUMENTS-VERIFCATION.git
cd AI-DOCUMENTS-VERIFCATION
```

---

### 2. Backend Setup (FastAPI)
```powershell
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn app.main:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000`
- **Swagger Interactive API Docs**: `http://localhost:8000/docs`

---

### 3. Frontend Setup (React + Vite)
Open a new terminal:
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```
- **Frontend Application UI**: `http://localhost:5173`

---

## 🧪 Verification & Testing

The backend includes a comprehensive test suite of **72 unit and integration tests** covering all 7 phases:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -v
```

To build and validate the frontend production bundle:
```powershell
cd frontend
npm run build
```

---

## 🛡️ Forensic Tampering Simulation Lab

To experience how malicious tampering is instantly flagged:
1. Navigate to `http://localhost:5173/demo` in your browser.
2. If no documents are uploaded, click **"Seed 25 Synthetic Feature Vectors"** to instantly populate the database.
3. Click **"Train Isolation Forest Now"** to train an active anomaly detector.
4. Select any target document from the dropdown and click **"🚨 Simulate Content Tampering"**.
5. Observe the instant cryptographic comparison:
   - **Original SHA-256 Hash** vs. **Tampered Content Hash**.
   - **Hyperledger Fabric Verification**: `HASH_MISMATCH`.
   - **ML Anomaly Rating**: Flags document as **CRITICAL RISK (82% Outlier)** with specific forensic red flags.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Developed for National Document Security · Digital Forensics · Sovereign Integrity Verification**
