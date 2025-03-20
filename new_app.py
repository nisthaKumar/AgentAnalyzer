import os
import pandas as pd
import streamlit as st
import openai
import json
from io import BytesIO
import openpyxl
from dotenv import load_dotenv
import requests

# Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("⚠️ OpenAI API Key is missing! Set it in environment variables.")
    st.stop()

openai.api_key = OPENAI_API_KEY  # Set API key

### --------------- AGENT 1: Extract Context from CSV Files --------------- ###
def extract_csv_context(uploaded_files):
    """Reads multiple uploaded CSV files into Pandas DataFrames with debugging."""
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


### --------------- AGENT 2: Determine Merge Strategy --------------- ###
# def determine_merge_strategy(csv_data):
#     """Uses AI to decide the best merging strategy based on CSV context."""
#     prompt = f"Given the column names from multiple CSVs: {list(csv_data.keys())}, suggest a merging strategy."
#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "user", "content": prompt}]
#     )
    
#     strategy = response["choices"][0]["message"]["content"]
#     st.write("🔍 Debug: AI Merge Strategy ->", strategy)
#     return strategy
def determine_merge_strategy(csv_data):
    """Uses AI to decide the best merging strategy based on CSV context and ensures proper formatting."""
    
    # Extract column names from CSV data
    csv_columns = {name: list(df.columns) for name, df in csv_data.items()}
    
    prompt = (
        "Given the following CSV column structures:\n"
        f"{json.dumps(csv_columns, indent=2)}\n\n"
        "Suggest a merging strategy. Respond in JSON format as either:\n"
        "1. {\"strategy\": \"Merge on common columns\"}\n"
        "2. {\"strategy\": \"Merge on key column\", \"key_column\": \"column_name\"}\n"
        "Ensure the key_column is present in all files if suggested."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract and parse the response
        strategy_text = response["choices"][0]["message"]["content"]
        merge_strategy = json.loads(strategy_text)

        # Validate strategy format
        if not isinstance(merge_strategy, dict) or "strategy" not in merge_strategy:
            raise ValueError("Invalid strategy format received.")

        st.write("🔍 Debug: AI Merge Strategy ->", merge_strategy)
        return merge_strategy

    except json.JSONDecodeError:
        st.error("⚠️ Failed to parse AI response. Using fallback strategy.")
        return {"strategy": "Merge on common columns"}

    except Exception as e:
        st.error(f"⚠️ Error determining merge strategy: {e}")
        return {"strategy": "Merge on common columns"}  # Default fallback



# --------------- AGENT 3: Merge CSV Data --------------- ###

def merge_using_ai(csv_data, key_column):
    """Uses OpenAI API to intelligently merge CSVs on the given key column and group by it."""

    # Generate the AI prompt to guide the merge logic
    prompt = f"Merge the following CSV datasets using '{key_column}' as the key column. Handle missing values intelligently and resolve conflicts where possible. Ensure no duplicate entries. Group the data based on the {key_column}."

    # Send the prompt to OpenAI's API
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are an expert data analyst."},
                  {"role": "user", "content": prompt}]
    )

    # Get the merge instructions from the AI response
    merge_instructions = response["choices"][0]["message"]["content"].strip()
    st.write("🤖 AI Merge Instructions:", merge_instructions)

    # Merge the CSV datasets using the key column
    master_df = None
    for csv_name, df in csv_data.items():
        if master_df is None:
            master_df = df
        else:
            master_df = pd.merge(master_df, df, on=key_column, how='outer')  # Outer join to retain all rows

    # Handle missing values intelligently
    master_df = master_df.fillna('Missing')  # Example, can be customized based on AI's suggestion

    # Group the data based on the key_column
    grouped_df = master_df.groupby(key_column).agg('first').reset_index()  # Example aggregation: take the first value of each group

    # Display the grouped and merged dataframe
    st.write(grouped_df)

    return grouped_df

