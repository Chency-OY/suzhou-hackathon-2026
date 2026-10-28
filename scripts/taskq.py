#!/usr/bin/env python3
"""任务卡队列。让小模型每次只看一张卡，换助手也能接上。
  python scripts/taskq.py split TASK_CARDS_v1.md   拆成 tasks/cards/NN_ID.md（已有状态不覆盖）
  python scripts/taskq.py next                      打印下一张可做的卡
  python scripts/taskq.py done ID                   跑该卡的验收命令，通过才标记完成并追加 docs/PROGRESS.md
  python scripts/taskq.py status                    查看全部状态
  python scripts/taskq.py freeze                    记录 SPEC.md / AGENTS.md 哈希（人工修改它们后需重新 freeze）
  python scripts/taskq.py check                     校验冻结文件未被改动
"""
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "tasks" / "cards"
STATUS = ROOT / "tasks" / "status.json"
FROZEN = ROOT / "tasks" / "frozen.json"
RULES = ROOT / "tasks" / "RULES.md"
FROZEN_FILES = ["SPEC.md", "AGENTS.md"]
HEAD = re.compile(r"^## CARD (\S+) \| (.+?) \| deps: (.*?) \| verify: (.+)$")


def load_status() -> dict:
    return json.loads(STATUS.read_text("utf-8")) if STATUS.exists() else {}


def save_status(st: dict) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True), "utf-8")


def parse_card(path: Path) -> dict:
    text = path.read_text("utf-8")
    first, _, body = text.partition("\n")
    m = HEAD.match(first.strip())
    if not m:
        raise SystemExit(f"{path.name} 首行格式不对：{first}")
    cid, title, deps, verify = m.groups()
    return {"id": cid, "title": title, "verify": verify.strip(), "body": body.strip(),
            "deps": [d.strip() for d in deps.split(",") if d.strip() not in ("", "-")]}


def all_cards() -> list[dict]:
    return [parse_card(p) for p in sorted(CARDS.glob("*.md"))]


def digest() -> dict:
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FROZEN_FILES if (ROOT / f).exists()}


def check_frozen() -> bool:
    if not FROZEN.exists():
        print("提示：尚未 freeze（请人工运行 python scripts/taskq.py freeze）")
        return True
    saved, now = json.loads(FROZEN.read_text("utf-8")), digest()
    bad = [f for f in saved if saved[f] != now.get(f)]
    if bad:
        print("冻结文件被改动：", bad, "→ 用 git checkout 恢复；如确需修改，让人工改完再 freeze。")
        return False
    return True


def cmd_split(bundle: str) -> None:
    text = Path(bundle).read_text("utf-8")
    cards = [p for p in re.split(r"(?m)^(?=## CARD )", text) if p.startswith("## CARD ")]
    head = text.split("## CARD ", 1)[0].strip()
    CARDS.mkdir(parents=True, exist_ok=True)
    if head:
        RULES.write_text(head + "\n", "utf-8")
    for old in CARDS.glob("*.md"):
        old.unlink()
    st = load_status()
    for i, c in enumerate(cards, 1):
        m = HEAD.match(c.splitlines()[0].strip())
        if not m:
            raise SystemExit(f"卡片首行格式错误：{c.splitlines()[0]}")
        (CARDS / f"{i:02d}_{m.group(1)}.md").write_text(c.strip() + "\n", "utf-8")
        st.setdefault(m.group(1), "todo")
    save_status(st)
    print(f"已拆分 {len(cards)} 张卡 -> {CARDS}")


def cmd_next() -> int:
    if not check_frozen():
        return 2
    st = load_status()
    for c in all_cards():
        if st.get(c["id"], "todo") == "done":
            continue
        if all(st.get(d) == "done" for d in c["deps"]):
            if RULES.exists():
                print(RULES.read_text("utf-8"))
                print("=" * 60)
            print(f"# 当前任务卡：{c['id']}　{c['title']}\n# 验收命令：{c['verify']}\n# 完成后运行：python scripts/taskq.py done {c['id']}\n")
            print(c["body"])
            return 0
    print("没有可做的卡：全部完成，或剩余的卡被未完成的依赖挡住（运行 status 查看）。")
    return 0


def cmd_done(cid: str) -> int:
    cards = {c["id"]: c for c in all_cards()}
    if cid not in cards:
        print(f"没有这张卡：{cid}")
        return 2
    if not check_frozen():
        return 2
    c = cards[cid]
    print(f"运行验收：{c['verify']}")
    r = subprocess.run(c["verify"], shell=True, cwd=ROOT)
    if r.returncode != 0:
        print(f"验收未通过（返回码 {r.returncode}），不标记完成。只把失败输出的最后 40 行贴出来排查。")
        return 1
    st = load_status()
    st[cid] = "done"
    save_status(st)
    prog = ROOT / "docs" / "PROGRESS.md"
    prog.parent.mkdir(exist_ok=True)
    with prog.open("a", encoding="utf-8") as f:
        f.write(f"| {datetime.date.today()} | {cid} | 完成 | {c['title']} |\n")
    print(f'已标记完成并追加 docs/PROGRESS.md。下一步：git add -A && git commit -m "[{cid}] {c["title"]}"')
    return 0


def cmd_status() -> None:
    st = load_status()
    for c in all_cards():
        mark = {"done": "✔", "doing": "…"}.get(st.get(c["id"], "todo"), "◻")
        blocked = "" if all(st.get(d) == "done" for d in c["deps"]) else "（被依赖挡住）"
        print(f"{mark} {c['id']:<4} {c['title']} {blocked}")


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 0
    cmd = a[0]
    if cmd == "split" and len(a) == 2:
        cmd_split(a[1])
    elif cmd == "next":
        return cmd_next()
    elif cmd == "done" and len(a) == 2:
        return cmd_done(a[1])
    elif cmd == "status":
        cmd_status()
    elif cmd == "freeze":
        FROZEN.parent.mkdir(parents=True, exist_ok=True)
        FROZEN.write_text(json.dumps(digest(), indent=2), "utf-8")
        print("已记录冻结文件哈希：", list(digest()))
    elif cmd == "check":
        return 0 if check_frozen() else 2
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
