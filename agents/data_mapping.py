import streamlit as st

def generate_data_map(master_df):
    """Creates a column mapping for AI to refine."""
    if master_df is None:
        st.error("⚠️ No master dataset found!")
        return None
    
    mapping = {col: "" for col in master_df.columns}
    st.write("🔍 Debug: Initial Mapping ->", mapping)
    return mapping
