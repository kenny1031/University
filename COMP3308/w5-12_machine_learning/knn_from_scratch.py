from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from typing import Literal, Optional, Union, Tuple

import numpy as np


ArrayLike = Union[np.ndarray, list]


def _check_X_y(X: ArrayLike, y: ArrayLike) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validate and convert X, y to numpy arrays.

    Returns
    -------
    X : np.ndarray of shape (n_samples, n_features)
    y : np.ndarray of shape (n_samples,)
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)

    if X.ndim != 2:
        raise ValueError(f"X must be 2D, got shape {X.shape}")
    if y.ndim != 1:
        raise ValueError(f"y must be 1D, got shape {y.shape}")
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y must have same number of samples, got {X.shape[0]} and {y.shape[0]}")
    if X.shape[0] == 0:
        raise ValueError("X and y must not be empty")

    return X, y


def _check_X(X: ArrayLike) -> np.ndarray:
    """
    Validate and convert X to numpy array of shape (n_samples, n_features).
    """
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)
    if X.ndim != 2:
        raise ValueError(f"X must be 2D, got shape {X.shape}")
    if X.shape[0] == 0:
        raise ValueError("X must not be empty")
    return X


def train_test_split(
    X: ArrayLike,
    y: ArrayLike,
    test_size: float = 0.2,
    random_state: Optional[int] = None,
    shuffle: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Minimal train-test split utility
    """
    X, y = _check_X_y(X, y)
    if not (0.0 < test_size < 1.0):
        raise ValueError(f"test_size must be between 0 and 1, got {test_size}")
    n_samples = X.shape[0]
    indices = np.arange(n_samples)

    rng = np.random.default_rng(random_state)
    if shuffle:
        rng.shuffle(indices)

    test_count = max(1, int(round(n_samples * test_size)))
    test_idx = indices[:test_count]
    train_idx = indices[test_count:]

    if len(train_idx) == 0:
        raise ValueError("test_size too large; no training samples left")

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


@dataclass
class KNNBase:
    n_neighbours: int = 5
    weights: Literal["uniform", "distance"] = "uniform"
    metric: Literal["euclidean", "manhattan"] = "euclidean"

    def __post_init__(self) -> None:
        if self.n_neighbours <= 0:
            raise ValueError("n_neighbours must be positive")
        if self.weights not in {"uniform", "distance"}:
            raise ValueError("weights must be one of {uniform, distance}")
        if self.metric not in {"euclidean", "manhattan"}:
            raise ValueError("metric must be one of {euclidean, manhattan}")

        self._X_train: Optional[np.ndarray] = None
        self._y_train: Optional[np.ndarray] = None
        self._is_fitted: bool = False

    def fit(self, X: ArrayLike, y: ArrayLike) -> "KNNBase":
        """
        Store training data. KNN is a lazy learner: fit mainly memorises the dataset.
        """
        X, y = _check_X_y(X, y)

        if self.n_neighbours > X.shape[0]:
            raise ValueError(
                f"n_neighbours={self.n_neighbours} "
                f"cannot exceed number of training samples={X.shape[0]}"
            )

        self._X_train = X
        self._y_train = y
        self._is_fitted = True
        return self

    def _check_is_fitted(self) -> None:
        if (not self._is_fitted
            or self._X_train is None
            or self._y_train is None):
            raise ValueError("fit(X, y) must be called before _check_is_fitted()")

    def _pairwise_distances(self, X_query: np.ndarray) -> np.ndarray:
        """
        Compute pairwise distances between query points and training points.

        Returns
        -------
        distances : np.ndarray of shape (n_query, n_train)
        """
        self._check_is_fitted()
        X_train = self._X_train
        assert X_train is not None

        if X_query.shape[1] != X_train.shape[1]:
            raise ValueError(
                f"feature dimension mismatch: query has {X_query.shape[1]}, "
                f"train has {X_train.shape[1]}"
            )

        if self.metric == "euclidean":
            # Vectorised Euclidean distance
            # Shape: (n_query, 1, n_features) - (1, n_train, n_features)
            diff = X_query[:, np.newaxis, :] - X_train[np.newaxis, :, :]
            distances = np.sqrt(np.sum(diff**2, axis=2))
        elif self.metric == "manhattan":
            diff = np.abs(X_query[:, np.newaxis, :] - X_train[np.newaxis, :, :])
            distances = np.sum(diff, axis=2)
        else:
            raise ValueError(f"Unsupported metric {self.metric}")

        return distances

    def kneighbours(
        self,
        X: ArrayLike,
        n_neighbours: Optional[int] = None,
        return_distance: bool = True
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Find k nearest neighbours for each query point.

        Returns
        -------
        distances : np.ndarray of shape (n_query, k)
        indices : np.ndarray of shape (n_query, k)
        """
        self._check_is_fitted()
        X_query = _check_X(X)

        k = n_neighbours if n_neighbours is not None else self.n_neighbours
        if k <= 0:
            raise ValueError("n_neighbours must be positive")

        X_train = self._X_train
        assert X_train is not None

        if k > X_train.shape[0]:
            raise ValueError(
                f"Requested n_neighbours={k} exceeds number of "
                f"training samples={X_train.shape[0]}"
            )

        distances = self._pairwise_distances(X_query)

        # argpartition is more efficient than full argsort for top-k selection
        neighbour_idx = np.argpartition(distances, kth=k-1, axis=1)[:, :k]

        # Sort the selected k neighbours by actual distance
        neighbour_dist = np.take_along_axis(distances, neighbour_idx, axis=1)
        order = np.argsort(neighbour_dist, axis=1)

        neighbour_idx = np.take_along_axis(neighbour_idx, order, axis=1)
        neighbour_dist = np.take_along_axis(neighbour_dist, order, axis=1)

        if return_distance:
            return neighbour_dist, neighbour_idx
        return neighbour_idx

    def _compute_neighbour_weights(self, neighbour_dist: np.ndarray) -> np.ndarray:
        """
        Convert distances to weights.
        """
        if self.weights == "uniform":
            return np.ones_like(neighbour_dist, dtype=float)

        if self.weights == "distance":
            # Avoid division by 0, if exact match exists, give it dominant weight
            eps = 1e-12
            return 1.0 / (neighbour_dist + eps)

        raise ValueError(f"Unsupported weights {self.weights}")


class KNNClassifier(KNNBase):
    def fit(self, X: ArrayLike, y: ArrayLike) -> "KNNClassifier":
        super().fit(X, y)
        assert self._y_train is not None

        self.classes_ = np.unique(self._y_train)
        self.n_classes_ = len(self.classes_)
        return self

    def predict(self, X: ArrayLike) -> np.ndarray:
        self._check_is_fitted()
        distances, indices = self.kneighbours(X, return_distance=True)

        assert self._y_train is not None
        neighbour_labels = self._y_train[indices] # shape: (n_query, k)
        weights = self._compute_neighbour_weights(distances)

        predictions = []
        for labels_row, weights_row in zip(neighbour_labels, weights):
            class_scores = {cls: 0.0 for cls in self.classes_}
            for label, w in zip(labels_row, weights_row):
                class_scores[label] += w

            # Tie-breaking: choose class with largest score; if tied, smaller class value after sorting
            best_class = sorted(class_scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            predictions.append(best_class)

        return np.asarray(predictions)

    def predict_proba(self, X: ArrayLike) -> np.ndarray:
        self._check_is_fitted()
        distances, indices = self.kneighbours(X, return_distance=True)

        assert self._y_train is not None
        neighbour_labels = self._y_train[indices]
        weights = self._compute_neighbour_weights(distances)

        proba = np.zeros((neighbour_labels.shape[0], self.n_classes_), dtype=float)
        class_to_index = {cls: i for i, cls in enumerate(self.classes_)}

        for i, (labels_row, weights_row) in enumerate(zip(neighbour_labels, weights)):
            for label, w in zip(labels_row, weights_row):
                proba[i, class_to_index[label]] += w

            total = proba[i].sum()
            if total > 0:
                proba[i] /= total

        return proba

    def score(self, X: ArrayLike, y: ArrayLike) -> float:
        y_true = np.asarray(y)
        y_pred = self.predict(X)
        if y_true.shape != y_pred.shape:
            raise ValueError("Shape mismatch between y and predicitons")
        return float(np.mean(y_true == y_pred))


class KNNRegressor(KNNBase):
    def predict(self, X: ArrayLike) -> np.ndarray:
        self._check_is_fitted()
        distances, indices = self.kneighbours(X, return_distance=True)

        assert self._y_train is not None
        neighbour_targets = self._y_train[indices].astype(float)
        weights = self._compute_neighbour_weights(distances)

        if self.weights == "uniform":
            return np.mean(neighbour_targets * weights, axis=1)

        weighted_sum = np.sum(neighbour_targets * weights, axis=1)
        weight_sum = np.sum(weights, axis=1)
        return weighted_sum / weight_sum

    def score(self, X: ArrayLike, y: ArrayLike) -> float:
        """
        R^2 score
        """
        y_true = np.asarray(y)
        y_pred = self.predict(X)

        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)

        if ss_tot == 0:
            return 0.0
        return float(1.0 - ss_res / ss_tot)

    def accuracy_score(self, y_true: ArrayLike, y_pred: ArrayLike) -> float:
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError("Shape mismatch between y_true and y_pred")

        return float(np.mean(y_true == y_pred))

    def mean_squared_error(self, y_true: ArrayLike, y_pred: ArrayLike) -> float:
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        if y_true.shape != y_pred.shape:
            raise ValueError("y_true and y_pred must have same shape")

        return float(np.mean((y_true - y_pred)**2))




if __name__ == "__main__":
    # ---------------------------
    # Example 1: Classification
    # ---------------------------
    X_cls = np.array([
        [1.0, 1.0],
        [1.2, 0.9],
        [0.8, 1.1],
        [4.0, 4.0],
        [4.2, 3.9],
        [3.8, 4.1],
        [8.0, 1.0],
        [8.2, 1.1],
        [7.8, 0.9],
    ])
    y_cls = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])

    X_train, X_test, y_train, y_test = train_test_split(
        X_cls, y_cls, test_size=0.33, random_state=42
    )

    clf = KNNClassifier(n_neighbours=3, weights="uniform", metric="euclidean")
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)

    print("=== Classification Example ===")
    print("X_test:")
    print(X_test)
    print("Predicted labels:", y_pred)
    print("True labels     :", y_test)
    print("Predicted probas:")
    print(y_proba)
    print("Accuracy:", clf.score(X_test, y_test))

    dists, idxs = clf.kneighbours(X_test[:2], return_distance=True)
    print("\nNearest neighbors for first 2 query points:")
    print("Distances:\n", dists)
    print("Indices:\n", idxs)

    # ---------------------------
    # Example 2: Regression
    # ---------------------------
    X_reg = np.array([
        [1.0],
        [2.0],
        [3.0],
        [4.0],
        [5.0],
        [6.0],
    ])
    y_reg = np.array([1.2, 1.9, 3.2, 3.9, 5.1, 5.8])

    reg = KNNRegressor(n_neighbours=2, weights="distance", metric="euclidean")
    reg.fit(X_reg, y_reg)

    X_query = np.array([[2.5], [4.5], [5.5]])
    y_reg_pred = reg.predict(X_query)

    print("\n=== Regression Example ===")
    print("Query points:")
    print(X_query.ravel())
    print("Predictions:")
    print(y_reg_pred)