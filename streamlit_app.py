import streamlit as st
from helper import run_resume_review
from docx import Document
from pypdf import PdfReader
from io import BytesIO

st.set_page_config(page_title="Resume Roaster", page_icon="🔥")

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}
.block-container {
    max-width: 700px;
    padding-top: 2rem;
}
.stTextArea textarea {
    background-color: #262730;
    color: white;
    border: 1px solid #ff4b4b;
    border-radius: 8px;
}
.stButton button {
    background-color: #161922;
    color: white;
    border: 1px solid #454954;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 Resume Roaster")
st.caption("Upload your resume or paste your resume text to get an AI-powered review.")

resume_text = st.text_area(
    "Paste your resume text here (optional)",
    height=200,
    placeholder="Paste your resume text here..."
)

uploaded_file = st.file_uploader(
    "Or upload your resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

def extract_text(file):
    if file.name.endswith(".pdf"):
        pdf = PdfReader(BytesIO(file.getvalue()))
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

    if file.name.endswith(".docx"):
        doc = Document(BytesIO(file.getvalue()))
        return "\n".join(p.text for p in doc.paragraphs)

    return ""

def show_result(text):
    with st.spinner("Analyzing your resume..."):
        result = run_resume_review(text)

    if result.get("error"):
        st.error(result["error"])
        return

    st.success("Analysis completed!")
    st.metric("Resume Score", f"{result['score']}/10")

    st.subheader("✅ Strengths")
    for item in result["strengths"]:
        st.write(f"- {item}")

    st.subheader("🔧 Areas to Improve")
    for item in result["fixes"]:
        st.write(f"- {item}")

if st.button("🔥 Roast My Resume"):

    if uploaded_file and resume_text.strip():
        st.warning("Use either a file or pasted text, not both.")

    elif uploaded_file:
        text = extract_text(uploaded_file)

        if text.strip():
            show_result(text)
        else:
            st.error("Could not extract text from the file.")

    elif resume_text.strip():
        show_result(resume_text)

    else:
        st.warning("Please upload a file or paste resume text.")