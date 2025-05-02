# import pandas as pd
# import numpy as np
# import networkx as nx
# import difflib
# from Levenshtein import ratio as levenshtein_ratio  # returns similarity in [0,1]

# def main(input_path, output_path):
    
#     df = pd.read_excel(input_path)
#     df = df = df[:200]
#     # df=df.iloc[6051:6150,:]
#     df = df.reset_index()
#     # Step 1: Build similarity graph
#     threshold = 0.85  # or 0.9 for stricter matching
#     G = nx.Graph()
#     for i in range(len(df)):
#         G.add_node(i)
#         for j in range(i+1, len(df)):
#             sim = difflib.SequenceMatcher(None, df.loc[i, 'Name'], df.loc[j, 'Name']).ratio()
#             if sim >= threshold:
#                 G.add_edge(i, j)
    
#     # Step 2: Extract clusters (connected components)
#     clusters = list(nx.connected_components(G))
    
#     # Step 3: Assign alias labels a1, a2, ... for clusters with more than 1 record
#     alias_labels = {}
#     alias_counter = 1
#     for cluster in clusters:
#         if len(cluster) > 1:
#             label = f'a{alias_counter}'
#             for idx in cluster:
#                 alias_labels[idx] = label
#             alias_counter += 1
#         else:
#             for idx in cluster:
#                 alias_labels[idx] = ''
    
#     # Step 4: Add 'Alias' column to original df
#     df['Alias'] = df.index.map(alias_labels)
    
#     # Step 5: Build cleaned DataFrame
#     #cleaned_df = df.loc[representatives].reset_index(drop=True)
#     df.to_excel(output_path, index=False)

#     return output_path


# input_path = 'Semifinal CMDB.xlsx'
# output_path = 'Server_DHCP_Raw_fuzzy.xlsx'
# refinedm_path = main(input_path, output_path)



# def assign_priorities(df, group_col, date_col, priority_col='Priority'):
#     df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
#     df[priority_col] = ''

#     for name, group in df[df[date_col].notnull()].groupby(group_col):
#         unique_dates = group[date_col].drop_duplicates().sort_values(ascending=False).reset_index(drop=True)
#         if len(unique_dates) > 1:
#             date_to_priority = {date: f'P{i+1}' for i, date in enumerate(unique_dates)}
#             mask = df[group_col] == name
#             df.loc[mask & df[date_col].notnull(), priority_col] = df.loc[mask & df[date_col].notnull(), date_col].map(date_to_priority)

#     return df


# df = pd.read_excel('Server_DHCP_Raw_fuzzy.xlsx')

# df_pr = assign_priorities(df, 'Alias', 'Most recent discovery')

# df_pr.to_excel('Server_DHCP_Raw_fuzzy_pr.xlsx')


# # Separate rows with blank Alias values
# unique_blank_df = df_pr[df_pr['Alias'] == '']  # Blank aliases
# marked_alias_df = df_pr[df_pr['Alias'] != '']
# unique_blank_df.to_excel('unique_df.xlsx')
# marked_alias_df.to_excel('alias_df.xlsx')



import pandas as pd
import numpy as np
import networkx as nx
import difflib
from Levenshtein import ratio as levenshtein_ratio  # returns similarity in [0,1]


def main(input_path, output_path):
    df = pd.read_excel(input_path)
    df = df.iloc[6051:6150, :]
    df = df.reset_index()

    # Step 1: Build similarity graph
    threshold = 0.85
    G = nx.Graph()
    for i in range(len(df)):
        G.add_node(i)
        for j in range(i + 1, len(df)):
            sim = difflib.SequenceMatcher(None, df.loc[i, 'Name'], df.loc[j, 'Name']).ratio()
            if sim >= threshold:
                G.add_edge(i, j, weight=sim)  # Store similarity as edge weight

    # Step 2: Extract clusters (connected components)
    clusters = list(nx.connected_components(G))

    # Step 3: Assign alias labels and calculate confidence scores
    alias_labels = {}
    alias_counter = 1
    confidence_scores = {}  # Dictionary to store confidence scores
    for cluster in clusters:
        if len(cluster) > 1:
            label = f'a{alias_counter}'
            # Calculate the average similarity within the cluster
            similarities = []
            for i in cluster:
                for j in cluster:
                    if i != j:
                        # Get similarity from edge weight.  Default to 0 if edge doesn't exist.
                        similarity = G.get_edge_data(i, j, default={'weight': 0})['weight']
                        similarities.append(similarity)
            average_similarity = np.mean(similarities) if similarities else 0

            for idx in cluster:
                alias_labels[idx] = label
                confidence_scores[idx] = average_similarity  # Store the score
            alias_counter += 1
        else:
            for idx in cluster:
                alias_labels[idx] = ''
                confidence_scores[idx] = 0  # одиночные элементы имеют уверенность 0

    # Step 4: Add 'Alias' and 'Confidence Score' columns
    df['Alias'] = df.index.map(alias_labels)
    df['Confidence Score'] = df.index.map(confidence_scores) # Add the confidence scores

    df.to_excel(output_path, index=False)
    return output_path


