import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# =========================================================
# Deduction Audit Tool
# INPUT: One Excel File with 3 Tabs:
#   1. Uzio Data
#   2. ADP Data
#   3. Mapping Sheet
# =========================================================

APP_TITLE = "ADP to Uzio Deduction Audit Tool"

def norm_col(c):
    """Normalize column names to be case-insensitive and stripped."""
    if c is None: return ""
    return str(c).strip().replace("\n", " ").strip()

def clean_money_val(x):
    """Parse money/percentage strings to float."""
    if pd.isna(x) or x == "":
        return 0.0
    s = str(x).strip()
    s = s.replace("$", "").replace("%", "").replace(",", "")
    s = s.replace("(", "-").replace(")", "") # Handle accounting negative (100) -> -100
    try:
        return float(s)
    except:
        return 0.0

def run_audit(file_bytes):
    # Load Workbook
    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine='openpyxl')
    
    # 1. Identify Sheets
    sheet_map = {norm_col(s).lower(): s for s in xls.sheet_names}
    
    # Helper to find sheet by keywords
    def get_sheet(keywords):
        for k, real_name in sheet_map.items():
            if any(kw in k for kw in keywords):
                return real_name
        return None

    uzio_sheet = get_sheet(["uzio"])
    adp_sheet = get_sheet(["adp"])
    map_sheet = get_sheet(["mapping", "map"])

    if not all([uzio_sheet, adp_sheet, map_sheet]):
        missing = []
        if not uzio_sheet: missing.append("Uzio Data")
        if not adp_sheet: missing.append("ADP Data")
        if not map_sheet: missing.append("Mapping Sheet")
        return None, f"Missing Tabs: {', '.join(missing)}"

    # 2. Read Data
    df_uzio = pd.read_excel(xls, sheet_name=uzio_sheet)
    df_adp = pd.read_excel(xls, sheet_name=adp_sheet)
    df_map = pd.read_excel(xls, sheet_name=map_sheet)

    # Normalize Columns
    df_uzio.columns = [norm_col(c) for c in df_uzio.columns]
    df_adp.columns = [norm_col(c) for c in df_adp.columns]
    df_map.columns = [norm_col(c) for c in df_map.columns]

    # 3. Process Mapping
    # Expect columns like "ADP Deductions" and "Uzio Deductions"
    # Find columns that look like "ADP ..." and "Uzio ..."
    map_adp_col = next((c for c in df_map.columns if "adp" in c.lower()), None)
    map_uzio_col = next((c for c in df_map.columns if "uzio" in c.lower()), None)

    if not map_adp_col or not map_uzio_col:
        return None, "Mapping Sheet must have columns identifying 'ADP' and 'Uzio' deductions."

    # Create Dictionary: ADP_Code -> Uzio_Name
    # We clean whitespace to be safe
    mapping = {}
    for _, row in df_map.iterrows():
        k = str(row[map_adp_col]).strip()
        v = str(row[map_uzio_col]).strip()
        if k and v and k.lower() != 'nan' and v.lower() != 'nan':
            mapping[k] = v
            # Also handle case-insensitive match for robustness
            mapping[k.lower()] = v

    # 4. Process ADP Data (Source of Truth)
    # Required Cols: ASSOCIATE ID, DEDUCTION CODE, DEDUCTION AMOUNT
    # Optional but preferred for mapping: DEDUCTION DESCRIPTION
    adp_id_col = next((c for c in df_adp.columns if "associate" in c.lower() and "id" in c.lower()), None)
    adp_code_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "code" in c.lower()), None)
    adp_amt_col = next((c for c in df_adp.columns if "amount" in c.lower() or "rate" in c.lower()), None)
    adp_desc_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "description" in c.lower()), None)

    if not all([adp_id_col, adp_code_col, adp_amt_col]):
        return None, f"ADP Sheet missing required columns (Associate ID, Deduction Code, Deduction Amount). Found: {list(df_adp.columns)}", []

    adp_records = []
    for _, row in df_adp.iterrows():
        emp_id = str(row[adp_id_col]).strip()
        raw_code = str(row[adp_code_col]).strip()
        raw_desc = str(row[adp_desc_col]).strip() if adp_desc_col else ""
        
        # Map to Uzio Name
        # PRIORITY 1: Map by Description (User Preference)
        # PRIORITY 2: Map by Code
        deduction_name = None
        
        # Try Description
        if raw_desc:
            deduction_name = mapping.get(raw_desc, mapping.get(raw_desc.lower()))
            
        # Try Code if Description failed
        if not deduction_name and raw_code:
            deduction_name = mapping.get(raw_code, mapping.get(raw_code.lower()))
            
        # If still unknown
        if not deduction_name:
            # Use Description for the label if available, else Code
            label = raw_desc if raw_desc else raw_code
            deduction_name = f"UNKNOWN_DED_{label}"
        
        amt = clean_money_val(row[adp_amt_col])
        
        adp_records.append({
            "Employee_ID": emp_id,
            "Deduction_Name": deduction_name,
            "ADP_Raw_Code": raw_code,
            "ADP_Description": raw_desc,
            "ADP_Amount": amt,
            "Key": f"{emp_id}|{deduction_name}".lower()
        })
    
    df_adp_clean = pd.DataFrame(adp_records)
    # Aggregation: In case ADP has multiple lines for same deduction (rare but possible), sum them
    df_adp_clean = df_adp_clean.groupby(["Employee_ID", "Deduction_Name", "ADP_Raw_Code", "ADP_Description", "Key"], as_index=False)["ADP_Amount"].sum()


    # 5. Process Uzio Data (Target)
    # Required Cols: Employee ID, Deduction Name, Amount/Percentage
    uz_id_col = next((c for c in df_uzio.columns if "employee" in c.lower() and "id" in c.lower()), None)
    uz_ded_col = next((c for c in df_uzio.columns if "deduction" in c.lower() and "name" in c.lower()), None)
    
    # For Amount, look for "Amount", "Percentage", "Rate"
    # The sample file had "Amount/Percentage"
    uz_amt_col = next((c for c in df_uzio.columns if "amount" in c.lower() or "percent" in c.lower()), None)

    if not all([uz_id_col, uz_ded_col, uz_amt_col]):
        return None, f"Uzio Sheet missing required columns (Employee ID, Deduction Name, Amount/Percentage). Found: {list(df_uzio.columns)}"

    uzio_records = []
    for _, row in df_uzio.iterrows():
        emp_id = str(row[uz_id_col]).strip()
        ded_name = str(row[uz_ded_col]).strip()
        amt = clean_money_val(row[uz_amt_col])
        
        uzio_records.append({
            "Uzio_Employee_ID": emp_id,
            "Uzio_Deduction_Name": ded_name,
            "Uzio_Amount": amt,
            "Key": f"{emp_id}|{ded_name}".lower() # Normalize key for matching
        })
    
    df_uz_clean = pd.DataFrame(uzio_records)
    # Aggregation: Sum duplicate rows if any exist
    df_uz_clean = df_uz_clean.groupby(["Uzio_Employee_ID", "Uzio_Deduction_Name", "Key"], as_index=False)["Uzio_Amount"].sum()


    # 6. Comparison
    # Merge on Key (Outer Join to find missing in both sides)
    merged = pd.merge(df_adp_clean, df_uz_clean, on="Key", how="outer", suffixes=('_ADP', '_UZIO'))

    # Get Sets of Employees for "Employee Missing" checks
    adp_emps = set(df_adp_clean["Employee_ID"].unique())
    uzio_emps = set(df_uz_clean["Uzio_Employee_ID"].unique())

    # Check for Unknown Codes (Debug/Warning for User)
    # Check for rows where Deduction_Name starts with UNKNOWN_DED_
    unknown_mask = df_adp_clean["Deduction_Name"].str.startswith("UNKNOWN_DED_")
    unknown_df = df_adp_clean[unknown_mask]
    
    # Collect unique descriptions (or codes if desc missing) that failed to map
    unknown_items = set()
    for _, row in unknown_df.iterrows():
        desc = row["ADP_Description"]
        code = row["ADP_Raw_Code"]
        if desc and str(desc).strip() != "":
            unknown_items.add(desc)
        else:
            unknown_items.add(code)
            
    unknown_codes = sorted(list(unknown_items))

    # Determine Status
    results = []
    for _, row in merged.iterrows():
        # Clean up IDs and Names from either side
        emp_id = row["Employee_ID"] if pd.notna(row["Employee_ID"]) else row["Uzio_Employee_ID"]
        
        # Resolve Deduction Names for Output Columns
        # 1. ADP Deduction Description
        if pd.notna(row["ADP_Amount"]): # ADP Record Exists
            adp_final_name = row["ADP_Description"] if pd.notna(row["ADP_Description"]) and str(row["ADP_Description"]).strip() != "" else row["ADP_Raw_Code"]
        else:
            adp_final_name = "Not Available"
            
        # 2. Uzio Deduction Name
        if pd.notna(row["Uzio_Amount"]): # Uzio Record Exists
            uzio_final_name = row["Uzio_Deduction_Name"]
        else:
            uzio_final_name = "Not Available"

        raw_code = row["ADP_Raw_Code"] if pd.notna(row["ADP_Raw_Code"]) else ""
        
        adp_val = row["ADP_Amount"] if pd.notna(row["ADP_Amount"]) else 0.0
        uz_val = row["Uzio_Amount"] if pd.notna(row["Uzio_Amount"]) else 0.0
        
        # Check Existence
        has_adp = pd.notna(row["ADP_Amount"])
        has_uzio = pd.notna(row["Uzio_Amount"])
        
        status = ""
        
        if has_adp and has_uzio:
            # Both exist, compare amounts (tolerance 0.01)
            delta = abs(adp_val - uz_val)
            if delta < 0.01:
                status = "Data Match"
            else:
                status = "Data Mismatch"
        
        elif has_adp and not has_uzio:
            # Present in ADP, Missing in Uzio
            if emp_id in uzio_emps:
                status = "Value Missing in Uzio (ADP has Value)"
            else:
                status = "Employee Missing in Uzio"
                
        elif has_uzio and not has_adp:
            # Present in Uzio, Missing in ADP
            if emp_id in adp_emps:
                status = "Value Missing in ADP (Uzio has Value)"
            else:
                status = "Employee Missing in ADP"
        
        results.append({
            "Employee ID": emp_id,
            "ADP Deduction Description": adp_final_name,
            "Uzio Deduction Name": uzio_final_name,
            "ADP Code": raw_code,
            "ADP Amount": adp_val,
            "Uzio Amount": uz_val,
            "Status": status
        })

    df_res = pd.DataFrame(results)
    
    # 7. Generate Excel Output
    out_buffer = io.BytesIO()
    with pd.ExcelWriter(out_buffer, engine='openpyxl') as writer:
        # Summary Sheet
        summary_data = {
            "Total Records": [len(df_res)],
            "Matches": [len(df_res[df_res["Status"] == "Data Match"])],
            "Mismatches": [len(df_res[df_res["Status"] == "Data Mismatch"])],
            "Value Missing in Uzio": [len(df_res[df_res["Status"] == "Value Missing in Uzio (ADP has Value)"])],
            "Value Missing in ADP": [len(df_res[df_res["Status"] == "Value Missing in ADP (Uzio has Value)"])],
            "Emp Missing in Uzio": [len(df_res[df_res["Status"] == "Employee Missing in Uzio"])],
            "Emp Missing in ADP": [len(df_res[df_res["Status"] == "Employee Missing in ADP"])]
        }
        pd.DataFrame(summary_data).transpose().reset_index().rename(columns={"index": "Metric", 0: "Count"}).to_excel(writer, sheet_name="Summary", index=False)
        
        # Detailed Data
        df_res.to_excel(writer, sheet_name="Audit Details", index=False)
    
    return out_buffer.getvalue(), None, unknown_codes



# =========================================================
# UI
# =========================================================
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.markdown("""
**Instructions**:
1. Upload a single Excel file (`.xlsx`).
2. The file MUST contain 3 sheets:
   - **Uzio Data**: Exported Deduciton Report.
   - **ADP Data**: Voluntary Deduction Report.
   - **Mapping Sheet**: Columns `ADP Deductions` and `Uzio Deductions`.
""")

uploaded_file = st.file_uploader("Upload Input File", type=["xlsx"])

if uploaded_file:
    if st.button("Run Audit", type="primary"):
        with st.spinner("Processing..."):
            try:
                report_data, error_msg, unknown_codes = run_audit(uploaded_file.getvalue())
                
                if error_msg:
                    st.error(error_msg)
                else:
                    st.success("Audit Completed Successfully!")
                    
                    if len(unknown_codes) > 0:
                        st.warning(f"⚠️ **Warning**: The following **ADP Deduction Descriptions** were found in the ADP file but are missing from your Mapping Sheet. They have been labeled as 'UNKNOWN_DED_...' in the report.\n\n" + ", ".join([f"`{c}`" for c in unknown_codes]))
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="Download Audit Report",
                        data=report_data,
                        file_name=f"Deduction_Audit_Report_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.exception(e)
