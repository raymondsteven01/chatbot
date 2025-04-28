import streamlit as st
from openai import OpenAI  # Correct import for openai>=1.0.0

# --- CONFIGURATION ---
st.set_page_config(page_title="SQL Query Generator", page_icon="📝")

# --- INPUT OPENAI API KEY ---
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password")

if not openai_api_key:
    st.warning("Please provide your OpenAI API key to continue.")
    st.stop()

# Create OpenAI client
client = OpenAI(api_key=openai_api_key)

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
        response = client.chat.completions.create(
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

# --- FORM SECTION ---
with st.form("sql_generator_form"):
    user_input = st.text_area(
        "📝 Your Data Request:",
        placeholder="e.g., Show me total sales by month for 2024",
        height=150
    )
    submitted = st.form_submit_button("✨ Generate SQL")
    
    if submitted and user_input:
        with st.spinner("Generating SQL query..."):
            sql_query = generate_sql_from_text(user_input)
        
        st.subheader("🛠️ Generated SQL Query")
        st.code(sql_query, language="sql")
        
        st.subheader("💬 Your Original Request")
        st.write(user_input)
        
        # Button to simulate execution
        simulate = st.button("🚀 Simulate Query Execution")
        
        if simulate:
            if not is_select_query(sql_query):
                st.error("Only SELECT queries are allowed!")
            else:
                st.success("Query simulated successfully! (Execution would happen here)")
