import io
import os
import tempfile
import pytest
from httpx import AsyncClient, ASGITransport
from PIL import Image, ImageDraw
from main import app


def make_ramq_image(text: str) -> bytes:
    img = Image.new("RGB", (600, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 80), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_ocr_returns_fields_on_valid_image():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/ocr/ramq",
            files={"file": ("test.png", make_ramq_image("GUAN94012812"), "image/png")},
        )
    assert r.status_code == 200
    data = r.json()
    for field in ("prenom", "nom", "numero", "sequentiel", "dob_day", "dob_month", "dob_year"):
        assert field in data


@pytest.mark.asyncio
async def test_ocr_rejects_non_image():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/ocr/ramq",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
    assert r.status_code in (400, 422)


@pytest.mark.asyncio
async def test_ocr_image_not_retained(monkeypatch):
    saved_paths = []
    original_mkstemp = tempfile.mkstemp

    def tracking_mkstemp(*args, **kwargs):
        fd, path = original_mkstemp(*args, **kwargs)
        saved_paths.append(path)
        return fd, path

    monkeypatch.setattr(tempfile, "mkstemp", tracking_mkstemp)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/ocr/ramq",
            files={"file": ("test.png", make_ramq_image("GUAN94012812"), "image/png")},
        )

    for path in saved_paths:
        assert not os.path.exists(path), f"Image not deleted: {path}"
