// TypeScript interfaces matching the backend Pydantic schemas

export interface Document {
  id: number;
  document_id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  upload_timestamp: string;
  status: DocumentStatus;
  processing_status: string | null;
  file_hash?: string | null;
  hash_algorithm?: string | null;
  integrity_status?: string | null;
  current_ipfs_cid?: string | null;
  current_sha256?: string | null;
  created_at: string;
  updated_at: string;
}

export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'verified'
  | 'suspicious'
  | 'failed';

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface UploadResponse {
  success: boolean;
  document_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  message: string;
}

export interface DocumentListResponse {
  success: boolean;
  total: number;
  documents: Document[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface ApiError {
  success: false;
  error: string;
  detail?: string;
}

export interface ProcessResponse {
  success: boolean;
  document_id: string;
  processing_status: string;
  message?: string;
}

export interface DocumentAnalysis {
  document_id: string;
  file: {
    filename: string;
    type: string;
    size: number;
    hash: string | null;
    hash_algorithm: string | null;
  };
  text: {
    raw_text: string | null;
    cleaned_text: string | null;
    word_count: number;
    character_count: number;
    paragraph_count: number;
  };
  metadata: {
    title?: string | null;
    author?: string | null;
    subject?: string | null;
    creator?: string | null;
    producer?: string | null;
    keywords?: string | null;
    created_at?: string | null;
    modified_at?: string | null;
    last_modified_by?: string | null;
    [key: string]: any;
  };
  structure: {
    format?: string;
    page_count?: number;
    page_dimensions?: Array<{ page_number: number; width: number; height: number }>;
    total_text_blocks?: number;
    total_images?: number;
    total_links?: number;
    font_count?: number;
    font_names?: string[];
    font_size_range?: { min: number; max: number } | null;
    pages_with_low_text?: number[];
    pages_with_only_images?: number[];
    paragraph_count?: number;
    heading_count?: number;
    headings?: string[];
    table_count?: number;
    tables_info?: Array<{ table_index: number; rows: number; columns: number }>;
    image_count?: number;
    hyperlink_count?: number;
    section_count?: number;
    width?: number;
    height?: number;
    aspect_ratio?: number;
    color_mode?: string;
    has_exif?: boolean;
    [key: string]: any;
  };
  ocr: {
    used: boolean;
    status: string;
    error_message?: string | null;
  };
  processing_status: string;
  processing_error?: string | null;
}

export interface DocumentFeaturesResponse {
  document_id: string;
  feature_version: string;
  pipeline_version: string;
  feature_count: number;
  feature_names: string[];
  feature_values: any[];
  features: Record<string, any>;
  normalized_features?: Record<string, number> | null;
  extraction_timestamp: string;
}

export interface FeatureGenerationResponse {
  success: boolean;
  document_id: string;
  feature_version: string;
  feature_count: number;
  status: string;
  message?: string;
}

export interface DatasetExportResponse {
  total_documents: number;
  feature_version: string;
  feature_names: string[];
  records: Array<Record<string, any>>;
}

// ── Phase 4 Machine Learning Types ──────────────────────────────────────────

export interface FeatureContribution {
  feature_name: string;
  document_value: number;
  baseline_mean: number;
  baseline_std: number;
  deviation_score: number;
  description?: string | null;
}

export interface PredictionResult {
  document_id: string;
  model_id?: string | null;
  model_name: string;
  model_version: string;
  feature_version: string;
  raw_score: number;
  anomaly_score: number;
  prediction: number; // 0 = normal, 1 = anomalous
  status: 'normal' | 'anomalous';
  threshold: number;
  contributing_features: FeatureContribution[];
  disclaimer: string;
  prediction_timestamp: string;
}

export interface ConfusionMatrix {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export interface EvaluationMetrics {
  precision?: number | null;
  recall?: number | null;
  f1_score?: number | null;
  accuracy?: number | null;
  specificity?: number | null;
  false_positive_rate?: number | null;
  false_negative_rate?: number | null;
  roc_auc?: number | null;
  average_precision?: number | null;
  sample_count: number;
  normal_count: number;
  anomalous_count: number;
  confusion_matrix?: ConfusionMatrix | null;
}

export interface MLModel {
  id: string;
  model_name: string;
  model_version: string;
  feature_version: string;
  model_type: string;
  is_active: boolean;
  training_sample_count: number;
  configuration: Record<string, any>;
  metrics?: EvaluationMetrics | null;
  feature_names: string[];
  description?: string | null;
  created_at: string;
}

export interface MLMonitoringStats {
  total_predictions: number;
  normal_count: number;
  anomalous_count: number;
  anomaly_ratio: number;
  average_anomaly_score: number;
  model_breakdown: Record<string, number>;
  active_model?: {
    id: string;
    model_name: string;
    model_version: string;
    feature_version: string;
    training_samples: number;
    created_at: string;
  } | null;
}

export interface TrainModelParams {
  model_name?: string;
  model_version?: string;
  feature_version?: string;
  n_estimators?: number;
  contamination?: number | string;
  random_state?: number;
  set_active?: boolean;
  description?: string;
}

// ── Phase 5: Advanced ML (Autoencoder) ──────────────────────────
export interface AdvancedMLPrediction {
  model: string;
  model_version: string;
  reconstruction_error: number;
  threshold: number;
  anomaly_score: number;
  prediction: number;
  input_mode: string;
  prediction_id?: string;
}

export interface ModelComparisonResult {
  sample_count: number;
  isolation_forest: {
    model_name: string;
    model_version: string;
    metrics: Record<string, any>;
  };
  autoencoder: {
    model_name: string;
    model_version: string;
    status: string;
    metrics?: Record<string, any> | null;
  };
}

// ── Phase 6: Hyperledger Fabric ──────────────────────────────────
export interface BlockchainRegisterResponse {
  success: boolean;
  document_id: string;
  blockchain_status: string;
  transaction_id: string;
  document_hash: string;
  ipfs_cid: string;
  channel_name: string;
  chaincode_name: string;
  block_reference?: string | null;
  registered_at: string;
}

export interface BlockchainVerifyResponse {
  document_id: string;
  current_hash?: string | null;
  registered_hash?: string | null;
  hash_match: boolean;
  ipfs_cid_match: boolean;
  blockchain_record_found: boolean;
  integrity_status: string;
  transaction_id?: string | null;
  registered_at?: string | null;
}

export interface BlockchainHistoryEntry {
  transaction_id: string;
  timestamp: string;
  document_version: string;
  document_hash: string;
  ipfs_cid: string;
  event_type: string;
  block_number?: number | null;
}

export interface BlockchainHistoryResponse {
  document_id: string;
  total_events: number;
  history: BlockchainHistoryEntry[];
}

// ── Phase 7: IPFS ────────────────────────────────────────────────
export interface IPFSUploadResponse {
  success: boolean;
  document_id: string;
  ipfs_cid: string;
  status: string;
  content_size_bytes: number;
  content_sha256: string;
  storage_provider: string;
}

export interface IPFSVerifyResponse {
  document_id: string;
  ipfs_cid: string;
  current_file_sha256?: string | null;
  retrieved_content_sha256?: string | null;
  hash_match: boolean;
  retrieval_success: boolean;
  status: string;
}

// ── Unified Integrity Verification ───────────────────────────────
export interface IntegratedVerificationResponse {
  document_id: string;
  ml: {
    model: string;
    model_version: string;
    reconstruction_error?: number;
    anomaly_score: number;
    prediction: number;
    status: string;
  };
  ipfs: {
    cid?: string | null;
    hash_match: boolean;
    retrieval_success: boolean;
    status: string;
  };
  blockchain: {
    record_found: boolean;
    hash_match: boolean;
    transaction_id?: string | null;
    registered_at?: string | null;
    status: string;
  };
  integrity: {
    status: string;
  };
  final_status: string;
  technical_explanation: string;
  verification_id?: string | null;
  verified_at: string;
}

// ── Demo & Tampering Simulation ──────────────────────────────────
export interface TamperingSimulationResponse {
  document_id: string;
  prototype_note: string;
  tampering_simulation: {
    original_filename: string;
    original_hash: string;
    simulated_tampered_hash: string;
    hash_mismatch: boolean;
    mismatch_type: string;
  };
  blockchain_check: {
    registered: boolean;
    registered_hash: string | null;
    current_hash: string;
    hash_match: boolean;
    status: string;
  };
  anomaly_analysis: {
    anomaly_score: number;
    risk_level: string;
    anomaly_score_0_to_100: number;
    detected_issues: string[];
    final_verdict: string;
  };
  timestamp: string;
}

export interface SeedDataResponse {
  message: string;
  normal_count: number;
  anomalous_count: number;
  total_seeded: number;
  status: string;
}

