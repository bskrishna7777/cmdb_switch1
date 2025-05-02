import pandas as pd
import openai
from openai import OpenAI
import json
import os
from typing import List, Dict

from cryptography.fernet import Fernet

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

def map_os_values(df1, df2):
    """
    Maps OS values from df2 to df1's unique values
    Returns:
        - df2_with_mapping: DataFrame with mapped OS values
        - avg_confidence: Average confidence score of mappings
    """
    
    # Construct the prompt for column mapping
    prompt = f"""Analyze these two lists of OS names and find the best match for each item in List2 from List1.
For each List2 value:
1. Identify the most semantically similar value in List1
2. Assign a confidence score (0-100) indicating match certainty
3. One-to-many mapping (list1 can be mapped to many list2 but not viceversa)

List1 ({len(list1)} items): {', '.join(list1)} [...] 
List2 ({len(list2)} items): {', '.join(list2)}

Return JSON format:
{{
  "mappings": [
    {{
      "list2_value": "original_name",
      "list1_match": "best_match",
      "confidence": 0-100
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data mapping expert. Match values based on semantic similarity."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2,
            max_tokens=2000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Process mappings and ensure one-to-one
        os_mapping = {}
        confidences = []
        
        for mapping in result['mappings']:
            original = mapping['list2_value']
            match = mapping['list1_match']
            confidence = mapping['confidence']
            
            if match in list1:
                os_mapping[original] = match
                confidences.append(confidence)
        
        # Apply mapping to df2
        df2_mapped = df2.copy()
        df2_mapped['OS_mapped'] = df2_mapped['Operating system'].map(os_mapping)
        
        # Calculate average confidence
        confidences = [v['confidence'] for v in final_mapping.values() if v['confidence'] > confidence_threshold]
        avg_confidence = sum(confidences)/len(confidences) if confidences else 0
        
        return df2_mapped, round(avg_confidence, 2)
        
    except json.JSONDecodeError:
        print("Error parsing JSON response")
        return {}
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {}

def main():

    confidence_threshold = 60
    df1 = pd.read_excel("Primary CMDB.xlsx")
    
    #***********************************************
    #=========== Second File (csv or xlsx) =========
    df2 = pd.read_excel("Server-MCM-Norm2.xlsx")
    
    #***********************************************

    df1os = df1['Operating system']
    df2os = df2['Operating system']
    mapped_df, avg_conf = map_os_values(df1os, df2os)
    
    # Step 1: Build mapping for columns with confidence > confidence_threshold
    col_rename_map = {
        list2_col: details['list1_match']
        for list2_col, details in result['mappings'].items()
        if details['confidence'] > confidence_threshold
    }
    
    # Step 2: Filter and rename columns
    df_filtered_list2 = df2[list(col_rename_map.keys())].rename(columns=col_rename_map)
    
    #***********************************************
    #=========== Output File (csv or xlsx) =========
    df_filtered_list2.to_excel("Server-MCM-Norm2.xlsx")
    output_path = "Server-MCM-Norm2.xlsx"
    
    #***********************************************

    #print("Column Mappings:")
    #for list2_col, details in result['mappings'].items():
    #    print(f"{list2_col} → {details['list1_match']} (Confidence: {details['confidence']}%)")
    
    return output_path, result['average_confidence']