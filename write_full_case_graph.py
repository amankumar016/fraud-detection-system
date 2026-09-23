import glob
import json
from tg_client import FraudGraphClient

client = FraudGraphClient()
files = sorted(glob.glob("case_answers/*.json"))
print(f"Ingesting {len(files)} FraudCase vertices into TigerGraph Cloud...")

success_count = 0
for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)

    cid = str(d["case_id"])
    score = d.get("risk_score")
    
    if score is None:
        init_risk = 0.85 if d.get("trigger_type") == "customer_report" else 0.70
        uncertainty = "LOW" if d.get("trigger_type") == "customer_report" else "HIGH"
    else:
        init_risk = float(score)
        uncertainty = "LOW" if (score > 0.80 or score < 0.30) else "HIGH"

    final_risk = 0.95 if d.get("outcome") == "confirmed_fraud" else 0.05

    attrs = {
        "status": "CLOSED_" + str(d.get("outcome", "CONFIRMED")).upper(),
        "initial_risk": float(init_risk),
        "final_risk": float(final_risk),
        "uncertainty_level": str(uncertainty),
        "pre_nba": str(d.get("nba_before_additional_evidence", {}).get("action", ""))[:120],
        "post_nba": str(d.get("nba_after_additional_evidence", {}).get("action", ""))[:120],
        "sar_filed": bool(d.get("sar_required", False))
    }

    try:
        # Single vertex upsert: upsertVertex(vertexType, vertexId, attributes)
        client.conn.upsertVertex(vertexType="FraudCase", vertexId=cid, attributes=attrs)
        success_count += 1
        print(f"[{success_count}/{len(files)}] Upserted {cid}")
    except Exception as e:
        print(f"Failed to upsert {cid}: {e}")

# Verify total count in database
verified_count = client.conn.getVertexCount("FraudCase")
print(f"\n==========================================")
print(f"Verified 'FraudCase' vertices in TigerGraph: {verified_count}")
print(f"==========================================")