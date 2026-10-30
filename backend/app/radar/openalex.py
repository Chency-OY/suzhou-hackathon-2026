from __future__ import annotations

import re
from datetime import UTC, datetime
from hashlib import sha256
from urllib.parse import urlparse

import httpx
from pypinyin import lazy_pinyin

from ..models.radar import AcademicRadar, AcademicWork

BASE = "https://api.openalex.org"
USER_AGENT = "RepTrainerAcademicRadar/1.0 (public bibliographic metadata)"
_CHINESE = re.compile(r"[\u3400-\u9fff]")
_CLEAN = re.compile(r"[^a-z0-9]")


def _search_name(name: str) -> str:
    if not _CHINESE.search(name):
        return name.strip()
    return " ".join(lazy_pinyin(name.replace(" ", ""))).title()


def _name_matches(requested: str, returned: str) -> bool:
    parts = requested.lower().split()
    if len(parts) < 2:
        return False
    got = _CLEAN.sub("", returned.lower())
    return got in {_CLEAN.sub("", "".join(parts)), _CLEAN.sub("", "".join(reversed(parts)))}


def _safe_url(value: str) -> str:
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.hostname in {"openalex.org", "doi.org"} else ""


def radar_id(owner_id: str, doctor_name: str, hospital: str) -> str:
    source = "|".join((owner_id, doctor_name.casefold().strip(), hospital.casefold().strip()))
    return "radar_" + sha256(source.encode()).hexdigest()[:32]


def _get(client: httpx.Client, path: str, params: dict[str, str | int]) -> dict:
    response = client.get(BASE + path, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
    response.raise_for_status()
    return response.json()


def _institution(results: list[dict], hospital: str) -> dict | None:
    wanted = hospital.casefold().replace(" ", "")
    exact = [item for item in results if any(
        str(alias).casefold().replace(" ", "") == wanted
        for alias in [item.get("display_name", ""), *item.get("display_name_alternatives", [])])]
    return exact[0] if len(exact) == 1 else None


def search_academic(owner_id: str, doctor_name: str, hospital: str,
                    client: httpx.Client | None = None) -> AcademicRadar:
    name = _search_name(doctor_name)
    base = {"id": radar_id(owner_id, doctor_name, hospital), "owner_id": owner_id,
            "doctor_name": doctor_name, "hospital": hospital,
            "searched_at": datetime.now(UTC), "search_name": name}
    own_client = client is None
    client = client or httpx.Client()
    try:
        institutions = _get(client, "/institutions", {"search": hospital, "per_page": 5}).get("results", [])
        institution = _institution(institutions, hospital)
        if not institution:
            return AcademicRadar(**base, status="ambiguous_institution",
                                 note="没有找到唯一匹配的医院；请补全医院正式名称后重试。")
        inst_id = institution["id"].split("/")[-1]
        common = {"institution_name": institution["display_name"],
                  "institution_url": _safe_url(institution["id"])}
        authors = _get(client, "/authors", {
            "search": name, "filter": f"last_known_institutions.id:{inst_id}", "per_page": 25,
            "select": "id,display_name,works_count",
        }).get("results", [])
        ids = [item["id"].split("/")[-1] for item in authors
               if _name_matches(name, item.get("display_name", ""))][:6]
        if not ids:
            return AcademicRadar(**base, **common, status="no_match",
                                 note="公开索引中没有找到姓名与医院同时匹配的论文记录。")
        works = _get(client, "/works", {
            "filter": f"institutions.id:{inst_id},authorships.author.id:{'|'.join(ids)}",
            "sort": "publication_date:desc", "per_page": 25,
            "select": "id,display_name,publication_date,primary_location,authorships,doi",
        }).get("results", [])
        found = []
        for work in works:
            matches = [author for author in work.get("authorships", [])
                       if (author.get("author", {}).get("id") or "").split("/")[-1] in ids
                       and _name_matches(name, author.get("author", {}).get("display_name", ""))
                       and any((inst.get("id") or "").split("/")[-1] == inst_id
                               for inst in author.get("institutions", []))]
            if not matches:
                continue
            match = matches[0]
            doi = _safe_url(work.get("doi") or "")
            url = doi or _safe_url(work.get("id", ""))
            if not url:
                continue
            journal = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            found.append(AcademicWork(
                id=work["id"].split("/")[-1], title=work.get("display_name") or "未列题名",
                publication_date=work.get("publication_date") or "", journal=journal,
                author_name=match.get("author", {}).get("display_name") or "",
                affiliation=institution["display_name"], url=url, doi=doi,
            ))
        return AcademicRadar(**base, **common, status="found" if found else "no_match", works=found,
                             note="论文是公开索引中的候选记录；同名作者需人工核对，不能证明为这位医生。")
    finally:
        if own_client:
            client.close()
