import streamlit as st
import importlib

# Set Page Config (Must be first)
st.set_page_config(page_title="ADP Audit Tools", layout="wide")

# Custom CSS for UI enhancements
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0d47a1;
    }
    [data-testid="stSidebar"] * {
        color: #ecf0f1 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #0d47a1;
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
        transition: background-color 0.3s;
    }
    .stRadio label:hover {
        background-color: #1976d2;
    }
    
    /* Info box */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation with Icons
with st.sidebar:
    # Using an emoji as a logo since external images can be blocked/broken
    st.markdown("# 🛡️ Audit Hub") 
    st.markdown("---")
    
    # Using emojis to make it look "cool" and friendlier
    tool_option = st.radio("Select Tool", [
        "📊 Deduction Audit", 
        "💰 Prior Payroll Audit",
        "👥 Census Audit",
        "🚑 Payment & Emergency Audit",
        "🏢 Paycom Census Audit"
    ], index=0)
    
    st.markdown("---")
    st.info("ℹ️ Select a module to begin your audit.")
    st.markdown("v2.1 | Unified Platform")


# Router
if tool_option == "📊 Deduction Audit":
    import deduction_audit_app
    importlib.reload(deduction_audit_app) 
    deduction_audit_app.render_ui()
    
elif tool_option == "💰 Prior Payroll Audit":
    import prior_payroll_audit_app
    importlib.reload(prior_payroll_audit_app)
    prior_payroll_audit_app.render_ui()

elif tool_option == "👥 Census Audit":
    import census_audit_app
    importlib.reload(census_audit_app)
    census_audit_app.render_ui()

elif tool_option == "🚑 Payment & Emergency Audit":
    import payment_emergency_audit_app
    importlib.reload(payment_emergency_audit_app)
    payment_emergency_audit_app.render_ui()

elif tool_option == "🏢 Paycom Census Audit":
    import paycom_census_audit_app
    importlib.reload(paycom_census_audit_app)
    paycom_census_audit_app.render_ui()
