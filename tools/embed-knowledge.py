#!/usr/bin/env python3
"""把 knowledge/ 公共知识库嵌进 app/greenroom.html 的知识库数据块。

改了 knowledge/*.md 之后跑一遍：
    python3 tools/embed-knowledge.py
零依赖，标准库。README.md 不嵌入。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOW = ROOT / "knowledge"
HTML = ROOT / "app" / "greenroom.html"

START = "<!--KNOWLEDGE:START-->"
END = "<!--KNOWLEDGE:END-->"


def main():
    files = {}
    for p in sorted(KNOW.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        files[p.stem] = p.read_text(encoding="utf-8")
    for p in sorted((KNOW / "roles").glob("*.md")):
        files["roles/" + p.stem] = p.read_text(encoding="utf-8")
    if not files:
        raise SystemExit(f"知识库为空：{KNOW}")

    payload = json.dumps(files, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # </script> 防注入

    html = HTML.read_text(encoding="utf-8")
    block = (
        f"{START}\n"
        f'<script id="knowledge-data" type="application/json">{payload}</script>\n'
        f"{END}"
    )
    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    if not pattern.search(html):
        raise SystemExit("HTML 里找不到 KNOWLEDGE 标记块")
    HTML.write_text(pattern.sub(lambda _: block, html), encoding="utf-8")
    print(f"已嵌入 {len(files)} 个条目，共 {len(payload):,} 字符 → {HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
