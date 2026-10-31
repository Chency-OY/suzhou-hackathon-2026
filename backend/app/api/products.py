import json
import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..deps import get_provider
from ..llm import LLMProvider, load_prompt, structured_call
from ..models.auth import Account
from ..models.product import ProductPortfolioItem
from .auth import _rate_limit, get_current_account, is_guest_account

router = APIRouter(prefix="/api")
PRODUCTS_PATH = Path("data/products.json")
QUESTIONS = {
    "mechanism": "这款产品的作用靶点或通路是什么？它属于哪一类药物？",
    "scope": "请说出这款产品目前的阶段和主要适用或研究领域，不要把研究方向说成已获批。",
    "boundary": "如果医生问到这款产品的具体风险或尚未核对的适应症，你会怎样回答？",
}


class ProductCheckRequest(BaseModel):
    question_id: Literal["mechanism", "scope", "boundary"]
    answer: str = Field(min_length=8, max_length=1500)

    @field_validator("answer")
    @classmethod
    def trim(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 8:
            raise ValueError("请至少回答 8 个字")
        if re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)|(?<!\d)\d{17}[\dXx](?!\w)|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
            raise ValueError("请删除手机号、身份证号或邮箱后再提交回答")
        return value


class ProductCheckDraft(BaseModel):
    status: Literal["correct", "partial", "incorrect", "unavailable"]


class ProductCheckResult(BaseModel):
    product_id: str
    question_id: str
    status: Literal["correct", "partial", "incorrect", "unavailable"]
    feedback: str
    reference: str
    source_url: str


def _all_products() -> list[ProductPortfolioItem]:
    return [ProductPortfolioItem.model_validate(item)
            for item in json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))]


def _reference(item: ProductPortfolioItem, question_id: str) -> str:
    if question_id == "mechanism":
        return f"作用靶点或通路：{item.target}；药物类型：{item.modality}。"
    if question_id == "scope":
        stage = "已上市" if item.stage == "marketed" else "上市申请审评中" if item.stage == "nda_review" else "关键临床阶段"
        return f"阶段：{stage}；主要领域：{item.area}。{item.overview}"
    if item.stage != "marketed":
        return "该项目尚未获批，不应作为上市产品介绍；只能说明公司已公布的研究阶段和方向，不能承诺上市时间、疗效或安全性。"
    return "只依据已核对的当前获批说明书说明适应症、用法和风险；资料没有覆盖的部分明确说需核对，不作疗效承诺或跨产品优劣推断。"


@router.get("/products", response_model=list[ProductPortfolioItem])
def list_products():
    return _all_products()


@router.post("/products/{product_id}/check", response_model=ProductCheckResult)
def check_product_answer(product_id: str, body: ProductCheckRequest, request: Request,
                         account: Account = Depends(get_current_account), provider: LLMProvider = Depends(get_provider)):
    item = next((product for product in _all_products() if product.id == product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "产品不存在"}})
    _rate_limit(request, "product_check", account.id, 6 if is_guest_account(account) else 30, 3600)
    reference = _reference(item, body.question_id)
    prompt = load_prompt("product_check").render(product=item.name, stage=item.stage,
                                                  question=QUESTIONS[body.question_id], reference=reference,
                                                  answer=body.answer)
    try:
        draft, degraded = structured_call(provider, prompt_name="product_check",
                                          system="只按给定核对资料评价回答；只输出 JSON 分类。",
                                          messages=[{"role": "user", "content": prompt}], model_cls=ProductCheckDraft,
                                          fallback=ProductCheckDraft(status="unavailable"),
                                          max_retries=1, temperature=0, max_tokens=60)
    except RuntimeError:
        draft, degraded = ProductCheckDraft(status="unavailable"), True
    status = "unavailable" if degraded else draft.status
    if item.stage != "marketed" and re.search(r"(?:已经|现已|正式)(?:获批|上市)|(?<!尚未)(?<!未)已获批", body.answer):
        status = "incorrect"
    feedback = {
        "correct": "回答覆盖了这道题的关键点。请结合下方核对资料再确认表述。",
        "partial": "回答抓住了部分要点；请对照下方资料补全或收紧边界。",
        "incorrect": "回答与已核对资料不符，或把尚未获批的方向说成了已获批；请对照下方资料重试。",
        "unavailable": "AI 判断暂不可用；先按下方资料自行核对，稍后可再试。",
    }[status]
    source = item.detail_source_url if body.question_id == "scope" and item.detail_source_url else item.overview_source_url
    return ProductCheckResult(product_id=item.id, question_id=body.question_id, status=status,
                              feedback=feedback, reference=reference, source_url=source)
