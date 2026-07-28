#!/usr/bin/env python3
"""为 knowledge/roles/ 的每个岗位预生成像素头像，嵌进 app/greenroom.html。

素材：DiceBear pixel-art 风格（CC0 1.0，画师 Plastic Jam，https://www.dicebear.com/styles/pixel-art/）。
构建期经 HTTP API 生成一次（需要网络），SVG 嵌入后运行时零网络零依赖。

改了 knowledge/roles/*.md（新增/改名岗位）之后跑一遍：
    python3 tools/embed-avatars.py
零第三方依赖，标准库。结果缓存在 tools/.avatar-cache/，重跑只拉新增岗位。
"""
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLES = ROOT / "knowledge" / "roles"
HTML = ROOT / "app" / "greenroom.html"
CACHE = Path(__file__).resolve().parent / ".avatar-cache"

START = "<!--AVATARS:START-->"
END = "<!--AVATARS:END-->"
API = "https://api.dicebear.com/9.x/pixel-art/svg"

# 行业气质参数包：clothingColor 同行业统一色系（hex 不带 #，多值逗号分隔由 seed 决定），
# 眼镜/帽子/胡须概率贴职业刻板印象但不夸张。脸型发型由 seed（岗位英文名）决定。
IND_STYLE = {
    "product":        {"clothingColor": "456789,3a5a78,2e4a66", "glassesProbability": 35},
    "operations":     {"clothingColor": "c9764a,b5651d,a85f38", "glassesProbability": 20},
    "engineering":    {"clothingColor": "44475a,353a4f,2f3640", "glassesProbability": 70},
    "ai-data":        {"clothingColor": "5d4a7e,4a4e8c,3f3a6e", "glassesProbability": 60},
    "design":         {"clothingColor": "c98a2d,b3589a,3d8a8a", "hatProbability": 35, "glassesProbability": 30},
    "marketing":      {"clothingColor": "c0563b,d4804d,b8443f", "glassesProbability": 15},
    "sales":          {"clothingColor": "2f4f6f,35506b,274056", "glassesProbability": 15},
    "finance":        {"clothingColor": "1f2d3d,2c3e50,34495e", "glassesProbability": 50},
    "corporate":      {"clothingColor": "6b705c,5f6f65,737d6e", "glassesProbability": 30},
    "game":           {"clothingColor": "7a4fbf,3d8a8a,5568d4", "hatProbability": 30, "glassesProbability": 25},
    "medical":        {"clothingColor": "e8edf0,d7e3e8,cfe0dc", "glassesProbability": 40},
    "education":      {"clothingColor": "6d8a5b,8a6d5b,5b7a6d", "glassesProbability": 45},
    "media":          {"clothingColor": "3d8a9e,b3589a,c9764a", "hatProbability": 20, "glassesProbability": 25},
    "manufacturing":  {"clothingColor": "3a5f8a,8a7a3a,4a6a8a", "glassesProbability": 25},
    "public-service": {"clothingColor": "2c4a6e,4a5d3a,3a4a6e", "glassesProbability": 30},
}
FALLBACK_SEED = "greenroom"  # 未知岗位兜底头像

# 肤色：不用 pixel-art 自带的候选表。那张表把八级色阶从最浅到最深各占一格、等概率抽，
# 于是一屏岗位头像里中棕到深棕接近一半（实测 164 个头像 48%），和真实人群不像，更不像
# 这个产品的用户。这里一种肤色都没删，只改抽中的比例——DiceBear 按下标等概率抽，同一个
# 值写几次就是几份权重。八级按深浅归五档，份数 12 / 24 / 10 / 4 / 2，合计 52。
# 与 app-v2 的 src/lib/avatar-tone.ts 是同一份分布，改一处要想到另一处。
SKIN_MIX = ",".join(
    ["ffdbac"] * 6 + ["f5cfa0"] * 6          # 偏浅 12
    + ["eac393"] * 12 + ["e0b687"] * 12      # 东亚常见的浅暖色 24
    + ["cb9e6e"] * 10                        # 中间的黄褐 10
    + ["b68655"] * 4                         # 棕 4
    + ["a26d3d"] + ["8d5524"]                # 深棕 2
)


def parse_roles():
    """[(industry_slug, en_title)]，en 作 seed，industry/en 作 key。"""
    out = []
    for p in sorted(ROLES.glob("*.md")):
        ind = p.stem
        for m in re.finditer(r"^##\s+(.+)$", p.read_text(encoding="utf-8"), re.M):
            head = m.group(1).strip()
            cn, _, en = head.partition("·")
            out.append((ind, (en or cn).strip()))
    return out


def strip_svg(svg: str) -> str:
    """剥 metadata 与多余空白，保留 CC0 来源由 README/此脚本注明。"""
    svg = re.sub(r"<metadata[\s\S]*?</metadata>", "", svg)
    svg = re.sub(r"<desc[\s\S]*?</desc>", "", svg)
    svg = re.sub(r">\s+<", "><", svg).strip()
    return svg


def fetch(seed: str, style: dict) -> str:
    q = {"seed": seed, "skinColor": SKIN_MIX, **{k: str(v) for k, v in style.items()}}
    url = API + "?" + urllib.parse.urlencode(q)
    # 缓存键带上整条请求的指纹。只按 seed 存的话，改了配色重跑会安静地拿回旧图，
    # 看起来跑成功了其实什么都没变
    key = re.sub(r"[^a-z0-9]+", "-", seed.lower()).strip("-")
    cached = CACHE / f"{key}.{hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]}.svg"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": "greenroom-embed-avatars/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                svg = strip_svg(r.read().decode("utf-8"))
            CACHE.mkdir(exist_ok=True)
            cached.write_text(svg, encoding="utf-8")
            time.sleep(0.1)
            return svg
        except Exception as e:
            if attempt == 2:
                raise SystemExit(f"拉取失败 {seed}: {e}")
            time.sleep(1.5 * (attempt + 1))


def main():
    roles = parse_roles()
    if not roles:
        raise SystemExit(f"没解析到岗位：{ROLES}")
    avatars = {}
    for ind, en in roles:
        style = IND_STYLE.get(ind, IND_STYLE["corporate"])
        avatars[f"{ind}/{en}"] = fetch(en, style)
    avatars["_fallback"] = fetch(FALLBACK_SEED, IND_STYLE["corporate"])

    payload = json.dumps(avatars, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # </script> 防注入

    html = HTML.read_text(encoding="utf-8")
    block = (
        f"{START}\n"
        f'<script id="avatar-data" type="application/json">{payload}</script>\n'
        f"{END}"
    )
    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    if pattern.search(html):
        html = pattern.sub(lambda _: block, html)
    elif "<!--KNOWLEDGE:START-->" in html:
        html = html.replace("<!--KNOWLEDGE:START-->", block + "\n<!--KNOWLEDGE:START-->", 1)
    else:
        raise SystemExit("HTML 里找不到 AVATARS 或 KNOWLEDGE 标记块")
    HTML.write_text(html, encoding="utf-8")
    print(f"已嵌入 {len(avatars)} 个像素头像，共 {len(payload):,} 字符 → {HTML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
