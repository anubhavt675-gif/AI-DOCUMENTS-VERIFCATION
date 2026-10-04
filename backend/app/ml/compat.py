"""
Scikit-Learn Compatibility Layer with Graceful Fallback.
Provides transparent fallback implementations for StandardScaler, IsolationForest,
and standard evaluation metrics when native scikit-learn C-extensions are blocked
by Windows Smart App Control / WDAC policies.
"""
import math
import numpy as np

# Try importing real scikit-learn first
_SKLEARN_AVAILABLE = False
try:
    from sklearn.ensemble import IsolationForest as _SklearnIForest
    from sklearn.preprocessing import StandardScaler as _SklearnScaler
    from sklearn.metrics import (
        accuracy_score as _sklearn_accuracy,
        average_precision_score as _sklearn_avg_prec,
        confusion_matrix as _sklearn_cm,
        f1_score as _sklearn_f1,
        precision_score as _sklearn_prec,
        recall_score as _sklearn_rec,
        roc_auc_score as _sklearn_roc_auc,
    )
    _SKLEARN_AVAILABLE = True
except (ImportError, OSError):
    _SKLEARN_AVAILABLE = False


if _SKLEARN_AVAILABLE:
    IsolationForest = _SklearnIForest
    StandardScaler = _SklearnScaler
    accuracy_score = _sklearn_accuracy
    average_precision_score = _sklearn_avg_prec
    confusion_matrix = _sklearn_cm
    f1_score = _sklearn_f1
    precision_score = _sklearn_prec
    recall_score = _sklearn_rec
    roc_auc_score = _sklearn_roc_auc
