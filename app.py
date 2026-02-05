
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

# Set Page Config
st.set_page_config(page_title="Audit Assistant", layout="centered")

# =========================================================
# Custom CSS for Chatbot Feel
# =========================================================
st.markdown("""
<style>
    /* Chat Container */
    .stChatInput {
        position: fixed;
        bottom: 30px;
    }
    
    /* Message Styling */
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 10px;
    }
    
    /* Header Styling */
    h1 {
        color: #0d47a1;
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        margin-bottom: 30px;
    }
    
    /* Suggestions Area */
    .suggestion-container {
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 20px;
        background-color: #ffffff;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Button Chips */
    .stButton button {
        border-radius: 20px;
        background-color: #f0f7ff;
        color: #1976d2;
        border: 1px solid #1976d2;
        font-weight: 600;
        transition: all 0.2s;
        width: 100%; /* Full width within column */
    }
    .stButton button:hover {
        background-color: #1976d2;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(25, 118, 210, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# Session State Initialization
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Audit Assistant. I can help you reconcile data between Uzio and ADP/Paycom. Which audit would you like to run today?"}
    ]

if "current_tool" not in st.session_state:
    st.session_state.current_tool = None

if "step" not in st.session_state:
    st.session_state.step = "idle"  # idle, waiting_for_upload, processing, result

# =========================================================
# Helper Functions
# =========================================================

def reset_chat():
    st.session_state.messages = [
        {"role": "assistant", "content": "Is there anything else I can help you with?"}
    ]
    st.session_state.current_tool = None
    st.session_state.step = "idle"
    st.rerun()

def handle_tool_selection(tool_name, tool_key):
    """Transition to upload state for a selected tool"""
    st.session_state.current_tool = tool_key
    st.session_state.step = "waiting_for_upload"
    
    # Add user choice to chat
    st.session_state.messages.append({"role": "user", "content": f"I want to run the {tool_name}."})
    
    # Add bot response
    response = f"Great! Please upload the Excel file for the **{tool_name}**. It should contain the required Data and Mapping sheets."
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

def process_file(uploaded_file):
    """Route file to the correct tool and handle output"""
    tool_key = st.session_state.current_tool
    
    st.session_state.messages.append({"role": "user", "content": f"Uploaded: {uploaded_file.name}"})
    
    # Show processing message
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(f"Analyzing {uploaded_file.name} using {tool_key}..."):
            try:
                # ----------------Deduction Audit----------------
                if tool_key == "Deduction Audit":
                    report_bytes, error, _ = deduction_audit_app.run_audit(uploaded_file.getvalue())
                    if error:
                        raise Exception(error)
                    filename = f"Deduction_Audit_Report.xlsx"
                    post_process_success(report_bytes, filename)

                # ----------------Prior Payroll Audit----------------
                elif tool_key == "Prior Payroll Audit":
                    report_bytes, error, _ = prior_payroll_audit_app.run_audit(uploaded_file.getvalue())
                    if error:
                        raise Exception(error)
                    filename = "Prior_Payroll_Report.xlsx"
                    post_process_success(report_bytes, filename)

                # ----------------Census Audit----------------
                elif tool_key == "Census Audit":
                    # returns raw bytes, raises Exception on error
                    report_bytes = census_audit_app.run_comparison(uploaded_file.getvalue())
                    filename = "Census_Audit_Report.xlsx"
                    post_process_success(report_bytes, filename)

                # ----------------Payment & Emergency Audit----------------
                elif tool_key == "Payment & Emergency Audit":
                    # returns dict of bytes
                    reports = payment_emergency_audit_app.run_comparison(uploaded_file.getvalue())
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Done! I generated two reports for you.",
                        "downloads": [
                            {"label": "Download Payment Report", "data": reports["payment"], "name": "Payment_Report.xlsx"},
                            {"label": "Download Emergency Report", "data": reports["emergency_contact"], "name": "Emergency_Report.xlsx"}
                        ]
                    })
                    st.session_state.step = "result"

                # ----------------Paycom Census Audit----------------
                elif tool_key == "Paycom Census Audit":
                    report_bytes = paycom_census_audit_app.run_comparison(uploaded_file.getvalue())
                    filename = "Paycom_Census_Report.xlsx"
                    post_process_success(report_bytes, filename)
                
                st.rerun()

            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
                st.session_state.step = "idle" # Go back to allow retry
                st.rerun()

def post_process_success(data, name):
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Analysis complete! Here is your report:",
        "downloads": [{"label": "Download Report", "data": data, "name": name}]
    })
    st.session_state.step = "result"

# =========================================================
# Main UI Loop
# =========================================================

# Clear Chat Button in Top Right
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("🤖 Audit Assistant")
with col_reset:
    if st.button("🔄 Reset", help="Clear chat history"):
        reset_chat()

# 1. Render History
for msg in st.session_state.messages:
    # Set avatar based on role
    avatar_icon = "🤖" if msg["role"] == "assistant" else "👤"
    
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        
        # Render download buttons if present in message metadata
        if "downloads" in msg:
            cols = st.columns(len(msg["downloads"]))
            for i, dl in enumerate(msg["downloads"]):
                cols[i].download_button(
                    label=dl["label"],
                    data=dl["data"],
                    file_name=dl["name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# 2. Dynamic Input Area
if st.session_state.step == "idle":
    st.markdown("---")
    st.markdown("##### Quick Actions")
    
    # Grid Layout for Buttons
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💰 Deduction Audit"):
            handle_tool_selection("Deduction Audit", "Deduction Audit")
    with c2:
        if st.button("📅 Prior Payroll"):
            handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
    with c3:
        if st.button("👥 Census Audit"):
            handle_tool_selection("Census Audit", "Census Audit")
    
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("💳 Payment & Emergency"):
            handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
    with c5:
        if st.button("📊 Paycom Audit"):
            handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")
    with c6:
        pass # Empty slot for alignment

    # Handle text input (simple intent matching)
    user_input = st.chat_input("Type your request (e.g. 'run census audit')...")
    if user_input:
        txt = user_input.lower()
        if "deduction" in txt:
            handle_tool_selection("Deduction Audit", "Deduction Audit")
        elif "prior" in txt:
            handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
        elif "census" in txt and "paycom" not in txt:
            handle_tool_selection("Census Audit", "Census Audit")
        elif "payment" in txt or "emergency" in txt:
            handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
        elif "paycom" in txt:
            handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": "I'm not sure which tool you mean. Please select one of the Quick Actions above."})
            st.rerun()

elif st.session_state.step == "waiting_for_upload":
    # Show uploader only when triggered
    uploaded_file = st.file_uploader(f"Upload file for {st.session_state.current_tool}", key="dynamic_uploader")
    
    col_back, col_dummy = st.columns([1, 5])
    if col_back.button("🔙 Cancel"):
        st.session_state.step = "idle"
        st.session_state.messages.append({"role": "user", "content": "Cancel"})
        st.session_state.messages.append({"role": "assistant", "content": "Action cancelled."})
        st.rerun()

    if uploaded_file:
        process_file(uploaded_file)

elif st.session_state.step == "result":
    # Optionally, automatically switch back to idle after a delay or just leave the "Start New Audit" button
    if st.button("✨ Start New Audit"):
        reset_chat()
