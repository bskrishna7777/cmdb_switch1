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
        width: 24%;
        margin: 0;
        border: 1px solid
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
    return pd.read_excel("Primary CMDB.xlsx")

@st.cache_data
def load_server_dhcp():
    return pd.read_csv("Server_DHCP_Raw.csv")

@st.cache_data
def load_server_sccm():
    return pd.read_csv("Server_MCM_Raw.csv")

# --- Store dataframes and row counts in session state ---
if "df" not in st.session_state:
    st.session_state["df"] = load_cmdb_data()
if "total_rows" not in st.session_state:
    st.session_state["total_rows"] = len(st.session_state["df"])
if "server_dhcp" not in st.session_state:
    st.session_state["server_dhcp"] = load_server_dhcp()
if "server_sccm" not in st.session_state:
    st.session_state["server_sccm"] = load_server_sccm()
if "total_sccm_records" not in st.session_state:
    st.session_state["total_sccm_records"] = None

# --- Render Main Tabs ---
st.title("CMDB Enrichment Leveraging AI/ML")
main_tabs()

def change_tab(tab_index):
    st.session_state.active_tab = tab_index
    st.rerun()
# --- Main Content Areas ---
if st.session_state.main_active_tab == 0:
    st.header("CMDB Insights")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Class Distribution")
        image_path , server_count = graphcreation.create_pie_chart(st.session_state["df"])
        st.session_state.server_count = server_count
        st.image(image_path)

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
                    Total Server Records<br>
                    <span style="font-size: 60px; font-weight: bold; color: #388e3c;">
                        {st.session_state.server_count}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.header("CMDB Table")
    st.dataframe(st.session_state["df"])

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

    if st.session_state["server_checked"]:
        st.markdown("---")
        tab_dhcp, tab_sccm = st.tabs(["DHCP", "SCCM"])
        with tab_dhcp:
            with st.spinner("AI Processing..."):
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
                st.dataframe(st.session_state["server_dhcp"])

        with tab_sccm:
            with st.spinner("AI Processing..."):
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
                st.dataframe(st.session_state["server_sccm"])

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
        "Auto Model Data Mapping",
        "DHCP Standardisation",
        "SCCM Standardisation"
    ]

            

            # Render tabs
            tab_objs = st.tabs(standardisation_tabs)

            # --- Tab 0: Auto Model Data Mapping ---
            with tab_objs[0]:
                
                    def run_sccm_metadata_normalization():
                        with st.spinner("Mapping Data Model - please wait..."):
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
                        with st.spinner("Mapping Data Model - please wait..."):
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
                        st.write(st.session_state.get('dhcp_column_mapping', {}))
                    with col2:
                        st.subheader("SCCM Metadata Normalization")
                        st.write(st.session_state.get('sccm_column_mapping', {}))
                   

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
                        st.dataframe(st.session_state.get('raw_dhcp_df', pd.DataFrame()))
                    with col2:
                        st.subheader(f"Server DHCP Normalized Data, Confidence: {st.session_state.get('dhcp_data_confidence', 0):.2f}")
                        st.dataframe(st.session_state.get('standardized_df', pd.DataFrame()))
                    

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
                        st.dataframe(st.session_state.get('sccm_raw_df', pd.DataFrame()))
                    with col2:
                        st.subheader(f"Server SCCM Normalized Data, Confidence: {st.session_state.get('sccm_data_confidence', 0):.2f}")
                        st.dataframe(st.session_state.get('standardized_sccm_df', pd.DataFrame()))
                    if st.button("Next: Deduplication →",type="tertiary"):
                        # Move to your main tab for Deduplication, e.g.,
                        st.session_state.active_tab = 1
                        st.rerun()
        elif st.session_state.active_tab == 1:  # Deduplication

            def sccm_deduplication():
                with st.spinner("Deduplicating SCCM data - this may take a moment..."):
                    sccm_dedup_path , removed_records, sccm_dup_path= mcmdeduplication.main("Server-MCM-Norm2.xlsx")
                    duplicated_sccm_df = pd.read_csv(sccm_dup_path)
                    st.session_state.duplicated_sccm_df = duplicated_sccm_df
                    deduplicated_sccm_df = pd.read_csv(sccm_dedup_path)
                    st.session_state.deduplicated_sccm_df = deduplicated_sccm_df
                    st.session_state.sccm_removed_records =  len(duplicated_sccm_df)
                    st.session_state.total_sccm_records = len(st.session_state.sccm_raw_df)
                    st.session_state.sccm_deduplicated_records = len(st.session_state.deduplicated_sccm_df)
                    st.session_state.sccm_deduplication_completed = True

            if 'deduplicated_sccm_df' not in st.session_state:
                sccm_deduplication()

            def dhcp_deduplication():
                with st.spinner("Deduplicating DHCP data - this may take a moment..."):
                    dhcp_dedup_path , removed_records1, dhcp_dup_path= dhcpdeduplication.main()
                    duplicated_dhcp_df = pd.read_csv(dhcp_dup_path)
                    st.session_state.duplicated_dhcp_df = duplicated_dhcp_df
                    deduplicated_dhcp_df = pd.read_csv(dhcp_dedup_path)
                    st.session_state.deduplicated_dhcp_df = deduplicated_dhcp_df
                    st.session_state.removed_records = len(duplicated_dhcp_df)
                    st.session_state.total_dhcp_records = len(st.session_state.raw_dhcp_df)
                    st.session_state.dhcp_deduplicated_records = len(st.session_state.deduplicated_dhcp_df)
                    st.session_state.dhcp_deduplication_completed = True

            if 'deduplicated_dhcp_df' not in st.session_state:  
                dhcp_deduplication()

            tab1, tab2 = st.tabs(["DHCP Deduplication", "SCCM Deduplication"])
            with tab1:
                st.write(f"Total DHCP Records: {st.session_state.total_dhcp_records}")
                st.write(f"Duplicate Records: {st.session_state.removed_records}")
                st.write(f"De-duplicated Records: {st.session_state.dhcp_deduplicated_records}")
                st.write("")
                col1, col2 = st.columns([1, 1]) 
                with col1:
                    st.subheader("DHCP Duplicated Data")
                    st.dataframe(st.session_state.duplicated_dhcp_df)
                with col2:
                    st.subheader("DHCP Deduplicated Data")
                    st.dataframe(st.session_state.deduplicated_dhcp_df)

            with tab2:
                     
                st.write(f"Total SCCM Records: {st.session_state.total_sccm_records}")
                st.write(f"Duplicate Records: {st.session_state.sccm_removed_records}")
                st.write(f"De-duplicated Records: {st.session_state.sccm_deduplicated_records}") 
                st.write("")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("SCCM Duplicated Data")
                    st.dataframe(st.session_state.duplicated_sccm_df)
                with col2:
                    st.subheader("SCCM Deduplicated Data")
                    st.dataframe(st.session_state.deduplicated_sccm_df)
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

    tab1, tab2, tab3 = st.tabs(["100% Confidence Score", "AI Clusters", "Anomalies"])
    
              

    with tab1:
        if st.session_state.validation_started:
            with st.spinner("AI Validation in progress..."):
                if 'primary_df1' not in st.session_state:
                    output_paths = main3_server_mcm_dhcp.main()
                    output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"] 
                    
                    for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
                        combined_df = pd.read_excel(output_path)
                        st.session_state[f'normalized_df{i}'] = combined_df
                        st.session_state[f'normalized_df{i}_name'] = name
                    output_paths = main3_server_cmdbmerge.main()
                    output_names = ["Duplicate Records", "Updated Records", "Combined Discovery"]  # Adjust as needed
                    
                    for i, (output_path, name) in enumerate(zip(output_paths, output_names), 1):
                        combined_df = pd.read_excel(output_path)
                        st.session_state[f'primary_df{i}'] = combined_df
                        st.session_state[f'primary_df{i}_name'] = name
            if st.session_state.validation_started:
                df = pd.read_excel("updated_file2.xlsx")
                st.write(f"Total Records: {len(df)}")
                st.dataframe(df)
            

    with tab2:
        if st.session_state.validation_started:
            df = pd.read_excel("AI Cluster.xlsx")
            st.write(f"Total Records: {len(df)}")
            st.dataframe(df)

    with tab3:
        if st.session_state.validation_started:
            st.write("Anomaly Definition: Stale asset which was decommissioned previously shows up as operational in the latest discovery")
            df = pd.read_excel("asset_anomalies.xlsx")
            st.write(f"Total Records: {len(df)}")
            st.dataframe(df)

    if st.button("Enrich CMDB",type="tertiary"):
        st.session_state.enrich_cmdb = True

