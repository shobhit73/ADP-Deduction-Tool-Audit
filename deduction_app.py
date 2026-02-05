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
    adp_sheet = get_sheet(["adp", "prior", "payroll"])
    map_sheet = get_sheet(["mapping", "map"])

    if not all([uzio_sheet, adp_sheet, map_sheet]):
        missing = []
        if not uzio_sheet: missing.append("Uzio Data")
        if not adp_sheet: missing.append("ADP Data")
        if not map_sheet: missing.append("Mapping Sheet")
        return None, f"Missing Tabs: {', '.join(missing)}", []

    # 2. Read Data
    df_uzio = pd.read_excel(xls, sheet_name=uzio_sheet)
    df_adp = pd.read_excel(xls, sheet_name=adp_sheet)
    df_map = pd.read_excel(xls, sheet_name=map_sheet)

    # 3. Detect Audit Type based on ADP Columns
    # Deduction Tool (Long Format) has "Deduction Amount" or "Rate"
    # Prior Payroll (Wide Format) does NOT have a single amount column, but multiple deduction columns
    is_legacy_deduction = False
    
    # Check for Long Format indicators
    adp_amt_col = next((c for c in df_adp.columns if "amount" in c.lower() or "rate" in c.lower()), None)
    adp_code_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "code" in c.lower()), None)
    
    if adp_amt_col and adp_code_col:
        is_legacy_deduction = True
        
    if is_legacy_deduction:
        return _run_deduction_audit(df_uzio, df_adp, df_map)
    else:
        return _run_prior_payroll_audit(df_uzio, df_adp, df_map)

