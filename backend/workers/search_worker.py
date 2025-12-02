import logging
import os
import json

import duckdb
import requests

from .embed_worker import embed_text


def search_candidates(query: str):
    # 1. Local MLX embedding
    q_embed = embed_text(query)

    if not q_embed:
        return []

    # 2. DuckDB vector similarity search
    conn = duckdb.connect("db/candidates.duckdb", read_only=True)

    rows = conn.execute(
        """
        SELECT
            id,
            name,
            email,
            phone,
            experience_years,
            skills,
            education_summary,
            professional_summary,
            embedding <-> ? AS distance
        FROM candidates
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT 3
    """,
        [q_embed],
    ).fetchall()

    conn.close()

    if not rows:
        return []

    logging.info("Candidates Result 🙍 -> %s", rows)

    # 3. Format results into a list of dictionaries
    results = []
    column_names = [
        "id",
        "name",
        "email",
        "phone",
        "experience_years",
        "skills",
        "education_summary",
        "professional_summary",
        "distance",
    ]
    for row in rows:
        candidate = dict(zip(column_names, row))
        # Parse skills from JSON string to list
        try:
            if candidate["skills"]:
                candidate["skills"] = json.loads(candidate["skills"])
            else:
                candidate["skills"] = []
        except (json.JSONDecodeError, TypeError):
            # If skills is not valid JSON or not a string, default to empty list
            candidate["skills"] = []
        results.append(candidate)

    return results
