import streamlit as st
import pandas as pd
import mcm_normalise
import dhcp_normalise
import main3_server_mcm_dhcp
import vendor_confidence
import openpyxl
import main3_server_cmdbmerge
import main3_server_cmdb_finalval
import plotly.graph_objects as go
import llamaindex_solution_revised
import dhcpdeduplication
import mcmdeduplication
import anomalydetector
import time
import graphcreation
import fuzzymatch
import confidence 
import re
import fitz
from PIL import Image
from io import BytesIO
import base64
import os
from collections import defaultdict

#=====================Configure page====================================
st.set_page_config(
    page_title="CMDB Enrichment",
    page_icon="📊",
    layout="wide"
)

# =====================Initialize MAIN TAB session state variables=====================
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'main_active_tab' not in st.session_state:
    st.session_state.main_active_tab = 0
if 'unification_started' not in st.session_state:
    st.session_state.unification_started = False
if 'enrich_cmdb' not in st.session_state:    
    st.session_state.enrich_cmdb = False
if 'standardisation_active_tab' not in st.session_state:
    st.session_state.standardisation_active_tab = 0
if 'validation_started' not in st.session_state:
    st.session_state.validation_started = False
if 'image_path' not in st.session_state:
    st.session_state.image_path = None
if 'sccm_deduplication_completed' not in st.session_state:
    st.session_state.sccm_deduplication_completed = False   
if 'dhcp_deduplication_completed' not in st.session_state:
    st.session_state.dhcp_deduplication_completed = False
if 'merging_completed' not in st.session_state:
    st.session_state.merging_completed = False
#======================Configure page====================================
def switch_standardisation_tab(tab_index):
    st.session_state.standardisation_active_tab = tab_index
    st.rerun()

# Function to change active main tab
def change_main_tab(tab_index):
    st.session_state.main_active_tab = tab_index

