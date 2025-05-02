import pandas as pd
import numpy as np

def main():
    # Load Excel files and clean
    df_prim = pd.read_excel("Primary CMDB.xlsx").replace('', np.nan)
    df_secon = pd.read_excel("mcm_dhcp_combined_cleaned_fixed.xlsx").replace('', np.nan)
    
    # Show initial row counts
    print(f"Initial Primary rows: {len(df_prim)}")
    print(f"Initial Secondary rows: {len(df_secon)}")
    
    # Find duplicates in both dataframes
    duplicates_dhcp = df_prim[df_prim.duplicated()]
    duplicates_mcm = df_secon[df_secon.duplicated()]
    
    # Combine duplicates from both dataframes
    combined_duplicates = pd.concat([duplicates_dhcp, duplicates_mcm])
    
    # Save the combined duplicates to a new Excel file
    combined_duplicates.to_excel("Combined_Duplicates1.xlsx", index=False)
    print(f"Combined duplicate rows saved: {len(combined_duplicates)}")
    
    # Remove duplicates
    df_prim = df_prim.drop_duplicates()
    df_secon = df_secon.drop_duplicates()
    
    print(f"DHCP rows after drop_duplicates: {len(df_prim)}")
    print(f"MCM rows after drop_duplicates: {len(df_secon)}")
    
    # Get all column names and ensure 'Name' and 'IP Address' are first
    all_columns = sorted(set(df_prim.columns).union(df_secon.columns))
    all_columns = ['Name', 'IP Address'] + [col for col in all_columns if col not in ['Name', 'IP Address']]
    
    # Align dataframes
    df_prim = df_prim.reindex(columns=all_columns)
    df_secon = df_secon.reindex(columns=all_columns)
    
    # Combine for merging
    combined = pd.concat([df_prim, df_secon], ignore_index=True)
    print(f"Total combined rows before merging: {len(combined)}")
    #combined.to_excel("mcm_dhcp_combined_before_merging.xlsx", index=False)
    
    # ---------------------------
    # Dynamic Merging Logic
    # ---------------------------
    merged_rows = []
    merged_only_rows = []
    
    # Temporary fill for grouping (needed to group rows even with NaNs)
    combined['Name'] = combined['Name'].fillna('MISSING_NAME')
    combined['IP Address'] = combined['IP Address'].fillna('MISSING_IP')
    
    # Group and merge
    for _, group in combined.groupby(['Name', 'IP Address']):
        merged = group.iloc[0].copy()
        if len(group) > 1:
            for i in range(1, len(group)):
                merged = merged.combine_first(group.iloc[i])
            merged_only_rows.append(merged)
        merged_rows.append(merged)
    
    # Restore original NaNs
    for col in ['Name', 'IP Address']:
        for df in [merged_rows, merged_only_rows]:
            for row in df:
                if row[col] == 'MISSING_NAME' or row[col] == 'MISSING_IP':
                    row[col] = np.nan
    
    # Final cleaned DataFrame
    df_final = pd.DataFrame(merged_rows).reindex(columns=all_columns)
    df_merged_only = pd.DataFrame(merged_only_rows).reindex(columns=all_columns)
    
    # Save output files
    df_merged_only.to_excel("secondary_cmdb_merged_rows_only.xlsx", index=False)
    df_final.to_excel("Semifinal CMDB.xlsx", index=False)
    
    
    # Print summary
    print(f"Final merged unique rows saved: {len(df_final)}")
    print(f"Only merged (combined) rows saved: {len(df_merged_only)}")

    return "Combined_Duplicates1.xlsx", "secondary_cmdb_merged_rows_only.xlsx", "Semifinal CMDB.xlsx", 


