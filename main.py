import streamlit as st
import os
import openai
from dotenv import load_dotenv
from agents import (
    extract_csv, merge_strategy, merge_csv, 
    template_context, populate_template
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🕵️‍♀️ AgentAnalyzer")

uploaded_csvs = st.file_uploader("Upload CSV Files", type=["csv"], accept_multiple_files=True)
uploaded_template = st.file_uploader("Upload Excel Template", type=["xlsx"])

if st.button("Process Files"):
    #extract and display csv data
    csv_data = extract_csv.extract_csv_context(uploaded_csvs)
    st.write("✅ Extracted CSV Data")
    
    #determine merge strategy
    merge_strategy = merge_strategy.determine_merge_strategy(csv_data)
    st.write("✅ AI Merge Strategy ->", merge_strategy["strategy"])
    
    #merge csv data
    aggregated_dfs, aggregation_plan = merge_csv.aggregate_data(csv_data, merge_strategy['key_column'])
    master_data = merge_csv.merge_csv_data(aggregated_dfs,merge_strategy['key_column'])
    # master_data = merge_csv.merge_csv_data(csv_data, merge_strategy['key_column'], merge_strategy['strategy'])
    st.write("✅ CSVs Merged Successfully using key column:", master_data)
    
    #extract template columns
    template_fields = template_context.extract_template_context(uploaded_template)
    st.write("✅ Extracted Template Columns:", template_fields)
    
    # mapping = ai_mapping.ai_map_columns(master_data, template_fields)
    # st.write("🔍 Debug: AI Mapping ->", mapping)
    # final_file = populate_template.populate_template(master_data, mapping, uploaded_template)

    #generate data mapping and then populate the template
    final_file = populate_template.populate_template(master_data, uploaded_template)
    if final_file:
        st.download_button("📥 Download Processed Excel", data=final_file, file_name="populated_template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
