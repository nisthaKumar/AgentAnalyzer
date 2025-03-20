import pandas as pd
import streamlit as st

def extract_csv_context(uploaded_files):
    """Reads multiple uploaded CSV files into Pandas DataFrames."""
    csv_data = {}

    for file in uploaded_files:
        try:
            df = pd.read_csv(file, encoding="utf-8", on_bad_lines="skip")
            csv_data[file.name] = df
            st.write(f"✅ Loaded {file.name}: {df.shape}")
        except Exception as e:
            st.error(f"⚠️ Error loading {file.name}: {e}")

    if not csv_data:
        st.error("⚠️ No valid CSV files were loaded.")
        return None

    return csv_data
