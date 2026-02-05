import streamlit as st
import importlib

# Set Page Config (Must be first)
st.set_page_config(page_title="ADP Audit Tools", layout="wide")

# Sidebar Navigation
with st.sidebar:
    st.title("Navigation")
    tool_option = st.radio("Select Tool", ["Deduction Audit", "Prior Payroll Audit"])
    st.markdown("---")
    st.info("Select a tool above to begin.")

# Router
if tool_option == "Deduction Audit":
    import deduction_audit_app
    # Reloading module in case of hot-fixes during dev, 
    # though standard import is usually fine for prod.
    importlib.reload(deduction_audit_app) 
    deduction_audit_app.render_ui()
    
elif tool_option == "Prior Payroll Audit":
    import prior_payroll_audit_app
    importlib.reload(prior_payroll_audit_app)
    prior_payroll_audit_app.render_ui()
