import os
import requests
import pyTigerGraph as tg
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("TG_HOST").rstrip("/")
graph = os.getenv("TG_GRAPH")
secret = os.getenv("TG_SECRET")

print(f"Connecting to: {host}")
print(f"Target Graph: {graph}")

# Step 1: Exchange secret via the REST token endpoint
token_url = f"{host}/gsql/v1/tokens"
resp = requests.post(token_url, json={"secret": secret}, verify=True)
data = resp.json()

print(f"Server response: {data}")

# Extract token string
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

print(f"Extracted Token: {token}")

# Step 2: Connect pyTigerGraph using the extracted token
if token:
    conn = tg.TigerGraphConnection(
        host=host,
        graphname=graph,
        apiToken=token,
        tgCloud=True
    )
    
    queries = conn.getInstalledQueries()
    print("\nSUCCESS! Successfully authenticated and connected to TigerGraph.")
    print("Installed queries available:", list(queries.keys()) if isinstance(queries, dict) else queries)
else:
    print("\nFailed to extract token string from server response.")