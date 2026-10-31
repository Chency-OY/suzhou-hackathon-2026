from __future__ import annotations

import json

import httpx
from app.llm import MockLLM
from app.radar.deepseek_web import search_web, synthesize_answer


def test_search_uses_deepseek_live_endpoint_and_keeps_identity_uncertain():
    queries = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.deepseek.com/v1/tools/search"
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        queries.append(body["query"])
        assert body["need_content"] is True and len(body["query"]) <= 128
        if "论文" in body["query"]:
            hits = [{"url": "https://example.org/paper", "title": "甲某研究论文", "snippet": "甲某，某某医院，发表研究论文",
                     "content": "甲某在某某医院开展这项研究并发表论文。", "site_name": "期刊"},
                    {"url": "http://insecure.example/paper", "title": "不安全链接"}]
        elif "会议" in body["query"]:
            hits = [{"url": "https://example.org/paper", "title": "重复论文"},
                    {"url": "https://example.org/conference", "title": "会议日程", "snippet": "仅有甲某姓名"}]
        else:
            hits = []
        return httpx.Response(200, json={"results": hits})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        sources, evidence, status = search_web("甲某", "某某医院", client=client, api_key="test-key")
    assert status == "ok" and len(queries) == 3
    assert [source.kind for source in sources] == ["paper", "conference"]
    assert sources[0].name_in_source and sources[0].hospital_in_source
    assert sources[0].identity_status == "candidate"
    assert not sources[1].hospital_in_source
    assert "甲某在某某医院" in evidence["web_1"]


def test_deepseek_answer_needs_exact_quote_and_matched_name_hospital():
    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if "论文" in body["query"]:
            return httpx.Response(200, json={"results": [{"url": "https://example.org/paper",
                "title": "甲某研究论文", "content": "甲某来自某某医院，发表了一篇公开研究论文。"}]})
        return httpx.Response(200, json={"results": []})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        sources, evidence, _ = search_web("甲某", "某某医院", client=client, api_key="test-key")
    good = {"kind": "paper", "statement": "找到一篇待确认的研究论文。", "source_id": "web_1",
            "evidence_quote": "发表了一篇公开研究论文"}
    invented = {**good, "statement": "编造结论", "evidence_quote": "原文中不存在的疗效数据"}
    wrong_id = {**good, "statement": "错误来源", "source_id": "web_99"}
    planned = {**good, "statement": "计划邀请甲某参加会议"}
    mock = MockLLM({"radar_answer": json.dumps({"points": [good, invented, wrong_id, planned]}, ensure_ascii=False)})
    points = synthesize_answer("甲某", "某某医院", sources, evidence, mock)
    assert [point.statement for point in points] == [good["statement"]]
    prompt = mock.calls[0]["messages"][0]["content"]
    assert "同名候选" in prompt and "example.org/paper" in prompt


def test_no_identity_match_does_not_call_model():
    mock = MockLLM({"radar_answer": "{}"})
    sources, evidence, _ = search_web("甲某", "某某医院", client=httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"results": [
            {"url": "https://example.org/talk", "title": "甲某演讲", "summary": "未提医院"}
        ]}))), api_key="test-key")
    assert synthesize_answer("甲某", "某某医院", sources, evidence, mock) == []
    assert mock.calls == []
