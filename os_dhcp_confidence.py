import pandas as pd
from collections import Counter
import os
import re
import json
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
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

def standardize_with_llamaindex(csv_path, output_path):
    # Load the data
    df = pd.read_csv(csv_path)
    
    # Extract unique vendor IDs
    vendor_ids = df['Operating System'].dropna().tolist()
    vendor_counter = Counter(vendor_ids)
    unique_vendor_ids = list(vendor_counter.keys())
    
    # Group similar vendors
    vendor_groups = group_by_patterns(unique_vendor_ids)
    
    # Set up LlamaIndex
    llm = OpenAI(model="gpt-4o-mini")
    Settings.llm = llm
    
    # Define the standardization prompt with EXACT format specifications
    standardize_prompt = PromptTemplate(
        """You are an expert in standardizing OS and vendor names from DHCP logs.
        
        I will provide you with a list of Operating Systementifiers that represent similar operating systems or vendors.
        Your task is to standardize these entries using the EXACT formats specified below.
        
        Use these STRICT standardization rules:
        
        The output should:
        - Clearly identify the operating system or vendor type. Do not include "Microsoft"
        - Use a uniform naming convention across similar identifiers.
        - Include version numbers when relevant.
        - Provide a confidence score between 0 and 1 for each mapping that reflects how certain you are about the mapping.
        
        Here's the list of related vendor IDs:
        {vendor_list}
        
        Return a JSON dictionary where each key is the original vendor ID and the value is a dictionary like this:
        {{
          "standardized": "<standardized_name>",
          "confidence": <confidence_score>
        }}
        
        Include ALL entries from the provided list.
        """
    )
    
    # Process each group
    mapping = {}
    
    for group in vendor_groups:
        if not group:
            continue
            
        vendor_list_str = "\n".join(group)
        
        # Format and execute the prompt
        formatted_prompt = standardize_prompt.format(vendor_list=vendor_list_str)
        response = llm.complete(formatted_prompt)
        
        # Parse the JSON response
        try:
            # Find JSON in the response
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                json_str = match.group(0)
                group_mapping = json.loads(json_str)
                for original, info in group_mapping.items():
                    if isinstance(info, dict) and "standardized" in info and "confidence" in info:
                        mapping[original] = {
                            "standardized": info["standardized"],
                            "confidence": float(info["confidence"])
                        }
                    else:
                        mapping[original] = {
                            "standardized": original,
                            "confidence": 0.0
                        }
            else:
                # Fallback if no JSON found
                for vendor_id in group:
                    mapping[vendor_id] = {
                        "standardized": vendor_id,
                        "confidence": 0.0
                    }
                    
        except Exception as e:
            print(f"Error processing group: {e}")
            # Fallback
            for vendor_id in group:
                mapping[vendor_id] = {
                    "standardized": vendor_id,
                    "confidence": 0.0
                }
    
    # Apply mapping to the dataframe
    df['Standardized Operating System'] = df['Operating System'].map(lambda x: mapping.get(x, {}).get("standardized", x))
    df['Confidence Score'] = df.apply(lambda row: mapping.get(row['Operating System'], {}).get("confidence", "") if row['Standardized Operating System'] else "", axis=1)
    average_confidence = df['Confidence Score'].apply(pd.to_numeric, errors='coerce').mean()

# Print the average confidence score
    print(f"The standardization process was successfully completed using NLP, with a confidence score of {average_confidence:.2f}.")

    # Save outputs
    df.to_csv(output_path, index=False)
    with open('vendor_id_mappingwithaverageconfidence.json', 'w') as f:
        json.dump(mapping, f, indent=2)
        
    return df, mapping, average_confidence

def group_by_patterns(vendor_ids):
    """Group vendor IDs by OS type patterns"""
    groups = {
        'windows': [],
        'linux': [],
        'apple': [],
        'android': [],
        'unix': [],
        'dhcp': [],
        'other': []
    }
    
    patterns = {
        'windows': r'(?i)(win|windows|microsoft|ms|msft)',
        'linux': r'(?i)(linux|gnu|ubuntu|debian|fedora)',
        'apple': r'(?i)(mac|apple|ios)',
        'android': r'(?i)(android)',
        'unix': r'(?i)(unix|solaris|bsd)',
        'dhcp': r'(?i)(dhcp|udhcp)',
    }
    
    for vendor_id in vendor_ids:
        if pd.isna(vendor_id) or vendor_id == '':
            continue
            
        matched = False
        for category, pattern in patterns.items():
            if re.search(pattern, vendor_id):
                groups[category].append(vendor_id)
                matched = True
                break
        
        if not matched:
            groups['other'].append(vendor_id)
    
    # Return non-empty groups
    return [group for group in groups.values() if group]

# Function to verify all entries are processed
def check_coverage(original_df, mapping):
    missing = []
    for vendor_id in original_df['Operating System'].dropna().unique():
        if vendor_id and vendor_id not in mapping:
            missing.append(vendor_id)
    
    coverage = 100 - (len(missing) / len(original_df['Operating System'].dropna().unique()) * 100)
    print(f"Mapping coverage: {coverage:.2f}%")
    
    if missing:
        print(f"Missing mappings for {len(missing)} vendor IDs")
    
    return missing

# Example usage
#def main():
df, mapping, average_confidence = standardize_with_llamaindex("Server_DHCP_Raw.csv", "dhcp_discovery_data_Standardized_averageconfidence.csv")
missing = check_coverage(df, mapping)

# Display sample results
print("\nSample standardizations:")
sample = df[['Operating System', 'Standardized Operating System', 'Confidence Score']].dropna().sample(min(10, len(df)))
print(sample)
    #return sample
