import json
import re
import streamlit as st
from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"

def _client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .streamlit/secrets.toml locally or Streamlit Cloud secrets.")
    return Groq(api_key=api_key)

def _call_agent(system_prompt: str, user_prompt: str, model: str, max_tokens: int = 5000) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_completion_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty response.")
    return content.strip()

def _extract_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise RuntimeError("The AI agent did not return valid JSON. Please retry.")

ATS_SYSTEM = """
You are Agent 1, a resume ATS compatibility auditor supporting an HR professional.
Assess document structure and machine-readability, not candidate worth or protected characteristics.
Return ONLY valid JSON with this schema:
{
 "ats_score": integer 0-100,
 "summary": "brief assessment",
 "section_review": {"contact_information":"...","professional_summary":"...","work_experience":"...","education":"...","skills":"...","formatting_and_readability":"..."},
 "issues": ["specific issue"],
 "recommendations": ["specific practical improvement"]
}
Use a transparent heuristic: section clarity 20, standard headings 15, chronology/date clarity 15,
keyword/context relevance 15, readable text structure 15, contact details 10, consistency 10.
Do not claim to know the behavior of a specific ATS. Do not penalize a candidate for missing personal details
that are not job-relevant. Flag tables, columns, graphics or headers only when evidence exists in extracted text;
explain that plain-text extraction cannot reliably inspect visual layout. Avoid making up facts.
"""

MATCH_SYSTEM = """
You are Agent 2, a job-description matching analyst. Compare only evidence in the supplied resume
against the supplied job description. Do not infer skills from job titles alone. Do not treat missing
evidence as proof the candidate lacks a skill. Do not use age, gender, race, religion, disability,
nationality, marital status or other protected/personal characteristics.
Return ONLY valid JSON:
{
 "match_score": integer 0-100,
 "summary": "brief balanced assessment",
 "matched_requirements": ["JD requirement with resume evidence"],
 "gaps": ["requirement with no or weak evidence; say 'not evidenced' rather than 'does not have'"],
 "evidence": {"technical_skills":"...","experience":"...","leadership":"...","education_and_certifications":"...","industry_exposure":"..."},
 "recommendations": ["truthful action to improve alignment"]
}
Score weighting: essential technical/functional requirements 35, relevant experience 25,
responsibilities/seniority 20, education/certifications 10, industry/context 10.
Clearly distinguish direct evidence, transferable evidence and no evidence. Do not invent evidence.
"""

RESUME_SYSTEM = """
You are Agent 3, an expert resume writer. Produce a complete, professional, ATS-friendly resume
aligned to the supplied job description. Use the original resume as the sole source of candidate facts,
and use Agents 1 and 2 only as review guidance.
Rules:
- Never invent employers, job titles, dates, degrees, certifications, tools, projects, metrics or achievements.
- Preserve all factual details. Do not upgrade responsibilities or seniority beyond the source.
- You may improve wording, organization, grammar and keyword alignment where supported by evidence.
- If a JD asks for a skill not evidenced in the resume, do not insert it as a possessed skill.
- Do not include a fabricated name, phone, email, address or LinkedIn URL. Omit absent fields.
- Use standard headings: PROFESSIONAL SUMMARY, CORE COMPETENCIES, PROFESSIONAL EXPERIENCE,
  EDUCATION, CERTIFICATIONS (only if evidenced), and ADDITIONAL INFORMATION (only if evidenced).
- Use simple one-column formatting, plain bullets, consistent dates and no tables, icons or graphics.
- Keep the resume concise and achievement-focused. Preserve quantified outcomes accurately.
- Output only the resume in Markdown. No preamble, score or commentary.
"""

def run_ats_agent(resume_text: str, model: str = DEFAULT_MODEL) -> dict:
    raw = _call_agent(ATS_SYSTEM, f"Audit this extracted resume text:\n\n{resume_text}", model, 3500)
    data = _extract_json(raw)
    data["ats_score"] = max(0, min(100, int(data.get("ats_score", 0))))
    return data

def run_matching_agent(resume_text: str, jd_text: str, model: str = DEFAULT_MODEL) -> dict:
    prompt = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}"
    raw = _call_agent(MATCH_SYSTEM, prompt, model, 4500)
    data = _extract_json(raw)
    data["match_score"] = max(0, min(100, int(data.get("match_score", 0))))
    return data

def run_resume_agent(resume_text: str, jd_text: str, ats_result: dict, match_result: dict,
                     model: str = DEFAULT_MODEL) -> str:
    prompt = f"""
ORIGINAL RESUME (source of truth):
{resume_text}

JOB DESCRIPTION:
{jd_text}

AGENT 1 ATS AUDIT:
{json.dumps(ats_result, ensure_ascii=False)}

AGENT 2 JOB MATCH ANALYSIS:
{json.dumps(match_result, ensure_ascii=False)}

Create the complete revised resume now. Do not add facts that are absent from the original resume.
"""
    return _call_agent(RESUME_SYSTEM, prompt, model, 6500)
