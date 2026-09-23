import streamlit as st
import streamlit.components.v1 as components
import tempfile
from pyvis.network import Network
from langgraph.types import Command
from tg_client import FraudGraphClient
from agent import hitl_pipeline
from agent import hitl_pipeline, generate_sar_report

st.set_page_config(page_title="Fraud Intelligence Hub", page_icon="🛡️", layout="wide")
st.title("🛡️ Payment Fraud Intelligence Hub")

@st.cache_resource
def get_graph_client():
    return FraudGraphClient()

client = get_graph_client()

# Sidebar: Select Transaction
st.sidebar.header("Investigation Setup")
sample_txs = []
try:
    samples = client.get_sample_transactions(limit=10)
    sample_txs = [str(s["v_id"]) for s in samples]
except Exception as e:
    st.sidebar.error(f"Failed to fetch samples: {e}")

selected_tx = st.sidebar.selectbox("Select Sample ID", sample_txs if sample_txs else ["None"])
manual_tx = st.sidebar.text_input("Or enter custom Transaction ID", value="")
active_tx = manual_tx.strip() if manual_tx.strip() else selected_tx

run_btn = st.sidebar.button("Run Full Investigation", type="primary")

# PyVis graph visualizer
def build_network_graph(raw_graph_data, center_tx):
    net = Network(height="460px", width="100%", bgcolor="#0e1117", font_color="#e5e7eb")
    net.force_atlas_2based()
    net.add_node(center_tx, label=f"Tx: {center_tx}", color="#ff4b4b", size=28)
    
    type_colors = {
        "PaymentCard": "#3b82f6", "Card": "#3b82f6",
        "DeviceInfo": "#10b981", "Device": "#10b981",
        "IPNetwork": "#f59e0b", "IP": "#f59e0b"
    }

    if isinstance(raw_graph_data, list):
        for record in raw_graph_data:
            if not isinstance(record, dict):
                continue
            for group_name, entities in record.items():
                if isinstance(entities, list):
                    for entity in entities:
                        if isinstance(entity, dict):
                            v_id = str(entity.get("v_id") or entity.get("id", ""))
                            v_type = entity.get("v_type", group_name)
                            if v_id and v_id != center_tx:
                                net.add_node(v_id, label=f"{v_type}:\n{v_id}", color=type_colors.get(v_type, "#6b7280"), size=18)
                                net.add_edge(center_tx, v_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        with open(tmp_file.name, "r", encoding="utf-8") as f:
            return f.read()

col_graph, col_verdict = st.columns([1.1, 0.9])

if run_btn and active_tx and active_tx != "None":
    thread_config = {"configurable": {"thread_id": f"tx_session_{active_tx}"}}
    st.session_state["active_thread"] = thread_config
    st.session_state["active_tx"] = active_tx

    with col_graph:
        st.subheader("Graph Neighborhood")
        try:
            graph_data = client.get_subgraph(active_tx)
            components.html(build_network_graph(graph_data, active_tx), height=480)
        except Exception as e:
            st.error(f"Graph display error: {e}")

    with col_verdict:
        st.subheader("Investigation Status")
        with st.spinner("Analyzing graph signals..."):
            initial_state = {"transaction_id": active_tx, "verdict": None, "human_decision": None, "audit_notes": None}
            res = hitl_pipeline.invoke(initial_state, config=thread_config)
            
            # Check if execution paused at human interrupt
            if "__interrupt__" in res:
                st.session_state["paused_interrupt"] = res["__interrupt__"][0].value
                st.session_state["latest_verdict"] = res.get("verdict")
            else:
                st.session_state["paused_interrupt"] = None
                st.session_state["latest_verdict"] = res.get("verdict")
                st.session_state["final_res"] = res

# Display Results and HITL Action Controls
if "latest_verdict" in st.session_state and st.session_state["latest_verdict"]:
    v = st.session_state["latest_verdict"]
    with col_verdict:
        m1, m2 = st.columns(2)
        m1.metric("Risk Score", f"{v.risk_score} / 100")
        m2.markdown(f"**Classification:** `{v.classification}`")
        st.info(v.graph_evidence_summary)

        # Human-in-the-Loop decision form
        if st.session_state.get("paused_interrupt"):
            st.warning("⚠️ **Review Required:** Transaction triggered borderline risk threshold.")
            
            with st.form("human_action_form"):
                decision = st.selectbox(
                    "Select Operational Action",
                    ["Decline & Add to Blacklist", "Request Identity Verification (Step-Up)", "Clear False Positive"]
                )
                analyst_notes = st.text_input("Analyst Justification Notes")
                submitted = st.form_submit_button("Submit Operational Decision")
                
                if submitted:
                    config = st.session_state["active_thread"]
                    # Resume execution passing Command(resume=...)
                    final_state = hitl_pipeline.invoke(
                        Command(resume={"decision": decision, "notes": analyst_notes}),
                        config=config
                    )
                    st.session_state["paused_interrupt"] = None
                    st.success(f"Decision logged: {final_state.get('human_decision')}")
                    st.caption(f"Audit log: {final_state.get('audit_notes')}")
                    st.rerun()

if "final_res" in st.session_state and st.session_state["final_res"]:
    res = st.session_state["final_res"]
    st.success(f"Final Disposition: **{res.get('human_decision')}**")
    
    # If flagged for fraud, decline, or step-up, show SAR generation
    decision_text = str(res.get("human_decision", ""))
    if any(k in decision_text.upper() for k in ["DECLINE", "BLOCK", "FRAUD", "STEP-UP"]):
        st.markdown("---")
        st.subheader("📑 Regulatory Compliance & SAR")
        
        if st.button("Generate Regulatory SAR Narrative"):
            with st.spinner("Drafting FinCEN-standard SAR report via Gemini..."):
                sar_doc = generate_sar_report(
                    transaction_id=st.session_state["active_tx"],
                    verdict=st.session_state["latest_verdict"],
                    human_decision=res.get("human_decision"),
                    notes=res.get("audit_notes")
                )
                st.session_state["sar_doc"] = sar_doc
        
        if "sar_doc" in st.session_state:
            st.markdown(st.session_state["sar_doc"])
            st.download_button(
                label="📥 Download SAR Report (.md)",
                data=st.session_state["sar_doc"],
                file_name=f"SAR_{st.session_state['active_tx']}.md",
                mime="text/markdown"
            )