# Custom main tabs implementation
def main_tabs():
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin: 0;
    }
    .stButton>button[kind="tertiary"] {
        width: 15%;
        margin: 0;
        border: 1px solid;
        background-color: #e0e0e0; 
}
    [stale_data='true'] {
        display: none !important;
    }
    [stale_data='true'].tab-button {
        background-color: #f0f2f6;
        border: none;
        padding: 10px 20px;
        margin: 0 2px;
        cursor: pointer;
    }
    [stale_data='true'].tab-button.active {
        background-color: #e8f5e9;
        border-bottom: 3px solid #388e3c;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tabs = ["CMDB Data Profile", "Secondary Discovery", "Unification", "Review"]
    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        with cols[i]:
            if st.button(
                tab,
                key=f"main_tab_{i}",
                on_click=change_main_tab,
                args=(i,),
                type="primary" if i == st.session_state.main_active_tab else "secondary"
            ):
                pass

# --- Load Data (and cache for performance) ---
@st.cache_data
def load_cmdb_data():
    return pd.read_excel("Primary CMDB 1 2.xlsx")

@st.cache_data
def load_server_dhcp():
    return pd.read_csv("Server_DHCP_Raw.csv")

@st.cache_data
def load_server_sccm():
    return pd.read_csv("Server_MCM_Raw.csv")

@st.cache_data
def load_switch_grn():
    return pd.read_csv("GRN_Extraction 3.csv")

@st.cache_data
def load_switch_ipam():
    return pd.read_csv("IPAM_Data_1 2.csv")

# --- Store dataframes and row counts in session state ---
if "df" not in st.session_state:
    st.session_state["df"] = load_cmdb_data()
if "total_rows" not in st.session_state:
    st.session_state["total_rows"] = len(st.session_state["df"])
if "server_dhcp" not in st.session_state:
    st.session_state["server_dhcp"] = load_server_dhcp()
if "server_sccm" not in st.session_state:
    st.session_state["server_sccm"] = load_server_sccm()
if "switch_grn" not in st.session_state:
    st.session_state["switch_grn"] = load_switch_grn()
if "switch_ipam" not in st.session_state:
    st.session_state["switch_ipam"] = load_switch_ipam()


# --- Render Main Tabs ---
st.title("CMDB Enrichment Leveraging AI/ML")
main_tabs()

def change_tab(tab_index):
    st.session_state.active_tab = tab_index
    st.rerun()

def clear_cmdb_profile_state():
    st.session_state['df'] = pd.DataFrame() 
    st.session_state['server_count'] = 0
    st.session_state['total_rows'] = 0
def dynamic_data_profile(df):
    image_path , server_count, switch_count = graphcreation.create_pie_chart(df)
    st.session_state['df'] = df
    st.session_state['total_rows'] = len(df)
    st.session_state.server_count = server_count
    st.session_state.switch_count = switch_count
    st.session_state['image_path'] = image_path
    st.session_state['enrich_cmdb'] = False
    st.rerun()
# --- Main Content Areas ---
if st.session_state.main_active_tab == 0:
    st.header("CMDB Insights")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Class Distribution")
        
        if st.session_state.image_path == None:
            dynamic_data_profile(st.session_state["df"])
            print("hi")
        st.image(st.session_state.image_path)

    with col2:
        st.write("")
        st.write("")
        st.write("")
        col2a, col2b = st.columns(2)
        with col2a:
            
            st.markdown(
                f"""
                <div style="
                    background-color: #e8f5e9;
                    border-radius: 10px;
                    padding: 20px 10px;
                    margin-bottom: 10px;
                    height: 140px;
                    border: 1px solid #d3d3d3;
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;">
                    Total Records<br>
                    <span style="font-size: 60px; font-weight: bold; color: #388e3c;">
                        {st.session_state['total_rows']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2b:
            st.markdown(
                f"""
                <div style="
                    background-color: #e8f5e9;
                    border-radius: 10px;
                    padding: 20px 10px;
                    border: 1px solid #b2dfdb;
                    text-align: center;
                    height: 140px;
                    font-size: 20px;
                    font-weight: bold;">
                    Total Switch Records<br>
                    <span style="font-size: 60px; font-weight: bold; color: #388e3c;">
                        {st.session_state.switch_count}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.header("CMDB Table")
    st.dataframe(st.session_state["df"], hide_index=True)

elif st.session_state.main_active_tab == 1:
    st.header("Secondary Discovery")

    # --- Checkboxes using session state ---
    if "server_checked" not in st.session_state:
        st.session_state["server_checked"] = False
    if "switch_checked" not in st.session_state:
        st.session_state["switch_checked"] = False
    if "router_checked" not in st.session_state:
        st.session_state["router_checked"] = False
    if "workstation_checked" not in st.session_state:
        st.session_state["workstation_checked"] = False

    col_cb1, col_cb2 = st.columns([1, 3])
    with col_cb1:
        st.session_state["server_checked"] = st.checkbox("Server", value=st.session_state["server_checked"], key="server_cb")
        st.session_state["switch_checked"] = st.checkbox("Switch", value=st.session_state["switch_checked"], key="switch_cb")
        st.session_state["router_checked"] = st.checkbox("Router", value=st.session_state["router_checked"], key="router_cb")
        st.session_state["workstation_checked"] = st.checkbox("Workstation", value=st.session_state["workstation_checked"], key="workstation_cb")

    with col_cb2:
        if st.session_state["server_checked"]:
            st.markdown(
                """
                <div style="margin-top: 8px;">
                <b>Applicable Data Sources for Servers:</b> 2<br>
                <b>SCCM</b><br>
                <b>DHCP</b>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        elif st.session_state["switch_checked"]:
            st.markdown(
                """
                <div style="margin-top: 8px;">
                <b>Applicable Data Sources for Swithces:</b> 2<br>
                <b>GRN</b><br>
                <b>IPAM</b>
                </div>
                """,
                unsafe_allow_html=True
            )

    if st.session_state["server_checked"]:
        st.markdown("---")
        tab_dhcp, tab_sccm = st.tabs(["DHCP", "SCCM"])
        with tab_dhcp:
            with st.spinner("Processing..."):
                time.sleep(5)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        """
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #d3d3d3;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Total DHCP Records: 7022
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #b2dfdb;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Server DHCP Records: {len(st.session_state['server_dhcp'])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.dataframe(st.session_state["server_dhcp"], hide_index=True)

        with tab_sccm:
            with st.spinner("Processing..."):
                time.sleep(5)
                col1, col2 = st.columns(2)
                with col1:
                
                    st.markdown(
                        """
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #d3d3d3;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Total SCCM Records: 6480
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #b2dfdb;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Server SCCM Records: {len(st.session_state['server_sccm'])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.dataframe(st.session_state["server_sccm"], hide_index=True)
    elif st.session_state["switch_checked"]:
        st.markdown("---")
        tab_grn, tab_ipam = st.tabs(["GRN", "IPAM"])
        with tab_grn:
            PDF_FOLDER   = "GRN_UI"
            OUTPUT_EXCEL = "GRN_Extracted_Output_V1.0(new2).xlsx"
            REQUIRED_FIELDS = ["Manufacturer", "Serial Number", "item", "Model/Series", "GRN Number"]
            # ──────────────────────────────────────────────────────────
             
            # st.set_page_config(page_title="GRN Extractor", layout="wide")
            # st.title("📄 GRN Document Extractor")
             
            # Store previews by GRN number
            preview_images = {}
            # Store filename by GRN number
            grn_to_filename = {}
            # Store fields completeness by GRN number
            grn_field_completeness = defaultdict(list)
            # Store manufacturers by GRN number
            grn_manufacturers = {}
             
            def extract_po_and_grn(lines):
                # po_number = ""
                grn_number = ""
                for line in lines[:15]:
                    line = line.strip()
                    # if "PO Number" in line or "PO No" in line:
                    #     po_match = re.search(r"(PO\s*(Number|No)[^\dA-Z]*)([A-Z0-9\-\/]+)", line, re.IGNORECASE)
                    #     if po_match:
                    #         po_number = po_match.group(3)
                    if "Document No" in line or "GRN No" in line:
                        grn_match = re.search(r"(Document No|GRN No)[^\dA-Z]*([A-Z0-9\-\/]+)", line, re.IGNORECASE)
                        if grn_match:
                            grn_number = grn_match.group(2)
                return grn_number
             
            def convert_image_to_base64(pdf_path):
                doc = fitz.open(pdf_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=100)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode()
             
            def parse_pdf(pdf_path, filename):
                doc = fitz.open(pdf_path)
                text = "\n".join([page.get_text("text") for page in doc])
                lines = [line.strip() for line in text.splitlines()]
                grn_number = extract_po_and_grn(lines)
               
                # Link filename to GRN number for later reference
                if grn_number:
                    grn_to_filename[grn_number] = filename
             
                try:
                    header_idx = lines.index("Serial Number")
                except ValueError:
                    return []
             
                data_lines = lines[header_idx + 1:]
                records = []
                manufacturers_in_pdf = set()  # Track unique manufacturers in this PDF
                i = 0
                serial_re = re.compile(r"\b[A-Z0-9]{10}\b")
             
                while i < len(data_lines):
                    if data_lines[i].isdigit():
                        item = data_lines[i + 1] if (i + 1) < len(data_lines) else ""
             
                        k = None
                        for j in range(i + 2, len(data_lines) - 1):
                            if data_lines[j].isdigit() and data_lines[j + 1] == "EA":
                                k = j
                                break
                        if k is None:
                            i += 1
                            continue
             
                        block = data_lines[i + 2:k]
                        half = len(block) // 2
                        model_series = " ".join(block[:half]).strip()
                        manufacturer = " ".join(block[half:]).strip()
                       
                        # Add to unique manufacturers list
                        manufacturers_in_pdf.add(manufacturer)
             
                        j = k + 2
                        while j < len(data_lines) and not data_lines[j].isdigit():
                            for sn in serial_re.findall(data_lines[j]):
                                record = {
                                    "Manufacturer": manufacturer,
                                    "Serial Number": sn,
                                    "item": item,
                                    "Model/Series": model_series,
                                    "GRN Number": grn_number
                                }
                               
                                # Track field completeness for this GRN
                                grn_field_completeness[grn_number].append(
                                    {field: bool(str(record[field]).strip()) for field in REQUIRED_FIELDS}
                                )
                               
                                records.append(record)
                            j += 1
                        i = j
                    else:
                        i += 1
               
                # Store list of manufacturers per GRN
                if grn_number and manufacturers_in_pdf:
                    grn_manufacturers[grn_number] = list(manufacturers_in_pdf)
                   
                return records
             
            def calculate_document_confidence(grn_number):
                """Calculate confidence score for a specific document (GRN)"""
                if grn_number not in grn_field_completeness or not grn_field_completeness[grn_number]:
                    return 0.0
               
                records = grn_field_completeness[grn_number]
                field_scores = {}
               
                # Calculate completeness rate for each field
                for field in REQUIRED_FIELDS:
                    field_present_count = sum(1 for record in records if record[field])
                    field_scores[field] = field_present_count / len(records) if records else 0
               
                # Weight manufacturer more heavily in the confidence score
                manufacturer_weight = 1.5
                other_weight = (6 - manufacturer_weight) / (len(REQUIRED_FIELDS) - 1)
               
                confidence = (
                    manufacturer_weight * field_scores["Manufacturer"] +
                    sum(other_weight * field_scores[field] for field in REQUIRED_FIELDS if field != "Manufacturer")
                ) / 6 * 100
               
                return round(confidence, 2)
             
            def generate_html_table(df):
                html = """
                <style>
                    .tooltip {
                        position: relative;
                        display: inline-block;
                        cursor: pointer;
                        color: blue;
                        text-decoration: underline;
                    }
                    .tooltip .tooltip-image {
                        visibility: hidden;
                        width: 300px;
                        height: auto;
                        background-color: #fff;
                        border: 1px solid #ccc;
                        position: absolute;
                        z-index: 1;
                        top: 100%;
                        left: 50%;
                        transform: translateX(-50%);
                    }
                    .tooltip:hover .tooltip-image {
                        visibility: visible;
                    }
                    .confidence-high {
                        background-color: #d4edda;
                    }
                    .confidence-medium {
                        background-color: #fff3cd;  
                    }
                    .confidence-low {
                        background-color: #f8d7da;
                    }
                </style>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <thead><tr>
                """
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += "</tr></thead><tbody>"
             
                # Track current GRN and manufacturer to know when to show confidence
                current_grn = None
                current_manufacturer = None
               
                for _, row in df.iterrows():
                    grn = row["GRN Number"]
                    manufacturer = row["Manufacturer"]
                    img_b64 = preview_images.get(grn, "")
                    conf = row["Confidence Score"]
                   
                    # Check if this is the first row of the manufacturer for this GRN
                    show_confidence = (grn != current_grn) or (manufacturer != current_manufacturer)
                    current_grn = grn
                    current_manufacturer = manufacturer
                   
                    # Determine styling based on confidence score
                    conf_class = ""
                    if conf >= 80:
                        conf_class = "confidence-high"
                    elif conf >= 50:
                        conf_class = "confidence-medium"
                    else:
                        conf_class = "confidence-low"
             
                    tooltip = f'''
                    <div class="tooltip">{grn}
                        <div class="tooltip-image">
                            <img src="data:image/png;base64,{img_b64}" width="600">
                        </div>
                    </div>
                    '''
                    html += "<tr>"
                    for col in df.columns:
                        if col == "GRN Number":
                            cell_content = tooltip
                        elif col == "Confidence Score":
                            # Only display confidence score for the first row of each manufacturer in a GRN
                            cell_content = conf if show_confidence else ""
                            cell_class = conf_class if show_confidence else ""
                        else:
                            cell_content = row[col]
                            cell_class = ""
                           
                        html += f'<td class="{cell_class}">{cell_content}</td>'
             
                    html += "</tr>"
             
                html += "</tbody></table>"
                return html
             
            def is_valid_row(row):
                return all(str(row[field]).strip() != "" for field in REQUIRED_FIELDS)
             
             
             
            if st.spinner("Extracting GRN Docs"):
                all_records = []
                left_col, right_col = st.columns([1, 2])
                pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
                pdfs_with_data = 0
             
                with st.spinner("🔄 Extracting all GRN documents..."):
                    for fname in pdf_files:
                        pdf_path = os.path.join(PDF_FOLDER, fname)
                        base64_img = convert_image_to_base64(pdf_path)
             
                        records = parse_pdf(pdf_path, fname)
                        if records:
                            pdfs_with_data += 1
                           
                        # Store preview image by GRN number
                        for record in records:
                            preview_images[record["GRN Number"]] = base64_img
             
                        all_records.extend(records)
             
                if all_records:
                    # Create DataFrame with basic data
                    df = pd.DataFrame(all_records)
                   
                    # Add confidence scores for each GRN
                    grn_confidence = {grn: calculate_document_confidence(grn) for grn in df["GRN Number"].unique()}
                    df["Confidence Score"] = df["GRN Number"].map(grn_confidence)
                   
                    # Sort the dataframe by GRN Number and then by Manufacturer to ensure
                    # related items stay together and confidence score display works correctly
                    df = df.sort_values(["GRN Number", "Manufacturer"])
                   
                    # Reorder columns to put confidence score at the end (after GRN Number)
                    cols = list(df.columns)
                    cols.remove("Confidence Score")
                    new_cols = cols + ["Confidence Score"]
                    df = df[new_cols]
                   
                    # Save to Excel
                    df.to_excel(OUTPUT_EXCEL, index=False)
             
                    # ⬇️ Overall Confidence Score Calculation ⬇️
                    total_pdfs = len(pdf_files)
                    total_rows = len(df)
                    valid_rows = df.apply(is_valid_row, axis=1).sum()
             
                    overall_confidence = round(((pdfs_with_data / total_pdfs) * (valid_rows / total_rows)) * 100, 2)
             
                    with left_col:
                        #st.info(f"🧠 Overall Extraction Confidence Score: **{overall_confidence}%**")
                       
                        # Display document counts
                        # st.success(f"✅ Successfully processed {pdfs_with_data} of {total_pdfs} PDF files")
                       
                        # Add a small stats section
                        # st.subheader("Document Confidence Stats")
                        if grn_confidence:
                            avg_doc_confidence = sum(grn_confidence.values()) / len(grn_confidence)
                            highest_conf = max(grn_confidence.values())
                            lowest_conf = min(grn_confidence.values())
                           
                           
             
                    # with right_col:
                    #     st.subheader("📊 Extracted Data")
                   
                    with st.spinner("Processing..."):
                        html = generate_html_table(df)
                        time.sleep(5)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #e8f5e9;
                                    border-radius: 10px;
                                    padding: 20px 10px;
                                    margin-bottom: 10px;
                                    border: 1px solid #d3d3d3;
                                    text-align: center;
                                    font-size: 18px;
                                    font-weight: bold;">
                                    Total GRN Records: {len(st.session_state['switch_grn'])}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #e8f5e9;
                                    border-radius: 10px;
                                    padding: 20px 10px;
                                    margin-bottom: 10px;
                                    border: 1px solid #b2dfdb;
                                    text-align: center;
                                    font-size: 18px;
                                    font-weight: bold;">
                                    Total Switch Records: 492
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.components.v1.html(html, height=600, scrolling=True)
                        
                        # with st.spinner("Processing..."):
                        
                else:
                    st.warning("⚠️ No data extracted from PDFs.")
                
                # st.dataframe(st.session_state["switch_grn"], hide_index=True)
                

        with tab_ipam:
            with st.spinner("Processing..."):
                time.sleep(5)
                col1, col2 = st.columns(2)
                with col1:
                
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #d3d3d3;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Total IPAM Records: {len(st.session_state['switch_ipam'])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #e8f5e9;
                            border-radius: 10px;
                            padding: 20px 10px;
                            margin-bottom: 10px;
                            border: 1px solid #b2dfdb;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;">
                            Total Switch Records: 345
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.dataframe(st.session_state["switch_ipam"], hide_index=True)
    

elif st.session_state.main_active_tab == 2:
    # Button to start unification
    if not st.session_state.unification_started:
        if st.button("Start Unification",type="tertiary"):
            st.session_state.unification_started = True
            st.rerun()
    
    # Only show unification process after button is clicked
    if st.session_state.unification_started:
        # Create custom tabs appearance
        st.write("")  # Add spacing
        tabs = ["Standardization", "Deduplication"]
        
        # Create tab UI
        cols = st.columns(len(tabs))
        for i, tab in enumerate(tabs):
            with cols[i]:
                if i == st.session_state.active_tab:
                    st.markdown(
                        f"""
                        <div style="
                            text-align: center;
                            font-weight: bold;
                            color: red;">
                            {tab}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    if st.button(tab, key=f"tab_{i}"):
                        change_tab(i)

                
        if st.session_state.active_tab == 0:  # Standardization

            standardisation_tabs = [
        "Auto Data Model Mapping",
        "DHCP Standardisation",
        "SCCM Standardisation"
    ]

            

            # Render tabs
            tab_objs = st.tabs(standardisation_tabs)

            # --- Tab 0: Auto Data Model Mapping ---
            with tab_objs[0]:
                
                    def run_sccm_metadata_normalization():
                        with st.spinner("Data Model Mapping - In progress..."):
                            try:
                                sccm_out_path, sccm_confidence, column_mapping = mcm_normalise.main()  
                                st.session_state.sccm_column_mapping = column_mapping
                                sccm_standardized_df = pd.read_excel(sccm_out_path)
                                st.session_state.sccm_metadata_confidence = sccm_confidence
                                st.session_state.sccm_standardized_df = sccm_standardized_df
                                st.session_state.sccm_out_path = sccm_out_path
                                return True
                            except Exception as e:
                                st.error(f"Error in SCCM normalization: {e}")
                                return False

                    def run_dhcp_metadata_normalization():
                        with st.spinner("Data Model Mapping - In progress..."):
                            try:
                                dhcp_out_path, dhcp_confidence ,column_mapping= dhcp_normalise.main()  
                                st.session_state.dhcp_column_mapping = column_mapping
                                dhcp_standardized_df = pd.read_excel(dhcp_out_path)
                                st.session_state.dhcp_metadata_confidence = dhcp_confidence
                                st.session_state.dhcp_standardized_df = dhcp_standardized_df
                                st.session_state.dhcp_out_path = dhcp_out_path
                                return True
                            except Exception as e:
                                st.error(f"Error in DHCP normalization: {e}")
                                return False
                    
                    # Only run these if they haven't been run before
                    if 'sccm_column_mapping' not in st.session_state:
                        run_sccm_metadata_normalization()
                    if 'dhcp_standardized_df' not in st.session_state:
                        run_dhcp_metadata_normalization()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("DHCP Metadata Normalization")
                        st.dataframe(st.session_state.get('dhcp_column_mapping', {}), hide_index=True)
                    with col2:
                        st.subheader("SCCM Metadata Normalization")
                        st.dataframe(st.session_state.get('sccm_column_mapping', {}), hide_index=True)
                   

            # --- Tab 1: DHCP Standardisation ---
            with tab_objs[1]:
                
                    st.header("DHCP Standardisation")
                    # Run normalization
                    def run_normalization():
                        with st.spinner("Normalizing data - this may take a moment..."):
                            time.sleep(5)
                            standardized_xl_path = llamaindex_solution_revised.main("Server-DHCP-NormMetada.xlsx","Server-DHCP-Norm2.xlsx")
                            # cleaned_df_path = fuzzymatch.main(standardized_xl_path, "fuzzyclustering.xlsx")
                            # standardized_df = pd.read_excel(cleaned_df_path)
                            raw_dhcp_df = pd.read_csv('Server_DHCP_Raw.csv')
                            st.session_state.raw_dhcp_df = raw_dhcp_df
                            standardized_df = pd.read_excel(standardized_xl_path)
                            confidence = vendor_confidence.main("Server-DHCP-NormMetada.xlsx","dhcp_discovery_data_Standardized_averageconfidence.csv")
                            st.session_state.dhcp_data_confidence = confidence
                            st.session_state.standardized_df = standardized_df
                            st.session_state.normalization_completed = True

                    if 'standardized_df' not in st.session_state:
                        run_normalization()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Server DHCP Raw Data")
                        st.dataframe(st.session_state.get('raw_dhcp_df', pd.DataFrame()), hide_index=True)
                    with col2:
                        st.subheader(f"Server DHCP Normalized Data, Confidence: {st.session_state.get('dhcp_data_confidence', 0):.2f}")
                        st.dataframe(st.session_state.get('standardized_df', pd.DataFrame()), hide_index=True)
                    

            # --- Tab 2: SCCM Standardisation ---
            with tab_objs[2]:
                
                    st.header("SCCM Standardisation")
                    # Run SCCM data normalization
                    def run_sccm_data_normalization():
                        with st.spinner("Normalizing data - this may take a moment..."):
                            time.sleep(5)
                            standardized_sccm_path = llamaindex_solution_revised.main("Server-MCM-NormMetada.xlsx", "Server-MCM-Norm2.xlsx")
                            standardized_sccm_df = pd.read_excel(standardized_sccm_path)
                            sccm_raw_df = pd.read_csv('Server_MCM_Raw.csv')
                            st.session_state.sccm_raw_df = sccm_raw_df
                            sccm_confidence = vendor_confidence.main("Server-MCM-NormMetada.xlsx", "mcm_discovery_data_Standardized_averageconfidence.csv")
                            st.session_state.sccm_data_confidence = sccm_confidence
                            st.session_state.standardized_sccm_df = standardized_sccm_df
                            st.session_state.sccm_data_normalization_completed = True

                    if 'standardized_sccm_df' not in st.session_state:
                        run_sccm_data_normalization()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Server SCCM Raw Data")
                        st.dataframe(st.session_state.get('sccm_raw_df', pd.DataFrame()), hide_index=True)
                    with col2:
                        st.subheader(f"Server SCCM Normalized Data, Confidence: {st.session_state.get('sccm_data_confidence', 0):.2f}")
                        st.dataframe(st.session_state.get('standardized_sccm_df', pd.DataFrame()), hide_index=True)
                    if st.button("Next: Deduplication →",type="tertiary"):
                        # Move to your main tab for Deduplication, e.g.,
                        st.session_state.active_tab = 1
                        st.rerun()
        elif st.session_state.active_tab == 1:  # Deduplication

            def sccm_deduplication():
                with st.spinner("Deduplicating SCCM data - this may take a moment..."):
                    time.sleep(5)
                    sccm_dedup_path , removed_records, sccm_dup_path= mcmdeduplication.main("Server-MCM-Norm2.xlsx")
                    duplicated_sccm_df = pd.read_csv(sccm_dup_path)
                    st.session_state.duplicated_sccm_df = duplicated_sccm_df
                    deduplicated_sccm_df = pd.read_csv(sccm_dedup_path)
                    st.session_state.deduplicated_sccm_df = deduplicated_sccm_df
                    st.session_state.sccm_removed_records =  len(st.session_state.duplicated_sccm_df)
                    st.session_state.total_sccm_records = len(st.session_state.sccm_raw_df)
                    st.session_state.sccm_deduplicated_records = len(st.session_state.deduplicated_sccm_df)
                    st.session_state.sccm_deduplication_completed = True

            if st.session_state.sccm_deduplication_completed == False:
                sccm_deduplication()

            def dhcp_deduplication():
                with st.spinner("Deduplicating DHCP data - this may take a moment..."):
                    time.sleep(5)
                    dhcp_dedup_path , removed_records1, dhcp_dup_path= dhcpdeduplication.main()
                    duplicated_dhcp_df = pd.read_csv(dhcp_dup_path)
                    st.session_state.duplicated_dhcp_df = duplicated_dhcp_df
                    deduplicated_dhcp_df = pd.read_csv(dhcp_dedup_path)
                    st.session_state.deduplicated_dhcp_df = deduplicated_dhcp_df
                    st.session_state.removed_records = len(st.session_state.duplicated_dhcp_df)
                    st.session_state.total_dhcp_records = len(st.session_state.raw_dhcp_df)
                    st.session_state.dhcp_deduplicated_records = len(st.session_state.deduplicated_dhcp_df)
                    st.session_state.dhcp_deduplication_completed = True

            if st.session_state.dhcp_deduplication_completed == False:  
                dhcp_deduplication()

            tab1, tab2 = st.tabs(["DHCP Deduplication", "SCCM Deduplication"])
            with tab1:
                st.write(f"Total DHCP Records: {st.session_state.total_dhcp_records}")
                st.write(f"Duplicate Records Identified: {st.session_state.removed_records}")
                st.write(f"Total Remaining Records: {st.session_state.dhcp_deduplicated_records}")
                st.write("")
                col1, col2 = st.columns([1, 1]) 
                with col1:
                    st.subheader("DHCP Duplicated Data")
                    st.dataframe(st.session_state.duplicated_dhcp_df, hide_index=True)
                with col2:
                    st.subheader("DHCP Deduplicated Data")
                    st.dataframe(st.session_state.deduplicated_dhcp_df, hide_index=True)

            with tab2:
                     
                st.write(f"Total SCCM Records: {st.session_state.total_sccm_records}")
                st.write(f"Duplicate Records Identified: {st.session_state.sccm_removed_records}")
                st.write(f"Total Remaining Records: {st.session_state.sccm_deduplicated_records}") 
                st.write("")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("SCCM Duplicated Data")
                    st.dataframe(st.session_state.duplicated_sccm_df, hide_index=True)
                with col2:
                    st.subheader("SCCM Deduplicated Data")
                    st.dataframe(st.session_state.deduplicated_sccm_df, hide_index=True)
                # if st.button("Next: Merge →"):
                #     change_tab(2)
                    
        # elif st.session_state.active_tab == 2:  # Merge

            # if 'primary_df1' not in st.session_state:

            #     with st.spinner("Merging data..."):
            #         output_paths = main3_server_mcm_dhcp.main()
            #         output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"] 
                    
            #         for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
            #             combined_df = pd.read_excel(output_path)
            #             st.session_state[f'normalized_df{i}'] = combined_df
            #             st.session_state[f'normalized_df{i}_name'] = name

            #     with st.spinner("Merging data..."):
            #         output_paths = main3_server_cmdbmerge.main()
            #         output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"]  # Adjust as needed
                    
            #         for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
            #             combined_df = pd.read_excel(output_path)
            #             st.session_state[f'primary_df{i}'] = combined_df
            #             st.session_state[f'primary_df{i}_name'] = name

            #         st.session_state.count_duplicate_records = len(st.session_state.primary_df1)
            #         st.session_state.count_updated_records = len(st.session_state.primary_df2)
            #         st.session_state.count_combined_discovery = len(st.session_state.primary_df3)

            # st.write(f"Total Duplicate Records: {st.session_state.count_duplicate_records}")
            # st.write("")
            # st.write(f"Total Updated Records: {st.session_state.count_updated_records}")
            # st.write("")
            # st.write(f"Total Combined Discovery: {st.session_state.count_combined_discovery}")
            # st.write("")
            # st.subheader("Combined Discovery")
            # st.dataframe(st.session_state.primary_df3)

elif st.session_state.main_active_tab == 3:
    if st.button("Start AI Validation",type="tertiary"):
        st.session_state.validation_started = True

    tab1, tab2, tab3 = st.tabs(["Anomalies", "AI Clusters", "Final Review"])
    
    with tab1:
        if st.session_state.validation_started:
            st.write("Anomaly Definition: Stale asset which was decommissioned previously shows up as operational in the latest discovery")
            #anomalydetector.main("Semifinal CMDB.xlsx", "N")
            st.session_state.df_anomaly = pd.read_excel("anomalies_without_index.xlsx")
            st.write(f"Total Records: {len(st.session_state.df_anomaly)}")
            df_anomaly = st.data_editor(st.session_state.df_anomaly, column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
            })
            selected_rows = df_anomaly[df_anomaly['Select']]
            st.write("Selected Rows:")
            st.write(selected_rows)

    with tab2:
        if st.session_state.validation_started:
            #fuzzymatch.run_processing()
            cluster_df = pd.read_excel("Cleaned_Advanced_Flagging.xlsx")
            st.write(f"Total Records: {len(cluster_df)}")
            cluster_df = st.data_editor(cluster_df, column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
            })
            selected_rows = cluster_df[cluster_df['Select']]
            st.write("Selected Rows:")
            st.write(selected_rows)
            

    with tab3:
        if st.session_state.validation_started:
            with st.spinner("In progress..."):
                time.sleep(2)
            #     if 'primary_df1' not in st.session_state:
            #         output_paths = main3_server_mcm_dhcp.main()
            #         output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"] 
                    
            #         for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
            #             combined_df = pd.read_excel(output_path)
            #             st.session_state[f'normalized_df{i}'] = combined_df
            #             st.session_state[f'normalized_df{i}_name'] = name
            #         output_paths = main3_server_cmdbmerge.main()
            #         output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"]  # Adjust as needed
                    
            #         for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
            #             combined_df = pd.read_excel(output_path)
            #             st.session_state[f'primary_df{i}'] = combined_df
            #             st.session_state[f'primary_df{i}_name'] = name
            # if st.session_state.validation_started:
            #     confidence.confidence_code()
                
            df = pd.read_excel("Filtered_Semifinal_CMDB.xlsx")
            st.write(f"Total Records: {len(df)}")
            st.dataframe(df, hide_index=True)
        if st.button("Enrich CMDB", type="tertiary"):
            clear_cmdb_profile_state()
            st.session_state.enrich_cmdb = True
            enrich_df = pd.read_excel("Filtered_Semifinal_CMDB.xlsx")
            dynamic_data_profile(enrich_df)

    


