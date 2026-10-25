import re
import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.scenarios.review import load_review, save_review, set_status  # noqa: E402

HEAD = re.compile(r"^##\s*\d+\.\s*(scn_\d+)")
CHECK = re.compile(r"-\s*\[([ xX])\]\s*通过\s*\[([ xX])\]\s*需修改\s*\[([ xX])\]\s*剔除\s*备注[:：]?\s*(.*)$")


def parse(text: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    current = None
    for line in text.splitlines():
        h = HEAD.match(line.strip())
        if h:
            current = h.group(1)
            continue
        c = CHECK.search(line.strip())
        if c and current:
            ok, fix, rej = (g.lower() == "x" for g in c.groups()[:3])
            remark = c.group(4).strip()
            if rej:
                out[current] = ("rejected", remark)
            elif fix:
                out[current] = ("needs_fix", remark)
            elif ok:
                out[current] = ("approved", remark)
    return out


def main() -> int:
    path = Path("docs/REVIEW_SAMPLE.md")
    if not path.exists():
        print("缺少 docs/REVIEW_SAMPLE.md，请先运行 make review")
        return 2
    parsed = parse(path.read_text(encoding="utf-8"))
    data = load_review()
    for sid, (status, remark) in parsed.items():
        set_status(data, sid, status, remark)
    save_review(data)
    from collections import Counter
    print("已写入 review.json：", dict(Counter(s for s, _ in parsed.values())) or "（没有勾选项）")
    print("下一步：python scripts/regen_scenarios.py --pending-fix  然后  python scripts/seed.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
