import glob
import json
import pandas as pd

files = sorted(glob.glob("case_answers/*.json"))
summary_data = []

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    summary_data.append({
        "Case ID": d.get("case_id"),
        "Transaction ID": d.get("transaction_id"),
        "Customer ID": d.get("customer_id"),
        "Exposure ($)": d.get("exposure_usd", 0.0),
        "Trigger": d.get("trigger_type"),
        "Outcome": d.get("outcome"),
        "Pattern": d.get("identified_pattern"),
        "SAR Required": "Yes" if d.get("sar_required") else "No",
        "Pre-NBA": d.get("nba_before_additional_evidence", {}).get("action", "")[:40] + "...",
        "Post-NBA": d.get("nba_after_additional_evidence", {}).get("action", "")[:40] + "..."
    })

df = pd.DataFrame(summary_data)
df.to_csv("batch_investigation_summary.csv", index=False)

print("\n=== EXECUTIVE METRICS ===")
print(f"Total Cases Evaluated: {len(df)}")
print(f"Confirmed Fraud Cases: {len(df[df['Outcome'] == 'confirmed_fraud'])}")
print(f"Cleared / Legitimate:  {len(df[df['Outcome'] == 'cleared'])}")
print(f"SAR Reports Filed:     {len(df[df['SAR Required'] == 'Yes'])}")
print(f"Total Exposure Handled: ${df['Exposure ($)'].sum():,.2f}")
print("\nExported full overview to batch_investigation_summary.csv")