def _run_deduction_audit(df_uzio, df_adp, df_map):
    # Normalize Columns
    df_uzio.columns = [norm_col(c) for c in df_uzio.columns]
    df_adp.columns = [norm_col(c) for c in df_adp.columns]
    df_map.columns = [norm_col(c) for c in df_map.columns]

    # Process Mapping
    map_adp_col = next((c for c in df_map.columns if "adp" in c.lower()), None)
    map_uzio_col = next((c for c in df_map.columns if "uzio" in c.lower()), None)
    
    if not map_adp_col or not map_uzio_col:
        return None, "Mapping Sheet must have columns identifying 'ADP' and 'Uzio' deductions.", []

    mapping = {}
    for _, row in df_map.iterrows():
        k = str(row[map_adp_col]).strip()
        v = str(row[map_uzio_col]).strip()
        if k and v and k.lower() != 'nan' and v.lower() != 'nan':
            mapping[k] = v
            mapping[k.lower()] = v

    # Required Cols
    adp_id_col = next((c for c in df_adp.columns if "associate" in c.lower() and "id" in c.lower()), None)
    adp_code_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "code" in c.lower()), None)
    adp_amt_col = next((c for c in df_adp.columns if "amount" in c.lower() or "rate" in c.lower()), None)
    adp_desc_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "description" in c.lower()), None)
    adp_pct_col = next((c for c in df_adp.columns if "deduction" in c.lower() and "%" in c.lower()), None)

    if not all([adp_id_col, adp_code_col, adp_amt_col]):
        return None, f"ADP Sheet missing required columns (Associate ID, Deduction Code, Deduction Amount). Found: {list(df_adp.columns)}", []

    adp_records = []
    for _, row in df_adp.iterrows():
        emp_id = str(row[adp_id_col]).strip()
        raw_code = str(row[adp_code_col]).strip()
        raw_desc = str(row[adp_desc_col]).strip() if adp_desc_col else ""
        
        deduction_name = None
        if raw_desc:
            deduction_name = mapping.get(raw_desc, mapping.get(raw_desc.lower()))
        if not deduction_name and raw_code:
            deduction_name = mapping.get(raw_code, mapping.get(raw_code.lower()))
            
        if not deduction_name:
            continue
        
        amt = clean_money_val(row[adp_amt_col])
        if amt == 0.0 and adp_pct_col:
            pct_val = clean_money_val(row[adp_pct_col])
            if pct_val != 0.0:
                amt = pct_val
        
        adp_records.append({
            "Employee_ID": emp_id,
            "Deduction_Name": deduction_name,
            "ADP_Raw_Code": raw_code,
            "ADP_Description": raw_desc,
            "ADP_Amount": amt,
            "Key": f"{emp_id}|{deduction_name}".lower()
        })
    
    df_adp_clean = pd.DataFrame(adp_records)
    if not df_adp_clean.empty:
        df_adp_clean = df_adp_clean.groupby(["Employee_ID", "Deduction_Name", "ADP_Raw_Code", "ADP_Description", "Key"], as_index=False)["ADP_Amount"].sum()
    else:
        df_adp_clean = pd.DataFrame(columns=["Employee_ID", "Deduction_Name", "ADP_Raw_Code", "ADP_Description", "Key", "ADP_Amount"])

    # Process Uzio
    uz_id_col = next((c for c in df_uzio.columns if "employee" in c.lower() and "id" in c.lower()), None)
    uz_ded_col = next((c for c in df_uzio.columns if "deduction" in c.lower() and "name" in c.lower()), None)
    uz_amt_col = next((c for c in df_uzio.columns if "amount" in c.lower() or "percent" in c.lower()), None)

    if not all([uz_id_col, uz_ded_col, uz_amt_col]):
        return None, f"Uzio Sheet missing required columns (Employee ID, Deduction Name, Amount/Percentage). Found: {list(df_uzio.columns)}", []

    uzio_records = []
    for _, row in df_uzio.iterrows():
        emp_id = str(row[uz_id_col]).strip()
        ded_name = str(row[uz_ded_col]).strip()
        amt = clean_money_val(row[uz_amt_col])
        
        uzio_records.append({
            "Uzio_Employee_ID": emp_id,
            "Uzio_Deduction_Name": ded_name,
            "Uzio_Amount": amt,
            "Key": f"{emp_id}|{ded_name}".lower()
        })
    
    df_uz_clean = pd.DataFrame(uzio_records)
    if not df_uz_clean.empty:
        df_uz_clean = df_uz_clean.groupby(["Uzio_Employee_ID", "Uzio_Deduction_Name", "Key"], as_index=False)["Uzio_Amount"].sum()
    else:
        df_uz_clean = pd.DataFrame(columns=["Uzio_Employee_ID", "Uzio_Deduction_Name", "Key", "Uzio_Amount"])

    # Merge
    merged = pd.merge(df_adp_clean, df_uz_clean, on="Key", how="outer", suffixes=('_ADP', '_UZIO'))
    
    # IDs lists
    adp_emps = set(df_adp_clean["Employee_ID"].unique()) if not df_adp_clean.empty else set()
    uzio_emps = set(df_uz_clean["Uzio_Employee_ID"].unique()) if not df_uz_clean.empty else set()
    
    results = []
    for _, row in merged.iterrows():
        emp_id = row["Employee_ID"] if pd.notna(row["Employee_ID"]) else row["Uzio_Employee_ID"]
        
        adp_final_name = row["ADP_Description"] if pd.notna(row["ADP_Amount"]) and pd.notna(row["ADP_Description"]) else (row["ADP_Raw_Code"] if pd.notna(row["ADP_Amount"]) else "Not Available")
        uzio_final_name = row["Uzio_Deduction_Name"] if pd.notna(row["Uzio_Amount"]) else "Not Available"
        
        raw_code = row["ADP_Raw_Code"] if pd.notna(row["ADP_Raw_Code"]) else ""
        adp_val = row["ADP_Amount"] if pd.notna(row["ADP_Amount"]) else 0.0
        uz_val = row["Uzio_Amount"] if pd.notna(row["Uzio_Amount"]) else 0.0
        
        has_adp = pd.notna(row["ADP_Amount"])
        has_uzio = pd.notna(row["Uzio_Amount"])
        
        status = ""
        if has_adp and has_uzio:
            if abs(adp_val - uz_val) < 0.01:
                status = "Data Match"
            else:
                status = "Data Mismatch"
        elif has_adp and not has_uzio:
            if emp_id in uzio_emps:
                status = "Value Missing in Uzio (ADP has Value)"
            else:
                status = "Employee Missing in Uzio"
        elif has_uzio and not has_adp:
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
        
    return _generate_output(results)

