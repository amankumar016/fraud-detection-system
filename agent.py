import os
from typing import TypedDict, Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from tg_client import FraudGraphClient
from schemas import FraudInvestigationVerdict

load_dotenv()

tg_client = FraudGraphClient()

# Define graph tools
@tool
def fetch_transaction_network(transaction_id: str) -> str:
    """Fetches the 2-hop connected graph around a Payment_Transaction."""
    try:
        return str(tg_client.get_subgraph(tx_id=transaction_id))
    except Exception as e:
        return f"Error querying transaction subgraph: {e}"

@tool
def search_similar_fraud_cases(min_risk: float = 0.5, max_risk: float = 1.0) -> str:
    """Searches prior fraud cases matching a given risk range (0.0 to 1.0)."""
    try:
        return str(tg_client.get_similar_cases(risk_min=min_risk, risk_max=max_risk))
    except Exception as e:
        return f"Error finding similar cases: {e}"

tools = [fetch_transaction_network, search_similar_fraud_cases]

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
structured_llm = llm.with_structured_output(FraudInvestigationVerdict)

# ReAct Investigator
sub_agent = create_react_agent(
    llm, 
    tools, 
    prompt="You are an expert Anti-Fraud Graph Investigator. Use tools to gather subgraph topology and similar cases."
)

# Workflow State
class InvestigationState(TypedDict):
    transaction_id: str
    verdict: Optional[FraudInvestigationVerdict]
    human_decision: Optional[str]
    audit_notes: Optional[str]

# Node 1: AI Analysis
def analyze_node(state: InvestigationState) -> dict:
    tx_id = state["transaction_id"]
    query = f"Conduct a fraud analysis on Payment_Transaction '{tx_id}'."
    res = sub_agent.invoke({"messages": [{"role": "user", "content": query}]})
    
    conclusions = "\n".join([str(m.content) for m in res["messages"] if m.type == "ai"])
    verdict = structured_llm.invoke(f"Extract verdict for tx '{tx_id}':\n{conclusions}")
    return {"verdict": verdict}

# Node 2: Human Review Gate (Pauses if suspicious/borderline)
def human_review_gate(state: InvestigationState):
    verdict = state["verdict"]
    
    # Borderline threshold check
    if 35 <= verdict.risk_score <= 80 or verdict.classification == "Suspicious":
        review_data = {
            "message": "Human approval required for borderline transaction.",
            "transaction_id": state["transaction_id"],
            "risk_score": verdict.risk_score,
            "classification": verdict.classification
        }
        # Interrupt pauses graph and waits for analyst input
        analyst_response = interrupt(review_data)
        return {
            "human_decision": analyst_response.get("decision"),
            "audit_notes": analyst_response.get("notes", "")
        }
    
    # Auto-pass or auto-decline based on extremities
    auto_decision = "AUTO_BLOCKED" if verdict.risk_score > 80 else "AUTO_APPROVED"
    return {"human_decision": auto_decision, "audit_notes": "Automated pipeline disposition"}

# Build StateGraph with MemorySaver checkpointer
builder = StateGraph(InvestigationState)
builder.add_node("analyze", analyze_node)
builder.add_node("human_gate", human_review_gate)

builder.add_edge(START, "analyze")
builder.add_edge("analyze", "human_gate")
builder.add_edge("human_gate", END)

checkpointer = MemorySaver()
hitl_pipeline = builder.compile(checkpointer=checkpointer)

def generate_sar_report(transaction_id: str, verdict: FraudInvestigationVerdict, human_decision: str, notes: str) -> str:
    """Generates an official FinCEN-compliant Suspicious Activity Report (SAR) narrative."""
    sar_prompt = f"""
You are a Senior AML & Financial Crimes Compliance Officer.
Generate a structured, formal Suspicious Activity Report (SAR) narrative for regulatory filing based on this graph-backed investigation:

- Transaction ID: {transaction_id}
- Preliminary Risk Score: {verdict.risk_score} / 100
- Initial Classification: {verdict.classification}
- Detected Topological Patterns: {', '.join(verdict.detected_patterns)}
- Graph Evidence Summary: {verdict.graph_evidence_summary}
- Final Operational Decision: {human_decision}
- Lead Analyst Audit Notes: {notes}

Format the report using these standardized sections:
1. EXECUTIVE SUMMARY & FILING REASON
2. SUBJECT & ENTITY MAPPING (Cards, Devices, IP Networks involved)
3. CHRONOLOGY & SUSPICIOUS BEHAVIOR PATTERNS
4. GRAPH TOPOLOGY & EVIDENCE (Syndicate / Ring indicators)
5. DISPOSITION & RECOMMENDED LAW ENFORCEMENT ACTION
"""
    response = llm.invoke(sar_prompt)
    return response.content