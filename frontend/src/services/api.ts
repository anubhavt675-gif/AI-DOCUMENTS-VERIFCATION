/**
 * Centralised API service layer.
 * All HTTP requests go through here — never placed directly into components.
 */
import axios, { AxiosError } from 'axios';
import type {
  Document,
  DocumentAnalysis,
  DocumentListResponse,
  HealthResponse,
  ProcessResponse,
  UploadResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

// ── Response interceptor for uniform error messages ───────────────────────────
apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError<{ error?: string; detail?: string }>) => {
    const message =
      error.response?.data?.detail ??
      error.response?.data?.error ??
      error.message ??
      'An unexpected error occurred.';
    return Promise.reject(new Error(message));
  }
);

// ── Health ────────────────────────────────────────────────────────────────────
export async function checkHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/api/health');
  return data;
}

// ── Documents ─────────────────────────────────────────────────────────────────
export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);

  const { data } = await apiClient.post<UploadResponse>(
    '/api/documents/upload',
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) {
          onProgress(Math.round((evt.loaded * 100) / evt.total));
        }
      },
    }
  );
  return data;
}

export async function listDocuments(
  skip = 0,
  limit = 100
): Promise<DocumentListResponse> {
  const { data } = await apiClient.get<DocumentListResponse>(
    `/api/documents?skip=${skip}&limit=${limit}`
  );
  return data;
}

export async function getDocument(documentId: string): Promise<Document> {
  const { data } = await apiClient.get<Document>(
    `/api/documents/${documentId}`
  );
  return data;
}

export async function processDocument(
  documentId: string
): Promise<ProcessResponse> {
  const { data } = await apiClient.post<ProcessResponse>(
    `/api/documents/${documentId}/process`
  );
  return data;
}

export async function getAnalysis(
  documentId: string
): Promise<DocumentAnalysis> {
  const { data } = await apiClient.get<DocumentAnalysis>(
    `/api/documents/${documentId}/analysis`
  );
  return data;
}

// ── Feature Engineering (Phase 3) ─────────────────────────────────────────────
export async function generateFeatures(
  documentId: string
): Promise<import('../types').FeatureGenerationResponse> {
  const { data } = await apiClient.post<import('../types').FeatureGenerationResponse>(
    `/api/documents/${documentId}/features`
  );
  return data;
}

export async function getFeatures(
  documentId: string
): Promise<import('../types').DocumentFeaturesResponse> {
  const { data } = await apiClient.get<import('../types').DocumentFeaturesResponse>(
    `/api/documents/${documentId}/features`
  );
  return data;
}

export async function exportDatasetJson(): Promise<import('../types').DatasetExportResponse> {
  const { data } = await apiClient.get<import('../types').DatasetExportResponse>(
    '/api/documents/features/dataset?format=json'
  );
  return data;
}

export function getDatasetCsvUrl(): string {
  return `${BASE_URL}/api/documents/features/dataset?format=csv`;
}

// ── Machine Learning Anomaly Detection (Phase 4) ──────────────────────────────
export async function trainModel(
  params?: import('../types').TrainModelParams
): Promise<any> {
  const payload = {
    model_name: params?.model_name || 'IsolationForest',
    model_version: params?.model_version,
    feature_version: params?.feature_version || '1.0',
    config: {
      n_estimators: params?.n_estimators || 300,
      random_state: params?.random_state || 42,
    },
    contamination: params?.contamination,
    set_active: params?.set_active ?? true,
    description: params?.description,
  };
  const { data } = await apiClient.post('/api/ml/train', payload);
  return data;
}

export async function listMLModels(): Promise<import('../types').MLModel[]> {
  const { data } = await apiClient.get<import('../types').MLModel[]>('/api/ml/models');
  return data;
}

