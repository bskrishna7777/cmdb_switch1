import pandas as pd
from collections import Counter
import os
import re
import json
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
import json
from cryptography.fernet import Fernet
import process
with open('secret.key', 'rb') as key_file:
            key = key_file.read()
 
cipher_suite = Fernet(key)
 
# Load the encrypted configuration data
with open('config.json', 'r') as config_file:
    encrypted_data = json.load(config_file)

# Decrypt the sensitive information
data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
os.environ["OPENAI_API_KEY"] = data["API_KEY"] #os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=data["API_KEY"])

def detect_asset_status_anomalies(df):

    df = df[['Name','IP Address','Serial number','Most recent discovery','Operational status']]
    df = df.iloc[9200:,:]
    """
    Uses LLM to detect anomalies in asset records based on operational status changes.
    
    An anomaly is defined as: For a given non-empty pair of name/ip address/serial number, 
    if the exact pair (all three shall match if non-empty) contains a non-null most recent discovery and changed operational status, 
    then flag as anomaly.
    
    Args:
        df: DataFrame with asset data
        
    Returns:
        - DataFrame with 'Anomaly' column added marking 'Stale asset anomaly' or 'No'
        - Average confidence score
    """
    
    # Create a copy of the dataframe
    result_df = df.copy()
    
    # Add 'Anomaly' column with default value 'No'
    result_df['Anomaly'] = 'No'
    result_df['Confidence'] = 0.0
    
    # System prompt for consistent LLM behavior
    system_prompt = """
    You are an IT asset management expert. Your task is to identify anomalies in asset records.
    
    ANOMALY DEFINITION:
    If records sharing the same identifier (Name, IP Address, or Serial number) have:
    1. Non-null "Most recent discovery" dates AND
    2. Different "Operational status" values AND
    3. Exactly matched serial numbers if non-empty
    Then all records in that group are anomalies.

    For each potential anomaly, provide a confidence score (0%-100%) indicating 
    your certainty about the detection.
    
    Be precise in your analysis and only mark anomalies that exactly match this definition.
    """
    
    # List of identifiers to check
    identifiers = ['Name', 'IP Address', 'Serial number']

    # Track confidence scores for calculating average
    confidence_scores = []
    
    # Process each identifier
    for identifier in identifiers:
        # Filter to records with non-empty values for this identifier
        valid_df = df[df[identifier].notna() & (df[identifier].astype(str) != '')]
        
        # Group by this identifier
        for value, group in valid_df.groupby(identifier):
            # Skip if only one record
            if len(group) <= 1:
                continue
            
            # Convert group to string for LLM processing
            group_text = group.to_string()
            
            # Create prompt for LLM
            user_prompt = f"""
            Analyze these asset records that share the same {identifier} value: '{value}'.
            
            {group_text}
            
            Return JSON with this format:
            {{
              "is_anomaly": true/false,
              "confidence": 0.0%-100.0%,
              "explanation": "brief explanation",
              "row_indices": [list of row indices in the original dataframe to mark as anomalies]
            }}
            
            Remember: This is an anomaly ONLY IF the records have non-null "Most recent discovery" dates 
            AND different "Operational status" values. Identified pair cannot have different serial numbers.
            """
            
            # Call the LLM API
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                # Parse the response
                result = json.loads(response.choices[0].message.content)
                
                # If anomaly detected, mark those records
                if result.get("is_anomaly", False):
                    confidence = result.get("confidence", 0.0)
                    
                    # Store confidence for average calculation (only count once per group)
                    confidence_scores.append(confidence)
                    
                    for idx in group.index:
                        result_df.at[idx, 'Anomaly'] = 'Stale asset anomaly'
                        result_df.at[idx, 'Confidence'] = confidence
                        
            except Exception as e:
                print(f"Error processing records with {identifier}='{value}': {str(e)}")

    # Calculate average confidence (only for records marked as anomalies)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    return result_df, avg_confidence

def main(input_path, anomaly_count):

    df = pd.read_excel(input_path)
    df1 = df.copy()
    
    # Detect anomalies
    result_df, avg_confidence = detect_asset_status_anomalies(df)
    
    # Save results
    filtered_df = result_df[result_df['Anomaly'] == 'Stale asset anomaly']
    filtered_df.to_excel("asset_anomalies.xlsx")
    df_without_index = process.show_data()
    # filtered_df.to_excel("asset_anomalies.xlsx")
    
    remain_df = df1.drop(filtered_df.index)
    remain_df.to_excel("De-anomalized Coll Data.xlsx", index=False)
    
    # Print summary
    anomaly_count = (result_df['Anomaly'] == 'Stale asset anomaly').sum()
    print(f"Detected {anomaly_count} anomalies out of {len(result_df)} records.")
    print(f"Average confidence score: {avg_confidence:.2f}%")

    
    
    return df_without_index, avg_confidence, anomaly_count, remain_df
    # return filtered_df, avg_confidence, anomaly_count, remain_df

# if __name__ == "__main__":
#  main("Semifinal CMDB.xlsx", "N")
