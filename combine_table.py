import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Function to read multiple CSV files
def load_csv_files(uploaded_files):
    dfs = {}
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs[file.name] = df
            st.write(f"Loaded {file.name} with shape {df.shape}")
        except Exception as e:
            st.error(f"Error loading {file.name}: {e}")
    return dfs

# Function to detect the best key column
def detect_key_column(dfs):
    possible_keys = set(dfs[list(dfs.keys())[0]].columns)
    for df in dfs.values():
        possible_keys.intersection_update(df.columns)
    return possible_keys.pop() if possible_keys else None

# Function to aggregate all non-key columns into comma-separated values
def aggregate_data(dfs, key_column):
    aggregated_dfs = {}
    aggregation_plan = {}
    
    for name, df in dfs.items():
        if key_column not in df.columns:
            st.warning(f"Skipping {name}, as it does not contain the key column '{key_column}'.")
            continue

        non_key_columns = [col for col in df.columns if col != key_column]
        aggregation_dict = {col: lambda x: ', '.join(x.dropna().astype(str).unique()) for col in non_key_columns}
        
        aggregation_plan[name] = aggregation_dict
        aggregated_df = df.groupby(key_column, as_index=False).agg(aggregation_dict)
        aggregated_dfs[name] = aggregated_df
    
    return aggregated_dfs, aggregation_plan

# Function to merge all aggregated datasets
def merge_datasets(aggregated_dfs, key_column):
    merged_df = None
    for name, df in aggregated_dfs.items():
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.merge(df, on=key_column, how='left')
        st.write(f"Merged {name} - New Shape: {merged_df.shape}")
    return merged_df

# Streamlit App
st.title("CSV Data Aggregator")

uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type=["csv"])

if uploaded_files:
    dfs = load_csv_files(uploaded_files)
    key_column = detect_key_column(dfs)
    if not key_column:
        st.error("No common key column found across files.")
    else:
        st.success(f"Detected key column: {key_column}")
        
        aggregated_dfs, aggregation_plan = aggregate_data(dfs, key_column)
        
        st.subheader("Aggregation Plan")
        st.json(aggregation_plan)
        
        st.subheader("Aggregated Data Previews")
        for name, df in aggregated_dfs.items():
            st.write(f"### {name}")
            st.dataframe(df.head())
        
        st.subheader("Merging Aggregated Data")
        merged_df = merge_datasets(aggregated_dfs, key_column)
        st.dataframe(merged_df.head())
        
        # Allow downloading the merged file
        csv = merged_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Merged CSV",
            data=csv,
            file_name="merged_data.csv",
            mime="text/csv"
        )