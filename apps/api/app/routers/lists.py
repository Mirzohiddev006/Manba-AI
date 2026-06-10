"""/api/v1/lists — CRUD, tartiblash, eksport, ulashish, translit, havola tekshiruvi."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import current_user
from ..db import get_db
from ..models import ItemComment, ListItem, ListShare, ReferenceList, Source, User
from ..schemas.api import (
    CommentIn,
    ExportIn,
    ListCreate,
    ListDetailOut,
    ListItemOut,
    ListOut,
    ReorderIn,
    ShareIn,
)
from ..services import citations_check
from ..services.export_service import export_list

router = APIRouter(prefix="/api/v1/lists", tags=["lists"])


async def _owned_list(
    list_id: int, user: User, db: AsyncSession, *, with_items: bool = False
) -> ReferenceList:
    q = select(ReferenceList).where(ReferenceList.id == list_id)
    if with_items:
        q = q.options(selectinload(ReferenceList.items).selectinload(ListItem.source))
    res = await db.execute(q)
    ref = res.scalar_one_or_none()
    if ref is None or ref.user_id != user.id:
        raise HTTPException(404, "Ro'yxat topilmadi")
    return ref


def _item_out(item: ListItem) -> ListItemOut:
    s = item.source
    return ListItemOut(
        id=item.id, position=item.position, group_no=item.group_no,
        source={
            "id": s.id, "raw_input": s.raw_input, "source_type": s.source_type.value,
            "fields": s.fields, "formatted_text": s.formatted_text,
            "confidence": s.confidence, "parse_method": s.parse_method,
        },
    )


@router.get("", response_model=list[ListOut])
async def my_lists(
    user: Annotated[User, Depends(current_user)], db: Annotated[AsyncSession, Depends(get_db)]
) -> list[ListOut]:
    res = await db.execute(
        select(ReferenceList)
        .where(ReferenceList.user_id == user.id)
        .options(selectinload(ReferenceList.items))
        .order_by(ReferenceList.updated_at.desc())
    )
    return [
        ListOut(
            id=lst.id, title=lst.title, grouping_mode=lst.grouping_mode,
            sort_mode=lst.sort_mode, items_count=len(lst.items), updated_at=lst.updated_at,
        )
        for lst in res.scalars()
    ]


@router.post("", response_model=ListOut, status_code=201)
async def create_list(
    body: ListCreate,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ListOut:
    lst = ReferenceList(user_id=user.id, title=body.title, grouping_mode=body.grouping_mode)
    db.add(lst)
    await db.commit()
    await db.refresh(lst)
    return ListOut(
        id=lst.id, title=lst.title, grouping_mode=lst.grouping_mode, sort_mode=lst.sort_mode
    )


@router.get("/{list_id}", response_model=ListDetailOut)
async def get_list(
    list_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ListDetailOut:
    lst = await _owned_list(list_id, user, db, with_items=True)
    return ListDetailOut(
        id=lst.id, title=lst.title, grouping_mode=lst.grouping_mode, sort_mode=lst.sort_mode,
        items_count=len(lst.items), updated_at=lst.updated_at,
        items=[_item_out(i) for i in lst.items],
    )


@router.patch("/{list_id}", response_model=ListOut)
async def rename_list(
    list_id: int,
    body: ListCreate,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ListOut:
    lst = await _owned_list(list_id, user, db)
    lst.title = body.title
    lst.grouping_mode = body.grouping_mode
    await db.commit()
    return ListOut(
        id=lst.id, title=lst.title, grouping_mode=lst.grouping_mode, sort_mode=lst.sort_mode
    )


@router.delete("/{list_id}", status_code=204)
async def delete_list(
    list_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    lst = await _owned_list(list_id, user, db)
    await db.delete(lst)
    await db.commit()


@router.post("/{list_id}/items/{source_id}", response_model=ListItemOut, status_code=201)
async def add_item(
    list_id: int,
    source_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ListItemOut:
    lst = await _owned_list(list_id, user, db, with_items=True)
    src = await db.get(Source, source_id)
    if src is None or src.user_id != user.id:
        raise HTTPException(404, "Manba topilmadi")
    from citation_core.sorting import GROUP_LEGAL, GROUP_MAIN, GROUP_WEB

    group = {"legal": GROUP_LEGAL, "web": GROUP_WEB}.get(src.source_type.value, GROUP_MAIN)
    item = ListItem(list_id=lst.id, source_id=src.id, position=len(lst.items), group_no=group)
    db.add(item)
    await db.commit()
    await _resort(lst.id, db)
    await db.refresh(item)
    return _item_out(item)


async def _resort(list_id: int, db: AsyncSession) -> None:
    """Avto-saralash: OAK tartibida pozitsiyalarni yangilash."""
    from citation_core import collation_key

    res = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .options(selectinload(ListItem.source))
    )
    items = list(res.scalars())

    def key(item: ListItem):
        f = item.source.fields or {}
        authors = f.get("authors") or []
        head = authors[0]["surname"] if authors else f.get("title", "")
        return (item.group_no, collation_key(head or ""))

    for pos, item in enumerate(sorted(items, key=key)):
        item.position = pos
    await db.commit()


@router.post("/{list_id}/reorder", status_code=204)
async def reorder(
    list_id: int,
    body: ReorderIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    lst = await _owned_list(list_id, user, db, with_items=True)
    lst.sort_mode = "manual"
    positions = {item_id: pos for pos, item_id in enumerate(body.item_ids)}
    for item in lst.items:
        if item.id in positions:
            item.position = positions[item.id]
    await db.commit()


@router.delete("/{list_id}/items/{item_id}", status_code=204)
async def remove_item(
    list_id: int,
    item_id: int,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await _owned_list(list_id, user, db)
    item = await db.get(ListItem, item_id)
    if item is None or item.list_id != list_id:
        raise HTTPException(404, "Element topilmadi")
    await db.delete(item)
    await db.commit()


@router.post("/{list_id}/export")
async def export(
    list_id: int,
    body: ExportIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    lst = await _owned_list(list_id, user, db, with_items=True)
    content, filename, ctype = await export_list(
        db, lst, body.fmt, script=body.script, font_size=body.font_size
    )
    data = content.encode() if isinstance(content, str) else content
    return Response(
        content=data,
        media_type=ctype,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{list_id}/transliterate")
async def transliterate(
    list_id: int,
    direction: str,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """direction: cyr2lat | lat2cyr. Butun ro'yxat bir bosishda (TZ 16.4)."""
    from citation_core.translit import Transliterator

    from ..models import DictionaryWord

    res = await db.execute(
        select(DictionaryWord.word).where(DictionaryWord.category == "atoqli_ot")
    )
    tr = Transliterator(exceptions=set(res.scalars()))
    fn = tr.cyr_to_lat if direction == "cyr2lat" else tr.lat_to_cyr
    lst = await _owned_list(list_id, user, db, with_items=True)
    changed = 0
    for item in lst.items:
        item.source.formatted_text = fn(item.source.formatted_text)
        changed += 1
    await db.commit()
    return {"changed": changed}


