import streamlit as st
from openai import OpenAI  # Correct import for openai >= 1.0.0

# --- CONFIGURATION ---
st.set_page_config(page_title="SQL Query Generator", page_icon="📝")

# Create a box for the user to input the OpenAI API Key (so it's not hardcoded)
OPENAI_API_KEY = st.text_input("Enter your OpenAI API Key:", type="password")

# Validate if API key is provided
if not OPENAI_API_KEY:
    st.error("OpenAI API Key is required to proceed!")
    st.stop()

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# --- FUNCTIONS ---

def generate_sql_from_text(user_prompt):
    system_prompt = (
        "You are a Snowflake SQL expert. "
        "Fix typos if needed, and translate the user request into a safe SELECT SQL query. "
        "Ensure the query has a LIMIT 1000 if not specified. "
        "Do not use DELETE, UPDATE, INSERT, DROP, ALTER, CREATE, or any non-SELECT command. "
        "Respond ONLY with the SQL query."
    )
    
    try:
        response = client.chat.completions.create(  # ✅ Correct new API usage
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        sql_query = response.choices[0].message.content.strip()
        sql_query = enforce_limit(sql_query)
        return sql_query
    except Exception as e:
        st.error(f"Error while generating SQL from OpenAI: {e}")
        st.stop()

def enforce_limit(sql_query):
    sql_lower = sql_query.lower()
    if "limit" not in sql_lower:
        if ";" in sql_query:
            sql_query = sql_query.replace(";", " LIMIT 1000;")
        else:
            sql_query += " LIMIT 1000"
    return sql_query

def is_select_query(sql):
    sql_clean = sql.strip().lower()
    return sql_clean.startswith("select")

# --- UI LAYOUT ---

st.title("📝 Natural Language to SQL Generator")
st.write("Type your request in natural language, and I'll generate the corresponding SQL query for you.")

# User input for data request
# User input for data request
user_input = st.text_area(
    "📝 Your Data Request:",
    placeholder="e.g., Show me total sales by month for 2024",
    height=150
)
