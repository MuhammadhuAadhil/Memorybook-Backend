from io import BytesIO
from uuid import uuid4
import re

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.api.deps import CurrentUserId
from app.schemas.books import PhotoPlacement
from app.services.books import owned_book, owned_page, owned_photo
from app.services.supabase import admin_client

router = APIRouter(tags=["photos"])
BUCKET = "book-photos"


def safe_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "-", filename) or "photo"


@router.get("/books/{book_id}/photos")
def list_photos(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    photos = admin_client.table("photos").select("*").eq("book_id", book_id).order("created_at").execute().data
    for photo in photos:
        signed = admin_client.storage.from_(BUCKET).create_signed_url(photo["storage_path"], 3600)
        photo["name"] = photo["file_name"]
        photo["path"] = photo["storage_path"]
        photo["url"] = signed["signedURL"]
    return photos


@router.post("/books/{book_id}/photos")
async def upload_photo(book_id: str, user_id: CurrentUserId, file: UploadFile = File(...)):
    owned_book(book_id, user_id)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")
    content = await file.read()
    try:
        with Image.open(BytesIO(content)) as image:
            image.load()
            width, height = image.size
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.") from exc
    path = f"{user_id}/{book_id}/{uuid4()}-{safe_filename(file.filename or 'photo')}"
    admin_client.storage.from_(BUCKET).upload(path, content, {"content-type": file.content_type, "upsert": "false"})
    try:
        photo = admin_client.table("photos").insert({
            "book_id": book_id, "page_id": None, "storage_path": path,
            "file_name": file.filename or "photo", "width": width, "height": height,
        }).execute().data[0]
    except Exception:
        admin_client.storage.from_(BUCKET).remove([path])
        raise
    signed = admin_client.storage.from_(BUCKET).create_signed_url(path, 3600)
    photo.update({"name": photo["file_name"], "path": path, "url": signed["signedURL"]})
    return photo


@router.post("/photos/{photo_id}/placement")
def place_photo(photo_id: str, payload: PhotoPlacement, user_id: CurrentUserId):
    photo = owned_photo(photo_id, user_id)
    book_id = photo["book_id"]
    page_ids = [page_id for page_id in [payload.page_id, *(payload.photo_pages or {}).values()] if page_id]
    page_ids.extend(payload.page_slots.keys())
    for page_id in set(page_ids):
        page = owned_page(page_id, user_id)
        if page["book_id"] != book_id:
            raise HTTPException(status_code=400, detail="Photos can only be placed in their own book.")

    # Slot IDs and swapped-photo IDs must belong to this same book. Without
    # this check a request could create invalid cross-book editor state.
    related_photo_ids = {photo_id, *(payload.photo_pages or {}).keys()}
    related_photo_ids.update(slot_id for slots in payload.page_slots.values() for slot_id in slots if slot_id)
    for related_id in related_photo_ids:
        related_photo = owned_photo(related_id, user_id)
        if related_photo["book_id"] != book_id:
            raise HTTPException(status_code=400, detail="Photos can only be placed in their own book.")

    admin_client.table("photos").update({"page_id": payload.page_id}).eq("id", photo_id).execute()
    for other_id, page_id in (payload.photo_pages or {}).items():
        admin_client.table("photos").update({"page_id": page_id}).eq("id", other_id).execute()
    for page_id, slots in payload.page_slots.items():
        page = owned_page(page_id, user_id)
        content = {**(page.get("content") or {}), "photoSlots": slots}
        admin_client.table("book_pages").update({"content": content}).eq("id", page_id).execute()
    return {"ok": True}


@router.delete("/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: str, user_id: CurrentUserId):
    photo = owned_photo(photo_id, user_id)
    admin_client.table("photos").delete().eq("id", photo_id).execute()
    admin_client.storage.from_(BUCKET).remove([photo["storage_path"]])
