import pandas as pd
import json
import numpy as np  # For random time offset

LIMIT=500
def filter_retired_and_recent_discovery(df, limit=LIMIT):
    condition_status = df['Operational status'].str.lower() == 'retired'
    condition_discovery = df['Most recent discovery'].notnull()
    filtered_df = df[condition_status & condition_discovery]
    return filtered_df.head(limit)

def update_discovery_dates(df, date_column, days_to_add=10, max_hours_offset=5):
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    original_dates = df[date_column].copy()
    
    random_seconds = np.random.randint(0, max_hours_offset * 3600, size=len(df))
    df[date_column] = df[date_column] + pd.Timedelta(days=days_to_add) + pd.to_timedelta(random_seconds, unit='s')
    
    return df, original_dates

def modify_serial_numbers(df, limit=LIMIT):
    serial_col = 'Serial number'
    if serial_col not in df.columns:
        print(f"Column '{serial_col}' not found for serial number modification.")
        return pd.DataFrame(), None
    
    mask = df[serial_col].astype(str).str.startswith('F') & df[serial_col].notna() & (df[serial_col].astype(str) != '')
    filtered_serial = df[mask].head(limit).copy()
    
    original_serial_numbers = filtered_serial[serial_col].copy()
    
    # Change first letter 'F' to 'D'
    filtered_serial.loc[:, serial_col] = filtered_serial[serial_col].astype(str).apply(lambda x: 'D' + x[1:] if x.startswith('F') else x)
    
    return filtered_serial, original_serial_numbers

def main():
    input_file = "Primary with Anomalies.xlsx"
    
    try:
        df = pd.read_excel(input_file)
        print(f"Loaded original data with {len(df)} rows.")
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    # Step 1: Filter and update N retired rows with discovery dates
    filtered_stale = filter_retired_and_recent_discovery(df, limit=LIMIT)
    if filtered_stale.empty:
        print("No rows matched retired + discovery date filter. Exiting.")
        return
    
    filtered_stale = filtered_stale.copy()
    filtered_stale['Operational status'] = 'Operational'
    filtered_stale, original_dates = update_discovery_dates(filtered_stale, 'Most recent discovery', days_to_add=10)
    
    # Create JSON mapping for discovery dates
    discovery_json_data = []
    for idx, (orig_date, new_date) in enumerate(zip(original_dates, filtered_stale['Most recent discovery'])):
        discovery_json_data.append({
            "row_index": idx,
            "original_Most recent discovery": orig_date.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(orig_date) else None,
            "new_Most recent discovery": new_date.strftime('%Y-%m-%d %H:%M:%S') if pd.notnull(new_date) else None
        })
    
    discovery_json_file = "Most_recent_discovery_mapping.json"
    with open(discovery_json_file, 'w') as f:
        json.dump(discovery_json_data, f, indent=4)
    print(f"Saved discovery date mapping JSON to '{discovery_json_file}'")
    
    # Step 2: Filter and modify 50 serial numbers starting with 'F'
    filtered_sndiff, original_serial_numbers = modify_serial_numbers(df, limit=LIMIT)
    if filtered_sndiff.empty:
        print("No serial numbers starting with 'F' found to modify.")
    else:
        # Create JSON mapping for serial numbers
        serial_json_data = []
        serial_col = 'Serial number'
        for idx in range(len(filtered_sndiff)):
            serial_json_data.append({
                "row_index": idx,
                "original_serial_number": original_serial_numbers.iloc[idx],
                "new_serial_number": filtered_sndiff.iloc[idx][serial_col]
            })
        
        serial_json_file = "SerialNumber_mapping.json"
        with open(serial_json_file, 'w') as f:
            json.dump(serial_json_data, f, indent=4)
        print(f"Saved serial number mapping JSON to '{serial_json_file}'")
    
    # Append both sets of rows to original DataFrame
    appended_df = pd.concat([df, filtered_stale], ignore_index=True)
    if not filtered_sndiff.empty:
        appended_df = pd.concat([appended_df, filtered_sndiff], ignore_index=True)
    
    print(f"Appended total rows: {len(appended_df) - len(df)} ({len(filtered_stale)} from discovery update + {len(filtered_sndiff)} from serial number update)")
    
    # Save final appended DataFrame to Excel
    output_file = "PrimaryWithAnomalies.xlsx"
    appended_df.to_excel(output_file, index=False)
    print(f"Saved appended data to '{output_file}'")

if __name__ == "__main__":
    main()