@router.post("/{list_id}/check-citations")
async def check_citations(
    list_id: int,
    file: UploadFile,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Dissertatsiya .docx dagi [N] havolalarni ro'yxat bilan solishtirish (TZ 16.3)."""
    lst = await _owned_list(list_id, user, db, with_items=True)
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Fayl juda katta")
    return citations_check.check(data, list_size=len(lst.items))


@router.post("/{list_id}/share")
async def share(
    list_id: int,
    body: ShareIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await _owned_list(list_id, user, db)
    token = secrets.token_urlsafe(16)
    expires = (
        datetime.now(UTC) + timedelta(days=body.expires_days) if body.expires_days else None
    )
    db.add(
        ListShare(
            list_id=list_id, token=token, permission=body.permission,
            created_by=user.id, expires_at=expires,
        )
    )
    await db.commit()
    return {"token": token, "link": f"https://t.me/ManbaAIBot?start=share_{token}"}


@router.post("/items/{item_id}/comments", status_code=201)
async def add_comment(
    item_id: int,
    body: CommentIn,
    user: Annotated[User, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    item = await db.get(ListItem, item_id)
    if item is None:
        raise HTTPException(404, "Element topilmadi")
    comment = ItemComment(list_item_id=item_id, author_user_id=user.id, text=body.text)
    db.add(comment)
    await db.commit()
    return {"id": comment.id}
