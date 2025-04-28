import streamlit as st
from openai import OpenAI
import pandas as pd
import re

# --- CONFIGURATION ---
SUPERBANK_LOGO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSi6LE5N8oHmFoBSYpnJ6O_53in-360ewtuKQ&s"
PAGE_BACKGROUND_COLOR = "#afee00ff"

st.set_page_config(
    page_title="SQL Query Generator",
    page_icon=SUPERBANK_LOGO_URL,
)

# --- CUSTOM CSS ---
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: {PAGE_BACKGROUND_COLOR};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: #ffffff;
    }}
    .superbank-label {{
        display: flex;
        align-items: center;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }}
    .superbank-label img {{
        width: 24px;
        height: 24px;
        margin-right: 8px;
        vertical-align: middle;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- SESSION STATE INIT ---
if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = False

if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""

if "user_prompt" not in st.session_state:
    st.session_state.user_prompt = ""

if "explanation" not in st.session_state:
    st.session_state.explanation = ""

# --- FUNCTIONS ---

def get_openai_client(api_key):
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        st.stop()

def enforce_limit(sql_query):
    if re.search(r"\blimit\b", sql_query, re.IGNORECASE):
        return sql_query
    sql_query = re.sub(r";\s*$", "", sql_query)  # Remove trailing semicolon if present
    return sql_query + " LIMIT 1000;"

def is_select_query(sql):
    return sql.strip().lower().startswith("select")

def generate_sql_from_text(client, user_prompt):
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
        return enforce_limit(sql_query)
    except Exception as e:
        st.error(f"Error generating SQL: {e}")
        st.stop()

def generate_explanation(client, user_prompt, sql_query):
    explanation_prompt = (
        "Explain briefly how you interpreted the following request into an SQL query. "
        "Be concise, mention any assumptions, corrections, or interpretations you made.\n\n"
        f"Request: {user_prompt}\n\nSQL Query: {sql_query}\n\n"
        "Your Explanation:"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": explanation_prompt}
            ]
        )
        explanation = response.choices[0].message.content.strip()
        return explanation
    except Exception as e:
        st.error(f"Error generating explanation: {e}")
        return "No explanation available."

def simulate_query_execution():
    # Simulate dummy DataFrame
    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "value": [100, 200, 300]
    }
    df = pd.DataFrame(data)
    return df

def reset_form():
    st.session_state.generated_sql = ""
    st.session_state.user_prompt = ""
    st.session_state.explanation = ""

# --- SIDEBAR: API Key Input ---
with st.sidebar:
    if not st.session_state.api_key_provided:
        openai_api_key = st.text_input("🔑 Enter OpenAI API Key:", type="password")
        if openai_api_key:
            st.session_state.api_key = openai_api_key
            st.session_state.client = get_openai_client(openai_api_key)
            st.session_state.api_key_provided = True
            st.success("API Key saved. Ready to generate!")

# --- MAIN APP UI ---

st.title("📝 Superbank Data Analytics Team: Natural Language ➔ SQL Generator App")

st.markdown(
    """
    **About this App**  
    This application was developed by the **Data Analytics Team** to empower **business users** in generating accurate and secure **SQL queries** for extracting data from our **Snowflake database**.  
    By simply describing your data needs in natural language, the app automatically translates your request into an optimized SQL query, following best practices for security and efficiency.

    Our goal is to make data access easier, faster, and safer — without needing deep technical SQL knowledge. 🚀
    """
)

st.write("Describe your request, and I'll craft a secure SQL query for you.")

if not st.session_state.api_key_provided:
    st.info("Please enter your OpenAI API key in the sidebar to start.")
    st.stop()

# --- FORM ---
with st.form("sql_generator_form"):
    # Custom Label with Logo
    st.markdown(
        f"""
        <div class="superbank-label">
            <img src="{SUPERBANK_LOGO_URL}" alt="Logo"> Your Data Request:
        </div>
        """,
        unsafe_allow_html=True
    )

    user_input = st.text_area(
        label=" ",  # Empty because label is handled above
        placeholder="e.g., Show total sales by month for 2024",
        height=150,
        value=st.session_state.user_prompt
    )
    submitted = st.form_submit_button("✨ Generate SQL")
    reset = st.form_submit_button("🔄 Reset Form")

    if reset:
        reset_form()
        st.experimental_rerun()

    if submitted:
        if not user_input.strip():
            st.warning("Please enter a description.")
        else:
            with st.spinner("Generating SQL query..."):
                sql_query = generate_sql_from_text(st.session_state.client, user_input)

            st.session_state.generated_sql = sql_query
            st.session_state.user_prompt = user_input

            with st.spinner("Interpreting your request..."):
                explanation = generate_explanation(st.session_state.client, user_input, sql_query)

            st.session_state.explanation = explanation

# --- AFTER FORM SUBMIT ---
if st.session_state.generated_sql:
    st.subheader("🛠️ Generated SQL Query")
    st.code(st.session_state.generated_sql, language="sql")

    st.download_button(
        "💾 Download SQL as .sql",
        data=st.session_state.generated_sql,
        file_name="generated_query.sql",
        mime="text/plain"
    )

    st.subheader("💬 Interpretation of Your Request")
    st.write(st.session_state.explanation)

    simulate = st.button("🚀 Simulate Query Execution")

    if simulate:
        if is_select_query(st.session_state.generated_sql):
            st.success("✅ Query simulated successfully! (Dummy Data Generated Below)")
            df = simulate_query_execution()
            st.dataframe(df)

            st.download_button(
                "⬇️ Download Simulated Output (CSV)",
                data=df.to_csv(index=False),
                file_name="simulated_output.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Only SELECT queries are allowed for simulation.")
