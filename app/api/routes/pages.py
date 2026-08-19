from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserId
from app.schemas.books import PageUpdate
from app.services.books import owned_book, owned_page
from app.services.supabase import admin_client

router = APIRouter(tags=["pages"])


@router.get("/books/{book_id}/pages")
def list_pages(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    return admin_client.table("book_pages").select("*").eq("book_id", book_id).order("page_number").execute().data


@router.patch("/pages/{page_id}")
def update_page(page_id: str, payload: PageUpdate, user_id: CurrentUserId):
    page = owned_page(page_id, user_id)
    content = {**(page.get("content") or {}), **(payload.content or {})}
    if payload.layout is not None:
        content["layout"] = payload.layout
    if payload.photo_slots is not None:
        content["photoSlots"] = payload.photo_slots
    changes = {"content": content}
    if "background" in payload.model_fields_set:
        changes["background"] = payload.background
    return admin_client.table("book_pages").update(changes).eq("id", page_id).execute().data[0]


@router.post("/books/{book_id}/spreads")
def create_spread(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    pages = admin_client.table("book_pages").select("page_number").eq("book_id", book_id).execute().data
    last_number = max([0, *(page["page_number"] for page in pages)])
    first = last_number + 1 if last_number % 2 == 0 else last_number + 2
    return admin_client.table("book_pages").insert([
        {"book_id": book_id, "page_number": first, "page_type": "standard", "background": None, "content": {}},
        {"book_id": book_id, "page_number": first + 1, "page_type": "standard", "background": None, "content": {}},
    ]).execute().data


@router.post("/books/{book_id}/spreads/initial")
def ensure_initial_spread(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    pages = admin_client.table("book_pages").select("*").eq("book_id", book_id).order("page_number").execute().data
    return pages if pages else create_spread(book_id, user_id)


@router.delete("/books/{book_id}/spreads/{first_page_number}")
def delete_spread(book_id: str, first_page_number: int, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    pages = admin_client.table("book_pages").select("*").eq("book_id", book_id).order("page_number").execute().data
    removed = [p for p in pages if p["page_number"] in (first_page_number, first_page_number + 1)]
    if not removed:
        raise HTTPException(status_code=404, detail="Spread not found.")
    ids = [p["id"] for p in removed]
    admin_client.table("photos").update({"page_id": None}).in_("page_id", ids).execute()
    admin_client.table("book_pages").delete().in_("id", ids).execute()
    remaining = [p for p in pages if p["id"] not in ids]
    for number, page in enumerate(remaining, start=1):
        admin_client.table("book_pages").update({"page_number": number}).eq("id", page["id"]).execute()
        page["page_number"] = number
    return remaining
