
import streamlit as st
import time
import pandas as pd
import io
import datetime

# Import Audit Tools (Ensure these files are in the same directory)
import deduction_audit_app
import prior_payroll_audit_app
import census_audit_app
import payment_emergency_audit_app
import paycom_census_audit_app

# Set Page Config - WIDE LAYOUT for modern feel
st.set_page_config(page_title="Audit Assistant", layout="wide", page_icon="🤖")

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
        padding: 4rem 0;
        animation: fadeIn 0.8s ease-in;
    }
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        color: #1a202c;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        color: #718096;
        margin-bottom: 3rem;
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
    st.session_state.step = "idle"
    st.session_state.messages.append({"role": "user", "content": "Cancel"})
    st.session_state.messages.append({"role": "assistant", "content": "Action cancelled."})
    st.rerun()

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
    txt = txt.lower()
    if txt in ["cancel", "back", "stop"]:
        handle_cancel()
        return

    if "deduction" in txt: handle_tool_selection("Deduction Audit", "Deduction Audit")
    elif "prior" in txt: handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
    elif "census" in txt and "paycom" not in txt: handle_tool_selection("Census Audit", "Census Audit")
    elif "payment" in txt: handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
    elif "paycom" in txt: handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")
    else:
        st.session_state.messages.append({"role": "user", "content": txt})
        st.session_state.messages.append({"role": "assistant", "content": "I couldn't recognize that tool. Try selecting from the options above."})
        st.rerun()

# =========================================================
# Main UI Logic
# =========================================================

# 1. Reset Button (Floating Top Right)
if st.session_state.messages:
    if st.sidebar.button("🔄 Start Over"):
        reset_chat()

# 2. Hero View (Only when idle and empty)
if not st.session_state.messages and st.session_state.step == "idle":
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🤖 Audit Assistant</div>
            <div class="hero-subtitle">Reconcile your Uzio and ADP/Paycom data with precision.</div>
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

# 3. Chat View (When history exists)
else:
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

# 4. Contextual Interface (Uploaders inside columns to center)
if st.session_state.step == "waiting_for_upload":
    # Push content down a bit
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Center the uploader
    c_l, c_main, c_r = st.columns([1, 2, 1])
    with c_main:
        with st.container():
            st.info(f"📂 Upload **{st.session_state.current_tool}** File")
            uploaded_file = st.file_uploader("", type=["xlsx"], key="dynamic_uploader")
            if st.button("Cancel Operation", key="cancel_up"):
                handle_cancel()
        
        if uploaded_file:
            process_file(uploaded_file)

# 5. Persistent Input
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True) # Spacer
user_input = st.chat_input("Start a new audit (e.g., 'Run Census Audit')...")
if user_input:
    process_text_input(user_input)
