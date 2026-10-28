"""对已部署地址做端到端冒烟：python scripts/e2e_smoke.py --base http://<ip>:8000"""
import argparse
import re
import sys

import httpx

SECRETS = ["hidden_objection", "traps", "initial_trust", "initial_patience", "time_budget_turns", "speech_habits",
           "backstory"]
SESSION_SECRETS = SECRETS + ["meta", "bait", "baits", "turn_plan", "gold_moves", "compliance_checks"]
PUBLIC_KEYS = {"department", "title", "hospital_tier", "style_hint", "difficulty"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--with-session", action="store_true", help="额外跑一遍会话端到端（会真实调用模型）")
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
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    check("引用了构建资源", len(assets) > 0)
    for a in assets:
        check(f"asset {a}", c.get(a).status_code == 200)

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

    if args.with_session:
        rs = c.post("/api/sessions", json={"scenario_id": items[0]["id"], "rep_id": "rep_smoke",
                                           "pre_goal": "了解医生关注点并约下次沟通"})
        check("创建会话（带访前目标）", rs.status_code == 200)
        if rs.status_code != 200:
            print(rs.text[:300])
        else:
            sid = rs.json()["session_id"]
            check("回复含开场白", bool(rs.json().get("opening_line")))

            rt = c.post(f"/api/sessions/{sid}/turns", json={"text": "主任您好，想先了解一下您门诊这类患者的情况。"})
            check("提交一轮", rt.status_code == 200 and bool(rt.json().get("doctor_reply")))
            for s in SESSION_SECRETS:
                check(f"回合无泄露 {s}", s not in rt.text)

            check("未结束不能写记录", c.post(f"/api/sessions/{sid}/record",
                                        json={"note": "客户原话：先放资料。下一步：下周回访。"}).status_code == 409)

            rf = c.post(f"/api/sessions/{sid}/finish")
            check("结束会话", rf.status_code == 200 and rf.json().get("ended") is True)

            rr = c.post(f"/api/sessions/{sid}/record", json={"note": "客户原话：先放资料。下一步：下周回访。"})
            check("保存拜访记录", rr.status_code == 200 and rr.json().get("saved") is True)

            rg = c.get(f"/api/sessions/{sid}")
            body = rg.text
            check("回放含 pre_goal", rg.status_code == 200 and "了解医生关注点" in body)
            check("回放含 visit_note", "下周回访" in body)
            for s in SESSION_SECRETS:
                check(f"回放无泄露 {s}", s not in body)

    print(f"\n失败 {len(fails)} 项" if fails else "\n全部通过")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
