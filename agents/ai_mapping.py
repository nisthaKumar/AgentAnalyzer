import openai
import json
import streamlit as st

def ai_map_columns(master_df, template_columns):
    """Uses AI to intelligently map CSV data to the Excel template in JSON format."""
    
    prompt = (
        f"Given these CSV columns: {list(master_df.columns)}, map them to these template columns: {template_columns}. "
        "Return the mapping as a **valid JSON object** with the format: "
        '{ "mappings": { "CSV_column_name": "Template_column_name", ... } }. '
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        mapping = json.loads(response["choices"][0]["message"]["content"].strip())
        st.write("✅ AI Column Mapping:", mapping)
        return mapping["mappings"]
    except json.JSONDecodeError:
        st.error("⚠️ Error: AI response is not valid JSON.")
        return None
