from app.main import app
from fastapi.testclient import TestClient


def test_portfolio_has_20_marketed_and_separate_unapproved_assets():
    response = TestClient(app).get("/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 26
    assert len({item["id"] for item in products}) == len(products)
    marketed = [item for item in products if item["stage"] == "marketed"]
    pipeline = [item for item in products if item["stage"] != "marketed"]
    assert len(marketed) == 20
    assert {item["name"] for item in pipeline} == {"IBI343", "IBI363", "IBI354", "IBI3003", "IBI302", "IBI128"}
    assert {item["stage"] for item in pipeline} == {"nda_review", "pivotal"}
    assert all("尚未获批" in item["note"] for item in pipeline)
    assert all(item["verified"] and item["source_url"].startswith("https://") and item["checked_on"]
               for item in products)
