# app.py
# Updated on 30th April 2025
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import llamaindex_solution_revised
import anomalydetector
import mcm_normalise
import dhcp_normalise
import main3_server_mcm_dhcp
import vendor_confidence
import openpyxl
import main3_server_cmdbmerge
import main3_server_cmdb_finalval
import plotly.graph_objects as go
import fuzzymatch
import mcmdeduplication

# Configure page
st.set_page_config(
    page_title="CMDB Enrichment",
    page_icon="📊",
    layout="wide"
)


# --- File paths ---
backend_file_path = "Primary CMDB.xlsx"
csv_file_path = "Server_DHCP_Raw.csv"
csv_file_path1 = "Server_MCM_Raw.csv"

# --- Helper Functions ---
def display_metadata(df, columns, title):
    """Display filtered metadata table if all columns exist."""
    if df is not None and all(col in df.columns for col in columns):
        filtered_df = df[columns].drop_duplicates().reset_index(drop=True)
        st.subheader(title)
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning(f"Missing columns for {title} display")

def create_6x3_df(columns):
    padded = columns + [''] * (18 - len(columns))
    arr = np.array(padded).reshape(6, 3)
    dftest = pd.DataFrame(arr, columns=[".", "..", "..."])
    dftest.index = [''] * len(dftest)
    return dftest

# --- Session State Initialization ---
if 'main_df' not in st.session_state:
    try:
        st.session_state.main_df = pd.read_excel("Primary CMDB.xlsx", engine='openpyxl')
    except Exception as e:
        st.session_state.main_df = None
        st.error(f"Error loading Excel file: {str(e)}")

if 'csv_df' not in st.session_state:
    try:
        st.session_state.csv_df = pd.read_csv(csv_file_path)
    except Exception as e:
        st.session_state.csv_df = None
        st.warning(f"Unable to load the CSV file: {str(e)}")

# --- Metadata Columns Initialization ---
if 'SCCM_df' not in st.session_state:
    dfsccm = pd.read_csv(csv_file_path1)
    SCCM_COLUMNS = list(dfsccm.columns)
    st.session_state.SCCM_df = create_6x3_df(SCCM_COLUMNS)

if 'dhcp_df' not in st.session_state:
    dfdhcp = pd.read_csv(csv_file_path)
    DHCP_COLUMNS = list(dfdhcp.columns)
    st.session_state.dhcp_df = create_6x3_df(DHCP_COLUMNS)

# --- Normalization Flags ---
if 'SCCM_normalise_completed' not in st.session_state:
    st.session_state.SCCM_normalise_completed = False
if 'dhcp_normalise_completed' not in st.session_state:
    st.session_state.server_dhcp_normalise_completed = False
if 'dhcp_metadata_confidence' not in st.session_state:
    st.session_state.dhcp_metadata_confidence = None
if 'dhcp_data_confidence' not in st.session_state:
    st.session_state.dhcp_data_confidence = None
if 'sccm_metadata_confidence' not in st.session_state:
    st.session_state.sccm_metadata_confidence = None
if 'sccm_data_confidence' not in st.session_state:          
    st.session_state.sccm_data_confidence = None
if 'combined_normalized_completed' not in st.session_state:
    st.session_state.combined_normalized_completed = False
if 'combined_primary_completed' not in st.session_state:
    st.session_state.combined_primary_completed = False
if 'extract_clicked' not in st.session_state:
    st.session_state.extract_clicked = False
if 'extract_server' not in st.session_state:
    st.session_state.extract_server = False
if 'sccm_deduplication_completed' not in st.session_state:
    st.session_state.sccm_deduplication_completed = False


# ******************************************************************************************************
# ------------------------------------------------ UI --------------------------------------------------
st.title("Server CMDB Enrichment Using SCCM And DHCP Discovery")
st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)

# --- Original Data Section ---
if st.session_state.main_df is not None:
    st.header(f"Primary CMDB: {len(st.session_state.main_df)} Records")
    st.dataframe(st.session_state.main_df, height=400)
    
