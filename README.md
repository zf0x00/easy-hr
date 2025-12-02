<br />
<h1 align="center">Easy HR</h1>
<p align="center">Privacy-First, Local-LLM Powered HR Resume Management Built with Parallax, Next.js, and Local AI models for secure, offline candidate processing.</p>

## 🚀 Overview

<Callout type="info">
  <strong>Easy HR</strong> is a <strong>local, privacy-focused HR resume management system</strong> powered by <strong>Local LLMs</strong> via Parallax.
  It ensures that <em>no data ever leaves your environment</em>.
</Callout>

## 🦾 Designed for

- 🏢 Companies needing **offline / on-prem** resume processing  
- 🔐 Teams requiring **privacy, compliance & security**  
- 🤖 Developers using **local AI clusters**  
- 🧑‍💼 Recruiters needing fast, automated screening

  ---

## ✨ Features

### 🧠 Local LLM Resume Parsing
- Powered by **Parallax Cluster**
- Extracts:
  - Name
  - Email / Phone
  - Education
  - Experience
  - Skills
  - Summary
  - Raw text

### 🔍 Semantic Search (Embeddings)
- Uses local embedding models  
- Stores embeddings in local DuckDB  
- Search examples:
  - “React developer”
  - “5+ years experience”
  - “Data engineer + Python”


### 🗂️ Candidate Management Dashboard
- Upload multiple resumes  
- Auto indexing via LLM  
- View extracted structured data  

### 🛡️ Privacy & Security
- **100% local AI**  
- No external APIs  
- DuckDB local storage  
- Ideal for companies with compliance restrictions

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Tailwind CSS, TypeScript, ShadCn |
| Backend | Fast API |
| AI Engine | Parallax (distributed LLM inference) |
| Database | DuckDB |
| Embedding | Local embedding model |
| Storage | Local filesystem |
| Parsing | Local OCR + LLM |
| Deployment | Local / Docker |

---

## ? Prerequests
- Install Parllax from [Here](https://github.com/GradientHQ/parallax/blob/main/docs/user_guide/install.md)
- make sure it was running in the background
- git clone this repo

```bash
# Clone Repo
git clone https://github.com/zf0x00/easy-hr.git
cd easy-hr

# Install frontend packages
cd frontend
pnpm i

# Install backend packages
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start local development environment both frontend and backend
pnpm start-all
```
