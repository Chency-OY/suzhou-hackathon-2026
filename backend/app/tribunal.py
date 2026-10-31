from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from .llm import LLMProvider, load_prompt, structured_call
from .models.diary import ClaimFinding, FieldDiary, ReviewEvidence
from .rag.facts import Fact, load_facts

LABEL_URL = "https://img.innoventbio.com/product/W10030842001.pdf"
FACTS_PATH = Path(__file__).resolve().parents[2] / "data/kb/facts.yaml"
_MEDICAL = re.compile(r"药|疗效|有效|安全性|副作用|不良反应|适应症|临床|试验|剂量|处方|获批|治疗|禁忌")
_PRODUCT = re.compile(r"信尔美|玛仕度肽|mazdutide|IBI362", re.IGNORECASE)
_COMPARISON = re.compile(r"竞品|二代|三代|比.+(?:更好|更差|便宜|有效)")
_QUESTION = re.compile(r"有没有|是否|能否|会不会|[？?]|吗(?:$|[。！!])")
_CLEAN = re.compile(r"[^\u3400-\u9fffa-z0-9]")


class RelationChoice(BaseModel):
    relation: str
    evidence_id: str = ""
    evidence_quote: str = ""


@lru_cache
def label_facts() -> tuple[Fact, ...]:
    facts, errors = load_facts(FACTS_PATH)
    if errors:
        return ()
    return tuple(fact for fact in facts if fact.verified and fact.source.startswith("label.md#"))


def extract_claims(item: FieldDiary) -> list[str]:
    if item.degraded:
        return []
    candidates = [*item.digest.uncertain_claims]
    candidates.extend(text for text in item.digest.doctor_feedback if _MEDICAL.search(text))
    candidates.extend(text for text in item.digest.first_impressions if _MEDICAL.search(text))
    return list(dict.fromkeys(text.strip()[:220] for text in candidates if text.strip()))[:6]


def _grams(text: str) -> set[str]:
    cleaned = _CLEAN.sub("", text.casefold())
    return {cleaned[index:index + 2] for index in range(len(cleaned) - 1)}


@lru_cache
def _index() -> tuple[tuple[Fact, set[str]], ...]:
    return tuple((fact, _grams(fact.statement)) for fact in label_facts())


def candidate_facts(claim: str, limit: int = 3) -> list[Fact]:
    if not _PRODUCT.search(claim) or _COMPARISON.search(claim):
        return []
    if re.search(r"适应症|获批|治疗|用于", claim):
        category = "indication"
    elif re.search(r"副作用|不良反应|安全性|禁忌|风险", claim):
        category = "safety"
    elif re.search(r"剂量|给药|用法", claim):
        category = "dosing"
    elif re.search(r"疗效|有效|减重|降糖", claim):
        category = "efficacy"
    else:
        return []
    normalized = _PRODUCT.sub("", claim).replace("副作用", "不良反应")
    query = _grams(normalized)
    if not query:
        return []
    index = tuple((fact, grams) for fact, grams in _index() if fact.category == category)
    if not index:
        return []
    counts = Counter(gram for _, grams in index for gram in grams)
    ranked = []
    for fact, grams in index:
        shared = query & grams
        if not shared:
            continue
        weight = sum(math.log((len(index) + 1) / (counts[gram] + 1)) + 1 for gram in shared)
        ranked.append((weight / math.sqrt(len(grams) + 1), fact))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [fact for score, fact in ranked[:limit] if score >= 0.4]


def _evidence(fact: Fact) -> ReviewEvidence:
    return ReviewEvidence(id=fact.id, excerpt=fact.statement[:260], source=fact.source, url=LABEL_URL)


def assess_claim(claim: str, provider: LLMProvider, facts: list[Fact] | None = None,
                 raw_text: str | None = None) -> ClaimFinding:
    if raw_text is not None and claim not in raw_text:
        return ClaimFinding(claim=claim, status="insufficient", grounded_in_raw=False,
                            note="这句话无法逐字定位到保存的原话，未进行医学资料判断。")
    if not _PRODUCT.search(claim) or _COMPARISON.search(claim):
        return ClaimFinding(claim=claim, status="out_of_scope")
    facts = candidate_facts(claim) if facts is None else facts
    candidates = [_evidence(fact) for fact in facts[:3]]
    if not candidates:
        return ClaimFinding(claim=claim, status="insufficient")
    fallback = ClaimFinding(claim=claim, status="insufficient", candidates=candidates)
    if _QUESTION.search(claim):
        return fallback
    if provider.name == "mock" and not provider.responses.get("diary_tribunal"):
        return fallback
    sources = "\n".join(f"[{fact.id}] {fact.statement[:260]}" for fact in facts[:3])
    prompt = load_prompt("diary_tribunal").render(claim=claim, sources=sources)
    try:
        choice, degraded = structured_call(
            provider, prompt_name="diary_tribunal", system="你是保守的资料对照助手，只输出 JSON。",
            messages=[{"role": "user", "content": prompt}], model_cls=RelationChoice,
            fallback=RelationChoice(relation="insufficient"), max_retries=1, temperature=0.0, max_tokens=220)
    except RuntimeError:
        return fallback
    if degraded or choice.relation not in {"possible_support", "possible_conflict"}:
        return fallback
    matched = next((fact for fact in facts if fact.id == choice.evidence_id), None)
    if not matched or len(choice.evidence_quote.strip()) < 8 or choice.evidence_quote not in matched.statement:
        return fallback
    return ClaimFinding(claim=claim, status=choice.relation,
                        evidence_id=matched.id, evidence_quote=choice.evidence_quote, candidates=candidates)
