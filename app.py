import streamlit as st
import tempfile
import os
import matplotlib.pyplot as plt
import pandas as pd
from utils.processor import analyze_audits
from docx import Document
from fpdf import FPDF

st.set_page_config(page_title="Audit Insights Pro", layout="wide")
st.markdown("""
<style>
    .audit-preview {
        background-color: #f0f2f6;
        padding: 8px;
        border-left: 5px solid #0066cc;
        margin-bottom: 10px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Audit Insights Pro")
st.markdown("Upload 2 to 4 audit reports in PDF format. The app will summarize each and compare findings.")

uploaded_files = st.file_uploader("Upload PDF audit reports", type="pdf", accept_multiple_files=True)

if uploaded_files and 2 <= len(uploaded_files) <= 4:
    with st.spinner("Analyzing audits with AI..."):
        temp_paths = []
        filenames = []
        for file in uploaded_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(file.read())
            temp_file.close()
            temp_paths.append(temp_file.name)
            filenames.append(file.name)

        result = analyze_audits(temp_paths, filenames)

        summaries = result["summaries"]
        logos = result["logos"]
        themes = result["themes"]
        comparison = result["comparison"]
        learnings = result["learnings"]

        st.subheader("📝 Audit Summaries")
        for i, summary in enumerate(summaries):
            preview = "\n".join(summary.split("\n")[:4])
            st.markdown(f"<div class='audit-preview'>{preview}</div>", unsafe_allow_html=True)

            with st.expander(f"📄 Full Summary: {filenames[i]}"):
                if logos[i] and os.path.exists(logos[i]):
                    st.image(logos[i], width=120)
                st.text_area("Full Summary", summary, height=250)

                # Download TXT inside block
                text_file = os.path.join(tempfile.gettempdir(), f"{filenames[i]}.txt")
                with open(text_file, "w") as f:
                    f.write(summary)
                st.download_button("⬇ Download This Summary (.txt)", open(text_file, "rb"), file_name=f"{filenames[i]}.txt")

        st.subheader("📊 Common Audit Themes")
        theme_flat = [item for sublist in themes for item in sublist]
        theme_counts = pd.Series(theme_flat).value_counts()

        fig, ax = plt.subplots()
        theme_counts.plot(kind='barh', ax=ax, color="#1f77b4")
        plt.xlabel("Frequency")
        plt.ylabel("Audit Themes")
        st.pyplot(fig)

        st.subheader("🔍 Comparison of Audits")
        st.text(comparison)

        st.subheader("💡 Key Learnings for Future Audits")
        st.text(learnings)
else:
    st.warning("Please upload 2 to 4 PDF audit reports.")
