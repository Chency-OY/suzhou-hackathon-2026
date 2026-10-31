from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

import httpx

from ..config import settings
from ..llm import LLMProvider, load_prompt, structured_call
from ..models.radar import RadarAnswerDraft, RadarAnswerPoint, RadarWebSource

SEARCH_URL = "https://api.deepseek.com/v1/tools/search"
_UNCONFIRMED_EVENT = re.compile(r"计划邀请|拟邀请|预计邀请|将受邀|拟参加|预计参加")
TOPICS = (
    ("paper", "论文 研究 发表"),
    ("conference", "学术会议 大会 论坛"),
    ("talk", "演讲 报告 讲座"),
)


def _safe_url(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or (
            host == "localhost" or host.endswith(".local")):
        return ""
    try:
        if not ipaddress.ip_address(host).is_global:
            return ""
    except ValueError:
        pass
    return value


def _query(name: str, hospital: str, topic: str) -> str:
    # DeepSeek Search API 的单条检索词最多 128 个 Unicode 字符。
    return f'"{name[:40]}" "{hospital[:60]}" {topic}'[:128]


def search_web(name: str, hospital: str, client: httpx.Client | None = None,
               api_key: str | None = None) -> tuple[list[RadarWebSource], dict[str, str], str]:
    key = settings.llm_api_key if api_key is None else api_key
    if not key or (api_key is None and settings.llm_base_url.rstrip("/") != "https://api.deepseek.com"):
        return [], {}, "not_configured"
    own_client = client is None
    client = client or httpx.Client()
    sources: list[RadarWebSource] = []
    evidence: dict[str, str] = {}
    seen: set[str] = set()
    try:
        for kind, topic in TOPICS:
            response = client.post(SEARCH_URL, headers={"Authorization": f"Bearer {key}"},
                                   json={"query": _query(name, hospital, topic), "count": 6,
                                         "need_content": True}, timeout=25)
            response.raise_for_status()
            results = response.json().get("results", [])
            if not isinstance(results, list):
                raise TypeError("DeepSeek Search 返回格式不正确")
            for hit in results:
                if not isinstance(hit, dict):
                    continue
                url = _safe_url(str(hit.get("url") or ""))
                if not url or url in seen:
                    continue
                seen.add(url)
                corpus = "\n".join(str(hit.get(field) or "")[:12000]
                                   for field in ("title", "snippet", "summary", "content"))
                source_id = f"web_{len(sources) + 1}"
                sources.append(RadarWebSource(
                    id=source_id, kind=kind, title=str(hit.get("title") or "未列题名")[:240],
                    url=url, site_name=str(hit.get("site_name") or "")[:100],
                    published_at=str(hit.get("date") or "")[:32],
                    snippet=str(hit.get("snippet") or "")[:500],
                    name_in_source=name.casefold() in corpus.casefold(),
                    hospital_in_source=hospital.casefold() in corpus.casefold(),
                ))
                evidence[source_id] = corpus
        return sources, evidence, "ok"
    finally:
        if own_client:
            client.close()


def synthesize_answer(name: str, hospital: str, sources: list[RadarWebSource], evidence: dict[str, str],
                      provider: LLMProvider) -> list[RadarAnswerPoint]:
    matched = [source for source in sources if source.name_in_source and source.hospital_in_source][:10]
    if not matched or (provider.name == "mock" and not provider.responses.get("radar_answer")):
        return []
    blocks = "\n\n".join(
        f"[{source.id}] 类型={source.kind} 标题={source.title} 网址={source.url}\n"
        f"检索内容={evidence[source.id][:2000]}" for source in matched)
    prompt = load_prompt("radar_answer").render(name=name, hospital=hospital, sources=blocks)
    try:
        draft, degraded = structured_call(
            provider, prompt_name="radar_answer", system="你是谨慎的公开学术资料整理助手，只输出 JSON。",
            messages=[{"role": "user", "content": prompt}], model_cls=RadarAnswerDraft,
            fallback=RadarAnswerDraft(), max_retries=1, temperature=0.0, max_tokens=900)
    except RuntimeError:
        return []
    if degraded:
        return []
    by_id = {source.id: source for source in matched}
    accepted = []
    for point in draft.points:
        source = by_id.get(point.source_id)
        if (not source or point.kind != source.kind or
                point.evidence_quote not in evidence[source.id] or len(point.evidence_quote.strip()) < 8 or
                _UNCONFIRMED_EVENT.search(point.statement + point.evidence_quote)):
            continue
        accepted.append(point)
    return accepted[:8]
