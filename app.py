import streamlit as st
import fitz  # PyMuPDF
from transformers import pipeline
from fpdf import FPDF
import tempfile
from sentence_transformers import SentenceTransformer, util

# Setup page
st.set_page_config(page_title="ReSearchlight", layout="wide")
st.title("ReSearchlight – Decode Research Papers Intelligently")

col1, col2 = st.columns([2, 3])
with col1:
    uploaded_file = st.file_uploader("Upload a Research Paper (PDF)", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        pdf_path = temp_file.name

    # Load full text from PDF using PyMuPDF
    doc = fitz.open(pdf_path)
    full_text = ""
    abstract_text = ""
    intro_text = ""
    concl_text = ""
    all_pages = []

    for i, page in enumerate(doc):
        text = page.get_text()
        lower = text.lower()

        if "abstract" in lower:
            abstract_text += text
        elif "introduction" in lower:
            intro_text += text
        elif "conclusion" in lower or "conclusions" in lower:
            concl_text += text

        full_text += text + "\n"
        all_pages.append((f"Page {i+1}", text))

    key_text = abstract_text + "\n" + intro_text + "\n" + concl_text

    @st.cache_resource
    def load_summarizer():
        return pipeline("summarization", model="facebook/bart-large-cnn")

    summarizer = load_summarizer()

    with st.spinner("Generating summary..."):
        chunks = [key_text[i:i+2000] for i in range(0, len(key_text), 2000)]
        summaries = []
        for chunk in chunks:
            try:
                result = summarizer(chunk, max_length=512, min_length=150, do_sample=False)
                summaries.append(result[0]['summary_text'].strip())
            except:
                pass
        final_summary = "\n\n".join(summaries)
        st.success("Summary generated!")

    with col2:
        st.subheader("Summary")
        for para in final_summary.split("\n\n"):
            st.markdown(para)

    # Download PDF summary
    with st.expander("Download Summary as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for para in final_summary.split("\n\n"):
            clean = para.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, clean)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf.output(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                st.download_button("Download Summary as PDF", data=f, file_name="summary.pdf", mime="application/pdf")

    # Ask Questions
    st.subheader("Ask Anything About the Paper")

    @st.cache_resource
    def load_embedder():
        return SentenceTransformer("paraphrase-MiniLM-L3-v2")

    embedder = load_embedder()
    corpus = [text for _, text in all_pages]
    corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)

    user_q = st.text_input("Ask a question:")
    if user_q:
        with st.spinner("Searching..."):
            q_embedding = embedder.encode(user_q, convert_to_tensor=True)
            results = util.semantic_search(q_embedding, corpus_embeddings, top_k=1)[0]
            best_match = all_pages[results[0]['corpus_id']]
            st.markdown(f"**{best_match[0]}**:\n\n{best_match[1]}")
