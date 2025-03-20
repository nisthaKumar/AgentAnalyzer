import pandas as pd
import streamlit as st

def extract_template_context(template_file):
    """Reads the Excel template and extracts required fields."""
    try:
        df = pd.read_excel(template_file, engine="openpyxl")
        template_columns = list(df.columns)
        return template_columns
    except Exception as e:
        st.error(f"⚠️ Error reading template: {e}")
        return None