def assign_priorities(df, group_col, date_col, priority_col='Priority'):
    # Remove unnamed columns
    unnamed_cols = [col for col in df.columns if col.startswith('Unnamed')]
    df_processed = df.drop(columns=unnamed_cols, errors='ignore').copy()

    # Parse date
    df_processed[date_col] = pd.to_datetime(df_processed[date_col], errors='coerce')
    df_processed[priority_col] = ''

    # Assign priority labels
    for name, group in df_processed[df_processed[date_col].notnull()].groupby(group_col):
        unique_dates = group[date_col].drop_duplicates().sort_values(ascending=False).reset_index(drop=True)
        if len(unique_dates) > 1:
            date_to_priority = {date: f'P{i + 1}' for i, date in enumerate(unique_dates)}
            mask = df_processed[group_col] == name
            df_processed.loc[mask & df_processed[date_col].notnull(), priority_col] = df_processed.loc[
                mask & df_processed[date_col].notnull(), date_col].map(date_to_priority)

    # Fill NaN values in Alias and Priority for consistent checking
    df_processed[group_col] = df_processed[group_col].fillna('')
    df_processed[priority_col] = df_processed[priority_col].fillna('')

    # Split rows based on whether Alias or Priority has a value
    cleaned_df = df_processed[~((df_processed[group_col].str.strip() == '') & (df_processed[priority_col].str.strip() == ''))].copy()
    blank_df = df_processed[((df_processed[group_col].str.strip() == '') & (df_processed[priority_col].str.strip() == ''))].copy()

    # Save the blank DataFrame
    blank_df.to_excel('Blank_Alias_Priority.xlsx', index=False)

    # Add the tick box column to the cleaned DataFrame (for the cleaned output)
    cleaned_df['Select'] = False  # Initialize with False (unchecked)

    # Create and save the cleaned DataFrame with the index column
    cleaned_df_with_index = cleaned_df.copy()
    cols_with_index = ['Select', group_col, priority_col, 'index'] + [
        col for col in cleaned_df_with_index.columns if col not in ['Select', group_col, priority_col, 'index']]
    cleaned_df_with_index = cleaned_df_with_index[cols_with_index]
    cleaned_df_with_index.to_excel('Advanced Flagging_with_index.xlsx', index=False)

    # Create and save the cleaned DataFrame without the index column
    cleaned_df_without_index = cleaned_df.drop(columns=['index'], errors='ignore').copy()
    cols_without_index = ['Select', group_col, priority_col] + [
        col for col in cleaned_df_without_index.columns if col not in ['Select', group_col, priority_col]]
    cleaned_df_without_index = cleaned_df_without_index[cols_without_index]
    cleaned_df_without_index = cleaned_df_without_index.drop(columns=['Priority'])
    # Get the "Confidence Score" column
    confidence_score = cleaned_df_without_index.pop('Confidence Score')

    # Multiply the "Confidence Score" by 100
    confidence_score = confidence_score * 100

    # Insert the "Confidence Score" column at the 3rd position (index 2)
    cleaned_df_without_index.insert(2, 'Confidence Score', confidence_score)
    cleaned_df_without_index.to_excel('Cleaned_Advanced_Flagging.xlsx', index=False)


    return cleaned_df_without_index , len(cleaned_df_without_index)


def run_processing():  # Run processing
    input_path = 'De-anomalized Coll Data.xlsx'
    output_path = 'Alias Flagging.xlsx'
    refined_path = main(input_path, output_path)

    df = pd.read_excel(refined_path)
    df_processed = assign_priorities(df, 'Alias', 'Lease start date')

    print("Processing complete. 'Advanced Flagging_with_index.xlsx', 'Cleaned_Advanced_Flagging.xlsx', and 'Blank_Alias_Priority.xlsx' have been created.")
    print("The function 'assign_priorities' returned a DataFrame without the index and with the 'Select' column.")