export async function getActiveMLModel(): Promise<import('../types').MLModel | null> {
  try {
    const { data } = await apiClient.get<import('../types').MLModel>('/api/ml/models/active');
    return data;
  } catch (err: any) {
    if (err.response?.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function activateMLModel(modelId: string): Promise<import('../types').MLModel> {
  const { data } = await apiClient.post<import('../types').MLModel>(
    `/api/ml/models/${modelId}/activate`
  );
  return data;
}

export async function predictDocumentAnomaly(
  documentId: string,
  threshold?: number
): Promise<import('../types').PredictionResult> {
  const url = threshold !== undefined
    ? `/api/documents/${documentId}/predict?threshold=${threshold}`
    : `/api/documents/${documentId}/predict`;
  const { data } = await apiClient.post<import('../types').PredictionResult>(url);
  return data;
}

export async function getDocumentPredictions(
  documentId: string
): Promise<import('../types').PredictionResult[]> {
  const { data } = await apiClient.get<import('../types').PredictionResult[]>(
    `/api/documents/${documentId}/predictions`
  );
  return data;
}

export async function predictBatch(
  documentIds: string[],
  threshold?: number
): Promise<any> {
  const url = threshold !== undefined
    ? `/api/ml/predict-batch?custom_threshold=${threshold}`
    : '/api/ml/predict-batch';
  const { data } = await apiClient.post(url, { document_ids: documentIds });
  return data;
}

export async function getMLMonitoringStats(): Promise<import('../types').MLMonitoringStats> {
  const { data } = await apiClient.get<import('../types').MLMonitoringStats>('/api/ml/monitoring');
  return data;
}

// ── Phase 5: Advanced ML ─────────────────────────────────────────
export async function predictAdvancedAutoencoder(
  documentId: string
): Promise<import('../types').AdvancedMLPrediction> {
  const { data } = await apiClient.post<import('../types').AdvancedMLPrediction>(
    `/api/documents/${documentId}/advanced-predict`
  );
  return data;
}

export async function trainAdvancedAutoencoder(params: {
  model_version?: string;
  input_mode?: string;
  epochs?: number;
  learning_rate?: number;
}): Promise<any> {
  const { data } = await apiClient.post('/api/ml/advanced/train', params);
  return data;
}

export async function getModelComparison(): Promise<import('../types').ModelComparisonResult> {
  const { data } = await apiClient.get<import('../types').ModelComparisonResult>(
    '/api/ml/models/comparison'
  );
  return data;
}

// ── Phase 6: Blockchain ──────────────────────────────────────────
export async function registerOnBlockchain(
  documentId: string,
  issuerReference = 'Official Government Authority'
): Promise<import('../types').BlockchainRegisterResponse> {
  const { data } = await apiClient.post<import('../types').BlockchainRegisterResponse>(
    `/api/blockchain/register/${documentId}`,
    { issuer_reference: issuerReference, document_version: '1.0' }
  );
  return data;
}

export async function verifyOnBlockchain(
  documentId: string
): Promise<import('../types').BlockchainVerifyResponse> {
  const { data } = await apiClient.get<import('../types').BlockchainVerifyResponse>(
    `/api/blockchain/verify/${documentId}`
  );
  return data;
}

export async function getBlockchainHistory(
  documentId: string
): Promise<import('../types').BlockchainHistoryResponse> {
  const { data } = await apiClient.get<import('../types').BlockchainHistoryResponse>(
    `/api/blockchain/history/${documentId}`
  );
  return data;
}

// ── Phase 7: IPFS ────────────────────────────────────────────────
export async function uploadToIPFS(
  documentId: string
): Promise<import('../types').IPFSUploadResponse> {
  const { data } = await apiClient.post<import('../types').IPFSUploadResponse>(
    `/api/ipfs/upload/${documentId}`
  );
  return data;
}

export async function verifyIPFSContent(
  documentId: string
): Promise<import('../types').IPFSVerifyResponse> {
  const { data } = await apiClient.get<import('../types').IPFSVerifyResponse>(
    `/api/ipfs/verify/${documentId}`
  );
  return data;
}

export function getIPFSContentUrl(documentId: string): string {
  return `${BASE_URL}/api/ipfs/${documentId}`;
}

// ── Unified Integrity Verification ───────────────────────────────
export async function registerDocumentIntegrity(
  documentId: string,
  issuerReference = 'Official Government Authority'
): Promise<any> {
  const { data } = await apiClient.post(
    `/api/documents/${documentId}/register-integrity`,
    null,
    { params: { issuer_reference: issuerReference } }
  );
  return data;
}

export async function verifyDocumentIntegrity(
  documentId: string
): Promise<import('../types').IntegratedVerificationResponse> {
  const { data } = await apiClient.post<import('../types').IntegratedVerificationResponse>(
    `/api/documents/${documentId}/verify-integrity`
  );
  return data;
}

export async function getIntegrityHistory(documentId: string): Promise<any[]> {
  const { data } = await apiClient.get<any[]>(
    `/api/documents/${documentId}/integrity-history`
  );
  return data;
}

// ── Phase Demo: Forensic Simulation & Synthetic Data ─────────────
export async function simulateDocumentTampering(
  documentId: string
): Promise<import('../types').TamperingSimulationResponse> {
  const { data } = await apiClient.post<import('../types').TamperingSimulationResponse>(
    `/api/demo/tamper/${documentId}`
  );
  return data;
}

export async function seedTrainingData(
  normalCount = 20,
  anomalousCount = 5
): Promise<import('../types').SeedDataResponse> {
  const { data } = await apiClient.post<import('../types').SeedDataResponse>(
    '/api/demo/seed-training-data',
    null,
    { params: { normal_count: normalCount, anomalous_count: anomalousCount } }
  );
  return data;
}

export async function getSyntheticDataset(
  normalCount = 10,
  anomalousCount = 5
): Promise<any> {
  const { data } = await apiClient.get('/api/demo/synthetic-dataset', {
    params: { normal_count: normalCount, anomalous_count: anomalousCount },
  });
  return data;
}









