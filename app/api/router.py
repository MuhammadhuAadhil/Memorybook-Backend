from fastapi import APIRouter

from app.api.routes import books, health, orders, pages, photos

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(books.router)
api_router.include_router(pages.router)
api_router.include_router(photos.router)
api_router.include_router(orders.router)
