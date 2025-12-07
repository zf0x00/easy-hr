<p align="center">
  <img src="/graphics/easy-hr-icon.png" alt="Easy HR Logo" width="120" />
</p>

<h1 align="center">Easy HR</h1>
<p align="center">Privacy-First, Local-LLM Powered HR Resume Management Built with Parallax, React, and Local AI models for secure, offline candidate processing.</p>

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

## 🏗️ Architecture

<p align="center">
  <img src="/graphics/arch.png" alt="Easy HR Logo" width="500" />
</p>

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
## 📸 Screenshots

<div style="display: flex; justify-content: center; gap: 20px;">
  <img src="/graphics/images/pic_01.png" alt="Image 1" width="320" />
  <img src="/graphics/images/pic_02.png" alt="Image 2" width="320" />
  <img src="/graphics/images/pic_03.png" alt="Image 3" width="320" />
</div>

---

## ? Prerequests
- Install Parllax from [Here](https://github.com/GradientHQ/parallax/blob/main/docs/user_guide/install.md)
- Follow this to learn how to run a Parallax node [Here](https://github.com/GradientHQ/parallax/blob/main/docs/user_guide/quick_start.md)
- make sure Parllax was running in the background in 3001 port 
- git clone this repo

```bash
#Parllax Run after activation
parallax run -m Qwen/Qwen3-0.6B -n 1 #in this i am using Qwen3-0.6B can use any Qwen model bigger model better output
parallax join
```

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
