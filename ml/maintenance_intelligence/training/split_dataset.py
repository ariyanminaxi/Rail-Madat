"""Split the dataset into training, validation, and test sets."""

from typing import Tuple

import numpy as np
import pandas as pd

from app.maintenance_intelligence.config import RANDOM_SEED


def split_by_case(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    case_ids: pd.Series,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split features and labels by unique case ID."""
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

    unique_cases = case_ids.unique()
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_cases)

    n = len(unique_cases)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_cases = set(unique_cases[:n_train])
    val_cases = set(unique_cases[n_train : n_train + n_val])
    test_cases = set(unique_cases[n_train + n_val :])

    train_mask = case_ids.isin(train_cases)
    val_mask = case_ids.isin(val_cases)
    test_mask = case_ids.isin(test_cases)

    X_train = features[train_mask].reset_index(drop=True)
    y_train = labels[train_mask].reset_index(drop=True)

    X_val = features[val_mask].reset_index(drop=True)
    y_val = labels[val_mask].reset_index(drop=True)

    X_test = features[test_mask].reset_index(drop=True)
    y_test = labels[test_mask].reset_index(drop=True)

    print(f"Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
    print(f"Unique cases: train={len(train_cases)}, val={len(val_cases)}, test={len(test_cases)}")

    assert train_cases.isdisjoint(val_cases), "Leakage: train and val share cases"
    assert train_cases.isdisjoint(test_cases), "Leakage: train and test share cases"
    assert val_cases.isdisjoint(test_cases), "Leakage: val and test share cases"
    print("Leakage check passed: no case overlap between splits")

    return X_train, X_val, X_test, y_train, y_val, y_test
