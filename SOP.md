# Standard Operating Procedure (SOP) - Unified Audit Tool

## 1. Introduction
This Unified Audit Platform allows you to audit and reconcile data between **Uzio** and external payroll providers like **ADP** and **Paycom**. The tool automates the comparison process, identifying discrepancies, missing values, and data gaps.

**Target Audience:** Implementation Teams and Data Auditors.

---

## 2. General Instructions

### How to Access the Tool
1.  Open the application URL (or run `streamlit run app.py` if running locally).
2.  You will see a blue sidebar on the left with the title **"Audit Hub"**.
3.  Use the **"Select Tool"** menu to choose the specific audit module you need.

### File Requirements (Universal)
*   **Format:** All input files must be in **Excel (.xlsx)** format.
*   **Protection:** Files must not be password protected.
*   **Headers:** Ensure column headers are in the first row of each sheet.

---

## 3. Tool-Specific Instructions

### A. Deduction Audit
**Purpose:** Compares deduction amounts between ADP and Uzio to ensure payroll accuracy.

**Input File Preparation:**
Prepare a single Excel file with the following **3 Sheets** (names must match approximately):
1.  **`Uzio Data`**: Must contain *Employee ID*, *Deduction Name*, and *Amount* (or *Percentage*).
2.  **`ADP Data`**: Must contain *Associate ID*, *Deduction Code*, and *Deduction Amount*.
3.  **`Mapping Sheet`**: Maps ADP Codes to Uzio Deduction Names.
    *   **Column A:** ADP Deduction Code/Description
    *   **Column B:** Uzio Deduction Name

**How to Run:**
1.  Select **"Deduction Audit"** from the sidebar.
2.  Click **"Browse files"** and upload your prepared Excel file.
3.  The tool will process the data.
4.  Click **"Download Report"** to get the results.

**Understanding the Report:**
*   **Data Match:** Amounts match exactly.
*   **Data Mismatch:** Amounts differ between ADP and Uzio.
*   **Value missing in Uzio...:** ADP has a deduction, but Uzio does not.
*   **Employee Missing...:** Employee exists in one system but not the other.

---

### B. Prior Payroll Audit
**Purpose:** Transforms "Prior Payroll" input files (often wide format with multiple pay dates) into a consolidated report.

**Input File Preparation:**
Single Excel file with **3 Sheets**:
1.  **`Uzio Data`**: Standard census/deduction data.
2.  **`ADP Data`** (or "Prior Payroll"): Contains *Associate ID* and *Pay Date* columns.
3.  **`Mapping Sheet`**: Maps ADP header names to standardized Output names.

**How to Run:**
1.  Select **"Prior Payroll Audit"**.
2.  Upload the file.
3.  Download the **Consolidated Report**.

---

### C. Census Audit (ADP vs Uzio)
**Purpose:** Compares demographic data (Name, Address, SSN, Dates) between ADP and Uzio.

**Input File Preparation:**
Single Excel file with **3 Sheets**:
1.  **`Uzio Data`**: Must contain *Employee ID*.
2.  **`ADP Data`**: Must contain *Associate ID*.
3.  **`Mapping Sheet`**:
    *   **Column "Uzio Coloumn"**: Header name in Uzio sheet.
    *   **Column "ADP Coloumn"**: Header name in ADP sheet.

**Key Logic:**
*   **SSN:** Normalizes to 9 digits (pads with zeros).
*   **Dates:** Compares dates regardless of format (MM/DD/YYYY matches YYYY-MM-DD).
*   **Names:** Case-insensitive comparison.

**Output Statuses:**
*   **Active in Uzio / Terminated in ADP:** Specific status flags for employment changes.
*   **Data Match:** Fields are identical (after normalization).
*   **Data Mismatch:** Real discrepancy found.

---

### D. Payment & Emergency Audit
**Purpose:** Audits Bank Account details and Emergency Contacts.

**Input File Preparation:**
Single Excel file with **5 Sheets**:
1.  **`Uzio Data`**
2.  **`ADP Payment Data`**
3.  **`ADP Emergency Contact Data`**
4.  **`Payment_Mapping`**: Maps Uzio Payment fields to ADP Payment fields.
5.  **`Emergency_Mapping`**: Maps Uzio Emergency fields to ADP Emergency fields.

**How to Run:**
1.  Select **"Payment & Emergency Audit"**.
2.  Upload the workbook.
3.  The tool generates **two** reports (one for Payment, one for Emergency).

---

### E. Paycom Census Audit
**Purpose:** Audits Paycom census data against Uzio (Alternative to ADP Census).

**Input File Preparation:**
Single Excel file with **3 Sheets**:
1.  **`Uzio Data`**: Must contain *Employee ID*.
2.  **`Paycom Data`**: Must contain *Employee Code*.
3.  **`Mapping Sheet`**:
    *   **Column "Uzio Column"**: Header in Uzio sheet.
    *   **Column "Paycom Column"**: Header in Paycom sheet.

**How to Run:**
1.  Select **"Paycom Census Audit"**.
2.  Upload the file.
3.  Download the **Comparison Report**.

---

## 4. Troubleshooting
*   **"Missing Tabs" Error:** Check that your Excel sheet names match the requirements exactly.
*   **"Column Missing" Error:** Ensure the Mapping Sheet refers to exact column headers found in the Data sheets.
*   **Empty Report:** Check if the *Employee IDs* match between the two systems (e.g., one has leading zeros, one doesn't).

---
*Generated for Implementation Team Usage*