def merge_csv_data(csv_data, key_column, merge_strategy):
    """Merges multiple CSVs using OpenAI-determined method."""
    try:
        if merge_strategy == "Merge on key column":
            master_df = merge_using_ai(csv_data, key_column)
        else:
            master_df = pd.concat(csv_data.values(), ignore_index=True)
        
        st.write("✅ CSVs Merged Successfully using key column:", key_column)
        # st.write("✅ CSVs Merged Successfully: ", master_df.shape)
        return master_df
    
    except Exception as e:
        st.error(f"⚠️ Error merging CSV files: {e}")
        return None


### --------------- AGENT 4: Generate Data Mapping --------------- ###
def generate_data_map(master_df):
    """Creates a column mapping for AI to refine."""
    if master_df is None:
        st.error("⚠️ No master dataset found!")
        return None
    
    mapping = {col: "" for col in master_df.columns}
    st.write("🔍 Debug: Initial Mapping ->", mapping)
    return mapping


### --------------- AGENT 5: Extract Excel Template Context --------------- ###
def extract_template_context(template_file):
    """Reads the Excel template and extracts required fields."""
    try:
        df = pd.read_excel(template_file, engine="openpyxl")
        # df.columns = df.iloc[0]  # Set first row as header
        # df = df[1:].reset_index(drop=True)

        template_columns = list(df.columns)
        st.write("✅ Extracted Template Columns:", template_columns)
        return template_columns
    except Exception as e:
        st.error(f"⚠️ Error reading template: {e}")
        return None


### --------------- AGENT 6: AI-Powered Mapping --------------- ###


