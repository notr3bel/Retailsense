"""
Model Data Loading and Preprocessing Utilities for RetailSense-AI.
Handles data merging, feature selection, leakage prevention, train/test splitting,
and Scikit-Learn ColumnTransformer pipeline building.
"""

import os
from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from etl.utils import setup_logger

logger = setup_logger("ML_ModelUtils")

# Explicit list of columns excluded from training to prevent target leakage and ID noise
EXCLUDED_FEATURES = [
    "customer_id",
    "recency_days",
    "churn",
    "first_purchase",
    "last_purchase",
    "favorite_product"
]

LEAKAGE_NOTES = (
    "recency_days was explicitly excluded from model training features because churn "
    "was defined using the rule (recency_days >= 90). Including recency_days causes direct "
    "target leakage and artificially inflated performance metrics. customer_id, first_purchase, "
    "and last_purchase were excluded as identifiers / raw dates. favorite_product was excluded "
    "due to high cardinality stock codes."
)


def load_and_merge_data(
    features_path: str = "data/ml/customer_features.csv",
    churn_path: str = "data/ml/customer_churn_dataset.csv"
) -> pd.DataFrame:
    """
    Loads customer features and churn labels, merging on customer_id.
    
    Args:
        features_path: Path to customer_features.csv
        churn_path: Path to customer_churn_dataset.csv
        
    Returns:
        pd.DataFrame: Merged dataset containing features and target 'churn'.
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features dataset not found at: {features_path}")
    if not os.path.exists(churn_path):
        raise FileNotFoundError(f"Churn dataset not found at: {churn_path}")

    logger.info(f"Loading features from {features_path} and churn labels from {churn_path}...")
    df_feat = pd.read_csv(features_path)
    df_churn = pd.read_csv(churn_path)

    # Ensure customer_id column types match
    df_feat["customer_id"] = df_feat["customer_id"].astype(int, errors="ignore")
    df_churn["customer_id"] = df_churn["customer_id"].astype(int, errors="ignore")

    merged_df = pd.merge(df_feat, df_churn[["customer_id", "churn"]], on="customer_id", how="inner")
    logger.info(f"Successfully merged datasets: {len(merged_df):,} customers, {len(merged_df.columns)} total columns.")
    return merged_df


def prepare_preprocessor(df: pd.DataFrame, drop_cols: List[str] = None) -> Tuple[pd.DataFrame, pd.Series, List[str], List[str], List[str]]:
    """
    Separates feature matrix X and target vector y, excluding target-leaking and identifier columns.
    
    Args:
        df: Input merged DataFrame.
        drop_cols: List of column names to exclude. Defaults to EXCLUDED_FEATURES.
        
    Returns:
        Tuple: (X, y, num_cols, cat_cols, actual_excluded_cols)
    """
    if drop_cols is None:
        drop_cols = EXCLUDED_FEATURES

    actual_excluded_cols = [col for col in drop_cols if col in df.columns]
    X = df.drop(columns=actual_excluded_cols).copy()
    y = df["churn"].copy() if "churn" in df.columns else pd.Series(dtype=int)

    # Ensure no target leakage columns accidentally remain in X
    assert "recency_days" not in X.columns, "TARGET LEAKAGE ERROR: recency_days is present in feature matrix X!"
    assert "churn" not in X.columns, "TARGET LEAKAGE ERROR: churn target column is present in feature matrix X!"
    assert "customer_id" not in X.columns, "IDENTIFIER ERROR: customer_id is present in feature matrix X!"

    # Identify numeric and categorical columns
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]

    logger.info(f"Selected {len(X.columns)} model input features ({len(num_cols)} numeric, {len(cat_cols)} categorical).")
    logger.info(f"Excluded {len(actual_excluded_cols)} columns to prevent target leakage: {actual_excluded_cols}")
    return X, y, num_cols, cat_cols, actual_excluded_cols


def build_pipeline_preprocessor(num_cols: List[str], cat_cols: List[str]) -> ColumnTransformer:
    """
    Builds a Scikit-Learn ColumnTransformer for numeric scaling and categorical encoding.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
        ],
        remainder="drop"
    )
    return preprocessor


def preprocess_and_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series, ColumnTransformer, List[str], List[str], List[str]]:
    """
    Splits data FIRST, fits ColumnTransformer ONLY on training set X_train_raw to prevent data leakage,
    and returns transformed arrays along with metadata.
    
    Returns:
        Tuple: (X_train, X_test, y_train, y_test, preprocessor, feature_names, original_model_features, excluded_features)
    """
    X, y, num_cols, cat_cols, excluded_features = prepare_preprocessor(df)
    original_model_features = list(X.columns)

    # Stratified Train/Test Split BEFORE fitting preprocessor to avoid test data leakage
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Fit preprocessor strictly on training data
    preprocessor = build_pipeline_preprocessor(num_cols, cat_cols)
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)

    # Extract transformed feature names after OneHotEncoding
    cat_encoder = preprocessor.named_transformers_["cat"]
    encoded_cat_cols = cat_encoder.get_feature_names_out(cat_cols).tolist() if cat_cols else []
    feature_names = num_cols + encoded_cat_cols

    logger.info(f"Preprocessing complete (fitted ONLY on train). Train shape: {X_train.shape}, Test shape: {X_test.shape}.")
    return X_train, X_test, y_train, y_test, preprocessor, feature_names, original_model_features, excluded_features
