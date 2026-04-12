from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURES_NUMERIC = ["play_minutes", "listening_hour"]
FEATURES_CATEGORICAL = ["platform", "reason_start", "reason_end"]
FEATURES_BOOLEAN = ["shuffle", "offline", "incognito_mode"]


def train_skip_prediction_model(df: pd.DataFrame) -> dict:
    model_df = df.copy()
    model_df = model_df[model_df["is_song"]].copy()

    if model_df.empty or model_df["is_skipped"].nunique() < 2:
        return {"status": "insufficient_data"}

    X = model_df[FEATURES_NUMERIC + FEATURES_CATEGORICAL + FEATURES_BOOLEAN]
    y = model_df["is_skipped"].astype(int)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, FEATURES_NUMERIC),
            ("cat", categorical_pipeline, FEATURES_CATEGORICAL),
            ("bool", "passthrough", FEATURES_BOOLEAN),
        ]
    )

    clf = LogisticRegression(max_iter=200, class_weight="balanced")

    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", clf)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, preds, output_dict=True, zero_division=0)

    return {
        "status": "ok",
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "report": report,
        "pipeline": pipeline,
    }
