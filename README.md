# AI Resume Screening and Interview Assistant

An end-to-end AI-powered hiring tool built with Python and Streamlit. Upload a resume and job description to get instant match scores, skill gap analysis, and personalized interview questions with AI evaluation.

---

## Features

**Module 1 — Resume Screening**
- Upload resume (PDF) and job description (text, PDF, or image/screenshot)
- NLP-based skill extraction using a curated skills database
- Semantic similarity matching using `sentence-transformers` (all-MiniLM-L6-v2)
- Weighted match score: 60% skill overlap + 40% semantic similarity
- Skill gap analysis: matched, missing, and extra skills
- Actionable improvement suggestions
- Batch screening: rank multiple candidates against one JD

**Module 2 — Interview Assistant**
- AI-generated personalized interview questions (Technical, Behavioral, Role-Specific, Situational)
- Per-answer evaluation: score (1-10), feedback, strength, improvement tip
- Final interview report: overall score, hire recommendation, strengths, areas to improve

**Reliability**
- Centralized edge-case handling (`utils/edge_case_handler.py`) covers:
  - Corrupted, password-protected, or scanned/image-only PDF resumes
  - Very short resumes that give the matcher almost nothing to work with
  - Empty or whitespace-only job descriptions, and JDs with no detectable skills
  - Groq API failures (timeouts, rate limits, malformed responses)
- All of the above surface as clear, friendly messages in the UI instead of raw error tracebacks

---

## Project Structure

```
resume-screener/
├── app.py                          # Home page
├── pages/
│   ├── 1_Resume_Screening.py       # Single resume screening
│   ├── 2_Batch_Screening.py        # Multi-resume batch screening
│   └── 3_Interview_Prep.py         # Interview Q&A + report
├── parser/
│   ├── resume_parser.py            # PDF text extraction (with two-column support)
│   ├── skill_extractor.py          # Skill/experience/education extraction
│   ├── skills_db.py                # Skills dictionary
│   ├── jd_parser.py                # JD parsing
│   └── jd_input.py                 # JD input handler (text/PDF/image)
├── matcher/
│   ├── matcher.py                  # Match scoring + suggestions
│   └── batch_screener.py           # Batch screening pipeline
├── interview/
│   ├── question_generator.py       # Interview question generation (Groq)
│   ├── answer_evaluator.py         # Answer evaluation (Groq)
│   └── report_generator.py         # Final report generation (Groq)
├── utils/
│   └── edge_case_handler.py        # Input validation + friendly error handling
├── samples/                        # Sample resumes and JDs for testing
├── requirements.txt
└── .env                            # API keys (not committed to git)
```

---

## Setup

### Prerequisites
- Python 3.10+
- Tesseract OCR (for JD image/screenshot upload)
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - Mac: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

### Installation

```bash
# Clone or download the project
cd resume-screener

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### API Key Setup

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at https://console.groq.com

### Run the App

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| PDF Parsing | pdfplumber |
| OCR | pytesseract + Tesseract |
| Skill Extraction | Dictionary/regex matching |
| Semantic Similarity | sentence-transformers (all-MiniLM-L6-v2) |
| Generative AI | Groq API (LLaMA 3.3 70B) |
| Language | Python 3.10+ |

---

## Known Limitations

- **Scanned/image-only PDFs**: resumes saved as scanned images cannot be parsed — export from Word or Google Docs as a proper text-based PDF (the app now detects this case and shows a clear message instead of failing silently)
- **Narrative-style JDs**: job descriptions written as company pitches (no explicit requirements section) yield fewer detected skills than structured/bullet-point JDs — semantic similarity partially compensates
- **Skills database coverage**: skill extraction is limited to the skills defined in `skills_db.py` — uncommon or highly domain-specific skills may not be detected

---

## Sample Files

The `samples/` folder contains four test resumes (strong/medium/weak match + two-column layout) and a sample Backend Developer JD for testing.
