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

def map_columns_with_confidence(list1: List[str], list2: List[str]) -> Dict:
    """
    Maps columns from list2 to list1 using OpenAI API with confidence scoring
    Returns mapping dictionary and average confidence score
    """
    
    # Construct the prompt for column mapping
    prompt = f"""Analyze these two lists of column names and find the best match for each item in List2 from List1.
For each List2 column:
1. Identify the most semantically similar column in List1
2. Assign a confidence score (0-100) indicating match certainty
3. Ensure one-to-one mapping (no duplicate List1 matches)

List1 ({len(list1)} items): {', '.join(list1)} [...] 
List2 ({len(list2)} items): {', '.join(list2)}

Return JSON format:
{{
  "mappings": [
    {{
      "list2_column": "column_name",
      "list1_match": "best_match",
      "confidence": 0.0%-100.0%
    }}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data mapping expert. Match columns based on semantic similarity."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.3,
            max_tokens=2000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Process mappings and ensure one-to-one
        final_mapping = {}
        used_list1 = set()
        sorted_mappings = sorted(result['mappings'], key=lambda x: x['confidence'], reverse=True)
        
        for mapping in sorted_mappings:
            list2_col = mapping['list2_column']
            list1_match = mapping['list1_match']
            
            if list1_match in list1 and list1_match not in used_list1:
                final_mapping[list2_col] = {
                    'list1_match': list1_match,
                    'confidence': mapping['confidence']
                }
                used_list1.add(list1_match)
        
        # Calculate average confidence
        confidences = [v['confidence'] for v in final_mapping.values() if v['confidence'] > 60]
        avg_confidence = sum(confidences)/len(confidences) if confidences else 0
        
        return {
            'mappings': final_mapping,
            'average_confidence': round(avg_confidence, 2)
        }
        
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
    df2 = pd.read_csv("Server_DHCP_Raw.csv")
    
    #***********************************************
    
    list1 = list(df1.columns)  # 141 items
    list2 = list(df2.columns)    
    result = map_columns_with_confidence(list1, list2)
    
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
    df_filtered_list2.to_excel("Server-DHCP-NormMetada.xlsx", index=False)
    output_path = "Server-DHCP-NormMetada.xlsx"
    
    #***********************************************
    list2_cols = []
    list1_matches = []
    confidences = []

    for list2_col, details in result['mappings'].items():
        list2_cols.append(list2_col)
        list1_matches.append(details['list1_match'])
        confidences.append(float(details['confidence']))

    col_mapping_df = pd.DataFrame({
        'Raw': list2_cols,
        'AI-Mapped': list1_matches,
        'Confidence Score': confidences
    })

    col_mapping_df.reset_index(drop=True, inplace=True)

    return output_path, result['average_confidence'], col_mapping_df

# if __name__ == "main":
#     main()