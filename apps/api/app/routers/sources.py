"""/api/v1/sources — tahlil va tahrirlash."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..db import get_db
from ..models import Source, User
from ..schemas.api import ParseIn, ParseOut, SourceOut, SourcePatch
from ..services.limits import check_and_increment
from ..services.parse_service import build_pipeline, parse_and_store, reformat

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


def _to_out(row: Source, parsed=None) -> SourceOut:
    return SourceOut(
        id=row.id,
        raw_input=row.raw_input,
        source_type=row.source_type.value,
        fields=row.fields,
        formatted_text=row.formatted_text,
        confidence=row.confidence,
        field_confidence=parsed.field_confidence if parsed else {},
        parse_method=row.parse_method,
        warnings=parsed.warnings if parsed else [],
    )


@router.post("/parse", response_model=ParseOut)
async def parse(
    body: ParseIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ParseOut:
    await check_and_increment(user, "source")
    rows = await parse_and_store(db, user.id, body.text)
    return ParseOut(sources=[_to_out(r, p) for r, p in rows])


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    source_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceOut:
    row = await db.get(Source, source_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "Manba topilmadi")
    return _to_out(row)


@router.patch("/{source_id}", response_model=SourceOut)
async def patch_source(
    source_id: int,
    body: SourcePatch,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceOut:
    row = await db.get(Source, source_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "Manba topilmadi")
    if body.source_type:
        row.source_type = body.source_type
    if body.fields is not None:
        row.fields = {**row.fields, **body.fields}
    pipe = await build_pipeline(db)
    try:
        row.formatted_text = reformat(row, pipe.engine)  # jonli preview — faqat shablon motori
    except Exception as e:
        raise HTTPException(422, f"Maydon qiymati yaroqsiz: {e}") from e
    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.get(Source, source_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "Manba topilmadi")
    await db.delete(row)
    await db.commit()