else:
    # Pure-NumPy StandardScaler
    class StandardScaler:
        def __init__(self, with_mean: bool = True, with_std: bool = True):
            self.with_mean = with_mean
            self.with_std = with_std
            self.mean_ = None
            self.scale_ = None
            self.var_ = None
            self.n_samples_seen_ = 0

        def fit(self, X, y=None):
            X = np.asarray(X, dtype=np.float64)
            self.n_samples_seen_ = X.shape[0]
            if self.with_mean:
                self.mean_ = np.mean(X, axis=0)
            else:
                self.mean_ = np.zeros(X.shape[1], dtype=np.float64)

            if self.with_std:
                self.var_ = np.var(X, axis=0)
                self.scale_ = np.sqrt(self.var_)
                self.scale_[self.scale_ == 0.0] = 1.0
            else:
                self.scale_ = np.ones(X.shape[1], dtype=np.float64)
            return self

        def transform(self, X):
            X = np.asarray(X, dtype=np.float64)
            res = X.copy()
            if self.with_mean and self.mean_ is not None:
                res -= self.mean_
            if self.with_std and self.scale_ is not None:
                res /= self.scale_
            return res

        def fit_transform(self, X, y=None):
            return self.fit(X, y).transform(X)

    # Pure-NumPy Isolation Forest Implementation (Liu, Ting, Zhou 2008)
    class _IsolationTreeNode:
        def __init__(self, size: int):
            self.size = size
            self.split_feat = None
            self.split_val = None
            self.left = None
            self.right = None
            self.is_leaf = True

    def _c_factor(n: int) -> float:
        """Average path length of unsuccessful searches in Binary Search Tree."""
        if n <= 1:
            return 1.0
        if n == 2:
            return 1.0
        euler_gamma = 0.5772156649
        return 2.0 * (math.log(n - 1) + euler_gamma) - (2.0 * (n - 1) / n)

    class _IsolationTree:
        def __init__(self, max_depth: int, rng: np.random.RandomState):
            self.max_depth = max_depth
            self.rng = rng
            self.root = None

        def fit(self, X: np.ndarray):
            self.root = self._build_tree(X, depth=0)
            return self

        def _build_tree(self, X: np.ndarray, depth: int) -> _IsolationTreeNode:
            n_samples, n_features = X.shape
            node = _IsolationTreeNode(size=n_samples)

            if depth >= self.max_depth or n_samples <= 1:
                return node

            # Check if all rows are identical
            min_vals = np.min(X, axis=0)
            max_vals = np.max(X, axis=0)
            valid_feats = np.where(max_vals > min_vals)[0]
            if len(valid_feats) == 0:
                return node

            feat = self.rng.choice(valid_feats)
            f_min = min_vals[feat]
            f_max = max_vals[feat]
            split_val = self.rng.uniform(f_min, f_max)

            left_mask = X[:, feat] < split_val
            right_mask = ~left_mask

            if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                return node

            node.is_leaf = False
            node.split_feat = feat
            node.split_val = split_val
            node.left = self._build_tree(X[left_mask], depth + 1)
            node.right = self._build_tree(X[right_mask], depth + 1)
            return node

        def path_length(self, X: np.ndarray) -> np.ndarray:
            lengths = np.zeros(len(X), dtype=np.float64)
            for i, x in enumerate(X):
                node = self.root
                d = 0
                while node and not node.is_leaf:
                    if x[node.split_feat] < node.split_val:
                        node = node.left
                    else:
                        node = node.right
                    d += 1
                if node:
                    lengths[i] = d + _c_factor(node.size)
                else:
                    lengths[i] = d
            return lengths

    class IsolationForest:
        def __init__(
            self,
            n_estimators: int = 100,
            max_samples: float or int = "auto",
            contamination: float = 0.1,
            random_state: int = 42,
            **kwargs,
        ):
            self.n_estimators = n_estimators
            self.max_samples = max_samples
            self.contamination = contamination
            self.random_state = random_state
            self.trees = []
            self.offset_ = -0.5
            self.c_ = 1.0

        def fit(self, X, y=None):
            X = np.asarray(X, dtype=np.float64)
            n_samples = len(X)
            if self.max_samples == "auto" or self.max_samples > n_samples:
                subsample_size = min(256, n_samples)
            elif isinstance(self.max_samples, float):
                subsample_size = max(1, int(self.max_samples * n_samples))
            else:
                subsample_size = min(int(self.max_samples), n_samples)

            max_depth = int(math.ceil(math.log2(max(subsample_size, 2))))
            rng = np.random.RandomState(self.random_state)
            self.c_ = _c_factor(subsample_size)

            self.trees = []
            for _ in range(self.n_estimators):
                idx = rng.choice(n_samples, size=subsample_size, replace=False)
                tree = _IsolationTree(max_depth=max_depth, rng=rng)
                tree.fit(X[idx])
                self.trees.append(tree)

            # Fit offset based on contamination
            scores = self.score_samples(X)
            if self.contamination == "auto":
                self.offset_ = -0.5
            else:
                self.offset_ = float(np.percentile(scores, 100.0 * self.contamination))
            return self

        def score_samples(self, X) -> np.ndarray:
            X = np.asarray(X, dtype=np.float64)
            paths = np.zeros(len(X), dtype=np.float64)
            for tree in self.trees:
                paths += tree.path_length(X)
            avg_path = paths / len(self.trees)
            # scikit-learn definition: score = - 2^(- avg_path / c)
            return -np.power(2.0, -avg_path / self.c_)

        def decision_function(self, X) -> np.ndarray:
            return self.score_samples(X) - self.offset_

        def predict(self, X) -> np.ndarray:
            # 1 for inliers, -1 for outliers
            df = self.decision_function(X)
            preds = np.ones(len(X), dtype=np.int32)
            preds[df < 0] = -1
            return preds

    # Evaluation Metrics
    def precision_score(y_true, y_pred, pos_label=1, zero_division=0):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fp = np.sum((y_true != pos_label) & (y_pred == pos_label))
        if tp + fp == 0:
            return float(zero_division)
        return float(tp / (tp + fp))

    def recall_score(y_true, y_pred, pos_label=1, zero_division=0):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fn = np.sum((y_true == pos_label) & (y_pred != pos_label))
        if tp + fn == 0:
            return float(zero_division)
        return float(tp / (tp + fn))

    def f1_score(y_true, y_pred, pos_label=1, zero_division=0):
        p = precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
        r = recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
        if p + r == 0:
            return float(zero_division)
        return float(2 * p * r / (p + r))

    def accuracy_score(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        if len(y_true) == 0:
            return 0.0
        return float(np.mean(y_true == y_pred))

    def confusion_matrix(y_true, y_pred, labels=None):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        if labels is None:
            labels = np.unique(np.concatenate([y_true, y_pred]))
        matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
        for i, l_true in enumerate(labels):
            for j, l_pred in enumerate(labels):
                matrix[i, j] = np.sum((y_true == l_true) & (y_pred == l_pred))
        return matrix

    def roc_auc_score(y_true, y_score):
        y_true = np.asarray(y_true)
        y_score = np.asarray(y_score)
        pos = y_score[y_true == 1]
        neg = y_score[y_true == 0]
        if len(pos) == 0 or len(neg) == 0:
            return 0.5
        # Fast Mann-Whitney U test calculation
        ranks = np.argsort(np.argsort(y_score)) + 1
        pos_rank_sum = np.sum(ranks[y_true == 1])
        n_pos = len(pos)
        n_neg = len(neg)
        u = pos_rank_sum - (n_pos * (n_pos + 1)) / 2.0
        return float(u / (n_pos * n_neg))

    def average_precision_score(y_true, y_score):
        y_true = np.asarray(y_true)
        y_score = np.asarray(y_score)
        order = np.argsort(y_score)[::-1]
        y_true_sorted = y_true[order]
        n_pos = np.sum(y_true == 1)
        if n_pos == 0:
            return 0.0
        tp = np.cumsum(y_true_sorted == 1)
        fp = np.cumsum(y_true_sorted == 0)
        prec = tp / (tp + fp)
        rec = tp / n_pos
        # Integrate area under PR curve using step trapezoids
        rec_diff = np.diff(np.concatenate([[0], rec]))
        return float(np.sum(prec * rec_diff))
