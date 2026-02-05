# Standard Operating Procedure (SOP) - Unified Audit Tool

## 1. Introduction
This Unified Audit Platform allows you to audit and reconcile data between **Uzio** and external payroll providers like **ADP** and **Paycom**. The tool automates the comparison process, identifying discrepancies, missing values, and data gaps.

**Target Audience:** Implementation Teams and Data Auditors.

---

## 2. General Instructions

### How to Access the Tool
1.  Open the application URL.
2.  You will see the **"Audit Assistant"** chat interface.
3.  **Interact** by clicking the suggestion buttons (e.g., "Deduction Audit") or typing your request (e.g., "Run Census Audit").
4.  The assistant will guide you through uploading the correct files.

### File Requirements (Universal)
*   **Format:** All input files must be in **Excel (.xlsx)** format.
*   **Protection:** Files must not be password protected.
*   **Headers:** Ensure column headers are in the first row of each sheet.

### 💡 General Reporting & Filtering Strategy
For all tools, the general workflow to find errors is:
1.  Open the **Excel Output Report**.
2.  Go to the **Comparison Details** (or *Audit Details*) tab.
3.  **Enable Filters** in Excel (`Data` -> `Filter`).
4.  Go to the **Status** column (e.g., `Status` or `ADP_SourceOfTruth_Status`).
5.  **UNCHECK** the box for `"Data Match"`.
6.  **CHECK** all other boxes (Mismatch, Missing Value, etc.).
7.  **Result:** You will now see *only* the records that need attention.

---

## 3. Tool-Specific Instructions

### A. Deduction Audit
**Purpose:** Compares deduction amounts between ADP and Uzio to ensure payroll accuracy.

**Input File Preparation:**
Prepare a single Excel file with **3 Sheets**:
1.  **`Uzio Data`**: Must contain *Employee ID*, *Deduction Name*, and *Amount* (or *Percentage*).
2.  **`ADP Data`**: Must contain *Associate ID*, *Deduction Code*, and *Deduction Amount*.
3.  **`Mapping Sheet`**: Maps ADP Codes to Uzio Deduction Names.
    *   **Column A:** ADP Deduction Code/Description
    *   **Column B:** Uzio Deduction Name

**Understanding the Report:**
The report contains a sheet named **`Audit Details`**.
*   **Key Column:** `Status`
*   **Values:**
    *   `Data Match`: Difference is less than $0.01. (Ignore)
    *   `Data Mismatch`: Amounts differ. **Action:** Check calculating logic or update Uzio/ADP.
    *   `Value Missing in Uzio (ADP has Value)`: Employee has a deduction in ADP but nothing in Uzio. **Action:** Add deduction to Uzio.
    *   `Value Missing in ADP (Uzio has Value)`: Employee has a deduction in Uzio but nothing in ADP. **Action:** Verify if deduction should allow skipping.
    *   `Employee Missing...`: The ID exists in one file but not the other.

---

### B. Prior Payroll Audit
**Purpose:** Transforms "Prior Payroll" input files (often wide format with multiple pay dates) into a consolidated report compared against Uzio.

**Input File Preparation:**
Single Excel file with **3 Sheets**:
1.  **`Uzio Data`**: Standard census/deduction data.
2.  **`ADP Data`** (or "Prior Payroll"): Contains *Associate ID* and *Pay Date* columns.
3.  **`Mapping Sheet`**: Maps ADP header names to standardized Output names.

**Understanding the Report:**
The report helps reconcile historical payroll data.
*   **Sheet:** `Audit Details` output with columns like `Pay_Date`, `Deduction_Name`.
*   **Status Logic:** Same as *Deduction Audit*.
*   **Filtering:** Filter by `Pay_Date` to audit specific payroll periods.

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

**Understanding the Report:**
*   **Sheet:** `Comparison_Detail_AllFields`
*   **Status Column:** `ADP_SourceOfTruth_Status`
*   **Status Code Meanings:**
    *   `Data Match`: Values match (handling case, spacing, and date formats automatically).
    *   `Data Mismatch`: Real difference found. (e.g. "Smith" vs "Smyth").
    *   `Active in Uzio`: (Field: *Employment Status*) Employee is Active in Uzio but Terminated/Retired in ADP. **Action:** Terminate in Uzio?
    *   `Terminated in Uzio`: (Field: *Employment Status*) Employee is Terminated in Uzio but Active in ADP.
    *   `Value missing in...`: Field is blank in one system but populated in the other.

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

**Understanding the Report:**
This tool generates reports for both Payment and Emergency data.
*   **Logic:** It intelligently compares "Flat Dollar Amount" vs "Percentage" distributions.
*   **Status:** `Data Mismatch` here often means a bank account number typo or a distribution priority mismatch.

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

**Understanding the Report:**
*   **Key Logic:**
    *   Paycom "On Leave" is treated as "Active".
    *   "Salaried" (Uzio) matches "Salary" (Paycom).
*   **Status:** Similar to standard Census Audit. Use filters to identify specific field discrepancies like DOB or Salary mismatches.

---

## 4. Troubleshooting common issues
*   **"Missing Tabs" Error:** Check that your Excel sheet names match the requirements exactly.
*   **"Column Missing" Error:** Ensure the Mapping Sheet refers to exact column headers found in the Data sheets.
*   **Empty Report:** Check if the *Employee IDs* match between the two systems (e.g., one has leading zeros, one doesn't).
