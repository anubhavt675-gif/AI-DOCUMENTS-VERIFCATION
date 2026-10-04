import { useState, useEffect, useCallback } from 'react';
import {
  listDocuments,
  getDocument,
  getAnalysis,
  processDocument,
  getFeatures,
  generateFeatures,
  predictDocumentAnomaly,
  getDocumentPredictions,
  listMLModels,
  getActiveMLModel,
  activateMLModel,
  trainModel,
  getMLMonitoringStats,
} from '../services/api';
import type {
  Document,
  DocumentListResponse,
  DocumentAnalysis,
  DocumentFeaturesResponse,
  PredictionResult,
  MLModel,
  MLMonitoringStats,
  TrainModelParams,
} from '../types';

// ── useDocuments ──────────────────────────────────────────────────────────────
export function useDocuments() {
  const [data, setData] = useState<DocumentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listDocuments();
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load documents.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

// ── useDocument ───────────────────────────────────────────────────────────────
export function useDocument(documentId: string | undefined) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    getDocument(documentId)
      .then(setDocument)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [documentId]);

  return { document, loading, error };
}

// ── useDocumentAnalysis ───────────────────────────────────────────────────────
export function useDocumentAnalysis(documentId: string | undefined) {
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAnalysis(documentId);
      setAnalysis(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load analysis.');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const reprocess = useCallback(async () => {
    if (!documentId) return;
    setProcessing(true);
    setError(null);
    try {
      await processDocument(documentId);
      await fetchAnalysis();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Processing failed.');
    } finally {
      setProcessing(false);
    }
  }, [documentId, fetchAnalysis]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  return { analysis, loading, processing, error, refetch: fetchAnalysis, reprocess };
}

// ── useDocumentFeatures (Phase 3) ─────────────────────────────────────────────
export function useDocumentFeatures(documentId: string | undefined) {
  const [features, setFeatures] = useState<DocumentFeaturesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeatures = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getFeatures(documentId);
      setFeatures(data);
    } catch (e: unknown) {
      // If 404, document hasn't had features extracted yet; don't treat as blocking error
      setFeatures(null);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const extract = useCallback(async () => {
    if (!documentId) return;
    setGenerating(true);
    setError(null);
    try {
      await generateFeatures(documentId);
      await fetchFeatures();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Feature extraction failed.');
    } finally {
      setGenerating(false);
    }
  }, [documentId, fetchFeatures]);

  useEffect(() => {
    fetchFeatures();
  }, [fetchFeatures]);

  return { features, loading, generating, error, refetch: fetchFeatures, extract };
}

// ── useDocumentPredictions (Phase 4) ──────────────────────────────────────────
export function useDocumentPredictions(documentId: string | undefined) {
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPredictions = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getDocumentPredictions(documentId);
      setPredictions(data);
    } catch (e: unknown) {
      setPredictions([]);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const predict = useCallback(
    async (threshold?: number) => {
      if (!documentId) return;
      setPredicting(true);
      setError(null);
      try {
        const result = await predictDocumentAnomaly(documentId, threshold);
        setPredictions((prev) => [result, ...prev]);
        return result;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Anomaly detection failed.';
        setError(msg);
        throw e;
      } finally {
        setPredicting(false);
      }
    },
    [documentId]
  );

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  const latestPrediction = predictions.length > 0 ? predictions[0] : null;

  return {
    predictions,
    latestPrediction,
    loading,
    predicting,
    error,
    refetch: fetchPredictions,
    predict,
  };
}

// ── useMLModels (Phase 4) ─────────────────────────────────────────────────────
export function useMLModels() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [activeModel, setActiveModel] = useState<MLModel | null>(null);
  const [monitoringStats, setMonitoringStats] = useState<MLMonitoringStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [allModels, active, stats] = await Promise.all([
        listMLModels(),
        getActiveMLModel(),
        getMLMonitoringStats(),
      ]);
      setModels(allModels);
      setActiveModel(active);
      setMonitoringStats(stats);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load ML models data.');
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerTrain = useCallback(
    async (params?: TrainModelParams) => {
      setTraining(true);
      setError(null);
      try {
        const res = await trainModel(params);
        await fetchData();
        return res;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Model training failed.';
        setError(msg);
        throw e;
      } finally {
        setTraining(false);
      }
    },
    [fetchData]
  );

  const activate = useCallback(
    async (modelId: string) => {
      setLoading(true);
      setError(null);
      try {
        const updated = await activateMLModel(modelId);
        await fetchData();
        return updated;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Failed to activate model.';
        setError(msg);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [fetchData]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    models,
    activeModel,
    monitoringStats,
    loading,
    training,
    error,
    refetch: fetchData,
    train: triggerTrain,
    activate,
  };
}