def ai_map_columns(master_df, template_columns):
    """Uses OpenAI to intelligently map CSV data with support for calculated columns."""
    
    # Get sample data and infer data types
    sample_data = {}
    inferred_types = {}
    
    for col in master_df.columns:
        # Get sample values
        non_null_values = master_df[col].dropna().head(3).tolist()
        sample_data[col] = non_null_values if non_null_values else ['<empty>']
        
        # Try to infer data type
        try:
            if pd.to_datetime(master_df[col], errors='coerce').notna().any():
                inferred_types[col] = "date"
            elif master_df[col].dtype == 'float' or master_df[col].dtype == 'int':
                inferred_types[col] = "numeric"
            else:
                inferred_types[col] = "text"
        except:
            inferred_types[col] = "text"
    
    prompt = (
        f"Given these CSV columns with sample values and inferred types:\n"
        f"Sample data: {json.dumps(sample_data)}\n"
        f"Inferred types: {json.dumps(inferred_types)}\n\n"
        f"Map them to these template columns: {template_columns}.\n\n"
        "Some template columns may require calculations or transformations:\n"
        "1. For date columns, map to appropriate date components if needed (e.g., 'release_date' to 'year')\n"
        "2. For calculable columns (like 'total', 'average', 'percentage'), indicate no direct mapping\n"
        "3. For full names, try mapping both first_name and last_name if they exist\n\n"
        "Return the mapping as a **valid JSON object** with the format:\n"
        '{ "mappings": { "CSV_column_name": "Template_column_name", ... } }\n\n'
        "Only map columns that have direct correspondences. Do not include calculated columns in your mapping."
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



### --------------- AGENT 7: Populate Excel Template --------------- ###

def populate_template(master_df, mapping, template_file):
    """Creates a new Excel file with mapped data including support for calculated columns."""

    # Enhanced detection of required transformations
    def detect_field_transformations(mapping, master_df, template_headers):
        """Detect potential field transformations based on mapping and column names."""
        transformations = {}
        date_fields = []
        
        # Detect date fields
        for col in master_df.columns:
            try:
                if pd.to_datetime(master_df[col], errors='coerce').notna().any():
                    date_fields.append(col)
            except:
                pass
        
        # Date component transformations
        date_components = ['year', 'month', 'day', 'quarter', 'week']
        for source_col, target_col in mapping.items():
            if source_col in date_fields:
                for component in date_components:
                    if component.lower() in target_col.lower():
                        transformations[(source_col, target_col)] = {'type': 'date_component', 'component': component}
        
        # Detect calculated columns - columns in template not directly mapped
        calculated_columns = []
        for col in template_headers:
            if col not in mapping.values():
                calculated_columns.append(col)
        
        if calculated_columns:
            st.write("🧮 Potential calculated columns:", calculated_columns)
            
        return transformations, date_fields, calculated_columns
    
    # Enhanced transformation function with calculation support
    def transform_value(row, source_col, target_col, transformations, date_fields, master_df):
        """Apply transformations including calculations to values."""
        value = row[source_col] if source_col in row.index else None
        
        # Check if this is a defined transformation
        if (source_col, target_col) in transformations:
            transform_info = transformations[(source_col, target_col)]
            
            # Handle date transformations
            if transform_info['type'] == 'date_component' and source_col in date_fields and pd.notna(value):
                try:
                    date_value = pd.to_datetime(value)
                    component = transform_info['component']
                    if component == 'year':
                        return date_value.year
                    elif component == 'month':
                        return date_value.month
                    elif component == 'day':
                        return date_value.day
                    elif component == 'quarter':
                        return date_value.quarter
                    elif component == 'week':
                        return date_value.isocalendar()[1]
                except:
                    pass
        
        return value
    
    # New function to handle calculated columns
    def calculate_column_value(row, column_name, master_df):
        """Calculate values for derived columns based on column name and available data."""
        # Common calculated fields based on naming patterns
        column_lower = column_name.lower()
        
        try:
            # Date-based calculations
            if 'age' in column_lower or 'years_since' in column_lower:
                date_cols = [col for col in row.index if col in date_fields]
                if date_cols:
                    date_col = date_cols[0]  # Use first available date
                    if pd.notna(row[date_col]):
                        date_value = pd.to_datetime(row[date_col])
                        return (pd.Timestamp.now() - date_value).days // 365
            
            # Financial calculations
            elif 'total' in column_lower:
                numeric_cols = [col for col in row.index if pd.api.types.is_numeric_dtype(master_df[col])]
                if numeric_cols and len(numeric_cols) >= 2:
                    return row[numeric_cols].sum()
            
            # Percentage calculations
            elif 'percent' in column_lower or 'ratio' in column_lower:
                numeric_cols = [col for col in row.index if pd.api.types.is_numeric_dtype(master_df[col])]
                if len(numeric_cols) >= 2:
                    # Try to find appropriate numerator/denominator
                    for col1 in numeric_cols:
                        for col2 in numeric_cols:
                            if col1 != col2 and pd.notna(row[col2]) and row[col2] != 0:
                                return (row[col1] / row[col2]) * 100
            
            # Count-based calculations
            elif 'count' in column_lower:
                return len([x for x in row.values if pd.notna(x)])
            
            # Full name from first/last
            elif 'full_name' in column_lower or 'name' in column_lower:
                name_parts = []
                for col in row.index:
                    if 'name' in col.lower() and pd.notna(row[col]):
                        name_parts.append(str(row[col]))
                if name_parts:
                    return " ".join(name_parts)
            
            # Use AI to determine calculation method for complex cases
            elif ai_available:
                calculation = determine_calculation_ai(column_name, row.index.tolist(), master_df.dtypes.to_dict())
                if calculation:
                    # Execute the calculation safely
                    result = eval(calculation, {"__builtins__": {}}, 
                                 {col: row[col] for col in row.index if pd.notna(row[col])})
                    return result
        
        except Exception as e:
            st.write(f"Calculation error for {column_name}: {str(e)}")
        
        return None
    
    # AI helper function for complex calculations
    def determine_calculation_ai(column_name, available_columns, column_types):
        """Use AI to determine how to calculate a column."""
        try:
            prompt = (
                f"Given a column named '{column_name}' and these available columns: {available_columns} "
                f"with types: {column_types}, suggest a Python calculation expression using just these columns. "
                f"Return ONLY the calculation expression, no explanations. Example: 'column1 + column2' or "
                f"'column1 / column2 * 100'. Do not use any functions except basic math operations."
            )
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            
            calculation = response["choices"][0]["message"]["content"].strip()
            st.write(f"📊 AI suggested calculation for '{column_name}': {calculation}")
            return calculation
        except:
            return None
    
    try:
        # Check if OpenAI is available
        ai_available = True
        if not openai.api_key:
            ai_available = False
            st.warning("⚠️ OpenAI API not available for advanced calculations.")
        
        # Load template
        template_wb = openpyxl.load_workbook(template_file)
        template_sheet = template_wb.active
        template_headers = [cell.value for cell in template_sheet[1] if cell.value]
        
        # Detect transformations and calculated columns
        transformations, date_fields, calculated_columns = detect_field_transformations(mapping, master_df, template_headers)
        
        # Create new workbook
        new_wb = openpyxl.Workbook()
        new_sheet = new_wb.active
        new_sheet.title = "Sheet1"
        new_sheet.append(template_headers)
        
        # Populate data with transformations and calculations
        for idx, row in master_df.iterrows():
            new_row = []
            for template_col in template_headers:
                # Find direct mapping
                csv_col = next((key for key, value in mapping.items() if value == template_col), None)
                
                if csv_col and csv_col in master_df.columns:
                    # Apply transformation if needed
                    transformed_value = transform_value(
                        row, csv_col, template_col, transformations, date_fields, master_df
                    )
                    new_row.append(transformed_value)
                elif template_col in calculated_columns:
                    # Handle calculated column
                    calculated_value = calculate_column_value(row, template_col, master_df)
                    new_row.append(calculated_value)
                else:
                    new_row.append(None)
            
            new_sheet.append(new_row)
        
        # Save to BytesIO
        output = BytesIO()
        new_wb.save(output)
        output.seek(0)
        
        st.write("✅ New Excel File Created Successfully!")
        return output
        
    except Exception as e:
        st.error(f"⚠️ Error creating new Excel file: {e}")
        st.write(f"Error details: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
        return None

### --------------- STREAMLIT UI --------------- ###
st.title("🔗 CSV-to-Excel Mapping App")

# Upload CSV files
uploaded_csvs = st.file_uploader("Upload CSV Files", type=["csv"], accept_multiple_files=True)

# Upload Excel template
uploaded_template = st.file_uploader("Upload Excel Template", type=["xlsx"])

# Process Button
if st.button("Process Files"):
    if not uploaded_csvs or not uploaded_template:
        st.error("⚠️ Please upload both CSV files and an Excel template.")
    else:
        # Agent 1: Extract CSV Data
        csv_dataframes = extract_csv_context(uploaded_csvs)
        
        if csv_dataframes:
            # Agent 2: Determine Merge Strategy
            merge_strategy = determine_merge_strategy(csv_dataframes)
            print("DEBUG: Merge Strategy →", merge_strategy)

            # Agent 3: Merge CSVs
            master_data = merge_csv_data(csv_dataframes, merge_strategy['key_column'], merge_strategy['strategy'])
            st.write("DEBUG: Master DataFrame Columns:", master_data.columns)
            st.write("DEBUG: Master DataFrame Sample Data:\n", master_data.head())
            if master_data is not None:
                # Agent 4: Generate Data Mapping
                initial_mapping = generate_data_map(master_data)

                # Agent 5: Extract Template Context
                template_fields = extract_template_context(uploaded_template)
                
                if template_fields:
                    # Agent 6: AI-Powered Mapping
                    refined_mapping = ai_map_columns(master_data, template_fields)
		    
                    # Assume `refined_mapping` is the string causing the issue

                print("Refined Mapping Before:",refined_mapping)
                if isinstance(refined_mapping, str):
                    try:
                        # refined_mapping = json.loads(refined_mapping["choices"][0]["message"]["content"].strip())

                        # print("Refined Mapping After:",refined_mapping)
                        refined_mapping = json.loads(refined_mapping)  # Convert to dictionary
                        st.write("✅ Successfully converted refined_mapping to dictionary.")
                    except json.JSONDecodeError as e:
                        print("⚠️ JSON Decode Error:", e)
                        raise ValueError("❌ Invalid JSON format. Please check refined_mapping.")
                
                if not isinstance(refined_mapping, dict):
                    st.error("⚠️ AI response is not a valid mapping dictionary.")
                    st.stop()


                # Agent 7: Populate Template
                final_file = populate_template(master_data, refined_mapping, uploaded_template)

                # Download Button
                if final_file:
                    st.download_button(
                        label="📥 Download Processed Excel",
                        data=final_file,
                        file_name="populated_template.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