def _run_prior_payroll_audit(df_uzio, df_adp, df_map):
    # Mapping
    map_adp_col = next((c for c in df_map.columns if "adp" in c.lower()), None)
    map_uzio_col = next((c for c in df_map.columns if "uzio" in c.lower()), None)
    
    if not map_adp_col or not map_uzio_col:
        return None, "Mapping Sheet must have columns identifying 'ADP' and 'Uzio' deductions.", []

    # Map: ADP Header -> Uzio Header
    # Normalize input mapping keys to match headers we find
    mapping = {}
    for _, row in df_map.iterrows():
        k = str(row[map_adp_col]).strip()
        v = str(row[map_uzio_col]).strip()
        if k and v and k.lower() != 'nan' and v.lower() != 'nan':
            mapping[k] = v
            # Also precise match for ADP columns might be needed, so keep original and normalized
            mapping[k.lower()] = v

    # --- PROCESS ADP (WIDE) ---
    adp_id_col = next((c for c in df_adp.columns if "associate" in c.lower() and "id" in c.lower()), None)
    adp_date_col = next((c for c in df_adp.columns if "pay" in c.lower() and "date" in c.lower()), None)
    
    if not adp_id_col or not adp_date_col:
        return None, f"ADP Sheet missing required columns (Associate ID, Pay Date). Found: {list(df_adp.columns)}", []

    # Identify Deduction Columns in ADP Data
    # They should match keys in 'mapping'
    # We iterate ALL cols and check if they are in mapping
    adp_deduction_map = {} # ColName -> UzioName
    for col in df_adp.columns:
        norm_c = str(col).strip()
        if norm_c in mapping:
            adp_deduction_map[col] = mapping[norm_c]
        elif norm_c.lower() in mapping:
             adp_deduction_map[col] = mapping[norm_c.lower()]
             
    adp_records = []
    # Melt/Unpivot
    for _, row in df_adp.iterrows():
        emp_id = str(row[adp_id_col]).strip()
        # Normalize Date
        try:
            p_date = pd.to_datetime(row[adp_date_col]).strftime("%Y-%m-%d")
        except:
            p_date = str(row[adp_date_col])
            
        for d_col, uz_name in adp_deduction_map.items():
            val = clean_money_val(row[d_col])
            if val != 0:
                adp_records.append({
                    "Employee_ID": emp_id,
                    "Pay_Date": p_date,
                    "Deduction_Name": uz_name, # Map to Common Name
                    "ADP_Raw_Code": d_col, # Use Header as code
                    "ADP_Amount": val,
                    "Key": f"{emp_id}|{p_date}|{uz_name}".lower()
                })
                
    df_adp_clean = pd.DataFrame(adp_records)
    if not df_adp_clean.empty:
         df_adp_clean = df_adp_clean.groupby(["Employee_ID", "Pay_Date", "Deduction_Name", "ADP_Raw_Code", "Key"], as_index=False)["ADP_Amount"].sum() # Sum handling duplicates
    else:
         df_adp_clean = pd.DataFrame(columns=["Employee_ID", "Pay_Date", "Deduction_Name", "ADP_Raw_Code", "Key", "ADP_Amount"])

    # --- PROCESS UZIO (WIDE) ---
    uz_id_col = next((c for c in df_uzio.columns if "employee" in c.lower() and "id" in c.lower()), None)
    uz_date_col = next((c for c in df_uzio.columns if "pay" in c.lower() and "date" in c.lower()), None)
    
    if not uz_id_col or not uz_date_col:
        return None, f"Uzio Sheet missing required columns (Employee ID, Pay Date). Found: {list(df_uzio.columns)}", []

    # Identify Deduction Columns in Uzio Data
    # We should look for columns in Uzio data that match the VALUES in the mapping dictionary
    valid_uzio_names = set(mapping.values())
    uzio_cols_found = []
    for col in df_uzio.columns:
        norm_c = str(col).strip()
        if norm_c in valid_uzio_names:
            uzio_cols_found.append(col)
            
    uzio_records = []
    for _, row in df_uzio.iterrows():
        emp_id = str(row[uz_id_col]).strip()
        try:
            p_date = pd.to_datetime(row[uz_date_col]).strftime("%Y-%m-%d")
        except:
             p_date = str(row[uz_date_col])
             
        for col in uzio_cols_found:
            val = clean_money_val(row[col])
            if val != 0:
                uzio_records.append({
                    "Uzio_Employee_ID": emp_id,
                    "Pay_Date": p_date,
                    "Uzio_Deduction_Name": col, # The header is the name
                    "Uzio_Amount": val,
                    "Key": f"{emp_id}|{p_date}|{col}".lower()
                })

    df_uz_clean = pd.DataFrame(uzio_records)
    if not df_uz_clean.empty:
        df_uz_clean = df_uz_clean.groupby(["Uzio_Employee_ID", "Pay_Date", "Uzio_Deduction_Name", "Key"], as_index=False)["Uzio_Amount"].sum()
    else:
        df_uz_clean = pd.DataFrame(columns=["Uzio_Employee_ID", "Pay_Date", "Uzio_Deduction_Name", "Key", "Uzio_Amount"])

    # --- COMPARISON ---
    merged = pd.merge(df_adp_clean, df_uz_clean, on="Key", how="outer", suffixes=('_ADP', '_UZIO'))
    
    # ID Sets for Missing Check (Needs ID + Date context?)
    uzio_all_emps = set(df_uzio[uz_id_col].astype(str).str.strip().unique())
    adp_all_emps = set(df_adp[adp_id_col].astype(str).str.strip().unique())
    
    results = []
    for _, row in merged.iterrows():
        # Recover ID and Date from available side
        if pd.notna(row.get("Employee_ID")):
            emp_id = row["Employee_ID"]
            p_date = row["Pay_Date_ADP"] if "Pay_Date_ADP" in row else row["Pay_Date"]
        else:
            emp_id = row["Uzio_Employee_ID"]
            p_date = row["Pay_Date_UZIO"] if "Pay_Date_UZIO" in row else row["Pay_Date"]

        adp_val = row["ADP_Amount"] if pd.notna(row["ADP_Amount"]) else 0.0
        uz_val = row["Uzio_Amount"] if pd.notna(row["Uzio_Amount"]) else 0.0
        
        has_adp = pd.notna(row["ADP_Amount"])
        has_uzio = pd.notna(row["Uzio_Amount"])
        
        # Name resolution
        # For ADP side, we don't have a Description column in Wide format, just the Header (Raw Code) which mapped to the Name
        adp_desc = row["ADP_Raw_Code"] if has_adp else "Not Available" # The Header name
        uz_name = row["Uzio_Deduction_Name"] if has_uzio else "Not Available"
        
        # If match, both should be same (via mapping)
        final_ded_name = row["Deduction_Name"] if pd.notna(row.get("Deduction_Name")) else row["Uzio_Deduction_Name"]
        
        status = ""
        if has_adp and has_uzio:
            if abs(adp_val - uz_val) < 0.01:
                status = "Data Match"
            else:
                status = "Data Mismatch"
        elif has_adp and not has_uzio:
            if emp_id in uzio_all_emps:
                status = "Value Missing in Uzio (ADP has Value)"
            else:
                status = "Employee Missing in Uzio"
        elif has_uzio and not has_adp:
            if emp_id in adp_all_emps:
                status = "Value Missing in ADP (Uzio has Value)"
            else:
                status = "Employee Missing in ADP"

        results.append({
            "Employee ID": emp_id,
            "Pay Date": p_date,
            "ADP field": adp_desc, # Header Name (renamed from ADP Deduction Description)
            "Uzio field": uz_name, # Renamed from Uzio Deduction Name
            # "ADP Code": "", # Removed as requested
            "ADP Amount": adp_val,
            "Uzio Amount": uz_val,
            "Status": status
        })
        
    # Return using shared generator
    return _generate_output(results)

