"""从 pyproject.toml 提取第三方依赖（每行一个），供离线打包与服务器安装使用。
用法：python scripts/extract_requirements.py [--extras rag,dev]"""
import argparse
import sys
import tomllib
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extras", default="", help="逗号分隔的可选依赖组，如 rag,dev")
    ap.add_argument("--pyproject", default="pyproject.toml")
    args = ap.parse_args()
    data = tomllib.loads(Path(args.pyproject).read_text(encoding="utf-8"))["project"]
    reqs = list(data.get("dependencies", []))
    optional = data.get("optional-dependencies", {})
    for name in [x for x in args.extras.split(",") if x]:
        if name not in optional:
            print(f"没有名为 {name} 的可选依赖组", file=sys.stderr)
            return 2
        reqs += optional[name]
    print("\n".join(dict.fromkeys(reqs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
