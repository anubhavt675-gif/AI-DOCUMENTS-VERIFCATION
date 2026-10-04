import React, { useState } from 'react';
import { useMLModels } from '../hooks/useDocuments';
import { ModelComparisonTab } from '../components/ModelComparisonTab';

interface MLAnomalyDashboardProps {
  onBackToDocuments?: () => void;
  onViewDocument?: (docId: string) => void;
}

export const MLAnomalyDashboard: React.FC<MLAnomalyDashboardProps> = ({
  onBackToDocuments,
}) => {
  const {
    models,
    activeModel,
    monitoringStats,
    loading,
    training,
    error,
    refetch,
    train,
    activate,
  } = useMLModels();

  const [activeTab, setActiveTab] = useState<'models' | 'comparison'>('models');
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [nEstimators, setNEstimators] = useState<number>(300);
  const [contamination, setContamination] = useState<string>('auto');
  const [randomSeed, setRandomSeed] = useState<number>(42);
  const [versionInput, setVersionInput] = useState<string>('');
  const [setActiveCheck, setSetActiveCheck] = useState<boolean>(true);
  const [trainStatusMsg, setTrainStatusMsg] = useState<string | null>(null);

  const handleTrainSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTrainStatusMsg(null);
    try {
      const res = await train({
        model_name: 'IsolationForest',
        model_version: versionInput.trim() ? versionInput.trim() : undefined,
        n_estimators: nEstimators,
        contamination: contamination === 'auto' ? 'auto' : parseFloat(contamination),
        random_state: randomSeed,
        set_active: setActiveCheck,
      });
      setTrainStatusMsg(`Model version ${res.model_version} trained successfully!`);
      setTimeout(() => {
        setShowTrainModal(false);
        setTrainStatusMsg(null);
      }, 1500);
    } catch (err: any) {
      setTrainStatusMsg(`Error: ${err.message || 'Training failed'}`);
    }
  };

  const handleActivate = async (modelId: string) => {
    try {
      await activate(modelId);
    } catch (err: any) {
      alert(`Failed to activate model: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Phase 4 Architecture
            </span>
            <span className="text-xs text-slate-400">scikit-learn • Isolation Forest</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Machine Learning Anomaly Detection</h1>
          <p className="text-sm text-slate-400 mt-1">
            Unsupervised statistical outlier detection on 85-dimensional Phase 3 feature representations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {onBackToDocuments && (
            <button
              onClick={onBackToDocuments}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
            >
              ← Back to Documents
            </button>
          )}
          <button
            onClick={() => refetch()}
            disabled={loading}
            className="px-3.5 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
          >
            ↻ Refresh
          </button>
          <button
            onClick={() => setShowTrainModal(true)}
            className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-md hover:shadow-indigo-500/25 transition"
          >
            + Train Model
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Forensic Disclaimer */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-3">
        <span className="text-lg">⚖️</span>
        <div>
          <span className="font-semibold text-amber-200">Legal & Forensic Disclaimer:</span>{' '}
          The ML anomaly score reflects statistical divergence from learned document patterns and does
          not constitute conclusive or legal proof of document tampering or forgery. Documents flagged as
          statistically anomalous warrant multi-layer forensic or human review.
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-4 mt-2 mb-2">
        <button
          onClick={() => setActiveTab('models')}
          className={`pb-2.5 text-sm font-semibold transition border-b-2 ${
            activeTab === 'models'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          🌲 Isolation Forest Models & Monitoring
        </button>
        <button
          onClick={() => setActiveTab('comparison')}
          className={`pb-2.5 text-sm font-semibold transition border-b-2 ${
            activeTab === 'comparison'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          ⚡ Model Benchmark (Autoencoder vs. Isolation Forest)
        </button>
      </div>

      {activeTab === 'comparison' ? (
        <ModelComparisonTab />
      ) : (
        <>
          {/* Monitoring & Key Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Model */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs uppercase tracking-wider font-semibold text-slate-400">
            Active Production Model
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              {activeModel ? activeModel.model_version : 'None Active'}
            </span>
            {activeModel && (
              <span className="px-2 py-0.5 text-xs rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Active
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {activeModel
              ? `${activeModel.model_name} • Features v${activeModel.feature_version}`
              : 'Train and activate a model to enable inference'}
          </div>
        </div>

        {/* Training Samples */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs uppercase tracking-wider font-semibold text-slate-400">
            Learned Baseline Samples
          </div>
          <div className="mt-2 text-2xl font-bold text-indigo-400">
            {activeModel ? activeModel.training_sample_count : 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Documents fit in training distribution
          </div>
        </div>

        {/* Total Predictions */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs uppercase tracking-wider font-semibold text-slate-400">
            Total Inferences Evaluated
          </div>
          <div className="mt-2 text-2xl font-bold text-white">
            {monitoringStats ? monitoringStats.total_predictions : 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {monitoringStats && monitoringStats.total_predictions > 0
              ? `${monitoringStats.normal_count} Normal (${(
                  (monitoringStats.normal_count / monitoringStats.total_predictions) *
                  100
                ).toFixed(1)}%) • ${monitoringStats.anomalous_count} Anomalous`
              : 'No predictions recorded yet'}
          </div>
        </div>

        {/* Average Anomaly Score */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs uppercase tracking-wider font-semibold text-slate-400">
            Average Anomaly Score
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {monitoringStats ? monitoringStats.average_anomaly_score.toFixed(3) : '0.000'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Normalized range: 0.0 (Normal) to 1.0 (Outlier)
          </div>
        </div>
      </div>

      {/* Active Model Evaluation / Metrics Card */}
      {activeModel && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
            <div>
              <h2 className="text-lg font-bold text-white">
                Model Evaluation & Configuration: {activeModel.model_name} (v{activeModel.model_version})
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Architecture: Isolation Forest • Features: {activeModel.feature_names.length} inputs
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 text-xs rounded bg-slate-800 text-slate-300 font-mono">
                n_estimators: {activeModel.configuration?.n_estimators ?? 300}
              </span>
              <span className="px-2.5 py-1 text-xs rounded bg-slate-800 text-slate-300 font-mono">
                contamination: {activeModel.configuration?.contamination ?? 'auto'}
              </span>
              <span className="px-2.5 py-1 text-xs rounded bg-slate-800 text-slate-300 font-mono">
                seed: {activeModel.configuration?.random_state ?? 42}
              </span>
            </div>
          </div>

          {activeModel.metrics ? (
            <div className="mt-6 space-y-6">
              {/* Metric stats row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">Precision</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {activeModel.metrics.precision !== null && activeModel.metrics.precision !== undefined
                      ? `${(activeModel.metrics.precision * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">Recall</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {activeModel.metrics.recall !== null && activeModel.metrics.recall !== undefined
                      ? `${(activeModel.metrics.recall * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">F1 Score</div>
                  <div className="text-lg font-bold text-indigo-400 mt-1">
                    {activeModel.metrics.f1_score !== null && activeModel.metrics.f1_score !== undefined
                      ? activeModel.metrics.f1_score.toFixed(3)
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">Accuracy</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {activeModel.metrics.accuracy !== null && activeModel.metrics.accuracy !== undefined
                      ? `${(activeModel.metrics.accuracy * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">Specificity</div>
                  <div className="text-lg font-bold text-white mt-1">
                    {activeModel.metrics.specificity !== null && activeModel.metrics.specificity !== undefined
                      ? `${(activeModel.metrics.specificity * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                  <div className="text-xs text-slate-400">ROC-AUC</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">
                    {activeModel.metrics.roc_auc !== null && activeModel.metrics.roc_auc !== undefined
                      ? activeModel.metrics.roc_auc.toFixed(3)
                      : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Confusion Matrix */}
              {activeModel.metrics.confusion_matrix && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-3">Confusion Matrix</h3>
                  <div className="inline-block bg-slate-950 p-4 rounded-lg border border-slate-800 font-mono text-sm">
                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="p-2"></div>
                      <div className="p-2 text-slate-400 font-semibold">Pred Normal</div>
                      <div className="p-2 text-slate-400 font-semibold">Pred Anomaly</div>

                      <div className="p-2 text-slate-400 font-semibold text-left">Actual Normal</div>
                      <div className="p-2.5 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/40">
                        TN: {activeModel.metrics.confusion_matrix.tn}
                      </div>
                      <div className="p-2.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/40">
                        FP: {activeModel.metrics.confusion_matrix.fp}
                      </div>

                      <div className="p-2 text-slate-400 font-semibold text-left">Actual Anomaly</div>
                      <div className="p-2.5 rounded bg-rose-950/40 text-rose-300 border border-rose-800/40">
                        FN: {activeModel.metrics.confusion_matrix.fn}
                      </div>
                      <div className="p-2.5 rounded bg-indigo-950/40 text-indigo-300 border border-indigo-800/40">
                        TP: {activeModel.metrics.confusion_matrix.tp}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-4 p-4 rounded-lg bg-slate-800/40 border border-slate-800 text-xs text-slate-400">
              <span className="font-semibold text-slate-300">Unsupervised Baseline Model:</span>{' '}
              Trained on unlabelled document distribution ({activeModel.training_sample_count} samples).
              Standard precision and recall metrics become available when an external ground-truth benchmark is evaluated.
            </div>
          )}
        </div>
      )}

      {/* Registered Models Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Model Registry</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Trained model versions, serialized artifacts, and deployment status
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {models.length} model{models.length !== 1 ? 's' : ''} registered
          </span>
        </div>

        {models.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No models have been registered yet. Click &quot;Train Model&quot; to build an Isolation Forest model.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950 text-xs uppercase tracking-wider text-slate-400 font-medium">
                <tr>
                  <th className="px-5 py-3">Version</th>
                  <th className="px-5 py-3">Architecture</th>
                  <th className="px-5 py-3">Features Ver</th>
                  <th className="px-5 py-3">Training Samples</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {models.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-3 font-semibold text-white">{m.model_version}</td>
                    <td className="px-5 py-3 font-sans text-slate-300">{m.model_name}</td>
                    <td className="px-5 py-3 text-slate-400">v{m.feature_version}</td>
                    <td className="px-5 py-3 text-indigo-400 font-sans">{m.training_sample_count} docs</td>
                    <td className="px-5 py-3">
                      {m.is_active ? (
                        <span className="px-2 py-0.5 rounded text-[11px] font-sans font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active Production
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[11px] font-sans text-slate-400 bg-slate-800">
                          Archived
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-slate-400">
                      {new Date(m.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {!m.is_active && (
                        <button
                          onClick={() => handleActivate(m.id)}
                          className="px-3 py-1 text-xs font-sans font-medium text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition"
                        >
                          Set Active
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      </>
      )}

      {/* Train Model Modal */}
      {showTrainModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white">Train Isolation Forest Model</h3>
              <button
                onClick={() => setShowTrainModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleTrainSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Model Version (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 1.1.0 (auto-generated if blank)"
                  value={versionInput}
                  onChange={(e) => setVersionInput(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Number of Estimators (Trees)
                </label>
                <input
                  type="number"
                  min="20"
                  max="1000"
                  step="10"
                  value={nEstimators}
                  onChange={(e) => setNEstimators(parseInt(e.target.value) || 300)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
                />
                <span className="text-[11px] text-slate-500">Recommended: 200 - 500 trees</span>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Contamination Parameter
                </label>
                <select
                  value={contamination}
                  onChange={(e) => setContamination(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="auto">auto (recommended for official documents)</option>
                  <option value="0.05">0.05 (5% estimated anomalous)</option>
                  <option value="0.10">0.10 (10% estimated anomalous)</option>
                  <option value="0.15">0.15 (15% estimated anomalous)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Reproducible Random Seed
                </label>
                <input
                  type="number"
                  value={randomSeed}
                  onChange={(e) => setRandomSeed(parseInt(e.target.value) || 42)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="setActive"
                  checked={setActiveCheck}
                  onChange={(e) => setSetActiveCheck(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                />
                <label htmlFor="setActive" className="text-xs text-slate-300">
                  Automatically set as active production model upon completion
                </label>
              </div>

              {trainStatusMsg && (
                <div
                  className={`p-3 rounded-lg text-xs ${
                    trainStatusMsg.startsWith('Error')
                      ? 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                      : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                  }`}
                >
                  {trainStatusMsg}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowTrainModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={training}
                  className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition disabled:opacity-50"
                >
                  {training ? 'Training...' : 'Start Training'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
