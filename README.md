# Autonomous Fraud Investigation Agent & MCP Decision Engine

An end-to-end autonomous fraud detection, investigation, and compliance pipeline powered by a graph-backed Model Context Protocol (MCP) server, structured entity reasoning, and policy-governed triage workflows.

---

## 1. System Architecture

The pipeline processes fraud triggers through an autonomous loop combining graph database queries, deterministic fraud rules, and LLM-driven forensic reasoning:
[ Case Trigger / CSV Pack ]
│
▼
[ app.py / agent.py ] ◄───► [ TigerGraph Client (tg_client.py) ]
│                                 │
▼                                 ▼
[ MCP Server (mcp_server.py) ] ──► [ Graph Query & Traversal ]
│
├── Risk Scoring & Feature Extraction
├── Prior Case History Matching (closed_cases_history.csv)
├── Next-Best-Action (NBA) Policy Routing
│
▼
[ Evaluation Results (cases/HHG-001.json - HHG-020.json) ]
│
├── Structured SAR Filing Determinations
├── Exposure Calculations & Approval Routing
└── Executive Forensic Summaries


### Core Components
* **`agent.py` & `app.py`**: Orchestrates the multi-step investigation loop, synthesizing case details, evaluating policy bounds, and generating validated case deliverables.
* **`mcp_server.py`**: Model Context Protocol interface exposing investigation primitives, schema endpoints, and tool calls to client applications.
* **`tg_client.py` & `write_full_case_graph.py`**: Connects to the graph database backend, handling token exchanges via secure environment variables (`TG_SECRET`), mapping accounts, devices, and transaction paths.
* **`schemas.py`**: Pydantic data schemas enforcing strict typing for risk scoring, actions, SAR flags, and final case payloads.
* **`process_case_pack.py` & `generate_executive_summary.py`**: Batch processing modules that ingest raw case datasets and generate audit summaries.
* **`benchmark.py`**: Automated evaluation suite scoring model decisions against historic benchmark ground truth.

---

## 2. Model Context Protocol (MCP) Integration

The system exposes domain tools through an MCP interface to ensure standardized model-to-data communication:

* **Authentication & Graph Security**: Client credentials exchange secrets via runtime environment variables (`TG_SECRET`), preventing persistent credentials from leaking into repository trees.
* **Graph Introspection**: Standardized tools retrieve connected subgraphs (shared devices, IPs, beneficiary accounts, and transaction velocity) around suspicious entities.
* **Structured Tool Interfaces**:
  * `query_account_profile`: Pulls KYC data, linked cards, and historical transaction baselines.
  * `traverse_entity_graph`: Discovers 1-hop and 2-hop transaction flows and shared identifiers.
  * `evaluate_policy_rules`: Validates velocity rules, geographic impossibility, and amount thresholds.

---

## 3. Evaluation & Benchmark Performance

The system was evaluated across the standard 20-case test suite (`HHG-001` through `HHG-020`), evaluating precision across risk scoring, routing tiers, and compliance reporting:

| Metric | Target Policy | Achieved Score |
| :--- | :--- | :--- |
| **Case Completion Rate** | 100% (20 / 20 cases) | **100%** |
| **SAR Determination Accuracy** | > 95% | **100%** |
| **Approval Route Precision** | Tier 1 / Tier 2 Compliance | **100%** |
| **Schema Validation Rate** | 100% Strict JSON | **100%** |

### Key Benchmark Observations
1. **Low-Risk Transacting (`risk_score < 0.30`)**: Correctly classified as low exposure with non-invasive friction (e.g., standard monitoring, cleared outcome).
2. **Medium-Risk Anomalies (`0.30 ≤ risk_score < 0.70`)**: Correctly prompted intermediate next-best actions (e.g., Tier 1 Operations review, push verifications) without triggering unnecessary account freezes.
3. **High-Risk Syndicates (`risk_score ≥ 0.70`)**: Flagged for mandatory SAR filing, immediate beneficiary restrictions, and escalation to Senior Fraud Specialists.

---

## 4. Repository Structure

```text
├── cases/                          # 20 finalized case investigation JSON outputs (HHG-001.json - HHG-020.json)
├── agent.py                        # Core autonomous investigation agent logic
├── app.py                          # Agent application entry point
├── benchmark.py                    # Benchmark runner and scoring validation
├── case_pack.csv                   # Raw input evaluation case packs
├── closed_cases_history.csv        # Historical case ground truth & outcomes
├── generate_executive_summary.py   # Automated executive reporting script
├── mcp_server.py                   # Model Context Protocol server implementation
├── process_case_pack.py            # Batch case runner pipeline
├── schemas.py                      # Pydantic validation schemas
├── summary.py                      # Case result summarizer
├── test_connection.py             # TigerGraph token exchange & connectivity check
├── tg_client.py                    # Graph database API client
├── .gitignore                      # Environment and temporary file exclusions
└── README.md                       # Project documentation
5. Setup & Execution
1. Environment Configuration
Create a .env file in the root directory (ensuring it remains ignored by Git):
TG_SECRET="your_graph_token_or_secret"
TG_HOST="[https://your-graph-instance.tigergraph.cloud](https://your-graph-instance.tigergraph.cloud)"
2. Dependency Installation
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
3. Verify Graph Connection
python test_connection.py
4. Run the Full Case Benchmark Pipeline
python benchmark.py
5. Inspect Case Results
All structured solutions are stored in cases/:
# Example: inspect Case 001
cat cases/HHG-001.json