# =====================================================================================================
#--------------------------------------Split Data Section------------------------------------------------
# Initial two tables
st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
col1, col2 = st.columns(2)
with col1:
    df2 = pd.read_csv('Master_MCM_Raw.csv')
    st.session_state.sccm_raw_df = df2
    st.subheader(f"SCCM Raw Data: {len(st.session_state.sccm_raw_df)}")
    st.dataframe(st.session_state.sccm_raw_df)
    
with col2:
    
    df1 = pd.read_csv('Master_DHCP_Raw.csv')
    st.session_state.dhcp_raw_df = df1
    st.subheader(f"DHCP Raw Data: {len(st.session_state.dhcp_raw_df)}")
    st.dataframe(st.session_state.dhcp_raw_df)

# Button to proceed

if st.button("📊⬇️ Extract Server Assets"):
    st.session_state.extract_clicked = True

# Next two tables after button click
if st.session_state.extract_clicked:
    col3, col4 = st.columns(2)
    with col3:
        df4 = pd.read_csv('Server_MCM_Raw.csv')
        st.session_state.server_sccm_raw_df = df4
        st.subheader(f"Server SCCM Raw Data: {len(st.session_state.server_sccm_raw_df)}")
        st.dataframe(st.session_state.server_sccm_raw_df)
    with col4:
        df3 = pd.read_csv('Server_DHCP_Raw.csv')
        st.session_state.server_dhcp_raw_df = df3
        st.subheader(f"Server DHCP Raw Data: {len(st.session_state.server_dhcp_raw_df)}")
        st.dataframe(st.session_state.server_dhcp_raw_df)
        st.session_state.extract_server = True
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)


        
# =====================================================================================================        
# --- Metadata Normalization Section ---
if st.session_state.get('extract_server', False):
    st.header("Metadata Normalization")
if st.session_state.get('extract_server', False):
    col1, col2 = st.columns(2)  # Create two columns

    with col1:
        st.header("SCCM Metadata")
        st.table(st.session_state.SCCM_df)

    with col2:
        st.header("DHCP Metadata")
        st.table(st.session_state.dhcp_df)







    def run_sccm_metadata_normalization():
        if st.session_state.sccm_raw_df is not None:
            with st.spinner("Normalizing SCCM Metadata - please wait..."):
                sccm_out_path, sccm_confidence = mcm_normalise.main()  
                sccm_standardized_df = pd.read_excel(sccm_out_path)
                st.session_state.sccm_metadata_confidence = sccm_confidence
                SCCM_normalized_COLUMNS = list(sccm_standardized_df)
                st.session_state.sccm_standardized_df = create_6x3_df(SCCM_normalized_COLUMNS)
                st.session_state.SCCM_normalise_completed = True
                st.session_state.sccm_out_path = sccm_out_path
        else:
            st.warning("No Server SCCM data available to process")

    def run_dhcp_metadata_normalization():
        if st.session_state.dhcp_raw_df is not None:
            with st.spinner("Normalizing DHCP Metadata - please wait..."):
                dhcp_out_path,dhcp_confidence = dhcp_normalise.main()  
                dhcp_standardized_df = pd.read_excel(dhcp_out_path)
                st.session_state.dhcp_metadata_confidence = dhcp_confidence
                dhcp_normalized_COLUMNS = list(dhcp_standardized_df)
                st.session_state.dhcp_standardized_df = create_6x3_df(dhcp_normalized_COLUMNS)
                st.session_state.dhcp_normalise_completed = True  # Consistent flag name
                st.session_state.dhcp_out_path = dhcp_out_path
        else:
            st.warning("No Server DHCP data available to process")

    if st.button("🚀 Normalize Metadata", key="normalize_metadata", help="Click to start Server data transformation"):
        run_sccm_metadata_normalization()
        run_dhcp_metadata_normalization()
   

    # Split screen display using columns
    col_left, col_right = st.columns(2)

    # SCCM Normalization Results (Left Column)
    with col_left:
        if st.session_state.get('SCCM_normalise_completed', False):
            st.success("✅ SCCM Metadata Normalized!")
            st.markdown(f"<div style='font-size:1.3rem; font-weight:600;'>SCCM Normalized Metadata</div>", 
                       unsafe_allow_html=True)
            
            # Confidence score and dataframe
            conf_str = f"{st.session_state.sccm_metadata_confidence:.2f}" if st.session_state.sccm_metadata_confidence else "N/A"
            st.metric("Confidence Score", conf_str)
            st.dataframe(st.session_state.sccm_standardized_df)
            
            # Download button
            csv = st.session_state.sccm_standardized_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download SCCM Metadata",
                data=csv,
                file_name=f"sccm_metadata_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )

    # DHCP Normalization Results (Right Column)
    with col_right:
        if st.session_state.get('dhcp_normalise_completed', False):
            st.success("✅ DHCP Metadata Normalized!")
            st.markdown(f"<div style='font-size:1.3rem; font-weight:600;'>DHCP Normalized Metadata</div>", 
                       unsafe_allow_html=True)
            
            # Confidence score and dataframe
            conf_str = f"{st.session_state.dhcp_metadata_confidence:.2f}" if st.session_state.dhcp_metadata_confidence else "N/A"
            st.metric("Confidence Score", conf_str)
            st.dataframe(st.session_state.dhcp_standardized_df)
            
            # Download button
            csv = st.session_state.dhcp_standardized_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download DHCP Metadata",
                data=csv,
                file_name=f"dhcp_metadata_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    

