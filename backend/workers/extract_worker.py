import json
import logging
import os

import requests

PARALLAX_CHAT = "http://localhost:3001/v1/chat/completions"

EXTRACTION_PROMPT = """
Extract the following fields from this resume:

- Full Name
- Email
- Phone
- Total Experience in working
- Skills (as a list)
- Education summary
- Professional Summary

Return JSON only, no explanation, no markdown.
Resume:
{resume_text}
"""


def extract_fields(resume_text: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(resume_text=resume_text)
    url = PARALLAX_CHAT
    json_data = {
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    response = requests.post(url, json=json_data)

    data = response.json()
    try:
        content = data["choices"][0]["messages"]["content"]
        logging.info("Parallax content ->", content)

    except KeyError as e:
        return {"error": "Unexpected response format", "raw": data}

    try:
        return {"status": "ok", "message": content}

    except:
        return {
            "status": "error",
            "error": "Failed to parse JSON, here is raw output",
            "raw": content,
        }