def _generate_output(results):
    df_res = pd.DataFrame(results)
    
    # Consolidate Field (Deduction Name)
    # Handle both column naming conventions (Deduction vs Prior Payroll)
    def get_field_name(row):
        # Prior Payroll logic
        if "Uzio field" in row:
            if row["Uzio field"] != "Not Available":
                return row["Uzio field"]
            return row["ADP field"] if "ADP field" in row else "Unknown"
            
        # Deduction Audit logic
        uz_name = row.get("Uzio Deduction Name", "Not Available")
        adp_name = row.get("ADP Deduction Description", "Not Available")
        
        if uz_name != "Not Available":
            return uz_name
        return adp_name

    df_res["Field"] = df_res.apply(get_field_name, axis=1)

    # Pivot Summary
    expected_statuses = [
        "Data Match", "Data Mismatch", 
        "Value Missing in Uzio (ADP has Value)", "Value Missing in ADP (Uzio has Value)", 
        "Employee Missing in Uzio", "Employee Missing in ADP"
    ]
    
    if not df_res.empty:
        field_summary = df_res.groupby(["Field", "Status"]).size().unstack(fill_value=0)
    else:
        field_summary = pd.DataFrame()

    for col in expected_statuses:
        if col not in field_summary.columns:
            field_summary[col] = 0
            
    field_summary["Total"] = field_summary.sum(axis=1) if not field_summary.empty else 0
    
    # Reorder
    cols_order = ["Total"] + [c for c in expected_statuses if c in field_summary.columns] + [c for c in field_summary.columns if c not in expected_statuses and c != "Total"]
    field_summary = field_summary[cols_order]
    
    out_buffer = io.BytesIO()
    with pd.ExcelWriter(out_buffer, engine='openpyxl') as writer:
        summary_data = {
            "Total Records": [len(df_res)],
            "Matches": [len(df_res[df_res["Status"] == "Data Match"])] if not df_res.empty else [0],
            "Mismatches": [len(df_res[df_res["Status"] == "Data Mismatch"])] if not df_res.empty else [0],
            "Value Missing in Uzio": [len(df_res[df_res["Status"] == "Value Missing in Uzio (ADP has Value)"])] if not df_res.empty else [0],
            "Emp Missing in Uzio": [len(df_res[df_res["Status"] == "Employee Missing in Uzio"])] if not df_res.empty else [0],
             "Value Missing in ADP": [len(df_res[df_res["Status"] == "Value Missing in ADP (Uzio has Value)"])] if not df_res.empty else [0],
            "Emp Missing in ADP": [len(df_res[df_res["Status"] == "Employee Missing in ADP"])] if not df_res.empty else [0]
        }
        pd.DataFrame(summary_data).transpose().reset_index().rename(columns={"index": "Metric", 0: "Count"}).to_excel(writer, sheet_name="Summary", index=False)
        field_summary.to_excel(writer, sheet_name="field_summary_by_status")
        df_res.drop(columns=["Field"], inplace=True)
        df_res.to_excel(writer, sheet_name="Audit Details", index=False)
    
    # Return Unknown Codes (empty list for prior payroll for now)
    return out_buffer.getvalue(), None, []