# =====================================================================================================  
# --- SCCM Data Normalization Section ---
if st.session_state.get('SCCM_normalise_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("SCCM Data Normalization")

    def run_sccm_data_normalization():
        if st.session_state.get('SCCM_normalise_completed', False):
            with st.spinner("Normalizing SCCM data - this may take a moment..."):
                standardized_sccm_path = llamaindex_solution_revised.main("Server-MCM-NormMetada.xlsx", "Server-MCM-Norm2.xlsx")
                standardized_sccm_df = pd.read_excel(standardized_sccm_path)
                sccm_confidence = vendor_confidence.main("Server-MCM-NormMetada.xlsx", "mcm_discovery_data_Standardized_averageconfidence.csv")
                st.session_state.sccm_data_confidence = sccm_confidence
                st.session_state.standardized_sccm_df = standardized_sccm_df
                st.session_state.sccm_data_normalization_completed = True
        else:
            st.warning("Please complete SCCM metadata normalization first")

    if st.button("🚀 Normalize SCCM Data", help="Click to start SCCM data transformation"):
        run_sccm_data_normalization()

    if st.session_state.get('sccm_data_normalization_completed', False):
        st.success("✅ SCCM Normalization Completed!")
        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        with col1:
            st.markdown("<div style='font-size:1.8rem; font-weight:600; line-height:1.2; margin-bottom:0;'>SCCM - Normalized Data</div>", unsafe_allow_html=True)
        with col2:
            conf_str = f"{st.session_state.sccm_data_confidence:.2f}" if st.session_state.sccm_data_confidence else "N/A"
            st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:600;'>Confidence Score: {conf_str}</div>", unsafe_allow_html=True)
        
        st.dataframe(st.session_state.standardized_sccm_df, height=400)
        csv = st.session_state.standardized_sccm_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Normalized SCCM Data",
            data=csv,
            file_name=f"sccm_standardized_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )

# #======================================================================================================
# # ---------SCCM Deduplication Section-------------

# if st.session_state.get('sccm_data_normalization_completed', False):
#     st.markdown(
#     "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
#     unsafe_allow_html=true
# )
#     st.header("SCCM Deduplication")
    
#     def sccm_deduplication():
#         if st.session_state.get('sccm_data_normalization_completed', False):
#             with st.spinner("Deduplicating SCCM data - this may take a moment..."):
#                 sccm_dedup_path , removed_records= mcmdeduplication.main("Server-MCM-Norm2.xlsx")
#                 deduplicated_sccm_df = pd.read_csv(sccm_dedup_path)
#                 st.session_state.deduplicated_sccm_df = deduplicated_sccm_df
#                 st.session_state.removed_records = len(st.session_state.sccm_raw_df) - removed_records
#                 st.session_state.sccm_deduplication_completed = True

#     if st.button("🚀 Remove Duplicates SCCM", help="Click to start deduplication"):
#         sccm_deduplication()

#     if st.session_state.get('sccm_deduplication_completed', False):
#         st.success("✅ SCCM Deduplication Completed!")
#         col1, col2 = st.columns([3, 1], vertical_alignment="center")
#         with col1:
#             st.markdown("<div style='font-size:1.8rem; font-weight:600; line-height:1.2; margin-bottom:0;'>SCCM - Deduplicated Data</div>", unsafe_allow_html=True)
#         with col2:
#             st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:600;'>Removed Records: {st.session_state.removed_records}</div>", unsafe_allow_html=True)
        
#         st.dataframe(st.session_state.deduplicated_sccm_df, height=400)
#         csv = st.session_state.deduplicated_sccm_df.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label="📥 Download Deduplicated SCCM Data",
#             data=csv,
#             file_name=f"sccm_deduplicated_{datetime.now().strftime('%Y%m%d')}.csv",
#             mime='text/csv'
#         )


# # =====================================================================================================
# ---------DHCP Metadata Normalization Section-------------
# if st.session_state.get('sccm_deduplication_completed', False):
#     st.markdown(
#     "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
#     unsafe_allow_html=True
# )
#     st.header("DHCP Metadata Normalization")

#     # Load and show raw DHCP data (if not already loaded)
#     try:
#         dhcp_csv_file_path = "Server_DHCP_Raw.csv"
#         dhcp_raw_df = pd.read_csv(dhcp_csv_file_path)
#         st.subheader(f"Server DHCP Raw Data: {len(dhcp_raw_df)} Records")
#         st.dataframe(dhcp_raw_df, height=400)
#         st.session_state.dhcp_raw_df = dhcp_raw_df
#     except Exception as e:
#         st.error(f"Failed to load Server DHCP raw data: {str(e)}")
#         st.session_state.dhcp_raw_df = None

#     # Button to normalize Server DHCP data
#     def run_dhcp_normalization():
#         if st.session_state.dhcp_raw_df is not None:
#             with st.spinner("Normalizing DHCP Metadata - please wait..."):
#                 dhcp_out_path,dhcp_confidence = dhcp_normalise.main()  
#                 dhcp_standardized_df = pd.read_excel(dhcp_out_path)
#                 st.session_state.dhcp_metadata_confidence = dhcp_confidence
#                 st.session_state.dhcp_standardized_df = dhcp_standardized_df
#                 st.session_state.dhcp_normalise_completed = True  # Consistent flag name
#                 st.session_state.dhcp_out_path = dhcp_out_path
#         else:
#             st.warning("No Server DHCP data available to process")

#     if st.button("🚀 Normalize DHCP Metadata", key="normalize_dhcp", help="Click to start Server DHCP data transformation"):
#         run_dhcp_normalization()

# # Show results if normalization is done
# if st.session_state.get('dhcp_normalise_completed', False):
#     st.success("✅ DHCP Metadata Normalized!")
#     col1, col2 = st.columns([3, 1], vertical_alignment="center")
#     with col1:
#         st.markdown("<div style='font-size:1.8rem; font-weight:600; line-height:1.2; margin-bottom:0;'>DHCP - Normalized Metadata</div>", unsafe_allow_html=True)
#     with col2:
#         conf_str = f"{st.session_state.dhcp_metadata_confidence:.2f}" if st.session_state.dhcp_metadata_confidence else "N/A"
#         st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:600;'>Confidence Score: {conf_str}</div>", unsafe_allow_html=True)
    
#     st.dataframe(st.session_state.dhcp_standardized_df, height=400)
#     csv = st.session_state.dhcp_standardized_df.to_csv(index=False).encode('utf-8')
#     st.download_button(
#         label="📥 Download Metadata-Normalized DHCP",
#         data=csv,
#         file_name=f"standardized_dhcp_{datetime.now().strftime('%Y%m%d')}.csv",
#         mime='text/csv'
#     )

# =====================================================================================================
# --- DHCP Data Normalization Section ---
if st.session_state.get('sccm_data_normalization_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("DHCP Data Normalization")

    def run_normalization():
        with st.spinner("Normalizing data - this may take a moment..."):
            standardized_xl_path = llamaindex_solution_revised.main("Server-DHCP-NormMetada.xlsx","Server-DHCP-Norm2.xlsx")
            # cleaned_df_path = fuzzymatch.main(standardized_xl_path, "fuzzyclustering.xlsx")
            # standardized_df = pd.read_excel(cleaned_df_path)
            standardized_df = pd.read_excel(standardized_xl_path)
            confidence = vendor_confidence.main("Server-DHCP-NormMetada.xlsx","dhcp_discovery_data_Standardized_averageconfidence.csv")
            st.session_state.dhcp_data_confidence = confidence
            st.session_state.standardized_df = standardized_df
            st.session_state.normalization_completed = True

    if st.button("🚀 Normalize Data", help="Click to start data transformation"):
        run_normalization()

    if st.session_state.get('normalization_completed', False):
        st.success("✅ Normalization completed!")
        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        with col1:
            st.markdown("<div style='font-size:1.8rem; font-weight:600; line-height:1.2; margin-bottom:0;'>DHCP - Normalized Data</div>", unsafe_allow_html=True)
        with col2:
            conf_str = f"{st.session_state.dhcp_data_confidence:.2f}" if st.session_state.dhcp_data_confidence else "N/A"
            st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:600;'>Confidence Score: {conf_str}</div>", unsafe_allow_html=True)
        
        st.dataframe(st.session_state.standardized_df, height=400)
        csv = st.session_state.standardized_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Normalized Data",
            data=csv,
            file_name=f"standardized_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )

# =====================================================================================================
# ---------- Merge SCCM and DHCP ------------
if st.session_state.get('normalization_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("Merge SCCM & DHCP Discovery")
    
    if st.button("🔗 Merge Data", key="merge_data"):
        with st.spinner("Combining data..."):
            output_paths = main3_server_mcm_dhcp.main()
            output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"] 
            
            for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
                combined_df = pd.read_excel(output_path)
                st.session_state[f'normalized_df{i}'] = combined_df
                st.session_state[f'normalized_df{i}_name'] = name
            
            st.session_state.combined_normalized_completed = True

if st.session_state.get('combined_normalized_completed', False):
    st.success("✅ SCCM & DHCP Merged Successfully!")
    for i in range(1, 4):
        df = st.session_state.get(f'normalized_df{i}')
        name = st.session_state.get(f'normalized_df{i}_name')
        if df is not None:
            st.subheader(f"{name}: {len(df)}")
            st.dataframe(df, height=400)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download {name}",
                data=csv,
                file_name=f"{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )

# =====================================================================================================
# ---------- Merge with Primary CMDB ------------

if st.session_state.get('combined_normalized_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("Merge Primary & Latest Discovered Data")
    
    if st.button("🔗 Merge Primary Data", key="merge_primary_data"):
        with st.spinner("Combining data..."):
            output_paths = main3_server_cmdbmerge.main()
            output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"]  # Adjust as needed
            
            for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
                combined_df = pd.read_excel(output_path)
                st.session_state[f'primary_df{i}'] = combined_df
                st.session_state[f'primary_df{i}_name'] = name
            
            st.session_state.combined_primary_completed = True

if st.session_state.get('combined_primary_completed', False):
    st.success("✅ CMDB Discovery Enrichment Successful!")
    for i in range(1, 4):
        df = st.session_state.get(f'primary_df{i}')
        name = st.session_state.get(f'primary_df{i}_name')
        if df is not None:
            st.subheader(f"{name}: {len(df)}")
            st.dataframe(df, height=400)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                    label=f"📥 Download {name}",
                    data=csv,
                    file_name=f"{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                    key=f"download_{name}_{i}"  # Ensure this key is unique for each button
                )



# =====================================================================================================  
# --- Anomaly Flagging ---
if st.session_state.get('combined_primary_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("CMDB Validation ")

    def run_cmdb_validation():
        if st.session_state.get('combined_primary_completed', False):
            with st.spinner("Detecting anomalous records - this may take a moment..."):
                standardized_cmdb_df, cmdb_confidence, anomaly_count , remain_df= anomalydetector.main("Semifinal CMDB.xlsx", "N")
                #standardized_cmdb_df = pd.read_excel(standardized_cmdb_path)
                st.session_state.cmdb_validation_confidence = cmdb_confidence
                st.session_state.standardized_cmdb_df = standardized_cmdb_df
                st.session_state.standardized_cmdb_anol = anomaly_count
                st.session_state.CMDB_validation_completed = True
                st.session_state.cmdb_out_path = "assets_anomalies.xlsx"
        else:
            st.warning("Please complete required validation")

    if st.button("🚀 Flag Anomalies", key="anomaly_flag", help="Click to start anomaly detection"):
        run_cmdb_validation()

    # Show cmdb validation results if completed
    if st.session_state.get('CMDB_validation_completed', False):
        st.success("✅ Anomalies Detected Successfully!")
        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        with col1:
            st.markdown(f"<div style='font-size:1.8rem; font-weight:600; line-height:1.2; margin-bottom:0;'>CMDB Validation: {st.session_state.standardized_cmdb_anol} Anomalies Flagged</div>", unsafe_allow_html=True)
        with col2:
            conf_str = f"{st.session_state.cmdb_validation_confidence:.2f}" if st.session_state.cmdb_validation_confidence else "N/A"
            st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:600;'>Confidence Score: {conf_str}</div>", unsafe_allow_html=True)
        
        st.dataframe(st.session_state.standardized_cmdb_df, height=400)
        csv = st.session_state.standardized_cmdb_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Flagged Anomalies",
            data=csv,
            file_name=f"anomalies_flagged_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
# =====================================================================================================
# ---------- De-Duplication of Merged CMDB ------------
if st.session_state.get('CMDB_validation_completed', False):
    st.markdown(
    "<hr style='border:1.5px solid #888; margin-top:20px; margin-bottom:20px;'>",
    unsafe_allow_html=True
)
    st.header("De-duplication in Final CMDB")
    
    if st.button("🔗 De-duplicate Data", key="deduplicate_data"):
        with st.spinner("Evaluating data..."):
            output_paths = main3_server_cmdb_finalval.main()
            output_names = ["Duplicates in CMDB", "Final CMDB"] 
            
            for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
                combined_df = pd.read_excel(output_path)
                st.session_state[f'normalized_df2_{i}'] = combined_df  # Changed key format
                st.session_state[f'normalized_df2_{i}_name'] = name
            
            st.session_state.deduplication_completed = True

if st.session_state.get('deduplication_completed', False):
    st.success("✅ De-duplication Completed Successfully!")
    for i in range(1, 3):  # Only 2 outputs now
        df = st.session_state.get(f'normalized_df2_{i}')
        name = st.session_state.get(f'normalized_df2_{i}_name')
        if df is not None and not df.empty:
            st.subheader(f"{name}: {len(df)}")
            st.dataframe(df, height=400)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download {name}",
                data=csv,
                file_name=f"{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                key=f"dedupe_download_{i}"  # Added unique key
            )


# =====================================================================================================
#******************************* Visualization **************************



# # -------- Chart -------------
# # Define node labels
# labels = [
#     "DHCP Ingestion", "SCCM Ingestion", "AI",
#     "Duplicates", "Updates", "New", "Primary CMDB"
# ]

# # Define flows: sources and targets by index in labels
# sources = [0, 1, 2, 2, 2, 5]  # From DHCP, SCCM, AI to outputs, New to Primary CMDB
# targets = [2, 2, 3, 4, 5, 6]

# # Assign values for each flow
# values = [
#     dhcp_count,              # DHCP -> AI
#     sccm_count,              # SCCM -> AI
#     duplicates_count,        # AI -> Duplicates
#     updates_count,           # AI -> Updates
#     newly_discovered_count,  # AI -> Newly Discovered
#     primary_cmdb_count       # New -> Primary CMDB
# ]

# # -------- Create the Sankey diagram --------------
# fig = go.Figure(data=[go.Sankey(
#     node=dict(
#         pad=15,
#         thickness=20,
#         line=dict(color="black", width=0.5),
#         label=labels,
#         color="blue"
#     ),
#     link=dict(
#         source=sources,
#         target=targets,
#         value=values,
#         color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#19D3F3", "#FF6692"]
#     )
# )])

# fig.update_layout(title_text="Data Flow Overview", font_size=12)


# # -------- Display -------------
# st.title("Static Data Flow Chart")
# st.plotly_chart(fig, use_container_width=True) 
# =======================================================================