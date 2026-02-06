import streamlit as st
import importlib

# Set Page Config (Must be first)
st.set_page_config(page_title="Audit Hub", layout="wide", page_icon="📊")

# Custom CSS for UI enhancements
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #070738; /* Deep navy */
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important; /* White text */
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #070738;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #e74c3c;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }
    .stButton > button:hover {
        background-color: #c0392b;
        color: white;
    }
    
    /* Radio buttons in sidebar */
    .stRadio > div {
        background-color: transparent;
    }
    .stRadio label {
        font-size: 16px;
        padding: 10px;
        border-radius: 5px;
        color: #ffffff !important;
        transition: background-color 0.3s;
    }
    .stRadio label:hover {
        background-color: #1a1a4b;
    }
    
    /* Info box */
    .stAlert {
        border-radius: 8px;
    }
    
    /* Style for Provider Headers in Sidebar */
    .provider-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #e2e8f0;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #4a5568;
        padding-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Navigation Grouping
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## Audit Hub") 
    st.markdown("---")
    
    # 1. Select Provider
    provider = st.radio("Select Provider", ["ADP", "Paycom"], index=0)
    
    st.markdown("---")
    
    # 2. Dynamic Tool Selection based on Provider
    tool_option = None
    
    if provider == "ADP":
        st.markdown('<div class="provider-header">ADP Tools</div>', unsafe_allow_html=True)
        tool_option = st.radio("Select ADP Tool", [
            "Deduction Audit", 
            "Prior Payroll Audit",
            "Census Audit",
            "Payment & Emergency Audit",
            "ADP Withholding Audit"
        ], index=0, label_visibility="collapsed")
        
    elif provider == "Paycom":
        st.markdown('<div class="provider-header">Paycom Tools</div>', unsafe_allow_html=True)
        tool_option = st.radio("Select Paycom Tool", [
            "Paycom Census Audit",
            "Paycom Withholding Audit"
        ], index=0, label_visibility="collapsed")

    st.markdown("---")
    st.info(f"Mode: {provider} Audit")
    st.markdown("v2.2 | Unified Platform")

# ---------------------------------------------------------
# Router Logic
# ---------------------------------------------------------
if tool_option == "Deduction Audit":
    import deduction_audit_app
    importlib.reload(deduction_audit_app) 
    deduction_audit_app.render_ui()
    
elif tool_option == "Prior Payroll Audit":
    import prior_payroll_audit_app
    importlib.reload(prior_payroll_audit_app)
    prior_payroll_audit_app.render_ui()

elif tool_option == "Census Audit":
    import census_audit_app
    importlib.reload(census_audit_app)
    # Note: This is practically "ADP Census Audit"
    census_audit_app.render_ui()

elif tool_option == "Payment & Emergency Audit":
    import payment_emergency_audit_app
    importlib.reload(payment_emergency_audit_app)
    payment_emergency_audit_app.render_ui()

elif tool_option == "Paycom Census Audit":
    import paycom_census_audit_app
    importlib.reload(paycom_census_audit_app)
    paycom_census_audit_app.render_ui()

elif tool_option == "Paycom Withholding Audit":
    import paycom_withholding_audit_app
    importlib.reload(paycom_withholding_audit_app)
    paycom_withholding_audit_app.render_ui()

elif tool_option == "ADP Withholding Audit":
    import adp_withholding_audit_app
    importlib.reload(adp_withholding_audit_app)
    adp_withholding_audit_app.render_ui()
