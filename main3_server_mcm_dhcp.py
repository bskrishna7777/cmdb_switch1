import pandas as pd
import numpy as np

def main():
    # Load Excel files and clean
    df_dhcp = pd.read_csv("DHCP_Deduplicated.csv").replace('', np.nan)
    df_mcm = pd.read_csv("SCCM_Deduplicated.csv").replace('', np.nan)
    
    # Show initial row counts
    print(f"Initial DHCP rows: {len(df_dhcp)}")
    print(f"Initial MCM rows: {len(df_mcm)}")
    
    # Find duplicates in both dataframes
    
    duplicates_dhcp = df_dhcp[df_dhcp.duplicated()]
    duplicates_mcm = df_mcm[df_mcm.duplicated()]
    
    # Combine duplicates from both dataframes
    combined_duplicates = pd.concat([duplicates_dhcp, duplicates_mcm])
    
    # Save the combined duplicates to a new Excel file
    combined_duplicates.to_excel("Combined_Duplicates.xlsx", index=False)
    print(f"Combined duplicate rows saved: {len(combined_duplicates)}")
    
    # Remove duplicates
    df_dhcp = df_dhcp.drop_duplicates()
    df_mcm = df_mcm.drop_duplicates()
    
    print(f"DHCP rows after drop_duplicates: {len(df_dhcp)}")
    print(f"MCM rows after drop_duplicates: {len(df_mcm)}")
    
    # Get all column names and ensure 'Name' and 'IP Address' are first
    all_columns = sorted(set(df_dhcp.columns).union(df_mcm.columns))
    all_columns = ['Name', 'IP Address'] + [col for col in all_columns if col not in ['Name', 'IP Address']]
    
    # Align dataframes
    df_dhcp = df_dhcp.reindex(columns=all_columns)
    df_mcm = df_mcm.reindex(columns=all_columns)
    
    # Combine for merging
    combined = pd.concat([df_dhcp, df_mcm], ignore_index=True)
    print(f"Total combined rows before merging: {len(combined)-1}")
    #combined.to_excel("mcm_dhcp_combined_before_merging.xlsx", index=False)
    
    # ---------------------------
    # Dynamic Merging Logic
    # ---------------------------
    merged_rows = []
    merged_only_rows = []
    
    # Temporary fill for grouping (needed to group rows even with NaNs)
    combined['Name'] = combined['Name'].fillna('MISSING_NAME')
    combined['MAC Address'] = combined['MAC Address'].fillna('MISSING_MAC')
    
    # Group and merge
    for _, group in combined.groupby(['Name', 'MAC Address']):
        merged = group.iloc[0].copy()
        if len(group) > 1:
            for i in range(1, len(group)):
                merged = merged.combine_first(group.iloc[i])
            merged_only_rows.append(merged)
        merged_rows.append(merged)
    
    # Restore original NaNs
    for col in ['Name', 'MAC Address']:
        for df in [merged_rows, merged_only_rows]:
            for row in df:
                if row[col] == 'MISSING_NAME' or row[col] == 'MISSING_MAC':
                    row[col] = np.nan
    
    # Final cleaned DataFrame
    df_final = pd.DataFrame(merged_rows).reindex(columns=all_columns)
    df_merged_only = pd.DataFrame(merged_only_rows).reindex(columns=all_columns)
    
    # Save output files
    df_merged_only.to_excel("Merge1_Updated_Records.xlsx", index=False)
    df_final.to_excel("Merge1_Combined_Records.xlsx", index=False)
    
    
    # Print summary
    print(f"Final merged unique rows saved: {len(df_final)}")
    print(f"Only merged (combined) rows saved: {len(df_merged_only)}")

    return "Combined_Duplicates.xlsx", "Merge1_Updated_Records.xlsx", "Merge1_Combined_Records.xlsx", 

# if __name__ == "__main__":
#  main()
