import pandas as pd

def main(input_path):
    df = pd.read_excel(input_path)
    
    # Create composite key and sort
    df['key'] = df[['Name', 'MAC Address', 'Operating System']].fillna('').agg('_'.join, axis=1)
    df_sorted = df.sort_values(['key', 'Most recent discovery'], ascending=[True, False])
    
    # Get all older records
    df_duplicates = df_sorted[df_sorted.duplicated(subset='key', keep=False)]
    
    # Keep latest records
    df_deduplicated = df_sorted.drop_duplicates(subset='key', keep='first')

    # Reorder columns for both dataframes
    cols_order = ['Name', 'Operating System', 'MAC Address', 'Most recent discovery']
    cols_order += [col for col in df.columns if col not in cols_order]
    df_duplicates = df_duplicates[cols_order]
    df_deduplicated = df_deduplicated[cols_order]
    
    # Save results
    df_duplicates.drop(columns='key').to_csv("SCCM_Duplicates.csv", index=False)
    df_deduplicated.drop(columns='key').to_csv("SCCM_Deduplicated.csv", index=False)
    
    print(f"Total records: {len(df)}")
    print(f"Older records: {len(df_duplicates)}")
    print(f"Latest records: {len(df_deduplicated)}")

     # Calculate removed records count
    removed_count = len(df_duplicates)

    return "SCCM_Deduplicated.csv", removed_count, 'SCCM_Duplicates.csv'
