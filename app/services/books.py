from fastapi import HTTPException, status

from app.services.supabase import admin_client


def data_or_404(response, message: str):
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return response.data[0] if isinstance(response.data, list) else response.data


def owned_book(book_id: str, user_id: str) -> dict:
    response = admin_client.table("books").select("*").eq("id", book_id).eq("user_id", user_id).limit(1).execute()
    return data_or_404(response, "Book not found.")


def owned_page(page_id: str, user_id: str) -> dict:
    response = admin_client.table("book_pages").select("*, books!inner(user_id)").eq("id", page_id).eq("books.user_id", user_id).limit(1).execute()
    return data_or_404(response, "Page not found.")


def owned_photo(photo_id: str, user_id: str) -> dict:
    response = admin_client.table("photos").select("*, books!inner(user_id)").eq("id", photo_id).eq("books.user_id", user_id).limit(1).execute()
    return data_or_404(response, "Photo not found.")
