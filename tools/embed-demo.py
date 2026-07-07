#!/usr/bin/env python3
"""把 examples/demo-workspace 嵌进 app/greenroom.html 的示例数据块。

改了示例工作台之后跑一遍：
    python3 tools/embed-demo.py
零依赖，标准库。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "examples" / "demo-workspace"
HTML = ROOT / "app" / "greenroom.html"

START = "<!--DEMO:START-->"
END = "<!--DEMO:END-->"


def main():
    files = {}
    for p in sorted(DEMO.rglob("*.md")):
        rel = p.relative_to(DEMO).as_posix()
        files[rel] = p.read_text(encoding="utf-8")
    if not files:
        raise SystemExit(f"示例工作台为空：{DEMO}")

    payload = json.dumps(files, ensure_ascii=False)
    # </script> 防注入：JSON 字符串里不允许出现闭合标签
    payload = payload.replace("</", "<\\/")

    html = HTML.read_text(encoding="utf-8")
    block = (
        f"{START}\n"
        f'<script id="demo-data" type="application/json">{payload}</script>\n'
        f"{END}"
    )
    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    if not pattern.search(html):
        raise SystemExit("HTML 里找不到 DEMO 标记块")
    HTML.write_text(pattern.sub(lambda _: block, html), encoding="utf-8")
    print(f"已嵌入 {len(files)} 个文件，共 {len(payload):,} 字符 → {HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
