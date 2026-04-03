import os
import re
import tempfile

import pytesseract
from fastapi import APIRouter, HTTPException, UploadFile, File
from PIL import Image

router = APIRouter(prefix="/ocr", tags=["ocr"])

_NUMERO_RE = re.compile(r'\b([A-Z]{4}\d{8})\b', re.IGNORECASE)
_SEQ_RE = re.compile(r'\b(\d{2})\b')
_DATE_RE = re.compile(r'\b(\d{1,2})[/\-\s](\d{1,2})[/\-\s](\d{4})\b')


def _extract_fields(text: str) -> dict:
    result = {
        "prenom": "", "nom": "", "numero": "",
        "sequentiel": "", "dob_day": "", "dob_month": "", "dob_year": "",
    }
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    numero_match = _NUMERO_RE.search(text.upper())
    if numero_match:
        result["numero"] = numero_match.group(1)
        after = text[numero_match.end():]
        seq = _SEQ_RE.search(after)
        if seq:
            result["sequentiel"] = seq.group(1)

    date_match = _DATE_RE.search(text)
    if date_match:
        result["dob_day"] = date_match.group(1).zfill(2)
        result["dob_month"] = date_match.group(2).zfill(2)
        result["dob_year"] = date_match.group(3)

    name_lines = [
        ln for ln in lines
        if ln.isupper()
        and not _NUMERO_RE.search(ln)
        and not any(c.isdigit() for c in ln)
        and 1 <= len(ln.split()) <= 5
        and len(ln) <= 40
    ]
    if len(name_lines) >= 2:
        result["nom"] = name_lines[0]
        result["prenom"] = name_lines[1]
    elif len(name_lines) == 1:
        parts = name_lines[0].split()
        result["nom"] = parts[0]
        result["prenom"] = " ".join(parts[1:])

    return result


@router.post("/ramq")
async def ocr_ramq(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    fd, tmp_path = tempfile.mkstemp(suffix=".png")
    try:
        content = await file.read()
        with os.fdopen(fd, "wb") as f:
            f.write(content)

        try:
            img = Image.open(tmp_path)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not open image")

        try:
            text = pytesseract.image_to_string(img, lang="fra+eng")
        except Exception:
            text = ""

        return _extract_fields(text)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
