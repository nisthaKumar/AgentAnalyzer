import streamlit as st
import pandas as pd
# Function to aggregate all non-key columns into comma-separated values
def aggregate_data(dfs, key_column):
    aggregated_dfs = {}
    aggregation_plan = {}
    
    for name, df in dfs.items():
        if key_column not in df.columns:
            st.warning(f"Skipping {name}, as it does not contain the key column '{key_column}'.")
            continue

        non_key_columns = [col for col in df.columns if col != key_column]
        aggregation_dict = {col: lambda x: ', '.join(x.dropna().astype(str).tolist()) for col in non_key_columns}
        
        aggregation_plan[name] = aggregation_dict
        aggregated_df = df.groupby(key_column, as_index=False).agg(aggregation_dict)
        aggregated_dfs[name] = aggregated_df
    
    return aggregated_dfs, aggregation_plan


# Function to merge all aggregated datasets
def merge_csv_data(aggregated_dfs, key_column):
    merged_df = None
    for name, df in aggregated_dfs.items():
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.merge(df, on=key_column, how='left')
        # st.write(f"Merged {name} - New Shape: {merged_df.shape}")
    return merged_df


