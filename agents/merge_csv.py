# import pandas as pd
# import streamlit as st
# import openai

# def merge_csv_data(csv_data, key_column, merge_strategy):
#     """Merges multiple CSVs using the determined strategy."""
#     try:
#         if merge_strategy == "Merge on key column":
#             master_df = merge_using_ai(csv_data, key_column)
#         else:
#             master_df = pd.concat(csv_data.values(), ignore_index=True)
        
#         st.write("✅ CSVs Merged Successfully using key column:", key_column)
#         return master_df
    
#     except Exception as e:
#         st.error(f"⚠️ Error merging CSV files: {e}")
#         return None

# def merge_using_ai(csv_data, key_column):
#     """Uses OpenAI API to intelligently merge CSVs on the given key column and group by it."""

#     # Generate the AI prompt to guide the merge logic
#     prompt = f"Merge the following CSV datasets using '{key_column}' as the key column. Handle missing values intelligently and resolve conflicts where possible. Ensure no duplicate entries. Group the data based on the {key_column}. Store the merged data in pandas dataframe: master_df"

#     # Send the prompt to OpenAI's API
#     response = openai.ChatCompletion.create(
#         model="gpt-4o",
#         messages=[{"role": "system", "content": "You are an expert data analyst."},
#                   {"role": "user", "content": prompt}]
#     )
#     # Get the merge instructions from the AI response
#     merge_instructions = response["choices"][0]["message"]["content"].strip()
#     st.write("🤖 AI Merge Instructions:", merge_instructions)

#     # Merge the CSV datasets using the key column
#     master_df = None
#     for csv_name, df in csv_data.items():
#         if master_df is None:
#             master_df = df
#         else:
#             master_df = pd.merge(master_df, df, on=key_column, how='outer')  # Outer join to retain all rows

#     # Handle missing values intelligently
#     master_df = master_df.fillna('Missing')  # Example, can be customized based on AI's suggestion

#     # Group the data based on the key_column
#     # grouped_df = master_df.groupby(key_column).agg('first').reset_index()  # Example aggregation: take the first value of each group
#     #grouped_df = master_df.groupby(key_column).agg(lambda x: ', '.join(x.astype(str))).reset_index()
#     grouped_df = master_df.groupby(key_column).agg(lambda x: ', '.join(x.astype(str).unique()) if x.nunique() > 1 else x.iloc[0]).reset_index()

#     # Display the grouped and merged dataframe
#     st.write(grouped_df)

#     return grouped_df
####################################################################################################################################

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
        st.write(f"Merged {name} - New Shape: {merged_df.shape}")
    return merged_df


