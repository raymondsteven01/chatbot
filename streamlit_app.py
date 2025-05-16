import streamlit as st
import pandas as pd
from openai import OpenAI
import time

# Page config
st.set_page_config(page_title="📊 Daily Transacting User Insight Generator", page_icon="📈")

# Title
st.title("📊 Digital Banking - Daily Transacting User Insight Generator")

# Input OpenAI API Key
openai_api_key = st.text_input("🔐 Enter your OpenAI API Key:", type="password")

if not openai_api_key:
    st.warning("Please enter your OpenAI API key to continue.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# File uploader
uploaded_file = st.file_uploader("📁 Upload your DTU xlsx file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Show the uploaded data
        st.subheader("🧾 Preview of Uploaded Data")
        st.dataframe(df.head(10))

        # Button to generate insight
        if st.button("🧠 Generate Insights"):
            with st.spinner("Generating insights using GPT-4..."):

                # Convert DataFrame to text (for context to GPT)
                data_text = df.to_csv(index=False)

                prompt = (
                    "You are a data analyst specialized in digital banking metrics. "
                    "Based on the following daily transacting user data, generate insights explaining significant day-over-day "
                    "(DoD) and week-over-week (WoW) growth changes. Include commentary on potential root causes using the context "
                    "from LIST_MERCHANT (e.g., push notification exposure) and EVENT_DESCRIPTION (e.g., public holidays). "
                    "Avoid summarizing all rows. Focus on days with high or low growth. Provide insights in a structured and readable format.\n\n"
                    f"Here is the data:\n{data_text}"
                )

                # Generate insights
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a senior product analyst at a digital banking company."},
                        {"role": "user", "content": prompt}
                    ]
                )

                insight = response.choices[0].message.content.strip()

                # Display insight
                st.subheader("📌 Generated Insight")
                st.markdown(insight)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
