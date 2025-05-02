import pandas as pd
import matplotlib.pyplot as plt
 
def create_pie_chart(df):
    # Define mapping function
    def map_class(value):
        # Treat NaN or blank ('') as 'server'
        if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
            return 'server'
        value = value.lower()
        if 'server' in value or value == 'ibm frame':
            return 'server'
        elif 'router' in value:
            return 'router'
        elif 'switch' in value:
            return 'switch'
        else:
            return 'other network hardware'
 
    # Map classes
    df['category'] = df['Class'].apply(map_class)
    # print()
    # Count occurrences
    counts = df['category'].value_counts()
    # print(counts)
    # Plot pie chart with rectangular shape
    plt.figure(figsize=(8, 4))  # Rectangular shape
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
 
    # Save as image (PNG) with tight bounding box
    plt.savefig('network_hardware_distribution.png', bbox_inches='tight')
 
    plt.close()
 
    # Get server count (returns 0 if not present)
    server_count = counts.get('server', 0)
    switch_count = counts.get('switch', 0)
    return "network_hardware_distribution.png", server_count, switch_count