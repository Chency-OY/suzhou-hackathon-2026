import json
from uuid import uuid4

from app.db import Repo
from app.deps import get_provider, get_repo
from app.llm import MockLLM
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
    assert all(item["target"] and item["modality"] and item["area"] and len(item["overview"]) >= 20
               and item["overview_source_url"].endswith(".pdf")
               for item in products)
    assert all("尚无获批适应症" in item["overview"] for item in pipeline)
    xinermei = next(item for item in products if item["id"] == "xinermei")
    assert "BMI≥28" in xinermei["overview"] and xinermei["detail_source_url"].endswith(".pdf")


def test_product_specific_answer_uses_verified_reference_and_guest_access(tmp_path):
    repo = Repo(f"sqlite:///{tmp_path}/products.db")
    provider = MockLLM({"product_check": json.dumps({"status": "correct"})})
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_provider] = lambda: provider
    try:
        client = TestClient(app, headers={"x-real-ip": str(uuid4())})
        assert client.post("/api/products/xinermei/check", json={"question_id": "mechanism",
                                                           "answer": "它作用于双受体通路。"}).status_code == 401
        assert client.post("/api/auth/guest").status_code == 200
        result = client.post("/api/products/xinermei/check", json={"question_id": "mechanism",
                                                               "answer": "它作用于 GCGR 和 GLP-1R，属于多肽双受体激动剂。"})
        assert result.status_code == 200
        assert result.json()["status"] == "correct"
        assert "GCGR/GLP-1R" in result.json()["reference"]
        assert "信尔美" in provider.calls[-1]["messages"][0]["content"]

        pipeline = client.post("/api/products/ibi343/check", json={"question_id": "scope",
                                                                   "answer": "这个产品已经上市，可以直接用于胃癌。"})
        assert pipeline.status_code == 200
        assert pipeline.json()["status"] == "incorrect"
        assert "尚无获批适应症" in pipeline.json()["reference"]
        assert client.post("/api/products/missing/check", json={"question_id": "scope",
                                                                "answer": "我想核对一下这个产品。"}).status_code == 404
        assert client.post("/api/products/xinermei/check", json={"question_id": "scope",
                                                               "answer": "   "}).status_code == 422
        assert client.post("/api/products/xinermei/check", json={"question_id": "scope",
                                                               "answer": "患者手机是13800000000，请直接联系。"}).status_code == 422
    finally:
        app.dependency_overrides.clear()