# =========================================================
# UI
# =========================================================
st.set_page_config(page_title="ADP Audit Tools", layout="wide")

# Sidebar for Tool Selection
with st.sidebar:
    st.title("Navigation")
    tool_option = st.radio("Select Tool", ["Deduction Audit", "Prior Payroll Audit"])
    st.markdown("---")
    st.markdown("**Instructions**:")
    if tool_option == "Deduction Audit":
        st.markdown("""
        1. Upload **Deduction Input** File.
        2. Must contain:
           - `Uzio Data`
           - `ADP Data`
           - `Mapping Sheet`
        """)
    else:
        st.markdown("""
        1. Upload **Prior Payroll Input** File.
        2. Must contain:
           - `Uzio Data`
           - `ADP Data` (Prior Payroll)
           - `Mapping Sheet`
        """)

# Dynamic Title and Config
if tool_option == "Deduction Audit":
    APP_TITLE = "ADP to Uzio Deduction Audit Tool"
    report_suffix = "Deduction_Report"
else:
    APP_TITLE = "ADP to Uzio Prior Payroll Audit Tool"
    report_suffix = "Prior_Payroll_Report"

st.title(APP_TITLE)

uploaded_file = st.file_uploader(f"Upload {tool_option} File", type=["xlsx"])
client_name = st.text_input("Enter Client Name (for Report Filename)", value="Client_Name")

if uploaded_file:
    if st.button(f"Run {tool_option}", type="primary"):
        with st.spinner("Processing..."):
            try:
                # Reuse the same logic as the structure is identical
                report_data, error_msg, _ = run_audit(uploaded_file.getvalue())
                
                if error_msg:
                    st.error(error_msg)
                else:
                    st.success("Audit Completed Successfully!")
                    
                    # Format: Client_Name_ReportType_Jan-31-2026.xlsx
                    today_str = datetime.now().strftime("%b-%d-%Y")
                    # Clean client name to ensure valid filename (replace spaces with underscores)
                    clean_client = "".join([c if c.isalnum() or c in (' ', '_', '-') else '' for c in client_name]).strip().replace(" ", "_")
                    filename = f"{clean_client}_{report_suffix}_{today_str}.xlsx"
                    
                    st.download_button(
                        label="Download Audit Report",
                        data=report_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.exception(e)
