# Read Excel files
import pandas as pd
def main():
    dfm = pd.read_excel(r"Server-MCM-Norm1.xlsx")
    dfn = pd.read_excel(r"Server-DHCP-Norm1.xlsx")
    
    # Compare columns
    mcm_cols = set(dfm.columns)
    dhcp_cols = set(dfn.columns)
    
    common_cols = mcm_cols & dhcp_cols
    print(len(common_cols))
    only_in_mcm = mcm_cols - dhcp_cols
    print(len(only_in_mcm))
    only_in_dhcp = dhcp_cols - mcm_cols
    print(len(only_in_dhcp))
    
    # Print the differences
    print("Common columns:")
    print(list(common_cols))
    
    print("\nColumns only in MCM File:")
    print(list(only_in_mcm))
    
    print("\nColumns only in DHCP File:")
    print(list(only_in_dhcp))
    
    
    # Combine the dataframes
    df_combined = pd.concat([dfm, dfn], ignore_index=True, sort=False)

    df_combined = df_combined.sort_values(by='MAC Address', ascending=True)
    # Save to Excel
    df_combined.to_excel(r"Server-MCM-DHCP Combined.xlsx", index=False)
    
    output_path = "Server-MCM-DHCP Combined.xlsx"
    return output_path