from dotenv import load_dotenv

load_dotenv()

import asyncio
import json
import logging
import os
import re
import shutil
import uuid

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from typing import Any, Dict, List, Optional, Tuple

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
PARALLAX_HOST = os.environ.get("PARALLAX_HOST", "http://localhost:3001")

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


# --- Helper functions (included here so you can paste as a single block) ---
def try_extract_json_from_raw(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to salvage structured JSON from parsed['raw'] (OpenAI-style response).
    Returns dict if successful, else empty dict.
    """
    raw = parsed.get("raw") if isinstance(parsed, dict) else None
    if not raw:
        return {}

    try:
        choices = raw.get("choices") or []
        if not choices:
            return {}

        content = None
        for choice in choices:
            msg = choice.get("message") or {}
            c = msg.get("content")
            if c:
                content = c
                break
        if not content:
            return {}

        content = content.strip()

        # Remove code fences if present
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        # Try direct json.loads
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except Exception:
            # fallback: extract substring from first '{' to last '}' and try load
            m = re.search(r"(\{.*\})", content, re.DOTALL)
            if m:
                candidate = m.group(1)
                # common fixes: remove trailing commas before closing braces/brackets
                candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict):
                        return data
                except Exception as e:
                    logging.warning("Could not json.loads candidate, error: %s", e)

    except Exception as e:
        logging.exception("Failed to extract JSON from raw: %s", e)

    return {}


KEY_MAPPING = {
    "full name": "Full Name",
    "fullname": "Full Name",
    "Full Name": "Full Name",
    "name": "Full Name",
    "email": "Email",
    "Email": "Email",
    "phone": "Phone",
    "Phone": "Phone",
    "phone number": "Phone",
    "skills": "Skills",
    "Skills (as a list)": "Skills",
    "Skills": "Skills",
    "total experience": "Total Experience",
    "Total Experience in working": "Total Experience",
    "Total Experience": "Total Experience",
    "education summary": "Education Summary",
    "Education summary": "Education Summary",
    "Education Summary": "Education Summary",
    "professional summary": "Professional Summary",
    "Professional Summary": "Professional Summary",
    "Professional summary": "Professional Summary",
}

# small mapping of common variant keys -> canonical keys
_KEY_VARIANTS = {
    "full name": ["Full Name", "fullname", "name", "candidate_name", "candidateName"],
    "email": ["Email", "email", "e-mail", "contact_email"],
    "phone": ["Phone", "phone", "phone number", "contact_number", "mobile"],
    "skills": ["Skills", "skills", "Skills (as a list)", "skillset"],
    "total_experience": [
        "Total Experience",
        "Total Experience in working",
        "Experience",
        "TotalExperience",
    ],
    "education": [
        "Education Summary",
        "Education summary",
        "Education",
        "education_summary",
    ],
    "professional": [
        "Professional Summary",
        "Professional summary",
        "Summary",
        "professional_summary",
    ],
}


def normalize_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if not isinstance(k, str):
            continue
        key_l = k.strip()
        mapped = KEY_MAPPING.get(key_l) or KEY_MAPPING.get(key_l.lower())
        if mapped:
            out[mapped] = v
        else:
            out[k] = v
    return out


# Endpoint: health
@app.get("/health")
def health():
    return {"status": "ok"}


def _find_variant(parsed: Dict[str, Any], variants: list):
    """Return the first non-empty value for any key variant, else None."""
    for k in variants:
        if k in parsed:
            val = parsed[k]
            if val is None:
                continue
            # treat empty strings or empty lists as missing
            if isinstance(val, str) and len(val.strip()) == 0:
                continue
            if isinstance(val, (list, dict)) and len(val) == 0:
                continue
            return val
    return None


def _extract_email_from_text(text: str):
    if not text:
        return None
    # looser search for emails anywhere in text
    m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def _extract_phone_from_text(text: str):
    if not text:
        return None
    # Accept common international formats, spaces, dashes, parentheses.
    # We look for sequences of digits with optional + at start, min length 7
    m = re.search(r"(\+?\d[\d\-\s().]{6,}\d)", text)
    if not m:
        return None
    # Clean up extracted phone
    phone = re.sub(r"[^\d+]", " ", m.group(1)).strip()
    return phone


def _extract_name_from_text(text: str):
    if not text:
        return None
    # Heuristic: take the first non-empty line that contains 2 words and letters (likely name)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines[:10]:  # only check the top portion
        # ignore lines that look like emails or phones or contain too many chars
        if re.search(r"@", ln) or re.search(r"\d", ln):
            continue
        # if line has 2-4 space-separated words and words are alphabetic-ish, choose it
        parts = ln.split()
        if 1 < len(parts) <= 4 and all(re.search(r"[A-Za-z]", p) for p in parts):
            # sanity length check
            joined = " ".join(parts)
            if 3 <= len(joined) <= 60:
                return joined
    return None


def validate_parsed_data(parsed: dict, raw_text: str) -> Tuple[bool, str]:
    """
    Validate parsed resume data and return (is_valid, error_message).

    - Accepts common key variants
    - Attempts to salvage name/phone/email from raw_text
    - Scores fields with weights and enforces minimal required fields
    """
    # 0. Basic raw text sanity
    if not raw_text or len(raw_text.strip()) < 50:
        return False, "Extracted text too short (< 50 chars). Resume may be unreadable."

    # 1. canonicalize: try to find values for each logical field using variants
    canonical: Dict[str, Any] = {}

    canonical["Full Name"] = _find_variant(parsed, _KEY_VARIANTS["full name"])
    canonical["Email"] = _find_variant(parsed, _KEY_VARIANTS["email"])
    canonical["Phone"] = _find_variant(parsed, _KEY_VARIANTS["phone"])
    canonical["Skills"] = _find_variant(parsed, _KEY_VARIANTS["skills"])
    canonical["Total Experience"] = _find_variant(
        parsed, _KEY_VARIANTS["total_experience"]
    )
    canonical["Education Summary"] = _find_variant(parsed, _KEY_VARIANTS["education"])
    canonical["Professional Summary"] = _find_variant(
        parsed, _KEY_VARIANTS["professional"]
    )

    # 2. salvage from raw_text if missing (email/phone/name)
    if not canonical["Email"]:
        canonical["Email"] = _extract_email_from_text(raw_text)
    if not canonical["Phone"]:
        canonical["Phone"] = _extract_phone_from_text(raw_text)
    if not canonical["Full Name"]:
        canonical["Full Name"] = _extract_name_from_text(raw_text)

    # 3. Normalize skill field: allow comma-separated string or list-of-strings
    skills_val = canonical.get("Skills")
    normalized_skills = []
    if isinstance(skills_val, list):
        for it in skills_val:
            if isinstance(it, str):
                # split comma-separated entries inside list items
                normalized_skills += [s.strip() for s in it.split(",") if s.strip()]
    elif isinstance(skills_val, str):
        normalized_skills = [s.strip() for s in skills_val.split(",") if s.strip()]
    elif skills_val is None:
        normalized_skills = []
    else:
        # fallback: try to coerce to str
        normalized_skills = [str(skills_val)]

    canonical["Skills"] = normalized_skills

    # 4. scoring setup
    field_weights = {
        "Full Name": 2,
        "Email": 2,
        "Phone": 1,
        "Skills": 2,
        "Total Experience": 2,
        "Education Summary": 1,
        "Professional Summary": 1,
    }

    score = 0
    present_fields = set()

    # helpers for email/phone detection
    def is_valid_email(v):
        if not v:
            return False
        return bool(
            re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", str(v))
        )

    def is_valid_phone(v):
        if not v:
            return False
        return bool(re.search(r"\+?\d[\d\-\s().]{6,}\d", str(v)))

    for field, weight in field_weights.items():
        value = canonical.get(field)
        valid = False

        if value is None:
            valid = False
        elif field == "Email":
            if is_valid_email(value):
                valid = True
        elif field == "Phone":
            if is_valid_phone(value):
                valid = True
        elif field == "Skills":
            if isinstance(value, list) and len(value) > 0:
                valid = True
        elif isinstance(value, str) and len(value.strip()) > 0:
            valid = True
        elif isinstance(value, (int, float)):
            valid = True
        else:
            valid = False

        if valid:
            score += weight
            present_fields.add(field)

    total_weight = sum(field_weights.values())
    score_ratio = score / total_weight if total_weight > 0 else 0.0
    logger.info(
        f" Validation - Score: {score}/{total_weight} ({score_ratio:.2f}) | Fields: {present_fields}"
    )

    # 5. Critical failures (must have a name and at least one contact)
    errors = []
    if "Full Name" not in present_fields:
        errors.append("Missing 'Full Name'")

    if "Email" not in present_fields and "Phone" not in present_fields:
        errors.append("Missing contact info (Email or Phone)")

    if errors:
        return False, f"Validation failed: {'; '.join(errors)}"

    # 6. Overall Quality Threshold (40%)
    if score_ratio < 0.4:
        return (
            False,
            "Insufficient data extracted (Score too low). Resume details are sparse.",
        )

    # If passed, you may wish to return the canonicalized fields back to the caller;
    # but for compatibility we keep the same signature.
    return True, ""


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

            salvaged = try_extract_json_from_raw(
                parsed if isinstance(parsed, dict) else {}
            )
            if salvaged:
                logging.info(
                    "Salvaged JSON from raw assistant content for %s", file.filename
                )
                normalized = normalize_keys(salvaged)

                # Normalize Skills -> list of strings
                skills = normalized.get("Skills")
                if isinstance(skills, list):
                    flattened = []
                    for item in skills:
                        if isinstance(item, str):
                            flattened += [
                                s.strip() for s in item.split(",") if s.strip()
                            ]
                    normalized["Skills"] = flattened
                elif isinstance(skills, str):
                    normalized["Skills"] = [
                        s.strip() for s in skills.split(",") if s.strip()
                    ]
                else:
                    normalized["Skills"] = []

                te = normalized.get("Total Experience")
                normalized["Total Experience"] = (
                    te.strip() if isinstance(te, str) else None
                )

                parsed = {
                    "Full Name": normalized.get("Full Name"),
                    "Email": normalized.get("Email"),
                    "Phone": normalized.get("Phone"),
                    "Skills": normalized.get("Skills", []),
                    "Total Experience": normalized.get("Total Experience"),
                    "Education Summary": normalized.get("Education Summary"),
                    "Professional Summary": normalized.get("Professional Summary"),
                    # keep original raw if present
                    "raw": parsed.get("raw") if isinstance(parsed, dict) else None,
                }
            else:
                logging.warning(
                    "Could not salvage JSON; using fallback for %s", file.filename
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

        # logging.info(f"👉 Parsed text {parsed}")
        # logging.info(f"👉 Raw text {raw_text}")

        is_valid, error_message = validate_parsed_data(parsed, raw_text)

        # logging.info(f"👉 is_valid text {is_valid}")
        # logging.info(f"👉 error_message text {error_message}")

        if not is_valid:
            logging.error(f"Validation failed for {file.filename}: {error_message}")
            return {
                "status": "error",
                "filename": file.filename,
                "detail": error_message,
            }

        # 3) Embedding
        emb = embed_worker.embed_text(raw_text)
        logging.info(f"🚀 Embedding complete for {file.filename}")

        # logging.info(f"🚀 PParsed for {parsed}")

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
