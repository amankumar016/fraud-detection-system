import glob
import json

files = sorted(glob.glob("case_answers/*.json"))
print(f"Total investigation files found: {len(files)}\n")
print(f"{'Case ID':<10} | {'Outcome':<16} | {'SAR':<6} | {'Exposure':<10} | {'NBA Before Evidence':<40}")
print("-" * 92)

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    cid = d.get("case_id", "N/A")
    outcome = d.get("outcome", "N/A")
    sar = "YES" if d.get("sar_required") else "NO"
    exposure = f"${d.get('exposure_usd', 0.0):,.2f}"
    nba = d.get("nba_before_additional_evidence", {}).get("action", "")[:38] + "..."
    print(f"{cid:<10} | {outcome:<16} | {sar:<6} | {exposure:<10} | {nba:<40}")