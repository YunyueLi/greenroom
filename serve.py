#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenroom 本地取数服务：把工作台目录按契约开放给任意客户端，单文件标准库、零依赖。

这是 docs/workspace-spec.md 那套工作台格式的参考读取端。它只提供取数接口，不带界面，也不调模型——
给 agent 当取数后端、自己写客户端渲染工作台，或者照着它实现一份自己的服务端，都从这里开始。

    python3 serve.py ~/my-greenroom        # 挂载工作台（jobs/ 下的岗位自动成为 personas）
    python3 serve.py                       # 不挂载 = 只有 /config 与静态取数

端点：
    /                  端点清单（JSON）
    /workspace/bundle  工作台 .md 全文 + 资产清单（实时读盘）
    /workspace/file    单文件取回（?path=，pdf 等二进制）
    /config            personas（自动扫 jobs/）
    /api/resolve-logo  公司图标解析（?company=&domain=，返回直链）
"""
import json
import sys
import re
import struct
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote, urlencode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else None

STATIC_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
}


# ---------------- 工作台读取（全部按 docs/workspace-spec.md 契约） ----------------

def _frontmatter(text):
    m = re.match(r"^---\n([\s\S]*?)\n---", text or "")
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def list_personas():
    """扫 jobs/ 目录自动发现岗位：persona key = 目录名，name = company · role。"""
    out = {}
    if not WORKSPACE:
        return out
    jobs = WORKSPACE / "jobs"
    if not jobs.exists():
        return out
    for d in sorted(jobs.iterdir()):
        jm = d / "job.md"
        if not (d.is_dir() and jm.exists()):
            continue
        try:
            fm = _frontmatter(jm.read_text(encoding="utf-8"))
        except Exception:
            continue
        company, role = fm.get("company", ""), fm.get("role", "")
        name = " · ".join(x for x in (company, role) if x) or d.name
        out[d.name] = name
    return out


# ---------------- 工作台打包 ----------------

def workspace_bundle():
    files, assets = {}, []
    if WORKSPACE and WORKSPACE.exists():
        for fp in sorted(WORKSPACE.rglob("*")):
            try:
                rel = fp.relative_to(WORKSPACE).as_posix()
                if any(seg.startswith(".") for seg in rel.split("/")):
                    continue
                if rel.count("/") > 4 or fp.is_dir():
                    continue
                suffix = fp.suffix.lower()
                if suffix in (".md", ".markdown"):
                    files[rel] = fp.read_text(encoding="utf-8")
                elif suffix == ".pdf":
                    assets.append(rel)
            except Exception:
                continue
    return {"root": WORKSPACE.name if WORKSPACE else "", "files": files, "assets": assets}


# ---------------- 公司高清 logo 自动解析（/api/resolve-logo） ----------------

_LOGO_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
_logo_cache = {}


def _img_size(data):
    """从图片字节读宽高（PNG / JPEG / GIF / ICO），读不出返回 (0, 0)。"""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24]); return w, h
        if data[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", data[6:10]); return w, h
        if data[:2] == b"\xff\xd8":  # JPEG：扫到 SOF 段读尺寸
            i, n = 2, len(data)
            while i + 9 < n:
                if data[i] != 0xFF:
                    i += 1; continue
                m = data[i + 1]
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
                i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
            return 0, 0
        if data[:4] == b"\x00\x00\x01\x00":  # ICO：取最大一帧
            cnt = struct.unpack("<H", data[4:6])[0]; best = 0
            for k in range(cnt):
                wb = data[6 + k * 16]; best = max(best, 256 if wb == 0 else wb)
            return best, best
    except Exception:
        pass
    return 0, 0


def _fetch_img(url, timeout=4, limit=900_000):
    """取图并校验，返回 (url, 最大边, 字节数) 或 None。拒绝非 200 / 非图片 / HTML。"""
    try:
        req = urllib.request.Request(url, headers=_LOGO_UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            ctype = (r.headers.get("Content-Type") or "").lower()
            data = r.read(limit)
        if not data:
            return None
        head = data[:64].lstrip().lower()
        if head.startswith(b"<!doctype") or head.startswith(b"<html") or "html" in ctype:
            return None
        if "image" not in ctype and not url.split("?")[0].lower().endswith((".ico", ".png", ".jpg", ".jpeg", ".gif")):
            return None
        w, h = _img_size(data)
        return (url, max(w, h), len(data))
    except Exception:
        return None


def _itunes_icon(company, domain=""):
    """App Store 官方图标（消费类 App 最准，512px）。命名强匹配 + 域名佐证（开发者官网域名含本域名主词，或厂商名含主词≥4），
    杜绝『同名无关 App』误配（如 converge.ai 误命中第三方 Converge App）。给了 domain 却佐证不上就不返回，交给域名权威源。"""
    norm = lambda s: re.sub(r"[\s\-–—_·•|()\[\]【】（）.,，、]+", "", (s or "").lower())
    target = norm(company)
    if not target:
        return ""
    labels = [x for x in domain.split(".") if x]
    dom_label = labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")
    countries = ["cn", "us"] if re.search(r"[一-鿿]", company) else ["us", "cn"]
    fallback = ""
    for cc in countries:
        try:
            q = urlencode({"term": company, "entity": "software", "limit": 8, "country": cc})
            req = urllib.request.Request("https://itunes.apple.com/search?" + q, headers=_LOGO_UA)
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status != 200:
                    continue
                results = json.loads(r.read(300_000).decode("utf-8", "ignore")).get("results", [])
            for it in results:
                nn = norm(it.get("trackName"))
                if not nn:
                    continue
                strong = (nn == target or nn.startswith(target)
                          or (target.startswith(nn) and len(nn) >= 4)
                          or target in nn or nn in target)
                if not strong:
                    continue
                art = it.get("artworkUrl512") or it.get("artworkUrl100") or it.get("artworkUrl60") or ""
                if not art:
                    continue
                art = re.sub(r"/\d+x\d+(bb)?\.(png|jpe?g)$", "/512x512bb.png", art)
                if dom_label:
                    try:
                        host_labels = set((urlparse(it.get("sellerUrl") or "").hostname or "").lower().split("."))
                    except Exception:
                        host_labels = set()
                    artist = re.sub(r"[^a-z0-9]", "", (it.get("artistName") or "").lower())
                    if dom_label in host_labels or (len(dom_label) >= 4 and dom_label in artist):
                        return art            # 域名佐证通过 → 强信任
                    # 有 domain 但本条佐证不上 → 跳过，避免误配
                elif not fallback:
                    fallback = art            # 无 domain 时，留首个强名匹配兜底
        except Exception:
            continue
    return fallback


def resolve_logo(company, domain):
    """解析公司高清图标，返回直链或空串。结果按 公司|域名 缓存。
    阶梯：App Store 官方图标 → Clearbit → 站点 apple-touch-icon → Google favicon(过滤通用地球) → DuckDuckGo。"""
    company = (company or "").strip()
    domain = re.sub(r"^https?://", "", (domain or "").strip().lower()).split("/")[0]
    key = company + "|" + domain
    if key in _logo_cache:
        return _logo_cache[key]
    found = _itunes_icon(company, domain)  # mzstatic 512；命名强匹配 + 域名佐证，不再回探
    if not found and domain:
        v = _fetch_img(f"https://logo.clearbit.com/{quote(domain)}?size=256")
        if v and v[1] >= 64:
            found = v[0]
    if not found and domain:
        for path in ("apple-touch-icon.png", "apple-touch-icon-precomposed.png"):
            v = _fetch_img(f"https://{domain}/{path}")
            if v and v[1] >= 96:
                found = v[0]; break
    if not found and domain:  # Google favicon：通用地球是 404（已拒）或 16px，这里再卡 32
        v = _fetch_img(f"https://www.google.com/s2/favicons?domain={quote(domain)}&sz=128")
        if v and v[1] >= 32:
            found = v[0]
    if not found and domain:
        v = _fetch_img(f"https://icons.duckduckgo.com/ip3/{quote(domain)}.ico")
        if v and v[1] >= 32:
            found = v[0]
    _logo_cache[key] = found
    return found


# ---------------- HTTP ----------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        # 带上长度，响应体的边界就不靠关连接来界定，客户端不会把正常响应读成连接中断
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        route = url.path
        if route == "/":
            index = {
                "service": "greenroom local backend",
                "spec": "docs/workspace-spec.md",
                "workspace": str(WORKSPACE) if WORKSPACE else None,
                "endpoints": {
                    "GET /workspace/bundle": "工作台 .md 全文 + 资产清单",
                    "GET /workspace/file?path=": "单文件取回",
                    "GET /config": "personas（自动扫 jobs/）",
                    "GET /api/resolve-logo?company=&domain=": "公司图标解析",
                },
            }
            self._send(200, json.dumps(index, ensure_ascii=False, indent=2).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif route == "/config":
            cfg = {"personas": list_personas()}
            self._send(200, json.dumps(cfg, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif route == "/api/resolve-logo":
            qs = parse_qs(url.query)
            logo = resolve_logo((qs.get("company") or [""])[0], (qs.get("domain") or [""])[0])
            self._send(200, json.dumps({"logo": logo}, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif route == "/workspace/bundle":
            if WORKSPACE is None:
                self._send(404, b"no workspace mounted")
                return
            self._send(200, json.dumps(workspace_bundle(), ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif route == "/workspace/file":
            rel = unquote((parse_qs(url.query).get("path") or [""])[0])
            if WORKSPACE is None or not rel or rel.startswith("/") or ".." in rel.split("/"):
                self._send(400, b"bad path")
                return
            fp = WORKSPACE / rel
            if not (fp.exists() and fp.is_file()):
                self._send(404, b"not found")
                return
            suffix = fp.suffix.lower()
            ctype = ("application/pdf" if suffix == ".pdf"
                     else "text/markdown; charset=utf-8" if suffix in (".md", ".markdown")
                     else "application/octet-stream")
            self._send(200, fp.read_bytes(), ctype)
        else:
            rel = unquote(route.lstrip("/"))
            if rel and ".." not in rel.split("/") and not rel.startswith("."):
                fp = ROOT / rel
                suffix = fp.suffix.lower()
                if fp.is_file() and suffix in STATIC_TYPES:
                    self._send(200, fp.read_bytes(), STATIC_TYPES[suffix])
                    return
            self._send(404, b"not found")

    def do_POST(self):
        # 本服务只取数，没有任何 POST 端点。这个方法存在是为了让 404 带上 CORS 头：
        # 标准库默认回 501 且不带 Access-Control-Allow-Origin，浏览器端客户端只会看到一个看不出原因的跨域错误。
        #
        # 回 404 之前必须把请求体读干。不读就直接关连接的话，内核回 RST，客户端在读响应体时
        # 撞上 ConnectionResetError——本该看到的 404 变成一个连不上的错误。撞过期地址的客户端
        # 往往正把整个工作台上下文 POST 上来，体积远超一个包，这条路径是常态。
        try:
            left = int(self.headers.get("Content-Length") or 0)
            while left > 0:
                chunk = self.rfile.read(min(left, 65536))
                if not chunk:
                    break
                left -= len(chunk)
        except (ValueError, OSError):
            pass
        self._send(404, b"not found")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    ws = str(WORKSPACE) if WORKSPACE else "（未挂载：python3 serve.py ~/my-greenroom）"
    personas = list_personas()
    print("greenroom 本地取数服务已启动")
    print(f"  端点     http://127.0.0.1:{PORT}/ （格式见 docs/workspace-spec.md）")
    print(f"  工作台   {ws}")
    print(f"  岗位     {('、'.join(personas.values())) if personas else '（无 jobs/ 目录）'}")
    print("  关闭     Control + C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已关闭。")


if __name__ == "__main__":
    main()
