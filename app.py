import streamlit as st
from pypdf import PdfReader
from fpdf import FPDF
import io
import re

st.set_page_config(page_title="ReSearchlight", layout="wide")
st.title("📘 ReSearchlight – Research Paper Summarizer")

uploaded_file = st.file_uploader("Upload a research paper (PDF)", type="pdf")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    summary_sentences = [s.strip() for s in sentences if len(s.split()) > 8]
    summary = "\n\n".join(sorted(summary_sentences, key=len, reverse=True)[:5])

    st.subheader("Summary")
    st.write(summary)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in summary.split("\n\n"):
        safe_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 10, safe_line)
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    st.download_button(
        "Download Summary as PDF",
        data=buffer,
        file_name="summary.pdf",
        mime="application/pdf"
    )
