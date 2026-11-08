import streamlit as st
from agents import run_ats_agent, run_matching_agent, run_resume_agent
from document_parser import extract_text
from resume_export import markdown_to_docx

st.set_page_config(page_title="AI Resume HR Assistant", page_icon="🧑‍💼", layout="wide")

st.title("🧑‍💼 AI Resume Screening & Optimization")
st.caption("Three-agent recruitment assistant powered by Groq")

with st.sidebar:
    st.header("Configuration")
    model = st.selectbox(
    "Groq model",
    options=[
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b"
    ],
    index=0
)
    st.info("Your Groq API key is read from Streamlit secrets. Never paste it into this app or commit it to GitHub.")
    st.markdown("---")
    st.caption("Agent 1: ATS audit · Agent 2: JD match · Agent 3: Resume development")

if "results" not in st.session_state:
    st.session_state.results = None

left, right = st.columns(2)
with left:
    resume_file = st.file_uploader("Upload candidate resume", type=["pdf", "docx"])
with right:
    jd_file = st.file_uploader("Optional: upload job description", type=["pdf", "docx"])

resume_text = ""
jd_from_file = ""
if resume_file:
    try:
        resume_text = extract_text(resume_file, resume_file.name)
        st.success(f"Resume extracted: {len(resume_text):,} characters")
    except Exception as exc:
        st.error(f"Could not read resume: {exc}")

if jd_file:
    try:
        jd_from_file = extract_text(jd_file, jd_file.name)
    except Exception as exc:
        st.error(f"Could not read job description: {exc}")

jd_text = st.text_area(
    "Job description",
    value=jd_from_file,
    height=260,
    placeholder="Paste the complete job description here, including responsibilities, qualifications and required skills."
)

if resume_text:
    with st.expander("Preview extracted resume text"):
        st.text(resume_text[:12000] + ("\n\n[Preview truncated]" if len(resume_text) > 12000 else ""))

run = st.button("🚀 Run all 3 agents", type="primary", use_container_width=True,
                disabled=not (resume_text.strip() and jd_text.strip()))

if run:
    if len(resume_text) > 30000 or len(jd_text) > 18000:
        st.error("Input is too long. Please use a resume under 30,000 characters and a job description under 18,000 characters.")
    else:
        try:
            with st.status("Running the three-agent assessment...", expanded=True) as status:
                st.write("Agent 1 — auditing ATS compatibility...")
                ats = run_ats_agent(resume_text, model)
                st.write("Agent 2 — comparing resume with the job description...")
                match = run_matching_agent(resume_text, jd_text, model)
                st.write("Agent 3 — developing a job-aligned resume...")
                optimized = run_resume_agent(resume_text, jd_text, ats, match, model)
                status.update(label="All three agents completed.", state="complete", expanded=False)
            st.session_state.results = {
                "ats": ats, "match": match, "optimized": optimized,
                "resume_text": resume_text, "jd_text": jd_text
            }
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.caption("Check your Groq API key, model availability, internet connection and Streamlit logs.")

results = st.session_state.results
if results:
    ats, match, optimized = results["ats"], results["match"], results["optimized"]
    st.divider()
    st.header("Assessment dashboard")
    c1, c2 = st.columns(2)
    with c1:
        score = ats.get("ats_score", 0)
        st.metric("Estimated ATS compatibility", f"{score}/100")
        st.progress(max(0, min(100, int(score))) / 100)
    with c2:
        score = match.get("match_score", 0)
        st.metric("Estimated job-description match", f"{score}/100")
        st.progress(max(0, min(100, int(score))) / 100)

    tab1, tab2, tab3 = st.tabs(["① ATS audit", "② Job match", "③ Optimized resume"])
    with tab1:
        st.subheader("ATS compatibility review")
        st.markdown(ats.get("summary", ""))
        st.markdown("**Section and formatting review**")
        st.json(ats.get("section_review", {}))
        st.markdown("**Issues to fix**")
        for item in ats.get("issues", []):
            st.warning(item)
        st.markdown("**Recommendations**")
        for item in ats.get("recommendations", []):
            st.write(f"• {item}")
        st.caption("This is an AI-estimated screening assessment, not a score from a specific employer ATS.")
    with tab2:
        st.subheader("Resume-to-job-description match")
        st.markdown(match.get("summary", ""))
        st.markdown("**Matched requirements**")
        for item in match.get("matched_requirements", []):
            st.success(item)
        st.markdown("**Missing or weak requirements**")
        for item in match.get("gaps", []):
            st.warning(item)
        st.markdown("**Evidence and recommendations**")
        st.json(match.get("evidence", {}))
        for item in match.get("recommendations", []):
            st.write(f"• {item}")
    with tab3:
        st.subheader("Job-aligned resume")
        st.info("Review every statement before using this resume. The agent is instructed not to invent experience, qualifications, employers, dates or achievements.")
        st.markdown(optimized)
        st.download_button("⬇️ Download optimized resume (Markdown)",
                           data=optimized.encode("utf-8"),
                           file_name="job_aligned_resume.md",
                           mime="text/markdown")
        try:
            docx_bytes = markdown_to_docx(optimized)
            st.download_button("⬇️ Download optimized resume (Word)",
                               data=docx_bytes,
                               file_name="job_aligned_resume.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as exc:
            st.warning(f"DOCX export was unavailable: {exc}")

    st.divider()
    st.caption("Human review is required. Do not use automated scores as the sole basis for hiring, rejection or other employment decisions.")
