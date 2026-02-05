
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
st.set_page_config(page_title="Audit Assistant", layout="wide")

# =========================================================
# Custom CSS for Chatbot Feel (ChatGPT Style)
# =========================================================
st.markdown("""
<style>
    /* 1. Main Container: Center content with max-width */
    .main .block-container {
        max-width: 900px; /* Limit width like ChatGPT */
        padding-top: 2rem;
        padding-bottom: 5rem; /* Space for chat input */
        margin: 0 auto;
    }

    /* 2. Header Styling */
    h1 {
        color: #2d3748;
        text-align: center;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 700;
        margin-bottom: 40px;
    }
    
    /* 3. Chat Message Styling */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 1rem 0;
    }
    .stChatMessage[data-testid="stChatMessageAvatarUser"] {
        background-color: transparent;
    }
    
    /* 4. Chat Input Styling - Fixed Bottom & Centered */
    div[data-testid="stChatInput"] {
        position: fixed;
        bottom: 2rem; /* Floating above bottom */
        left: 50%;
        transform: translateX(-50%);
        max-width: 800px; /* Match standard reading width */
        width: 100%;
        padding-inline: 1rem;
        z-index: 1000;
    }
    
    /* Style the actual input box */
    div[data-testid="stChatInput"] > div {
        border-radius: 25px !important;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: white;
    }
    
    /* 5. Suggestions Grid Styling */
    .stButton button {
        border-radius: 12px;
        background-color: #f7fafc;
        color: #4a5568;
        border: 1px solid #e2e8f0;
        font-weight: 500;
        transition: all 0.2s;
        width: 100%;
        padding: 0.5rem 1rem;
    }
    .stButton button:hover {
        background-color: #ebf8ff;
        color: #2b6cb0;
        border-color: #bee3f8;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Hide default header/footer */
    header, footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# =========================================================
# Session State Initialization
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Audit Assistant. I can help you reconcile data between **Uzio** and **ADP/Paycom**.\n\nType a command like **\"Run Census Audit\"** or click a button below to start."}
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
        {"role": "assistant", "content": "Chat cleared. Ready for a new task."}
    ]
    st.session_state.current_tool = None
    st.session_state.step = "idle"
    st.rerun()

def handle_tool_selection(tool_name, tool_key):
    """Transition to upload state for a selected tool"""
    st.session_state.current_tool = tool_key
    st.session_state.step = "waiting_for_upload"
    
    # Add user choice to chat
    st.session_state.messages.append({"role": "user", "content": f"Run {tool_name}"})
    
    # Add bot response
    response = f"Sure! Please upload the Excel file for **{tool_name}**."
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

def handle_cancel():
    st.session_state.step = "idle"
    st.session_state.messages.append({"role": "user", "content": "Cancel"})
    st.session_state.messages.append({"role": "assistant", "content": "Action cancelled. What would you like to do next?"})
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

def process_text_input(txt):
    """Identify intent from text input"""
    txt = txt.lower()
    
    # Handle Cancellation
    if txt in ["cancel", "stop", "abort", "back"]:
        handle_cancel()
        return

    # Handle Tools
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
    
    # Handle Greetings / Unknown
    else:
        st.session_state.messages.append({"role": "user", "content": txt})
        st.session_state.messages.append({"role": "assistant", "content": "I'm not sure which tool you mean. Try typing **\"Deduction\"**, **\"Census\"**, or select a Quick Action."})
        st.rerun()

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
    # Use standard avatars or emojis
    avatar_icon = "🤖" if msg["role"] == "assistant" else "👤"
    
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        
        # Render download buttons if present in message metadata
        if "downloads" in msg:
            # Use smaller columns for buttons to look cleaner
            cols = st.columns(len(msg["downloads"]) + 2) # padding columns
            for i, dl in enumerate(msg["downloads"]):
                cols[i].download_button(
                    label=f"📥 {dl['label']}",
                    data=dl["data"],
                    file_name=dl["name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# 2. Dynamic Input Area (Contextual Widgets)
# This sits visually ABOVE the persistent chat input but below the messages
if st.session_state.step == "idle":
    st.markdown("---")
    st.caption("Quick Actions")
    
    # Grid Layout for Buttons - 3 columns, then 2 centered
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💰 Deduction Audit", use_container_width=True):
            handle_tool_selection("Deduction Audit", "Deduction Audit")
    with c2:
        if st.button("📅 Prior Payroll", use_container_width=True):
            handle_tool_selection("Prior Payroll Audit", "Prior Payroll Audit")
    with c3:
        if st.button("👥 Census Audit", use_container_width=True):
            handle_tool_selection("Census Audit", "Census Audit")
    
    c4, c5, c6 = st.columns(3)
    with c4:
        # Centering the bottom two by using offsets or just 2 cols
        pass
    
    with c5:
        # Try a different layout for the last 2 to center them? 
        # Actually standard grid is fine, let's just fill the next row
        pass
        
    # Re-doing the 2nd row to look better
    c_r2_1, c_r2_2, c_r2_3 = st.columns(3)
    with c_r2_1:
        if st.button("💳 Payment & Emergency", use_container_width=True):
            handle_tool_selection("Payment & Emergency Audit", "Payment & Emergency Audit")
    with c_r2_2:
        if st.button("📊 Paycom Audit", use_container_width=True):
            handle_tool_selection("Paycom Census Audit", "Paycom Census Audit")
    # c_r2_3 is empty

elif st.session_state.step == "waiting_for_upload":
    # Show uploader
    with st.container():
        st.info(f"Please upload the Excel file for **{st.session_state.current_tool}**")
        uploaded_file = st.file_uploader("", type=["xlsx"], key="dynamic_uploader")
        
        if st.button("🔙 Cancel", key="cancel_upload"):
            handle_cancel()

        if uploaded_file:
            process_file(uploaded_file)

elif st.session_state.step == "result":
    if st.button("✨ Start New Audit", type="primary"):
        reset_chat()

# Spacer to ensure content doesn't get hidden behind fixed input
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

# 3. Persistent Chat Input (ChatGPT Style)
user_input = st.chat_input("Type your request here (e.g. 'Run Census Audit')...")
if user_input:
    process_text_input(user_input)
