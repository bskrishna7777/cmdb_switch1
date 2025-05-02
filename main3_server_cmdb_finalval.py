import pandas as pd
import numpy as np

def main():
    # Load Excel files and clean
    df_semifinal = pd.read_excel("Semifinal CMDB.xlsx").replace('', np.nan)

    # Find duplicates in both dataframes

    duplicates_dhcp = df_semifinal[df_semifinal.duplicated()]

    # Save the combined duplicates to a new Excel file
    duplicates_dhcp.to_excel("Final Duplicates.xlsx", index=False)
    print(f"Combined duplicate rows saved: {len(duplicates_dhcp)}")

    # Remove duplicates
    df_semifinal = df_semifinal.drop_duplicates()

    print(f"DHCP rows after drop_duplicates: {len(df_semifinal)}")

    # Save output files
    df_semifinal.to_excel("Final Validated CMDB.xlsx", index=False)

    return "Final Duplicates.xlsx", "Final Validated CMDB.xlsx" 


