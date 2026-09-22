"""Helpers for calibrating model probability outputs."""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


class ProbabilityOnlyClassifier(ClassifierMixin, BaseEstimator):
    """Expose predict_proba so calibration uses the project's raw score."""

    def __init__(self, estimator: Any):
        self.estimator = estimator
        self.classes_ = estimator.classes_

    def fit(self, x: pd.DataFrame, y: pd.Series) -> "ProbabilityOnlyClassifier":
        return self

    def predict_proba(self, x: pd.DataFrame) -> np.ndarray:
        return self.estimator.predict_proba(x)
