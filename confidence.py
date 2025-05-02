import pandas as pd
def confidence_code():
    try:
        advanced_flagging_df = pd.read_excel("Advanced Flagging_with_index.xlsx")
        anomalies_df = pd.read_excel("anomalies_with_index.xlsx")
        semifinal_cmdb_df = pd.read_excel("Semifinal CMDB.xlsx")
        print(f"Successfully loaded all excel files")
        print(f"Advanced flagging shape: {advanced_flagging_df.shape}")
        print(f"Anomalies shape: {anomalies_df.shape}")
        print(f"Semifinal CMDB shape: {semifinal_cmdb_df.shape}")
    except FileNotFoundError as e:
        print(f"Error: One or more files not found: {e}")
        exit()

    # Extract the index columns from the flagging files
    # Assuming the index column is named 'index'
    advanced_flagging_indices = advanced_flagging_df['index'].tolist()
    anomalies_indices = anomalies_df['index'].tolist()

    # Combine the indices to remove
    indices_to_remove = list(set(advanced_flagging_indices + anomalies_indices))
    print(f"Total number of unique indices to remove: {len(indices_to_remove)}")

    # Create an actual row index for each row in the Semifinal CMDB file
    # The index is calculated as row_number - 2, where row_number starts from 1
    # In pandas, index starts from 0, so we add 1 to get the row_number, then subtract 2
    semifinal_cmdb_df['calculated_index'] = semifinal_cmdb_df.index + 1 - 1  # Adding 1 for row number, subtracting 1 to match 0-based index

    # Filter out rows based on the calculated index
    filtered_cmdb_df = semifinal_cmdb_df[~semifinal_cmdb_df['calculated_index'].isin(indices_to_remove)]
    print(f"Number of rows removed: {semifinal_cmdb_df.shape[0] - filtered_cmdb_df.shape[0]}")
    print(f"Shape of filtered dataframe: {filtered_cmdb_df.shape}")

    # Remove the temporary calculated_index column
    filtered_cmdb_df = filtered_cmdb_df.drop(columns=['calculated_index'])

    # Save the filtered DataFrame to a new Excel file
    output_file = "Filtered_Semifinal_CMDB.xlsx"
    filtered_cmdb_df.to_excel(output_file, index=False)

    print(f"Filtered data saved to {output_file}")