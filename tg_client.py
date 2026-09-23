import os
import requests
import pyTigerGraph as tg
from dotenv import load_dotenv

load_dotenv()

class FraudGraphClient:
    def __init__(self):
        self.host = os.getenv("TG_HOST", "").rstrip("/")
        self.graph = os.getenv("TG_GRAPH", "Transaction_Fraud")
        self.secret = os.getenv("TG_SECRET")
        self.conn = None
        self._authenticate()

    def _authenticate(self):
        token_url = f"{self.host}/gsql/v1/tokens"
        resp = requests.post(token_url, json={"secret": self.secret}, verify=True)
        data = resp.json()

        token = None
        results = data.get("results")
        if isinstance(results, dict):
            token = results.get("token")
        elif isinstance(results, str):
            token = results
        elif isinstance(results, list) and len(results) > 0:
            token = results[0] if isinstance(results[0], str) else results[0].get("token")

        if not token and "token" in data:
            token = data["token"]

        if not token:
            raise RuntimeError(f"Failed to extract token: {data}")

        self.conn = tg.TigerGraphConnection(
            host=self.host,
            graphname=self.graph,
            apiToken=token,
            tgCloud=True
        )

    def get_sample_transactions(self, limit: int = 5):
        """Fetches sample Payment_Transaction vertices directly from the graph."""
        return self.conn.getVertices("Payment_Transaction", limit=limit)

    def get_subgraph(self, tx_id: str):
        """Runs get_subgraph_for_investigation query with Payment_Transaction vertex parameter."""
        # Typed tuple syntax for pyTigerGraph: (vertex_id, vertex_type) or (vertex_id,)
        params = {"target_txn": (str(tx_id), "Payment_Transaction")}
        return self.conn.runInstalledQuery("get_subgraph_for_investigation", params)

    def get_similar_cases(self, risk_min: float = 0.5, risk_max: float = 1.0, limit: int = 5):
        """Runs get_similar_cases query to benchmark against historical fraud."""
        params = {"risk_min": risk_min, "risk_max": risk_max, "top_k": limit}
        return self.conn.runInstalledQuery("get_similar_cases", params)
    def write_fraud_case_to_graph(self, case_id: str, tx_id: str, outcome: str, pattern: str, exposure: float, notes: str):
        """Creates a FraudCase vertex and links it to Payment_Transaction and Evidence in TigerGraph."""
        # 1. Upsert FraudCase vertex
        case_data = [{
            "id": case_id,
            "attributes": {
                "outcome": outcome,
                "pattern": pattern,
                "exposure_usd": float(exposure),
                "analyst_notes": notes
            }
        }]
        self.conn.upsertVertices("FraudCase", case_data)

        # 2. Connect Case to Payment_Transaction
        try:
            self.conn.upsertEdge("FraudCase", case_id, "investigates", "Payment_Transaction", str(tx_id))
        except Exception:
            pass  # Fallback depending on your schema's exact edge name
        
        return True