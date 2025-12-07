import json
import logging
import os
import re
from typing import Any, Dict

import requests

PARALLAX_CHAT = "http://localhost:3001/v1/chat/completions"


EXTRACTION_PROMPT = """
Extract the following fields from this resume and return ONLY valid JSON:

- Full Name
- Email
- Phone
- Total Experience in working
- Skills (as a list)
- Education summary
- Professional Summary

Return ONLY the JSON object, no markdown, no explanation.

Resume:
{resume_text}
"""


def clean_response_content(content: str) -> str:
    """Clean and extract JSON from response content."""
    # Remove markdown code blocks if present
    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"\s*```", "", content)
    # Remove any leading/trailing whitespace
    return content.strip()


def extract_fields(resume_text: str) -> Dict[str, Any]:
    """
    Extract fields from resume text using Parallax API.

    Returns normalized dictionary with the requested format.
    """
    try:
        prompt = EXTRACTION_PROMPT.format(resume_text=resume_text)
        url = PARALLAX_CHAT

        json_data = {
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        }

        response = requests.post(url, json=json_data, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract content from response
        if "choices" not in data or not data["choices"]:
            raise ValueError("No choices in response")

        choice = data["choices"][0]
        content = ""

        # Handle different response formats
        if "message" in choice:
            content = choice["message"]["content"]
        elif "messages" in choice:
            content = choice["messages"]["content"]
        else:
            raise ValueError("Unexpected response format")

        logging.info(
            "Parallax content received: %s",
            content[:200] + "..." if len(content) > 200 else content,
        )

        cleaned_content = clean_response_content(content)

        try:
            extracted_data = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logging.error("JSON decode error: %s", str(e))
            return {
                "status": "error",
                "error": "Failed to parse JSON response",
                "Full Name": "",
                "Email": "",
                "Phone": "",
                "Skills": [],
                "Total Experience": "",
                "Education Summary": "",
                "Professional Summary": "",
                "raw_text": resume_text,
            }

        # Normalize the data to the requested format
        normalized = {
            "Full Name": extracted_data.get(
                "Full Name", extracted_data.get("full_name", "")
            ),
            "Email": extracted_data.get("Email", extracted_data.get("email", "")),
            "Phone": extracted_data.get("Phone", extracted_data.get("phone", "")),
            "Skills": extracted_data.get("Skills", extracted_data.get("skills", [])),
            "Total Experience": extracted_data.get(
                "Total Experience", extracted_data.get("total_experience", "")
            ),
            "Education Summary": extracted_data.get(
                "Education Summary", extracted_data.get("education_summary", "")
            ),
            "Professional Summary": extracted_data.get(
                "Professional Summary", extracted_data.get("professional_summary", "")
            ),
            "raw_text": resume_text,
        }

        return {"status": "ok", "data": normalized}

    except requests.exceptions.RequestException as e:
        logging.error("Request error: %s", str(e))
        return {
            "status": "error",
            "error": f"API request failed: {str(e)}",
            "Full Name": "",
            "Email": "",
            "Phone": "",
            "Skills": [],
            "Total Experience": "",
            "Education Summary": "",
            "Professional Summary": "",
            "raw_text": "",
        }

    except Exception as e:
        logging.error("Unexpected error: %s", str(e))
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "Full Name": "",
            "Email": "",
            "Phone": "",
            "Skills": [],
            "Total Experience": "",
            "Education Summary": "",
            "Professional Summary": "",
            "raw_text": "",
        }
