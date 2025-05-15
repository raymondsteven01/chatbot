import streamlit as st
import pandas as pd
from openai import OpenAI

# --- CONFIGURATION ---
st.set_page_config(page_title="📈 Digital Banking Metric Insight Generator", page_icon="💡")

# --- API KEY INPUT ---
openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password")
if not openai_api_key:
    st.warning("Please enter your OpenAI API key to continue.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# --- TITLE ---
st.title("💡 Digital Banking Metric Insight Generator")
st.write(
    "Upload two CSV files: one for overall monthly transacting metrics and one for breakdown by transaction type. "
    "The AI will generate growth insights and suggest potential root causes."
)

# --- FILE UPLOAD ---
col1, col2 = st.columns(2)

with col1:
    overall_csv = st.file_uploader("📊 Upload Monthly Transacting Metrics CSV", type=["csv"])
with col2:
    breakdown_csv = st.file_uploader("📉 Upload Breakdown Performance CSV", type=["csv"])

# --- PROCESS ---
if overall_csv and breakdown_csv:
    overall_df = pd.read_csv(overall_csv)
    breakdown_df = pd.read_csv(breakdown_csv)

    st.subheader("📋 Preview: Overall Transacting Metrics")
    st.dataframe(overall_df)

    st.subheader("📋 Preview: Breakdown by Transaction Type")
    st.dataframe(breakdown_df)

    # Combine and summarize for the prompt
    try:
        overall_text = overall_df.to_markdown(index=False)
        breakdown_text = breakdown_df.to_markdown(index=False)
    except:
        st.error("Make sure your CSVs follow the expected format.")
        st.stop()

    st.markdown("---")

    if st.button("🧠 Generate Insights"):
        with st.spinner("Analyzing your data..."):

            prompt = (
                "You are a data analyst in a digital banking team.\n"
                "Given the monthly transacting user data and its breakdown by transaction type, "
                "analyze the month-on-month growth and identify possible root causes for any increase or decrease.\n\n"
                "Here is the overall metric data:\n"
                f"{overall_text}\n\n"
                "And here is the breakdown data:\n"
                f"{breakdown_text}\n\n"
                "Please generate an executive-level summary insight."
            )

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": "You are a banking analytics expert."},
                              {"role": "user", "content": prompt}]
                )
                insight = response.choices[0].message.content.strip()

                st.subheader("🔍 AI-Generated Insight")
                st.write(insight)

            except Exception as e:
                st.error(f"Error while generating insights: {e}")

else:
    st.info("Please upload both CSV files to continue.")
