import os
import sys
import pandas as pd
import datetime

# Add code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import FinancialEngine

def main():
    print("=" * 60)
    print("  HackerRank Orchestrate 2026 - Buy or Wait? Financial Agent")
    print("=" * 60)

    dataset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")
    if not os.path.exists(dataset_dir):
        dataset_dir = "dataset"

    print(f"Loading financial engine from: {dataset_dir}")
    engine = FinancialEngine(dataset_dir)

    requests_df = pd.read_csv(os.path.join(dataset_dir, "requests.csv"))
    print(f"Processing {len(requests_df)} evaluation requests...")

    results = []
    for idx, row in requests_df.iterrows():
        res = engine.evaluate_request(row)
        results.append(res)
        if (idx + 1) % 50 == 0 or (idx + 1) == len(requests_df):
            print(f"  Processed {idx + 1}/{len(requests_df)} requests...")

    output_df = pd.DataFrame(results)
    
    # Ensure exact column order specified in problem_statement.md
    output_cols = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation"
    ]
    output_df = output_df[output_cols]

    target_out_path = os.path.join(dataset_dir, "output.csv")
    output_df.to_csv(target_out_path, index=False)
    print(f"\nSuccessfully saved predictions to: {target_out_path}")

    root_out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output.csv")
    output_df.to_csv(root_out_path, index=False)
    print(f"Saved duplicate copy to: {root_out_path}")

    # Summary Statistics
    print("\n" + "=" * 40)
    print("  PREDICTION SUMMARY")
    print("=" * 40)
    print("Affordability Status Distribution:")
    print(output_df['affordability_status'].value_counts().to_string())
    print("\nRecommended Payment Method Distribution:")
    print(output_df['recommended_payment_method'].value_counts().to_string())
    print("=" * 40)

if __name__ == "__main__":
    main()
