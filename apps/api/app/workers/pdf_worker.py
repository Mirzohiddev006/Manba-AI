"""PDF worker — SQS dan vazifa oladi, adabiyotlar bo'limini topadi, quvurga beradi.

Oqim (TZ 4.3, 16.9): S3 dan PDF → matn qatlami bormi? yo'q → Tesseract OCR
(uzb, uzb_cyrl, rus, eng) → adabiyotlar bo'limi → har satr citation-core ga.
"""

from __future__ import annotations

import asyncio
import logging
import re

import boto3

from ..config import get_settings
from ..db import SessionLocal
from ..models import OcrTask, PdfTask
from ..services.parse_service import parse_and_store

log = logging.getLogger("pdf_worker")

# Adabiyotlar bo'limi sarlavhalari (uz-lotin/kirill/ru/en)
_REF_HEADING = re.compile(
    r"^\s*(?:FOYDALANILGAN\s+ADABIYOTLAR|АДАБИЁТЛАР|ФОЙДАЛАНИЛГАН|"
    r"СПИСОК\s+(?:ИСПОЛЬЗОВАННОЙ\s+)?ЛИТЕРАТУРЫ|REFERENCES|BIBLIOGRAPHY)",
    re.IGNORECASE | re.MULTILINE,
)


def extract_text(pdf_bytes: bytes) -> tuple[str, bool]:
    """Qaytaradi: (matn, ocr_ishlatildimi)."""
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text.strip()) > 200:
        return text, False
    # Matn qatlami yo'q — OCR (premium, TZ 16.9)
    return _ocr(pdf_bytes), True


def _ocr(pdf_bytes: bytes) -> str:
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    if not shutil.which("tesseract") or not shutil.which("pdftoppm"):
        log.warning("tesseract/poppler yo'q — OCR o'tkazib yuborildi")
        return ""
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "in.pdf"
        pdf.write_bytes(pdf_bytes)
        subprocess.run(  # noqa: S603, S607
            ["pdftoppm", "-r", "300", "-png", str(pdf), str(Path(td) / "p")], check=True
        )
        chunks = []
        for img in sorted(Path(td).glob("p*.png")):
            out = subprocess.run(  # noqa: S603, S607
                ["tesseract", str(img), "-", "-l", "uzb+uzb_cyrl+rus+eng"],
                capture_output=True, text=True, check=False,
            )
            chunks.append(out.stdout)
        return "\n".join(chunks)


def find_references_section(text: str) -> str:
    """Adabiyotlar bo'limini topadi; topilmasa raqamlangan satrlar blokini qidiradi."""
    m = _REF_HEADING.search(text)
    if m:
        return text[m.end():]
    # Zaxira: ko'p raqamlangan satrli dum qismi
    lines = text.splitlines()
    numbered = [i for i, ln in enumerate(lines) if re.match(r"^\s*\d{1,3}[.)]\s+\S", ln)]
    if len(numbered) >= 5:
        return "\n".join(lines[numbered[0]:])
    return ""


async def process_task(task_id: int) -> None:
    s = get_settings()
    s3 = boto3.client("s3", region_name=s.aws_region, endpoint_url=s.aws_endpoint_url)
    async with SessionLocal() as db:
        task = await db.get(PdfTask, task_id)
        if task is None:
            return
        task.status = "processing"
        await db.commit()
        try:
            obj = s3.get_object(Bucket=s.s3_bucket_pdf, Key=task.s3_key)
            text, used_ocr = extract_text(obj["Body"].read())
            if used_ocr:
                db.add(OcrTask(pdf_task_id=task.id, engine="tesseract", status="done"))
            refs = find_references_section(text)
            if not refs.strip():
                task.status = "done"
                task.result = {"sources": [], "unparsed": [], "note": "Adabiyotlar bo'limi topilmadi"}
                await db.commit()
                return
            rows = await parse_and_store(db, task.user_id, refs)
            ok = [
                {"id": r.id, "formatted_text": r.formatted_text, "confidence": r.confidence,
                 "source_type": r.source_type.value}
                for r, p in rows if r.confidence >= 0.4
            ]
            unparsed = [r.raw_input for r, p in rows if r.confidence < 0.4]
            task.status = "done"
            task.result = {"sources": ok, "unparsed": unparsed, "ocr": used_ocr}
        except Exception as e:
            log.exception("PDF tahlil xatosi")
            task.status = "error"
            task.error = str(e)[:500]
        await db.commit()


async def main() -> None:
    """SQS long-polling tsikli."""
    s = get_settings()
    sqs = boto3.client("sqs", region_name=s.aws_region, endpoint_url=s.aws_endpoint_url)
    queue_url = sqs.get_queue_url(QueueName=s.sqs_queue_pdf)["QueueUrl"]
    log.info("PDF worker ishga tushdi: %s", queue_url)
    while True:
        resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=20)
        for msg in resp.get("Messages", []):
            try:
                await process_task(int(msg["Body"]))
            finally:
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
        await asyncio.sleep(0)


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(main())
