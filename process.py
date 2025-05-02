import pandas as pd
import numpy as np
# def show_data():
def show_data():
    # Read the Excel file
    # file_path = "asset_anomalies.xlsx"  # Replace with your file path
    df = pd.read_excel("asset_anomalies.xlsx")
    if "Unnamed: 0" in df.columns:
        df.rename(columns={"Unnamed: 0": "index"}, inplace=True)
    # print(df)

    filtered_df = df

    # Get the current column names
    column_names = list(filtered_df.columns)

    # Check for empty or NaN column names and replace with "Index"
    for i, col_name in enumerate(column_names):
        if pd.isna(col_name) or col_name == '' or col_name is None:
            column_names[i] = "Index"

    # Update the DataFrame with the new column names
    filtered_df.columns = column_names

    # FILE 1: With Index column and Anomaly moved after Index
    # Get the list of columns
    cols = list(filtered_df.columns)

    # If "Anomaly" is in columns, remove it to reposition later
    if "Anomaly" in cols:
        cols.remove("Anomaly")
        
    # Find the position of "Index" column (if it exists)
    if "Index" in cols:
        index_pos = cols.index("Index")
        # Insert "Anomaly" right after "Index"
        cols.insert(index_pos + 1, "Anomaly")
    else:
        # If no "Index" column, just add "Anomaly" to the beginning
        cols.insert(0, "Anomaly")

    # Reorder the DataFrame
    filtered_df_with_index = filtered_df[cols]

    # Save the first file with Index and repositioned Anomaly
    print(filtered_df_with_index)
    filtered_df_with_index.to_excel("anomalies_with_index.xlsx", index=False)
    print("saving the df the filter in anomalies_with_index.xlsx")
    # FILE 2: Without Index column, with Select column as first column (all FALSE), and Anomaly as second column
    # Get all columns except "Index"
    cols_no_index = [col for col in cols if col != "Index"]

    # Remove "Anomaly" if it exists to reposition it
    if "Anomaly" in cols_no_index:
        cols_no_index.remove("Anomaly")
        
    # Add "Anomaly" at the beginning
    cols_no_index.insert(0, "Anomaly")

    # Create DataFrame without Index and with Anomaly first
    filtered_df_no_index = filtered_df[cols_no_index].drop(columns=["index"], errors="ignore")

    # Add a new "Select" column with all FALSE values
    # Step 1: Insert the "Select" column at the beginning
    filtered_df_no_index.insert(0, "Select", False)

    # Step 2: Move the "Confidence" column to the 3rd position (index 2)
    confidence_column = filtered_df_no_index.pop('Confidence')
    filtered_df_no_index.insert(2, 'Confidence', confidence_column)

    # Step 3: Create the "Datasource" column based on "Operational status"
    def get_datasource(operational_status):
        if operational_status == 'Retired':
            return 'CMDB'
        elif operational_status == 'Operational':
            return 'SCCM'
        else:
            return None  # Or some other default value if needed

    filtered_df_no_index['Datasource'] = filtered_df_no_index['Operational status'].apply(get_datasource)

    # Step 4: Move the "Datasource" column to the 4th position (index 3)
    datasource_column = filtered_df_no_index.pop('Datasource')  # Remove the column
    filtered_df_no_index.insert(3, 'Datasource', datasource_column)  # Insert at index 3

    filtered_df_no_index.to_excel("anomalies_without_index.xlsx", index=False)
    print("DataFrame after creating and moving 'Datasource' column:")
    print(filtered_df_no_index)

    # print("Created two Excel files:")
    # print("1. anomalies_with_index.xlsx - Contains Index column with Anomaly after Index")
    # print("2. anomalies_without_index.xlsx - Has Select column (all FALSE) first, then Anomaly column, and no Index column")

show_data()