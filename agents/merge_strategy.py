import openai
import json
import streamlit as st

def determine_merge_strategy(csv_data):
    """Uses AI to decide the best merging strategy based on CSV context."""
    
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

        strategy_text = response["choices"][0]["message"]["content"]
        merge_strategy = json.loads(strategy_text)

        if not isinstance(merge_strategy, dict) or "strategy" not in merge_strategy:
            raise ValueError("Invalid strategy format received.")

        return merge_strategy

    except json.JSONDecodeError:
        st.error("⚠️ Failed to parse AI response. Using fallback strategy.")
        return {"strategy": "Merge on common columns"}

    except Exception as e:
        st.error(f"⚠️ Error determining merge strategy: {e}")
        return {"strategy": "Merge on common columns"}
