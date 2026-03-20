import pandas as pd
import json
import numpy as np
from app.services.feature_extractor import FEATURE_ORDER


def parse_dynamodb_json(blob):
    """
    Converts DynamoDB-style JSON string into flat numeric dict.
    Example:
    {"key": {"N": "123"}} → {"key": 123.0}
    """
    if not isinstance(blob, str):
        return {}

    try:
        data = json.loads(blob)
    except Exception:
        return {}

    parsed = {}

    for key, value in data.items():
        if isinstance(value, dict):
            if "N" in value:
                parsed[key] = float(value["N"])
            elif "BOOL" in value:
                parsed[key] = float(value["BOOL"])
            else:
                parsed[key] = 0.0
        else:
            parsed[key] = 0.0

    return parsed

def build_feature_dataframe(df):
    rows = []

    for _, row in df.iterrows():
        # Parse DynamoDB-style JSON (training only)
        interaction = parse_dynamodb_json(row.get("interaction"))
        keyboard = parse_dynamodb_json(row.get("keyboard"))
        mouse = parse_dynamodb_json(row.get("mouse"))
        timing = parse_dynamodb_json(row.get("timing"))

        behavior = {
            "interaction": interaction,
            "keyboard": keyboard,
            "mouse": mouse,
            "timing": timing,
        }

        vector = []

        # Enforce exact same order as inference
        for key in FEATURE_ORDER:
            group, field = key.split(".", 1)

            value = behavior.get(group, {}).get(field, 0.0)

            if isinstance(value, bool):
                value = 1.0 if value else 0.0

            vector.append(float(value))

        rows.append(vector)

    # IMPORTANT: enforce column order explicitly
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

    validate_dataset(feature_df)

    return feature_df


if __name__ == "__main__":
    # Change filename if needed
    feature_df = preprocess_csv("behavioral_events.csv")

    print("\nPreview:")
    print(feature_df.head())