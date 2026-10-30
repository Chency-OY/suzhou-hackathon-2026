"""重生成场景。needs_fix：同画像同类型重写；rejected：同画像换一个类型重写（肝病科的 off_label_bait 保持类型）。
默认处理 review.json 中 needs_fix + rejected；--ids 可指定。成功后状态置为 pending。"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.llm import get_provider  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.rag import KnowledgeBase  # noqa: E402
from app.scenarios.generate import TYPE_PLAN, generate_one  # noqa: E402
from app.scenarios.review import load_review, save_review, set_status, status_of  # noqa: E402


def load(path, cls):
    p = Path(path)
    return [cls.model_validate_json(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def alt_type(p: DoctorPersona, cur: str) -> str:
    if p.department == "hepatology" and cur == "off_label_bait":
        return cur
    return next((t for t in TYPE_PLAN[p.department] if t != cur), cur)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--pending-fix", action="store_true", help="处理 needs_fix 与 rejected")
    args = ap.parse_args()
    review = load_review()
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    scenarios = load("data/scenarios/scenarios.jsonl", Scenario)
    ids = [x for x in args.ids.split(",") if x] or [
        s.id for s in scenarios if status_of(review, s.id) in ("needs_fix", "rejected")]
    if not ids:
        print("没有需要重生成的场景。")
        return 0
    provider = get_provider()
    if provider.name == "mock":
        print("当前为 mock，无法重生成。")
        return 2
    try:
        kb = KnowledgeBase()
        kb = kb if kb.count() else None
    except Exception:  # noqa: BLE001
        kb = None
    by_id = {s.id: s for s in scenarios}
    done = 0
    for sid in ids:
        s = by_id.get(sid)
        if not s:
            continue
        p = personas[s.persona_id]
        t = alt_type(p, s.type) if status_of(review, sid) == "rejected" else s.type
        draft, reason = generate_one(provider, p, t, kb)
        if draft is None:
            print("失败：", sid, reason)
            continue
        by_id[sid] = Scenario(id=sid, type=t, persona_id=p.id, source="generated", **draft.model_dump())
        set_status(review, sid, "pending", f"已重生成（类型 {t}）")
        done += 1
        print("已重生成：", sid, t)
    Path("data/scenarios/scenarios.jsonl").write_text(
        "\n".join(by_id[s.id].model_dump_json() for s in scenarios) + "\n", encoding="utf-8")
    save_review(review)
    print(f"完成 {done}/{len(ids)}。请运行 python scripts/seed.py 入库。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
