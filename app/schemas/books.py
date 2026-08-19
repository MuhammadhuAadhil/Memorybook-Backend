from typing import Any, Literal

from pydantic import BaseModel, Field

BookSize = Literal["square", "portrait", "landscape"]


class BookCreate(BaseModel):
    size: BookSize = "square"


class BookUpdate(BaseModel):
    title: str | None = None
    size: BookSize | None = None
    status: str | None = None
    cover_design: dict[str, Any] | None = None
    category: str | None = None
    editor_data: dict[str, Any] | None = None
    photos_count: int | None = Field(default=None, ge=0)


class PageUpdate(BaseModel):
    background: str | None = None
    content: dict[str, Any] | None = None
    layout: str | None = None
    photo_slots: list[str | None] | None = None


class PhotoPlacement(BaseModel):
    page_id: str | None
    page_slots: dict[str, list[str | None]]
    photo_pages: dict[str, str | None] | None = None


class AddressCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=50)
    area: str | None = None
    pincode: str = Field(min_length=1, max_length=20)
    landmark: str | None = None
    house_street: str = Field(min_length=1, max_length=500)


class OrderCreate(BaseModel):
    address_id: str
    quantity: int = Field(ge=1, le=100)
    payment_method: str = Field(min_length=1, max_length=100)
