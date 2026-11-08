# Three-Agent AI Resume Screening & Optimization

Streamlit + Groq application with three independent agents:
1. ATS compatibility auditor
2. Resume-to-job-description matcher
3. Job-aligned resume developer

## Features
- PDF and DOCX resume upload
- PDF and DOCX job-description upload, or paste JD text
- Separate ATS and JD-match scores with findings
- Resume rewrite grounded in the original candidate resume
- Markdown and DOCX downloads

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment:

   Windows:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Create `.streamlit/secrets.toml` and add:

   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key"
   ```

   Get an API key from https://console.groq.com/keys. Never commit this file.

6. Start the app:

   ```bash
   streamlit run app.py
   ```

## Push to GitHub

Create an empty GitHub repository, then run from this project folder:

```bash
git init
git add .
git commit -m "Initial three-agent resume screening app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Check that `.streamlit/secrets.toml` is not included in the commit. The `.gitignore` excludes it.

## Deploy on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/
2. Select **Create app**.
3. Choose the GitHub repository, `main` branch and `app.py`.
4. Open **Advanced settings → Secrets**.
5. Paste:

   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key"
   ```

6. Deploy. Streamlit installs packages from `requirements.txt`.

## Important safeguards

- AI scores are estimates, not scores from a particular ATS vendor.
- Text extraction may not reveal visual layout problems in a PDF.
- Scanned PDFs need OCR before analysis.
- Agent 3 must not invent experience or qualifications. HR must verify every claim.
- Do not use the scores as the sole basis for hiring or rejection.
- Resume files contain personal data. Limit access, avoid retaining files unnecessarily,
  disclose use of external AI processing, and obtain appropriate consent.
- For production use, add authentication, access controls, audit logging, retention/deletion
  controls, rate limits and a privacy notice.
