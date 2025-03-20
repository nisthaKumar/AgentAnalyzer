import openpyxl
from io import BytesIO
import streamlit as st
import openai
import os
from dotenv import load_dotenv
import json
import pandas as pd

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_ai_transformed_data(master_df, template_headers):
    """Uses OpenAI to generate a transformed dataset matching the template."""
    
    # Convert DataFrame to JSON format to send structured data to AI
    sample_data = master_df.to_dict(orient="records")  # Send first 10 rows
    
    prompt = (
        f"Given this dataset (JSON format):\n{json.dumps(sample_data, indent=2)}\n\n"
        f"Transform it to match the following template columns: {template_headers}.\n"
        "- Perform necessary calculations and transformations.\n"
        "- Return only a JSON array where each object represents a row in the final dataset."
        "- Ensure correct mappings, format conversions, and required calculations."
        "- Do NOT return any extra text, only a valid JSON list of dictionaries."
    )

    st.write("✅ Requesting AI to Transform Data:")
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are an AI that transforms raw CSV data into structured Excel format."},
                  {"role": "user", "content": prompt}],
        api_key=OPENAI_API_KEY
    )

    try:
        content = response["choices"][0]["message"]["content"]
        
        # Extract JSON from AI response
        json_start = content.find("[")
        json_end = content.rfind("]") + 1
        json_str = content[json_start:json_end]  # Extract JSON part

        # Parse JSON to dictionary list
        transformed_data = json.loads(json_str)
        st.write("✅ AI Transformed Data Preview:", transformed_data[:2])  # Show first 5 rows
        return transformed_data
    
    except Exception as e:
        st.error(f"⚠️ Error parsing AI-transformed data: {e}")
        return []

def populate_template(master_df, template_file):
    """Creates a new Excel file with AI-transformed data matching the template structure."""
    
    try:
        # Load the template
        template_wb = openpyxl.load_workbook(template_file)
        template_sheet = template_wb.active  
        template_headers = [cell.value for cell in template_sheet[1] if cell.value]  # Extract column names

        # Get AI-transformed data
        transformed_data = get_ai_transformed_data(master_df, template_headers)
        st.write("✅ Extracted AI-Transformed Data:", transformed_data[:50])
        if not transformed_data:
            st.error("⚠️ AI failed to generate transformed data.")
            return None

        # Create a new workbook
        new_wb = openpyxl.Workbook()
        new_sheet = new_wb.active
        new_sheet.title = "Sheet1"

        # Write headers
        new_sheet.append(template_headers)

        # Write transformed data
        for row in transformed_data:
            new_row = [row.get(col, "") for col in template_headers]  # Ensure all template columns exist
            new_sheet.append(new_row)

        # Save to BytesIO
        output = BytesIO()
        new_wb.save(output)
        output.seek(0)

        st.write("✅ New Excel File Created with AI-transformed data!")
        return output

    except Exception as e:
        st.error(f"⚠️ Error creating new Excel file: {e}")
        return None
