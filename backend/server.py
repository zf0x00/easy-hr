from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import logging
import os
import shutil
import uuid

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from typing import List, Optional

import duckdb
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from workers import embed_worker, extract_worker, ocr_worker, search_worker

# --- Config (change if needed) ---
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "db", "candidates.duckdb")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
PARALLAX_HOST = os.environ.get(
    "PARALLAX_HOST", "http://localhost:3001"
)

os.makedirs(TMP_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

logger = logging.getLogger(__name__)

# --- FastAPI app ---
app = FastAPI(title="Resume-AI Backend")
# Allow Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for responses
class Candidate(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    experience_years: Optional[float]
    skills: Optional[str]
    education: Optional[str]
    summary: Optional[str]
    raw_text: Optional[str]
    created_at: Optional[str]


class Chat(BaseModel):
    id: int
    title: str
    created_at: str


class ChatMessage(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: str

# Endpoint: semantic search
class SearchIn(BaseModel):
    query: str
    top_k: Optional[int] = 10

class ChatDetail(Chat):
    messages: List[ChatMessage]

class CreateChatRequest(BaseModel):
    messages: List[dict]


class AddMessagesRequest(BaseModel):
    messages: List[dict]

# Helper: connect
def get_conn():
    return duckdb.connect(DB_PATH)


# Helper: safe insert
def insert_candidate(conn, candidate_obj: dict, embedding: List[float]):
    logging.info("Inserting candidate: %s", candidate_obj.get("Full Name", "N/A"))

    # Normalize storage: skills as JSON string
    skills_field = candidate_obj.get("Skills") or None
    if isinstance(skills_field, (list, tuple)):
        skills_val = json.dumps(skills_field)
    else:
        skills_val = (
            json.dumps([s.strip() for s in skills_field.split(",")])
            if skills_field
            else json.dumps([])
        )

    conn.execute(
        """
        INSERT INTO candidates
        (name, email, phone, experience_years, skills, education_summary, professional_summary, raw_text, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            candidate_obj.get("Full Name") or None,
            candidate_obj.get("Email") or None,
            candidate_obj.get("Phone") or None,
            candidate_obj.get("Total Experience") or None,
            skills_val,
            candidate_obj.get("Education Summary") or None,
            candidate_obj.get("Professional Summary") or None,
            candidate_obj.get("raw_text") or None,
            embedding,
        ],
    )
    # DuckDB autocommit by default for single execute


# Endpoint: health
@app.get("/health")
def health():
    return {"status": "ok"}


def process_and_insert_resume(file: UploadFile):
    """
    Process a single resume file: save, OCR, parse, embed, and insert into DB.
    This is a synchronous function intended to be run in a thread pool.
    """
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    logging.info(f"Processing file: {filename}")
    file_path = os.path.join(TMP_DIR, filename)

    # Always ensure file is closed to prevent resource leaks
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        file.file.close()

    try:
        # 1) OCR
        raw_text = ocr_worker.extract_text(file_path)
        logging.info(f"🚀 OCR complete for {file.filename}")

        # 2) Extract structured fields
        parsed = extract_worker.extract_fields(raw_text)
        logging.info(f"🚀 Parsed data for {file.filename}: {parsed}")

        # If extraction failed, use a fallback structure with correct keys
        if not isinstance(parsed, dict) or parsed.get("error"):
            logging.warning(
                f"Could not parse structured data for {file.filename}. Using fallback. Error: {parsed.get('error', 'Not a dict')}"
            )
            parsed = {
                "Full Name": None,
                "Email": None,
                "Phone": None,
                "Skills": [],
                "Total Experience": None,
                "Education Summary": None,
                "Professional Summary": None,
            }

        # Always store the raw text
        parsed["raw_text"] = raw_text

        # 3) Embedding
        emb = embed_worker.embed_text(raw_text)
        logging.info(f"🚀 Embedding complete for {file.filename}")

        # 4) Insert into DuckDB
        with get_conn() as conn:
            insert_candidate(conn, parsed, emb)
        logging.info(f"🚀 Inserted into DB for {file.filename}")

        return {"status": "ok", "parsed": parsed, "filename": file.filename}
    except Exception as e:
        logging.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
        return {"status": "error", "filename": file.filename, "detail": str(e)}
    finally:
        pass


# Endpoint: upload resume (PDF)
@app.post("/upload")
async def upload_resume(files: List[UploadFile] = File(...)):
    """
    Accepts multiple resume files, processes them concurrently, and stores them.
    """
    tasks = [asyncio.to_thread(process_and_insert_resume, file) for file in files]
    results = await asyncio.gather(*tasks)
    return JSONResponse(content={"results": results})


# Endpoint: list candidates (basic)
@app.get("/candidates", response_model=List[Candidate])
def list_candidates(limit: int = 50, offset: int = 0):
    logger.info("candidates endpoint accessed")
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, name, email, phone, experience_years, skills, education_summary, professional_summary, raw_text, created_at
        FROM candidates
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """,
        [limit, offset],
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append(
            {
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "phone": r[3],
                "experience_years": r[4],
                "skills": r[5],
                "education_summary": r[6],
                "professional_summary": r[7],
                "raw_text": r[8],
                "created_at": r[9],
            }
        )
    return results


# Endpoint: get candidate by id
@app.get("/candidate/{candidate_id}", response_model=Candidate)
def get_candidate(candidate_id: int):
    conn = get_conn()
    row = conn.execute(
        """
        SELECT id, name, email, phone, experience_years, skills, education, summary, raw_text, created_at
        FROM candidates
        WHERE id = ?
    """,
        [candidate_id],
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "experience_years": row[4],
        "skills": row[5],
        "education": row[6],
        "summary": row[7],
        "raw_text": row[8],
        "created_at": row[9],
    }



# Endpoint: searching with embeddings
@app.post("/search")
def semantic_search(body: SearchIn):
    try:
        result_text = search_worker.search_candidates(body.query)
        return JSONResponse({"result": result_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chats", response_model=List[Chat])
def get_chats():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at FROM chats ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "created_at": str(row[2])} for row in rows]



@app.get("/api/chats/{chat_id}", response_model=ChatDetail)
def get_chat(chat_id: int):
    conn = get_conn()
    chat_row = conn.execute(
        "SELECT id, title, created_at FROM chats WHERE id = ?", [chat_id]
    ).fetchone()
    if not chat_row:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages_rows = conn.execute(
        "SELECT id, chat_id, role, content, created_at FROM chat_messages WHERE chat_id = ? ORDER BY created_at ASC",
        [chat_id],
    ).fetchall()
    conn.close()

    messages = [
        {
            "id": row[0],
            "chat_id": row[1],
            "role": row[2],
            "content": row[3],
            "created_at": str(row[4]),
        }
        for row in messages_rows
    ]

    return {
        "id": chat_row[0],
        "title": chat_row[1],
        "created_at": str(chat_row[2]),
        "messages": messages,
    }



@app.post("/api/chats", response_model=Chat)
def create_chat(request: CreateChatRequest):
    conn = get_conn()
    try:
        # Create a title for the chat from the first user message
        first_user_message = next(
            (msg for msg in request.messages if msg["role"] == "user"), None
        )
        title = first_user_message["content"][:50] if first_user_message else "New Chat"

        # Insert into chats table
        chat_id = conn.execute(
            "INSERT INTO chats (title) VALUES (?) RETURNING id", [title]
        ).fetchone()[0]

        # Insert messages into chat_messages table
        for message in request.messages:
            conn.execute(
                "INSERT INTO chat_messages (chat_id, role, content) VALUES (?, ?, ?)",
                [chat_id, message["role"], message["content"]],
            )

        chat_row = conn.execute(
            "SELECT id, title, created_at FROM chats WHERE id = ?", [chat_id]
        ).fetchone()

        return {
            "id": chat_row[0],
            "title": chat_row[1],
            "created_at": str(chat_row[2]),
        }
    finally:
        conn.close()


@app.post("/api/chats/{chat_id}/messages")
def add_messages_to_chat(chat_id: int, request: AddMessagesRequest):
    conn = get_conn()
    try:
        # Check if chat exists
        chat_row = conn.execute(
            "SELECT id FROM chats WHERE id = ?", [chat_id]
        ).fetchone()
        if not chat_row:
            raise HTTPException(status_code=404, detail="Chat not found")

        # Insert messages into chat_messages table
        for message in request.messages:
            conn.execute(
                "INSERT INTO chat_messages (chat_id, role, content) VALUES (?, ?, ?)",
                [chat_id, message["role"], message["content"]],
            )

        return {"status": "ok"}
    finally:
        conn.close()
