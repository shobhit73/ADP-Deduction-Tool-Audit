
import streamlit as st
import time
import pandas as pd
import io
import datetime

# Import Audit Tools
import deduction_audit_app
import prior_payroll_audit_app
import census_audit_app
import payment_emergency_audit_app
import paycom_census_audit_app

# Import Semantic Router
try:
    from router import router
except ImportError:
    router = None

# Set Page Config - WIDE LAYOUT for modern feel, collapse sidebar by default
st.set_page_config(page_title="Uzio AI Audit", layout="wide", page_icon="🤖", initial_sidebar_state="collapsed")

# =========================================================
# Custom CSS for World Class UI
# =========================================================
st.markdown("""
<style>
    /* 1. Main Container: Center content with max-width */
    .main .block-container {
        max-width: 1000px; 
        padding-top: 2rem;
        padding-bottom: 6rem; /* Space for chat input */
        margin: 0 auto;
    }

    /* 2. Chat Message Styling */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 1rem 0;
        max-width: 800px;
        margin: 0 auto; /* Center chat bubbles column */
    }
    
    /* 3. Hero Section Styling */
    .hero-container {
        text-align: center;
        padding: 2rem 0 4rem 0;
        animation: fadeIn 0.8s ease-in;
    }
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        color: #1a202c;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        color: #718096;
        margin-bottom: 3rem;
        font-weight: 500;
    }
    
    /* 4. Chat Input Styling - Fixed Bottom & Centered */
    div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        max-width: 800px;
        width: 100%;
        padding-inline: 1rem;
        z-index: 1000;
    }
    
    div[data-testid="stChatInput"] > div {
        border-radius: 25px !important;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    
    /* 5. Custom Button Chips */
    .stButton button {
        border-radius: 16px;
        background-color: #ffffff;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        padding: 0.75rem 1rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        width: 100%;
        height: 100%;
    }
    .stButton button:hover {
        background-color: #f7fafc;
        border-color: #cbd5e0;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: #3182ce;
    }
    
    /* Hide Sidebar completely if possible or just style it away */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Hide standard header */
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# =========================================================
# Session State Initialization
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = [] # Start empty to trigger Hero View

if "current_tool" not in st.session_state:
    st.session_state.current_tool = None

if "step" not in st.session_state:
    st.session_state.step = "idle"

# Initialize Semantic Router (Lazy Load)
if router and not router.initialized:
    with st.spinner("Initializing AI Brain..."):
        router.initialize()

# =========================================================
# Helper Functions
# =========================================================
def reset_chat():
    st.session_state.messages = []
    st.session_state.current_tool = None
    st.session_state.step = "idle"
    st.rerun()

def handle_tool_selection(tool_name, tool_key):
    st.session_state.current_tool = tool_key
    st.session_state.step = "waiting_for_upload"
    
    # Append messages to history
    st.session_state.messages.append({"role": "user", "content": f"Run {tool_name}"})
    st.session_state.messages.append({"role": "assistant", "content": f"Please upload the Excel file for **{tool_name}**."})
    st.rerun()

def handle_cancel():
    """On cancel, just reset to home"""
    st.toast("Action cancelled. Returning to Home.")
    reset_chat()

def process_file(uploaded_file):
    tool_key = st.session_state.current_tool
    st.session_state.messages.append({"role": "user", "content": f"Uploaded: {uploaded_file.name}"})
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(f"Analyzing {uploaded_file.name} using {tool_key}..."):
            try:
                if tool_key == "Deduction Audit":
                    report_bytes, error, _ = deduction_audit_app.run_audit(uploaded_file.getvalue())
                    if error: raise Exception(error)
                    post_process_success(report_bytes, f"Deduction_Audit_Report.xlsx")

                elif tool_key == "Prior Payroll Audit":
                    report_bytes, error, _ = prior_payroll_audit_app.run_audit(uploaded_file.getvalue())
                    if error: raise Exception(error)
                    post_process_success(report_bytes, "Prior_Payroll_Report.xlsx")

                elif tool_key == "Census Audit":
                    report_bytes = census_audit_app.run_comparison(uploaded_file.getvalue())
                    post_process_success(report_bytes, "Census_Audit_Report.xlsx")

                elif tool_key == "Payment & Emergency Audit":
                    reports = payment_emergency_audit_app.run_comparison(uploaded_file.getvalue())
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Done! I generated two reports for you.",
                        "downloads": [
                            {"label": "Payment Report", "data": reports["payment"], "name": "Payment_Report.xlsx"},
                            {"label": "Emergency Report", "data": reports["emergency_contact"], "name": "Emergency_Report.xlsx"}
                        ]
                    })
                    st.session_state.step = "result"

                elif tool_key == "Paycom Census Audit":
                    report_bytes = paycom_census_audit_app.run_comparison(uploaded_file.getvalue())
                    post_process_success(report_bytes, "Paycom_Census_Report.xlsx")
                
                st.rerun()

            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
                st.session_state.step = "idle"
                st.rerun()

def post_process_success(data, name):
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Analysis complete! Download your report below:",
        "downloads": [{"label": "Download Report", "data": data, "name": name}]
    })
    st.session_state.step = "result"

def process_text_input(txt):
    lower_txt = txt.lower()
    
    # 1. Check for Commands
    if lower_txt in ["cancel", "back", "stop", "home"]:
        handle_cancel()
        return

    # 2. Try Semantic Router (AI)
    predicted_tool = None
    confidence = 0.0
    
    if router and router.initialized:
        predicted_tool, confidence = router.predict(lower_txt)
    
    # 3. Decision Logic (AI > Keyword)
    if predicted_tool and confidence > 0.3: # Threshold for AI confidence
        handle_tool_selection(predicted_tool, predicted_tool)
        return
        
    # 4. Fallback to Simple Keywords (Legacy)
    if "deduction" in lower_txt: handle_tool_selection("Deduction Audit", "Deduction Audit")
    elif "prior" in lower_txt: handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
    elif "census" in lower_txt and "paycom" not in lower_txt: handle_tool_selection("Census Audit", "Census Audit")
    elif "payment" in lower_txt: handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
    elif "paycom" in lower_txt: handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")
    
    # 5. Unknown
    else:
        st.session_state.messages.append({"role": "user", "content": txt})
        st.session_state.messages.append({"role": "assistant", "content": "I wasn't sure what you meant. Try keywords like **'deduction'**, **'census'**, or **'prior payroll'**."})
        st.rerun()


# =========================================================
# Main UI Logic
# =========================================================

# 1. Hero View (Only when idle and empty)
if not st.session_state.messages and st.session_state.step == "idle":
    
    # Hero Container
    with st.container():
        # CENTER THE LOGO AND TITLE
        # Use columns to effectively center the image since st.image defaults to left
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("uzio_logo.png", width=200) # Adjust width as needed
                        
        st.markdown("""
            <div class="hero-container">
                <div class="hero-title">AI Powered Audit Assistant</div>
                <div class="hero-subtitle">Intelligent reconciliation for Uzio, ADP, and Paycom data.</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Centered Button Grid
    c_l, c_main, c_r = st.columns([1, 2, 1])
    with c_main:
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("💰 Deduction", use_container_width=True): handle_tool_selection("Deduction Audit", "Deduction Audit")
        with c2: 
            if st.button("📅 Prior Payroll", use_container_width=True): handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
        with c3: 
            if st.button("👥 Census", use_container_width=True): handle_tool_selection("Census Audit", "Census Audit")
        
        st.write("") # Spacer
        
        # Second Row Centered (2 buttons)
        c4, c5 = st.columns(2)
        with c4: 
            if st.button("💳 Payment & Emergency", use_container_width=True): handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
        with c5: 
            if st.button("📊 Paycom Census", use_container_width=True): handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")

# 2. Chat View (When history exists)
else:
    # Small Top Bar for "Home" when in chat mode (since sidebar is gone)
    c_home, _, _ = st.columns([1, 4, 1])
    with c_home:
        if st.button("🏠 Home", key="home_btn"):
            handle_cancel()

    for msg in st.session_state.messages:
        avatar_icon = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.markdown(msg["content"])
            if "downloads" in msg:
                cols = st.columns(len(msg["downloads"]) + 2)
                for i, dl in enumerate(msg["downloads"]):
                    cols[i].download_button(
                        label=f"📥 {dl['label']}",
                        data=dl["data"],
                        file_name=dl["name"],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# 3. Contextual Interface
if st.session_state.step == "waiting_for_upload":
    st.markdown("<br>", unsafe_allow_html=True)
    c_l, c_main, c_r = st.columns([1, 2, 1])
    with c_main:
        with st.container():
            st.info(f"📂 Upload **{st.session_state.current_tool}** File")
            uploaded_file = st.file_uploader("", type=["xlsx"], key="dynamic_uploader")
            if st.button("Cancel Operation", key="cancel_up"):
                handle_cancel()
        
        if uploaded_file:
            process_file(uploaded_file)

# 4. Persistent Input
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True) 
user_input = st.chat_input("Start a new audit (e.g., 'Run Census Audit')...")
if user_input:
    process_text_input(user_input)
