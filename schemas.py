from typing import List, Literal
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class NextBestActionStage(BaseModel):
    action: str = Field(description="Operational next step (e.g., Soft hold card, Out-of-band customer verification, Permanent block)")
    approval_route: str = Field(description="Required governance level (e.g., Tier 1 Analyst, Tier 2 Supervisor, Compliance SAR Officer)")
    justification: str

class CaseResolutionRecord(BaseModel):
    case_id: str
    transaction_id: str
    customer_id: str
    card_id: str
    trigger_type: str
    risk_score: Optional[float]
    exposure_usd: float
    
    # Dual-Stage NBA
    nba_before_additional_evidence: NextBestActionStage
    nba_after_additional_evidence: NextBestActionStage
    
    # Findings and Decisions
    investigation_findings: str
    identified_pattern: str
    outcome: Literal["confirmed_fraud", "cleared"]
    actions_taken: List[str]
    
    # Compliance
    sar_required: bool
    sar_narrative: Optional[str] = None
    written_to_graph: bool = False

class FraudInvestigationVerdict(BaseModel):
    transaction_id: str = Field(description="The transaction ID evaluated")
    risk_score: int = Field(description="Fraud probability score from 0 (safest) to 100 (confirmed fraud)")
    classification: Literal["Legitimate", "Suspicious", "Fraudulent"] = Field(
        description="Categorical judgment based on graph topology and pattern analysis"
    )
    detected_patterns: List[str] = Field(
        description="List of suspicious structural signals (e.g. 'Card sharing across 4 devices', 'High-risk IP block')"
    )
    graph_evidence_summary: str = Field(
        description="Concise analytical explanation of the transaction's connected neighborhood"
    )
    recommended_action: Literal[
        "Approve", 
        "Require Step-Up Auth", 
        "Manual Review (Hold)", 
        "Decline & Freeze Entity"
    ] = Field(description="Operational decision for the fraud analyst")
