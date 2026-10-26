"""对已部署地址做端到端冒烟：python scripts/e2e_smoke.py --base http://<ip>:8000"""
import argparse
import re
import secrets
import sys

import httpx

SECRETS = ["hidden_objection", "traps", "initial_trust", "initial_patience", "time_budget_turns", "speech_habits",
           "backstory"]
PUBLIC_KEYS = {"department", "title", "hospital_tier", "style_hint", "difficulty"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--with-session", action="store_true")
    args = ap.parse_args()
    c = httpx.Client(base_url=args.base, timeout=30)
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(("PASS " if ok else "FAIL "), name, detail)
        if not ok:
            fails.append(name)

    r = c.get("/api/health")
    check("health", r.status_code == 200 and r.json().get("status") == "ok")

    r = c.get("/")
    html = r.text
    check("index.html", r.status_code == 200 and 'id="root"' in html)
    assets = re.findall(r'(?:src|href)="(/(?:rep-trainer/)?assets/[^"]+)"', html)
    check("引用了构建资源", len(assets) > 0)
    for a in assets:
        check(f"asset {a}", c.get(a.removeprefix("/rep-trainer")).status_code == 200)

    r = c.get("/api/scenarios")
    items = r.json() if r.status_code == 200 else []
    check("场景数量>0", len(items) > 0, f"({len(items)})")
    for s in SECRETS:
        check(f"列表无泄露 {s}", s not in r.text)

    for dept in sorted({i["department"] for i in items}):
        rr = c.get("/api/scenarios", params={"dept": dept})
        expect = sum(1 for i in items if i["department"] == dept)
        check(f"筛选 dept={dept}", rr.status_code == 200 and len(rr.json()) == expect and
              all(x["department"] == dept for x in rr.json()))
    for diff in ("easy", "normal", "hard"):
        rr = c.get("/api/scenarios", params={"difficulty": diff})
        check(f"筛选 difficulty={diff}", rr.status_code == 200 and all(x["difficulty"] == diff for x in rr.json()))

    for sid in [i["id"] for i in items[:5]]:
        rd = c.get(f"/api/scenarios/{sid}")
        ok = rd.status_code == 200 and set(rd.json().get("persona_public", {})) == PUBLIC_KEYS
        check(f"详情 {sid}", ok)
        for s in SECRETS:
            check(f"详情{sid}无泄露 {s}", s not in rd.text)

    check("SPA 回退", 'id="root"' in c.get("/scenarios/scn_001").text)
    r404 = c.get("/api/not-exist")
    check("未知 API 返回 404 且非 HTML", r404.status_code == 404 and "<html" not in r404.text.lower())

    if args.with_session and items:
        registered = c.post("/api/auth/register", json={"username": "smoke_" + secrets.token_hex(4),
                                                         "password": secrets.token_urlsafe(16)})
        check("注册独立账号", registered.status_code == 200)
        if registered.status_code != 200:
            return 1
        created = c.post("/api/sessions", json={"scenario_id": items[0]["id"]})
        check("创建演练", created.status_code == 200)
        if created.status_code == 200:
            sid = created.json()["session_id"]
            turn = c.post(f"/api/sessions/{sid}/turns", json={"text": "您怎么看相关资料的适用人群？"})
            check("提交一轮对话", turn.status_code == 200 and bool(turn.json().get("doctor_reply")))
            replay = c.get(f"/api/sessions/{sid}")
            check("会话回放", replay.status_code == 200 and len(replay.json().get("turns", [])) == 3)
            if replay.status_code == 200:
                check("会话无隐藏画像泄露", all(x not in replay.text for x in
                      ('"hidden_objection":', '"traps":', '"meta":', '"bait":')))
            finish = c.post(f"/api/sessions/{sid}/finish")
            check("结束演练", finish.status_code == 200 and finish.json().get("ended") is True)

    print(f"\n失败 {len(fails)} 项" if fails else "\n全部通过")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
