from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserId
from app.schemas.books import AddressCreate, OrderCreate
from app.services.books import data_or_404, owned_book
from app.services.supabase import admin_client

router = APIRouter(tags=["orders"])
PRICE_PER_PAGE = 150


@router.get("/checkout/{book_id}")
def checkout_data(book_id: str, user_id: CurrentUserId):
    book = owned_book(book_id, user_id)
    pages = admin_client.table("book_pages").select("id", count="exact").eq("book_id", book_id).execute()
    addresses = admin_client.table("addresses").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data
    return {"book": book, "page_count": pages.count or 0, "addresses": addresses}


@router.post("/addresses", status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, user_id: CurrentUserId):
    return admin_client.table("addresses").insert({"user_id": user_id, **payload.model_dump()}).execute().data[0]


@router.get("/orders")
def list_orders(user_id: CurrentUserId):
    return admin_client.table("orders").select("*, books(id,title,size)").eq("user_id", user_id).order("created_at", desc=True).execute().data


@router.get("/orders/{order_id}")
def get_order(order_id: str, user_id: CurrentUserId):
    response = admin_client.table("orders").select("*, books(id,title,size)").eq("id", order_id).eq("user_id", user_id).limit(1).execute()
    return data_or_404(response, "Order not found.")


@router.post("/books/{book_id}/orders", status_code=status.HTTP_201_CREATED)
def create_order(book_id: str, payload: OrderCreate, user_id: CurrentUserId):
    owned_book(book_id, user_id)
    address_response = admin_client.table("addresses").select("*").eq("id", payload.address_id).eq("user_id", user_id).limit(1).execute()
    address = data_or_404(address_response, "Delivery address not found.")
    pages = admin_client.table("book_pages").select("id", count="exact").eq("book_id", book_id).execute()
    total_pages = (pages.count or 0) + 2
    total = total_pages * PRICE_PER_PAGE * payload.quantity
    shipping_address = {
        "full_name": address["full_name"], "phone": address["phone"], "house_street": address["house_street"],
        "landmark": address.get("landmark"), "area": address.get("area"), "pincode": address["pincode"],
        "payment_method": payload.payment_method, "quantity": payload.quantity, "total_pages": total_pages,
    }
    order_number = f"MB-{int(datetime.now().timestamp() * 1000)}-{str(uuid4())[:4].upper()}"
    return admin_client.table("orders").insert({
        "user_id": user_id, "book_id": book_id, "order_number": order_number,
        "status": "confirmed", "total_amount": total, "shipping_address": shipping_address,
    }).execute().data[0]
