import os
import json

# Configure stateless HTTP mode via environment variable
os.environ["FASTMCP_STATELESS_HTTP"] = "true"

from fastmcp import FastMCP
from tg_client import FraudGraphClient

# Initialize MCP server
mcp = FastMCP(
    "TigerGraph-Fraud-Intelligence",
    instructions="MCP Server exposing TigerGraph Savanna fraud graph tools to AI agents"
)

client = FraudGraphClient()

@mcp.tool
def get_sample_transactions(limit: int = 5) -> str:
    """Fetches sample Payment_Transaction vertex IDs from the TigerGraph database."""
    try:
        vertices = client.get_sample_transactions(limit=limit)
        tx_ids = [str(v.get("v_id")) for v in vertices]
        return json.dumps({"sample_transaction_ids": tx_ids})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool
def fetch_transaction_network(transaction_id: str) -> str:
    """Traverses the 2-hop connected graph around a payment transaction.
    Returns connected cards, devices, IP networks, and chargeback evidence."""
    try:
        subgraph = client.get_subgraph(tx_id=str(transaction_id))
        return json.dumps({"transaction_id": transaction_id, "subgraph": subgraph})
    except Exception as e:
        return json.dumps({"error": f"Failed to traverse neighborhood for {transaction_id}: {str(e)}"})

@mcp.tool
def find_similar_fraud_cases(min_risk: float = 0.5, max_risk: float = 1.0, limit: int = 5) -> str:
    """Benchmarks against historical fraud clusters in TigerGraph matching a risk score window."""
    try:
        cases = client.get_similar_cases(risk_min=min_risk, risk_max=max_risk, limit=limit)
        return json.dumps({"similar_cases": cases})
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve similar cases: {str(e)}"})

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)