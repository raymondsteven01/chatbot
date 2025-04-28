import streamlit as st
from openai import OpenAI
import pandas as pd
import re

# --- CONFIGURATION ---
SUPERBANK_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png"  # <-- Replace with real Superbank logo (direct PNG)
PAGE_BACKGROUND_COLOR = "#afee00ff"

st.set_page_config(
    page_title="SQL Query Generator",
    page_icon=SUPERBANK_LOGO_URL,
)

# --- CUSTOM CSS ---
st.markdown(
    f"""
    <style>
    body {{
        background-color: {PAGE_BACKGROUND_COLOR};
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: #ffffff;
    }}
    .superbank-label::before {{
        content: url('{SUPERBANK_LOGO_URL}');
        display: inline-block;
        width: 24px;
        height: 24px;
        margin-right: 10px;
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
st.title("📝 Natural Language ➔ SQL Generator")
st.write("Describe your request, and I'll craft a secure SQL query for you.")

if not st.session_state.api_key_provided:
    st.info("Please enter your OpenAI API key in the sidebar to start.")
    st.stop()

# --- FORM ---
with st.form("sql_generator_form"):
    st.markdown('<label class="superbank-label">Your Data Request:</label>', unsafe_allow_html=True)
    user_input = st.text_area(
        label=" ",  # Empty because label handled manually
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

    st.subheader("💬 Your Original Request")
    st.write(st.session_state.user_prompt)

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
