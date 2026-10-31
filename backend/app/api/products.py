import json
from pathlib import Path

from fastapi import APIRouter

from ..models.product import ProductPortfolioItem

router = APIRouter(prefix="/api")
PRODUCTS_PATH = Path("data/products.json")


@router.get("/products", response_model=list[ProductPortfolioItem])
def list_products():
    return [ProductPortfolioItem.model_validate(item)
            for item in json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))]
