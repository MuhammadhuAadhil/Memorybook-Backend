from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUserId
from app.schemas.books import BookCreate, BookUpdate
from app.services.books import ensure_profile, owned_book
from app.services.supabase import admin_client

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
def list_books(user_id: CurrentUserId, status_filter: str | None = None):
    query = admin_client.table("books").select("*").eq("user_id", user_id).order("created_at", desc=True)
    if status_filter:
        query = query.eq("status", status_filter)
    return query.execute().data


@router.post("", status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, user_id: CurrentUserId):
    ensure_profile(user_id)
    return admin_client.table("books").insert({"user_id": user_id, "title": "My MemoryBook", "size": payload.size, "status": "draft"}).execute().data[0]


@router.get("/{book_id}")
def get_book(book_id: str, user_id: CurrentUserId):
    return owned_book(book_id, user_id)


@router.patch("/{book_id}")
def update_book(book_id: str, payload: BookUpdate, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return owned_book(book_id, user_id)
    return admin_client.table("books").update(changes).eq("id", book_id).eq("user_id", user_id).execute().data[0]


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    admin_client.table("books").delete().eq("id", book_id).eq("user_id", user_id).execute()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{book_id}/photo-count")
def count_photos(book_id: str, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    response = admin_client.table("photos").select("id", count="exact").eq("book_id", book_id).execute()
    return {"count": response.count or 0}
