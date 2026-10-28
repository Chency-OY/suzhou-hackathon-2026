"""重建知识库并导入画像/场景到数据库。可重复执行。"""
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.db import Repo  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.rag import KnowledgeBase, load_facts  # noqa: E402


def import_jsonl(repo: Repo, path: Path, cls) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            repo.save(cls.model_validate_json(line))
            n += 1
    return n


def main() -> int:
    facts, errors = load_facts("data/kb/facts.yaml")
    if errors:
        print("facts.yaml 存在错误，先运行 python scripts/check_facts.py：")
        print("\n".join(" - " + e for e in errors))
        return 1
    kb = KnowledgeBase()
    kb.reset()
    n_facts = kb.index_facts(facts)
    label = Path("data/sources/label.md")
    n_label = kb.index_label(label) if label.exists() else 0
    repo = Repo()
    n_p = import_jsonl(repo, Path("data/personas/personas.jsonl"), DoctorPersona)
    n_s = import_jsonl(repo, Path("data/scenarios/scenarios.jsonl"), Scenario)
    keep = {s.id for s in (Scenario.model_validate_json(x) for x in Path("data/scenarios/scenarios.jsonl")
                           .read_text(encoding="utf-8").splitlines() if x.strip())}
    for old in repo.list(Scenario):
        if old.id not in keep:
            repo.delete(Scenario, old.id)
    verified = sum(f.verified for f in facts)
    print(f"知识库：facts={n_facts}（已核验 {verified}），说明书分块={n_label}"
          + ("" if label.exists() else "（未找到 data/sources/label.md）"))
    print(f"数据库：画像={n_p}，场景={n_s}")
    for q in ("司美格鲁肽 头对头", "胃肠道 不良反应", "适应症"):
        top = kb.retrieve(q, k=2)
        print(f"检索[{q}] ->", [(c.id, round(c.score, 2)) for c in top])
    return 0


if __name__ == "__main__":
    sys.exit(main())
