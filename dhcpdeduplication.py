import pandas as pd

def main():
    raw_df = pd.read_excel("Server-DHCP-Norm2.xlsx")
    raw_df1 = raw_df.copy()
    
    # Find exact duplicates in each dataframe (excluding first occurrences)
    duplicates_dhcp = raw_df[raw_df.duplicated(keep='first')]  # Keep only duplicates, not first occurrence
    deduplicates_dhcp = raw_df1.drop_duplicates()

     # Reorder columns for both dataframes
    cols_order = ['Name', 'Operating System', 'MAC Address']
    cols_order += [col for col in raw_df1.columns if col not in cols_order]
    duplicates_dhcp = duplicates_dhcp[cols_order]
    deduplicates_dhcp = deduplicates_dhcp[cols_order]
    
    deduplicates_dhcp.to_csv("DHCP_Deduplicated.csv", index=False)
    duplicates_dhcp.to_csv("DHCP_Duplicates.csv", index=False)

     # Calculate removed records count
    removed_count = len(duplicates_dhcp)

    return "DHCP_Deduplicated.csv", removed_count, "DHCP_Duplicates.csv"
