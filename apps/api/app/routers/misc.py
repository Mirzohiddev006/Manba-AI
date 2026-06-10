"""Imlo, lookup, lex.uz, PDF, import — qolgan user endpointlar."""

import uuid
from typing import Annotated

import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..config import get_settings
from ..db import get_db
from ..models import PdfTask, User
from ..schemas.api import SpellIn, SpellIssueOut
from ..services import lexuz_service, lookup_service
from ..services.limits import check_and_increment, usage_today

router = APIRouter(prefix="/api/v1", tags=["misc"])


@router.post("/spell/check", response_model=list[SpellIssueOut])
async def spell_check(
    body: SpellIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SpellIssueOut]:
    from citation_core.spell import SpellChecker
    from sqlalchemy import select

    from ..models import DictionaryWord

    res = await db.execute(
        select(DictionaryWord.word).where(DictionaryWord.status == "active")
    )
    checker = SpellChecker(custom_words=set(res.scalars()))
    return [SpellIssueOut(**i.model_dump()) for i in checker.check(body.text)]


@router.post("/lookup/doi")
async def doi(
    doi_value: str, user: Annotated[User, Depends(current_user)]
) -> dict:
    result = await lookup_service.lookup_doi(doi_value)
    if result is None:
        raise HTTPException(404, "DOI topilmadi")
    return result


@router.post("/lookup/isbn")
async def isbn(
    isbn_value: str, user: Annotated[User, Depends(current_user)]
) -> dict:
    result = await lookup_service.lookup_isbn(isbn_value)
    if result is None:
        raise HTTPException(404, "ISBN topilmadi")
    return result


@router.get("/lexuz/search")
async def lexuz_search(
    q: str,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    return await lexuz_service.search(db, q)


@router.post("/pdf/upload")
async def pdf_upload(
    file: UploadFile,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """PDF → S3 → SQS → task_id (TZ 4.3)."""
    await check_and_increment(user, "pdf")
    s = get_settings()
    data = await file.read()
    max_mb = s.pdf_max_mb if user.tariff != "free" else s.free_pdf_max_mb
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"PDF {max_mb} MB dan katta")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Faqat PDF qabul qilinadi")
    key = f"pdf/{user.id}/{uuid.uuid4()}.pdf"
    if s.aws_endpoint_url is None and s.env == "lite":
        raise HTTPException(503, "PDF tahlili yengil rejimda o'chirilgan (S3/SQS yo'q)")
    s3 = boto3.client("s3", region_name=s.aws_region, endpoint_url=s.aws_endpoint_url)
    s3.put_object(Bucket=s.s3_bucket_pdf, Key=key, Body=data, ContentType="application/pdf")
    task = PdfTask(user_id=user.id, s3_key=key)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    sqs = boto3.client("sqs", region_name=s.aws_region, endpoint_url=s.aws_endpoint_url)
    queue_url = sqs.get_queue_url(QueueName=s.sqs_queue_pdf)["QueueUrl"]
    sqs.send_message(QueueUrl=queue_url, MessageBody=str(task.id))
    return {"task_id": task.id, "status": task.status}


@router.get("/pdf/tasks/{task_id}")
async def pdf_task_status(
    task_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    task = await db.get(PdfTask, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(404, "Vazifa topilmadi")
    return {"task_id": task.id, "status": task.status, "result": task.result, "error": task.error}


@router.post("/import/bibtex")
async def import_bibtex(
    file: UploadFile,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Zotero/Mendeley .bib import (TZ 16.7)."""
    import bibtexparser

    from ..services.parse_service import parse_and_store

    text = (await file.read()).decode("utf-8", errors="replace")
    bib = bibtexparser.loads(text)
    raws = []
    for entry in bib.entries:
        parts = [
            entry.get("author", "").replace(" and ", ", "),
            entry.get("title", ""),
            entry.get("journal", ""),
            entry.get("year", ""),
        ]
        raws.append(". ".join(p for p in parts if p))
    rows = await parse_and_store(db, user.id, "\n".join(raws))
    return {"imported": len(rows)}


@router.post("/import/ris")
async def import_ris(
    file: UploadFile,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    import rispy

    from ..services.parse_service import parse_and_store

    text = (await file.read()).decode("utf-8", errors="replace")
    entries = rispy.loads(text)
    raws = []
    for e in entries:
        authors = ", ".join(e.get("authors", []))
        parts = [authors, e.get("title", ""), e.get("journal_name", ""), str(e.get("year", ""))]
        raws.append(". ".join(p for p in parts if p))
    rows = await parse_and_store(db, user.id, "\n".join(raws))
    return {"imported": len(rows)}


@router.post("/feedback", status_code=201)
async def send_feedback(
    body: dict,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    from ..models import Feedback

    fb = Feedback(user_id=user.id, text=str(body.get("text", ""))[:4000])
    db.add(fb)
    await db.commit()
    return {"id": fb.id}


@router.get("/me")
async def me(user: Annotated[User, Depends(current_user)]) -> dict:
    usage = await usage_today(user)
    return {
        "tg_id": user.tg_id, "first_name": user.first_name, "lang": user.lang,
        "script": user.script, "tariff": user.tariff,
        "tariff_expires_at": user.tariff_expires_at, "usage_today": usage,
    }
