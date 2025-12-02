import os

from doctr.io import DocumentFile
from doctr.models import ocr_predictor

model = ocr_predictor(pretrained=True)


def extract_text(file_path: str) -> str:
    # Load document (PDF or image)
    doc = (
        DocumentFile.from_pdf(file_path)
        if file_path.lower().endswith(".pdf")
        else DocumentFile.from_images(file_path)
    )

    # Analyze document
    result = model(doc)

    # Extract text
    text_lines = []
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                line_text = " ".join([word.value for word in line.words])
                text_lines.append(line_text)

    return "\n".join(text_lines)