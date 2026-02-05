# Unified Audit: Uzio, ADP, and Paycom

**Repository:** [https://github.com/shobhit73/ADP-Deduction-Tool-Audit](https://github.com/shobhit73/ADP-Deduction-Tool-Audit)

A unified platform for auditing and reconciling data across **Uzio**, **ADP**, and **Paycom** HR/Payroll systems. This tool consolidates five powerful audit modules into a single Streamlit web application.

## 🛡️ Audit Modules

1.  **📊 Deduction Audit**
    *   Compares deduction data between ADP and Uzio.
    *   Identifies mismatches in deduction codes and amounts.

2.  **💰 Prior Payroll Audit**
    *   Analyzes "Prior Payroll Input" files.
    *   Transforms input data into a grouped, wide-format report suitable for payroll validation.

3.  **👥 Census Audit**
    *   Reconciles employee census data between Uzio and ADP.
    *   Checks for discrepancies in demographics, employment status, and more.

4.  **🚑 Payment & Emergency Audit**
    *   Reviews Payment details and Emergency Contact information.
    *   Generates independent reports for Payment and Emergency data.

5.  **🏢 Paycom Census Audit**
    *   Audits Paycom census data against Uzio records.
    *   Includes specific logic for Paycom fields and mapping.

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+
*   pip

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/shobhit73/ADP-Deduction-Tool-Audit.git
    cd ADP-Deduction-Tool-Audit
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

To start the Unified Audit Platform:

```bash
streamlit run app.py
```

The application will open in your default browser (usually at `http://localhost:8501`).

## 📂 Project Structure

*   `app.py`: **Main Router**. Contains the sidebar navigation and routes to specific tool modules.
*   `deduction_audit_app.py`: Logic for Deduction Audit.
*   `prior_payroll_audit_app.py`: Logic for Prior Payroll Audit.
*   `census_audit_app.py`: Logic for Census Audit.
*   `payment_emergency_audit_app.py`: Logic for Payment & Emergency Audit.
*   `paycom_census_audit_app.py`: Logic for Paycom Census Audit.

## 🎨 Features
*   **Unified Interface**: Single URL for all audit tasks.
*   **Secure Navigation**: Custom-styled sidebar with clear auditing categories.
*   **Excel Reporting**: all tools generate detailed Excel (.xlsx) reports for download.

---
*Maintained by Shobhit Sharma*
