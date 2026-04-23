import pandas as pd
import json
import numpy as np
from app.services.feature_extractor import FEATURE_ORDER
from app.services.feature_extractor import flatten_behavior

def parse_dynamodb_json(d):
    """
    Recursively converts DynamoDB JSON to standard Python dict.
    Handles M (map), N (number), BOOL, etc.
    """
    if not isinstance(d, dict):
        return d

    # Number
    if "N" in d:
        return float(d["N"])

    # Boolean
    if "BOOL" in d:
        return bool(d["BOOL"])

    # Map
    if "M" in d:
        return {k: parse_dynamodb_json(v) for k, v in d["M"].items()}

    # List (if ever used)
    if "L" in d:
        return [parse_dynamodb_json(i) for i in d["L"]]

    # Already normal dict
    return {k: parse_dynamodb_json(v) for k, v in d.items()}

def build_feature_dataframe(df):
    rows = []

    for _, row in df.iterrows():
        raw_payload = row.get("behaviorPayload")

        if not raw_payload:
            continue

        try:
            # Parse string → dict
            if isinstance(raw_payload, str):
                import json
                behavior_raw = json.loads(raw_payload)
            else:
                behavior_raw = raw_payload

            # KEY STEP: convert DynamoDB format → normal dict
            behavior = parse_dynamodb_json(behavior_raw)

            duration = behavior.get("timing", {}).get("session_duration_ms")
            if duration is None or duration < 2000:
                continue

            # Now this will work correctly
            vector = flatten_behavior(behavior)

            rows.append(vector)

        except Exception as e:
            print(f"[WARN] Failed to parse row: {e}")
            continue

    feature_df = pd.DataFrame(rows, columns=FEATURE_ORDER)

    return feature_df


def clean_dataframe(feature_df):
    """
    Ensures model-ready data:
    - No NaNs
    - No infinities
    """
    feature_df = feature_df.replace([np.inf, -np.inf], np.nan)
    feature_df = feature_df.fillna(0)

    return feature_df


def validate_dataset(feature_df):
    """
    Runs sanity checks and prints results.
    """

    print("\n--- DATASET VALIDATION ---")

    print(f"Shape: {feature_df.shape}")

    # Check NaNs
    nan_count = feature_df.isna().sum().sum()
    print(f"Total NaNs: {nan_count}")

    # Check constant columns
    constant_cols = [
        col for col in feature_df.columns
        if feature_df[col].nunique() <= 1
    ]

    print(f"Constant columns: {len(constant_cols)}")

    if constant_cols:
        print("WARNING: Constant features detected:")
        print(constant_cols)

    # Check numeric
    non_numeric = feature_df.select_dtypes(exclude=[np.number]).columns.tolist()
    print(f"Non-numeric columns: {non_numeric}")

    # Final verdict
    if nan_count == 0 and len(non_numeric) == 0:
        print("\nDATASET READY FOR TRAINING")
    else:
        print("\nDATASET NOT READY")


def preprocess_csv(file_path):
    """
    Full pipeline:
    CSV → parsed → cleaned → validated
    """
    df = pd.read_csv(file_path)

    feature_df = build_feature_dataframe(df)
    feature_df = clean_dataframe(feature_df)

    # validate_dataset(feature_df)

    return feature_df


if __name__ == "__main__":
    # Change filename if needed
    feature_df = preprocess_csv("behavioral_events.csv")

    print("\nPreview:")
    print(feature_df.head())