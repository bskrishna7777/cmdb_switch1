import pandas as pd
from collections import Counter
import os
import re
import json
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core import Settings
import json
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
    df = pd.read_excel(csv_path)
    
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
        
        I will provide you with a list of vendor class identifiers that represent similar operating systems or vendors.
        Your task is to standardize these entries using the EXACT formats specified below.
        
        Use these STRICT standardization rules:
        Use these STRICT standardization rules:
        1. Always use Windows Server [Year] [Edition] (e.g., Win srv 2022 → Windows Server 2022 Standard). Applies to all variants like Microsoft Windows, MSFT Windows, Win, etc.
        2. Use Linux (without suffixes like "OS" or "Server").
        3. Use Unix for generic Unix-based systems (e.g., Solaris, AIX).
        4. Use Ubuntu followed by version if available
        
        Here's the list of related vendor IDs:
        {vendor_list}
        
        Return a JSON dictionary where keys are the original values and values are the standardized names.
        Be comprehensive and include ALL entries from the provided list.
        Make sure to include the version number for Windows entries (e.g., "Windows 10").
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
                mapping.update(group_mapping)
            else:
                # Fallback if no JSON found
                for vendor_id in group:
                    mapping[vendor_id] = vendor_id
                    
        except Exception as e:
            print(f"Error processing group: {e}")
            # Fallback
            for vendor_id in group:
                mapping[vendor_id] = vendor_id
    
    # Apply mapping to the dataframe
    df['Standardized Operating System'] = df['Operating System'].map(mapping).fillna(df['Operating System'])

    df = df.drop('Operating System', axis=1)
    df.rename(columns={'Standardized Operating System': 'Operating System'}, inplace=True)

    col_to_move = 'Operating System'
    # Reorder columns
    cols = [col_to_move] + [col for col in df.columns if col != col_to_move]
    df = df[cols]

    # Save outputs
    df.to_excel(output_path, index=False)
    with open('vendor_id_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
        
    return df, mapping

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
def main(input_path, output_path):
    
    df, mapping = standardize_with_llamaindex(input_path, output_path)
    missing = check_coverage(df, mapping)
    
    # # Display sample results
    # print("\nSample standardizations:")
    # sample = df[['Operating System', 'Standardized Operating System']].dropna().sample(min(10, len(df)))
    # print(sample)
    # output_path = output_path
    # Show specific examples
    print("\nSpecific examples:")
    examples = {
        "Microsoft Windows 10": mapping.get("Microsoft Windows 10", "Not found"),
        "MSFT Windows 10": mapping.get("MSFT Windows 10", "Not found"),
        "Win 10": mapping.get("Win 10", "Not found"),
        "Linux OS": mapping.get("Linux OS", "Not found"),
        "Android Device": mapping.get("Android Device", "Not found")
    }
    for orig, stand in examples.items():
        print(f"'{orig}' → '{stand}'")

    return output_path
