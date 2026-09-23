import time
import json
import pandas as pd
from tg_client import FraudGraphClient
from agent import hitl_pipeline

client = FraudGraphClient()

def run_benchmark(sample_limit: int = 10):
    print(f"Fetching {sample_limit} transactions from TigerGraph...")
    vertices = client.get_sample_transactions(limit=sample_limit)
    
    results = []
    
    for idx, v in enumerate(vertices):
        tx_id = str(v.get("v_id"))
        attrs = v.get("attributes", {})
        # Actual ground truth label if present in graph attributes (0 = legit, 1 = fraud)
        actual_label = attrs.get("is_fraud", attrs.get("isFraud", None))
        
        start_time = time.time()
        
        config = {"configurable": {"thread_id": f"benchmark_{tx_id}_{idx}"}}
        initial_state = {
            "transaction_id": tx_id,
            "verdict": None,
            "human_decision": None,
            "audit_notes": None
        }
        
        try:
            state = hitl_pipeline.invoke(initial_state, config=config)
            elapsed = round(time.time() - start_time, 2)
            
            verdict = state.get("verdict")
            if verdict:
                predicted_cat = verdict.classification
                risk_score = verdict.risk_score
                recommended_action = verdict.recommended_action
            else:
                predicted_cat = "Unknown"
                risk_score = None
                recommended_action = "None"
                
            results.append({
                "Transaction_ID": tx_id,
                "Actual_Ground_Truth": actual_label,
                "Predicted_Risk_Score": risk_score,
                "Predicted_Classification": predicted_cat,
                "Recommended_Action": recommended_action,
                "Latency_Seconds": elapsed
            })
            print(f"[{idx+1}/{sample_limit}] Tx {tx_id} -> Score: {risk_score} | Pred: {predicted_cat} ({elapsed}s)")
            
        except Exception as e:
            print(f"[{idx+1}/{sample_limit}] Tx {tx_id} -> Failed: {e}")
            
    df = pd.DataFrame(results)
    
    print("\n--- Benchmark Summary Metrics ---")
    print(f"Average Latency: {df['Latency_Seconds'].mean():.2f}s per investigation")
    print(f"Classifications Breakdown:\n{df['Predicted_Classification'].value_counts().to_string()}")
    
    # Save results to CSV for reporting
    df.to_csv("benchmark_results.csv", index=False)
    print("\nDetailed results exported to benchmark_results.csv")
    return df

if __name__ == "__main__":
    run_benchmark(sample_limit=5)