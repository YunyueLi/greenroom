#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenroom 本地后端：工作台直连 + 实时提词 + 模拟面试，单文件标准库、零依赖。

这是 docs/realtime-bridge.md 那套 HTTP 契约的参考实现。它只提供接口，不带界面——
自己写提词客户端、给 agent 当取数后端，或者照着它实现一份自己的服务端，都从这里开始。

    python3 serve.py ~/my-greenroom        # 挂载工作台（jobs/ 下的岗位自动成为提词与模拟面试的选项）
    python3 serve.py                       # 不挂载 = 只有 /config 与静态取数

无 API key 时是纯阅读服务；要解锁「实时助手」与「模拟面试」，在工作台根目录（或本脚本目录）放 .env：

    MODEL_API_KEY=sk-xxxx                  # 必填（兼容旧名 DEEPSEEK_API_KEY / OPENAI_API_KEY）
    MODEL_API_BASE=https://api.deepseek.com    # 可选：任意 OpenAI 兼容接口（OpenAI / DeepSeek / Ollama…）
    MODEL_NAME=deepseek-v4-flash               # 可选：模型名

端点（协议见 docs/realtime-bridge.md）：
    /                  端点清单（JSON）
    /workspace/bundle  工作台 .md 全文 + 资产清单（实时读盘）
    /workspace/file    单文件取回（?path=，pdf 等二进制）
    /config            personas（自动扫 jobs/）+ 模型与 key 状态
    /api/answer        实时提词（流式纯文本）
    /api/mock          模拟面试：面试官出题 / 教练报告（流式纯文本）
    /api/setup         不依赖 Claude 的工作台生成：简历+公司+岗位+JD → resume/job/intel（流式进度）
"""
import json
import os
import sys
import re
import struct
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote, urlencode
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765
ROOT = Path(__file__).resolve().parent
WORKSPACE = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else None

DEFAULT_API_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
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


# ---------------- 配置（.env：工作台根目录优先，其次脚本目录） ----------------

def _read_env(name):
    val = os.environ.get(name, "").strip()
    if val:
        return val
    for d in ([WORKSPACE] if WORKSPACE else []) + [ROOT]:
        f = d / ".env"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def get_api_key():
    k = (_read_env("MODEL_API_KEY") or _read_env("DEEPSEEK_API_KEY") or _read_env("OPENAI_API_KEY")).strip()
    # 占位假 key（start.sh 从 .env.example 生成的）视作未配置，否则会拿它去调模型 → 401
    return "" if k == "sk-your-own-key-here" else k


def get_api_base():
    return (_read_env("MODEL_API_BASE") or DEFAULT_API_BASE).rstrip("/")


def get_model():
    return _read_env("MODEL_NAME") or _read_env("DEEPSEEK_MODEL") or DEFAULT_MODEL


def build_payload(messages, temperature, max_tokens, model=None):
    p = {"model": model or get_model(), "messages": messages, "stream": True,
         "temperature": temperature, "max_tokens": max_tokens}
    # DeepSeek V4 系默认开 thinking（首字延迟数秒），提词场景显式关掉；.env MODEL_THINKING=enabled 可开
    if "deepseek" in get_api_base():
        p["thinking"] = {"type": _read_env("MODEL_THINKING") or _read_env("DEEPSEEK_THINKING") or "disabled"}
    return json.dumps(p).encode("utf-8")


# ---------------- 工作台读取（全部按 docs/workspace-spec.md 契约） ----------------

def _read_ws(rel):
    if not WORKSPACE:
        return ""
    fp = WORKSPACE / rel
    try:
        return fp.read_text(encoding="utf-8") if fp.exists() else ""
    except Exception:
        return ""


def _frontmatter(text):
    m = re.match(r"^---\n([\s\S]*?)\n---", text or "")
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    return fm


def candidate_name():
    fm = _frontmatter(_read_ws("profile.md")) or _frontmatter(_read_ws("resume.md"))
    if fm.get("name"):
        return fm["name"]
    m = re.search(r"^#\s+(.+)$", _read_ws("resume.md"), re.M)
    return m.group(1).strip() if m else "候选人"


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


def persona_name(slug):
    return list_personas().get(slug) or slug


def load_transcript(slug):
    return _read_ws(f"jobs/{slug}/script.md") or "（该岗位还没有逐字稿：先跑 /greenroom:interview-script 生成）"


# ---------------- 实时提词 prompt ----------------

def build_system_prompt(slug, detail):
    name = candidate_name()
    transcript = load_transcript(slug)
    length_rule = (
        "长度以把这道题答透为准——有逐字稿就把那题的完整内容给足（数字、机制、论证一个不丢），可以讲到 1–2 分钟；别为了精炼牺牲质量。第一句必须是能照着直接念出口的话（提词从开头读起，新内容只往下接）。"
        if detail == "brief"
        else "给完整版本，可以讲到约 2 分钟，多铺一层细节、机制或例子。"
    )
    return f"""你是{name}的实时面试答题搭子。他正在面：{persona_name(slug)}。他会把面试官刚问出口的话原样打给你，你唯一的任务：立刻给一段「能直接念出口」的第一人称回答。他边看边念，所以要快、要短、像真人说话。

# 输出规则（最重要）
1. 开口即答案，第一人称，用他的口吻。没有任何前言（不要「好的」「这个问题在考察…」「建议你…」「以下是」）。
2. 第一行写 `【这么起】` 再跟一句能立刻开口的缓冲话（≤25 字）：给结论预告或复述要点，让他扫一眼先讲出去、争取思考时间；别把核心数字塞在这句里。
3. 之后分点给骨架，分点数量按内容定、把内容讲全，每点是可直接念的整句，**关键词加粗**方便他跳读。
4. {length_rule}他打「短」就压成 20–30 秒一句话版；打「深」或「展开」给完整版。
4b. 问题信息量大、多个子问或有歧义时：【这么起】改成复述确认式开场（「我理解您问的是…，我先从最关键的讲」），正文按最可能的理解作答；若确实存在另一种理解，最后用一行「若您问的是…，核心是…」兜住。
5. 命中逐字稿里的题：直接用那题的内容和原话，但贴着面试官此刻的具体问法微调，别整段背书。
6. 没有现成题：基于逐字稿里他的档案和素材即兴，但人设、口径、姿态必须和逐字稿一致。
7. 他打字会潦草、有错别字、可能是语音转文字。先猜出面试官真正问的是什么，再答，别纠结字面。
8. 如果他打的只是寒暄/过渡/口水话/识别噪音，只回一行「（继续听…）」，不硬答。

# 反编造红线（面试可被当场核实，编造比答不出更致命）
- 具体数字、职级、时间、项目细节，只能用逐字稿里出现过的；没有的，给定性说法（「一个不小的盘子」「带来明显增量」），绝不自己填一个数。
- 拿不准就往定性和逐字稿原话上靠，不要为了答得漂亮而虚构。

# 姿态（按高阶面试标准，不是求职者辩解）
- 从容、有掌控感。不自我否定、不示弱，绝不替面试官贬低他的履历或任职时长。
- 不卑微、不靠承诺表忠心；用「这件事值不值得我长期做」的判断说话。
- 不元叙述（别说「这个问题我正面回答」这种废话），开口即内容。不自我标榜、不喊口号。

# 语言（禁 AI 腔，一听就露背稿）
- 禁用：不是…而是 / 而非 / 而不是 / 恰恰是 / 这正是 / 不仅…而且 / 值得一提 / 与其…不如；不用「正好、反而」硬造对比。
- 少破折号、少工整对仗金句。说人话、口语流动，但用词有分量。

# 快捷指令（他当场会打，理解为对你上一条回答的调整）
短＝一句话 20–30 秒版 ｜ 深 / 展开＝完整版 ｜ 换＝换角度重答 ｜ 英文＝英文口语版 ｜ 怎么接＝给一句过渡或反问把球递回去 ｜ 追问＝预判面试官接下来最可能追的 1–2 问

==================== 逐字稿知识库（你回答的唯一事实来源）====================
{transcript}
==================== 知识库结束 ===================="""


# ---------------- 模拟面试 prompt ----------------

ROUND_FOCUS = {
    "hr": "HR 轮：动机与稳定性（为什么离开上家、为什么是我们、职业规划）、薪酬期望、文化匹配。",
    "biz": "业务面：简历项目深挖（数字怎么来的、个人贡献、失败复盘）、岗位专业题、实际工作场景题。",
    "director": "高管面：判断力与方向感（行业判断、方法论迁移、带人带事）、和老板风格的匹配。",
    "final": "终面：价值观、长期主义、综合素质，外加对前几轮疑点的复核。",
    "cross": "交叉面：来自相邻团队的面试官（非直接用人方），考察通用能力与协作——拿一个候选人不熟的业务场景看他怎么拆、跨团队冲突怎么处理、方法论能不能离开熟悉领域还成立；对岗位专业细节问得少，对思维质量和真诚度盯得紧。",
}
STYLE_DESC = {
    "gentle": "温和耐心，多给候选人台阶，但关键处仍会确认细节。",
    "standard": "专业标准，节奏适中，该追问就追问。",
    "tough": "严苛压迫式：对每个数字和说法刨根问底，三层追问起步，对含糊回答直接点破，不留情面。",
}


def build_mock_interviewer_prompt(slug, round_type, style, lang, minutes):
    resume = _read_ws("resume.md") or "（无简历，按候选人口述提问）"
    jd = _read_ws(f"jobs/{slug}/job.md")
    intel = _read_ws(f"jobs/{slug}/intel.md")
    lang_rule = "全程用英文面试。" if lang == "en" else "全程用中文面试。"
    return f"""你在进行一场高度拟真的模拟面试，扮演面试官。岗位：{persona_name(slug)}，本轮性质：{ROUND_FOCUS.get(round_type, ROUND_FOCUS['biz'])}
你的风格：{STYLE_DESC.get(style, STYLE_DESC['standard'])}{lang_rule}

# 候选人简历
{resume}

# 岗位 JD
{jd or '（无 JD 文件）'}

# 岗位情报（含真实面试官档案与考题预测，照此风格与考点出题）
{intel or '（无情报文件）'}

# 面试规则（严格遵守）
1. 你只输出面试官说的话，第一人称，无任何旁白、标注、括号说明。
2. 一次只问一个问题。候选人回答后：先一句自然的口头反应（嗯、好的、有意思），再决定追问还是换题。
3. 含糊、宏大、没有数字或个人贡献不清的回答，必须追问到具体（怎么做的？数字怎么算的？你自己做了哪部分？）。
4. 节奏按真实面试：开场让候选人自我介绍 → 简历与项目深挖 → 岗位匹配与专业题 → 留几分钟反问。整场对话设计成约 {minutes} 分钟的信息量（大约 {max(4, int(minutes) // 5)} 个主话题）。
5. 候选人明显答得好时不要廉价表扬，按真实面试官的克制反应。
6. 当主话题问完、或候选人请求结束时：说一段自然的结束语（含下一步流程），并在最后单独一行输出 [面试结束]。
7. 候选人发来「[开始面试]」时，从你的开场白和第一个问题开始。"""


def build_mock_coach_prompt(slug):
    jd = _read_ws(f"jobs/{slug}/job.md")
    return f"""你是顶级面试教练。用户会发来一场模拟面试（岗位：{persona_name(slug)}）的完整问答记录，输出一份犀利、可执行的复盘报告，Markdown 格式：

## 总评
两三句话，直说这场面试过不过、卡在哪。

## 评分
| 维度 | 分(1-5) | 依据 |
四个维度：结构化表达 / 证据密度（数字与出处）/ 岗位匹配 / 追问抗压。依据引用候选人原话片段。

## 最该修的三个点
每点：候选人原话 → 问题 → 改成怎么说（给出可直接背的版本）。

# 岗位 JD
{jd or ''}"""


# ---------------- 工作台生成（/api/setup：不依赖 Claude 的入口） ----------------

def llm_complete(system, user, max_tokens=4000):
    """非流式补全（生成工作台文件用）。"""
    payload = {"model": get_model(),
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "stream": False, "temperature": 0.3, "max_tokens": max_tokens}
    if "deepseek" in get_api_base():
        payload["thinking"] = {"type": "disabled"}
    req = urllib.request.Request(
        get_api_base() + "/chat/completions", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {get_api_key()}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    return obj["choices"][0]["message"]["content"]


def split_files(text):
    """按 ===FILE:path=== 标记切多文件输出。"""
    out = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^===FILE:(.+?)===\s*$", line.strip())
        if m:
            cur = m.group(1).strip()
            out[cur] = []
            continue
        if line.strip() == "===END===":
            cur = None
            continue
        if cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() + "\n" for k, v in out.items()}


SETUP_RESUME_SYS = """你负责把候选人的简历原文转写成 greenroom 工作台的两个 Markdown 文件。只输出文件内容，用标记分隔，不加任何解释。

输出格式（严格遵守）：
===FILE:resume.md===
---
type: resume
name: <候选人姓名>
updated: <YYYY-MM>
---

# <姓名>

<联系方式一行>

## <分区名，如 工作经历>

### <公司>｜<岗位>｜<YYYY.MM – YYYY.MM 或 至今>

- <要点，忠实原文，不增不减不润色>
…
===FILE:profile.md===
---
type: profile
name: <姓名>
updated: <YYYY-MM>
---

# 候选人档案

<三五行：当前身份、履历主线、可量化亮点，全部来自简历原文>
===END===

规则：忠实转写、零编造；日期一律「YYYY.MM – YYYY.MM」（在职用「至今」）；条目标题必须是「公司｜岗位｜日期」三段式（全角｜）；教育经历放「## 教育经历」分区。"""

SETUP_JOB_SYS = """你负责为 greenroom 面试准备工作台生成一个新岗位的档案。只输出文件内容，用标记分隔，不加任何解释。

第一行先单独输出岗位的目录名：SLUG: <小写英文-连字符，如 acme-product-manager>

然后输出两个文件：
===FILE:jobs/{slug}/job.md===
---
type: job
company: <公司名>
role: <岗位名>
domain: <公司官网域名，凭常识填，不确定留空>
status: tracking
updated: <YYYY-MM>
---

# <公司> · <岗位>

<JD 原文，原样保留>

<若有补充信息，列在「## 补充信息」下>
===FILE:jobs/{slug}/intel.md===
---
type: intel
job: {slug}
updated: <YYYY-MM>
---

# <公司> · <岗位> · 岗位情报（首稿）

> 本文件由模型基于自身知识生成（未联网调研）。建议之后用 /greenroom:job-intel 做带 web 检索的深度版替换。

## 公司概况
<你所知的公司业务、阶段、文化，三五条；不确定的明确标注「待核实」>

## JD 拆解
<逐条拆 JD 要求 → 这条考察什么、候选人简历里哪段经历能对上（对照下方简历）>

## 高概率考题（按轮次）
<HR 轮 3 题 / 业务面 5 题 / 高管面 2 题，贴着 JD 与简历出>

## 建议准备动作
<三条以内>
===END===

规则：JD 原文一字不动；公司信息凭真实知识、宁缺毋滥；考题必须扣 JD 和简历的交集。"""


def setup_storybank_skeleton():
    return """---
type: story-bank
updated: {date}
---

# 经历库

> 真实经历整理成经历卡：事实和数字只有一份、都标出处，讲法按岗位选。用 /greenroom:story-bank 生成，或手写。
""".replace("{date}", __import__("datetime").date.today().strftime("%Y-%m"))


# ---------------- JD 链接抓取（/api/fetch-jd） ----------------

class _TextExtractor(__import__("html.parser", fromlist=["HTMLParser"]).HTMLParser):
    _SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer"}

    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data.strip())


def fetch_page_text(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read(2_000_000)
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            html = raw.decode("gbk", "ignore")
    ex = _TextExtractor()
    ex.feed(html)
    return "\n".join(ex.parts)


FETCH_JD_SYS = """从下面的网页文本里提取招聘信息，只输出一个 JSON 对象，不加任何解释、不加代码块标记：
{"company": "公司名（中文优先）", "role": "岗位名", "jd": "职位描述全文（职责+要求，保留原文行文，Markdown 列表）", "domain": "公司官网域名（凭常识，不确定留空）"}
若页面里根本没有招聘信息，输出 {"error": "页面里没有可识别的职位信息"}。"""


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


# ---------------- 公司高清 logo 自动解析（/api/resolve-logo + setup 内嵌） ----------------

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
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Greenroom-Key, X-Greenroom-Model")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        route = url.path
        if route == "/":
            index = {
                "service": "greenroom local backend",
                "spec": "docs/realtime-bridge.md",
                "workspace": str(WORKSPACE) if WORKSPACE else None,
                "endpoints": {
                    "GET /workspace/bundle": "工作台 .md 全文 + 资产清单",
                    "GET /workspace/file?path=": "单文件取回",
                    "GET /config": "personas + 模型与 key 状态",
                    "POST /api/answer": "实时提词（流式纯文本）",
                    "POST /api/mock": "模拟面试（流式纯文本）",
                    "POST /api/setup": "工作台生成（流式进度）",
                },
            }
            self._send(200, json.dumps(index, ensure_ascii=False, indent=2).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif route == "/config":
            cfg = {"has_key": bool(get_api_key()), "model": get_model(), "personas": list_personas()}
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
        if self.path == "/api/answer":
            self._handle_answer()
        elif self.path == "/api/mock":
            self._handle_mock()
        elif self.path == "/api/setup":
            self._handle_setup()
        elif self.path == "/api/ping":
            self._handle_ping()
        elif self.path == "/api/fetch-jd":
            self._handle_fetch_jd()
        else:
            self._send(404, b"not found")

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return None

    def _require_key(self):
        key = get_api_key()
        if not key:
            self._send(401, "未配置 MODEL_API_KEY：在工作台根目录的 .env 写一行 MODEL_API_KEY=sk-xxx 后重启 serve.py。".encode("utf-8"))
        return key

    def _byok_key(self):
        """BYOK：优先用请求头 X-Greenroom-Key（客户端逐请求带上，本服务不落盘），否则回退 .env。
        占位假 key 视作未配置。返回 (key, model)；无 key 时已发 401、返回 (None, None)。"""
        hk = (self.headers.get("X-Greenroom-Key") or "").strip()
        if hk == "sk-your-own-key-here":
            hk = ""
        key = hk or get_api_key()
        if not key:
            self._send(401, "未配置模型 key：在 .env 写 MODEL_API_KEY=sk-xxx，或让客户端逐请求带上 X-Greenroom-Key 请求头。".encode("utf-8"))
            return None, None
        model = (self.headers.get("X-Greenroom-Model") or "").strip() or get_model()
        return key, model

    def _handle_ping(self):
        """极简连接探测：不走提词/面试 prompt，直接让模型回两个字，纯验 key+model+连通。返回 JSON（永远 200，结果在 body）。"""
        def out(d):
            self._send(200, json.dumps(d, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
        hk = (self.headers.get("X-Greenroom-Key") or "").strip()
        if hk == "sk-your-own-key-here":
            hk = ""
        key = hk or get_api_key()
        model = (self.headers.get("X-Greenroom-Model") or "").strip() or get_model()
        if not key:
            return out({"ok": False, "error": "未填 key"})
        payload = {"model": model, "messages": [{"role": "user", "content": "只回两个字：正常"}],
                   "stream": False, "max_tokens": 16, "temperature": 0}
        if "deepseek" in get_api_base():
            payload["thinking"] = {"type": "disabled"}
        try:
            r = urllib.request.Request(get_api_base() + "/chat/completions",
                                       data=json.dumps(payload).encode("utf-8"),
                                       headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                                       method="POST")
            with urllib.request.urlopen(r, timeout=30) as resp:
                obj = json.loads(resp.read().decode("utf-8"))
            sample = (((obj.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            out({"ok": bool(sample), "model": model, "sample": sample[:40],
                 "raw": "" if sample else json.dumps(obj, ensure_ascii=False)[:200]})
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            try:
                msg = (json.loads(body).get("error") or {}).get("message") or body[:160]
            except Exception:
                msg = body[:160]
            out({"ok": False, "status": e.code, "error": msg})
        except Exception as e:
            out({"ok": False, "error": str(e)[:160]})

    def _handle_answer(self):
        req = self._read_json()
        if req is None:
            self._send(400, b"bad request")
            return
        question = (req.get("question") or "").strip()
        slug = req.get("persona") or ""
        detail = req.get("detail") or "brief"
        history = req.get("history") or []
        if not question:
            self._send(400, b"empty question")
            return
        api_key, model = self._byok_key()
        if not api_key:
            return
        messages = [{"role": "system", "content": build_system_prompt(slug, detail)}]
        for h in history[-12:]:
            role, content = h.get("role"), (h.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": question})
        self._stream_upstream(build_payload(messages, 0.3, 800, model), api_key)

    def _handle_mock(self):
        req = self._read_json()
        if req is None:
            self._send(400, b"bad request")
            return
        api_key, model = self._byok_key()
        if not api_key:
            return
        slug = req.get("persona") or ""
        stage = req.get("stage") or "interview"
        history = req.get("history") or []
        if stage == "report":
            system = build_mock_coach_prompt(slug)
            qa = "\n\n".join(
                ("面试官：" if h.get("role") == "assistant" else "候选人：") + (h.get("content") or "")
                for h in history if h.get("content")
            )
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": "完整面试记录如下，请出报告：\n\n" + qa}]
            max_tokens = 2000
        else:
            system = build_mock_interviewer_prompt(
                slug, req.get("round") or "biz", req.get("style") or "standard",
                req.get("lang") or "zh", req.get("minutes") or 30)
            messages = [{"role": "system", "content": system}]
            for h in history[-40:]:
                role, content = h.get("role"), (h.get("content") or "").strip()
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
            max_tokens = 500
        self._stream_upstream(build_payload(messages, 0.5, max_tokens, model), api_key)

    def _handle_fetch_jd(self):
        """贴链接自动填充：抓取页面 → LLM 提取 {company, role, jd, domain}。"""
        req = self._read_json()
        if req is None or not (req.get("url") or "").strip():
            self._send(400, b"need url")
            return
        url = req["url"].strip()
        if not re.match(r"^https?://", url):
            self._send(400, "链接需要以 http(s):// 开头".encode("utf-8"))
            return
        api_key = self._require_key()
        if not api_key:
            return
        try:
            text = fetch_page_text(url)
        except Exception as e:
            self._send(502, f"抓取失败（站点可能需要登录或有反爬）：{e}".encode("utf-8"))
            return
        if len(text.strip()) < 80:
            self._send(502, "页面没有可读文本（多半是登录墙或纯前端渲染），请手动粘贴 JD。".encode("utf-8"))
            return
        try:
            out = llm_complete(FETCH_JD_SYS, text[:24000], 2500)
            m = re.search(r"\{[\s\S]*\}", out)
            obj = json.loads(m.group(0)) if m else {}
        except Exception as e:
            self._send(500, f"提取失败：{e}".encode("utf-8"))
            return
        if obj.get("error") or not obj.get("jd"):
            self._send(422, (obj.get("error") or "页面里没有可识别的职位信息").encode("utf-8"))
            return
        self._send(200, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _handle_setup(self):
        """不依赖 Claude 的工作台生成：简历转写 + 岗位档案 + 调研底稿，流式进度。
        协议：POST JSON {company, role, jd, notes?, resume_text?, resume_pdf_b64?, replace_resume?}
        响应：text/plain 按行——##STEP 进度 / ##OK {json} / ##ERR 信息"""
        req = self._read_json()
        if req is None:
            self._send(400, b"bad request")
            return
        company = (req.get("company") or "").strip()
        role = (req.get("role") or "").strip()
        jd = (req.get("jd") or "").strip()
        notes = (req.get("notes") or "").strip()
        resume_text = (req.get("resume_text") or "").strip()
        if not (company and role and jd):
            self._send(400, "公司、岗位、JD 为必填".encode("utf-8"))
            return
        if WORKSPACE is None:
            self._send(400, "服务未挂载工作台目录（启动时：python3 serve.py ~/my-greenroom）".encode("utf-8"))
            return
        api_key = self._require_key()
        if not api_key:
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        def emit(line):
            try:
                self.wfile.write((line + "\n").encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass

        try:
            WORKSPACE.mkdir(parents=True, exist_ok=True)
            # 1) 简历：提供了文本，且（无 resume.md 或要求替换）才转写
            has_resume = (WORKSPACE / "resume.md").exists()
            if resume_text and (req.get("replace_resume") or not has_resume):
                emit("##STEP 正在转写简历（契约格式 + 候选人档案）…")
                today = __import__("datetime").date.today().strftime("%Y-%m")
                out = llm_complete(SETUP_RESUME_SYS, f"（今天日期：{today}，updated 字段用它）\n\n" + resume_text[:20000])
                files = split_files(out)
                for rel in ("resume.md", "profile.md"):
                    if files.get(rel):
                        (WORKSPACE / rel).write_text(files[rel], encoding="utf-8")
            elif resume_text:
                emit("##STEP 已有 resume.md，跳过简历转写")
            # PDF 原件存档（可选）
            b64 = req.get("resume_pdf_b64") or ""
            if b64 and len(b64) < 14_000_000:
                try:
                    import base64
                    (WORKSPACE / "resume.pdf").write_bytes(base64.b64decode(b64))
                    emit("##STEP 简历 PDF 原件已存入工作台")
                except Exception:
                    emit("##STEP PDF 存档失败（不影响后续）")
            # 附件：文本类内容注入生成，原件落 jobs/<slug>/attachments/（slug 出来后再写）
            atts = req.get("attachments") or []
            att_texts = []
            for a in atts[:8]:
                nm = re.sub(r"[^\w.\u4e00-\u9fff-]", "_", (a.get("name") or "附件"))[:80]
                if a.get("text"):
                    att_texts.append(f"## 附件：{nm}\n{a['text'][:6000]}")
            # 2) 岗位档案 + 情报首稿
            emit("##STEP 正在生成岗位档案与调研底稿…")
            today = __import__("datetime").date.today().strftime("%Y-%m")
            extra = (notes or "") + ("\n\n" + "\n\n".join(att_texts) if att_texts else "")
            user = (f"（今天日期：{today}，updated 字段用它）\n公司：{company}\n岗位：{role}\n\n# JD\n{jd[:12000]}\n\n# 补充信息\n{extra or '无'}"
                    f"\n\n# 候选人简历（用于 JD 拆解对照）\n{_read_ws('resume.md')[:8000] or '（暂无）'}")
            out = llm_complete(SETUP_JOB_SYS, user, 5000)
            m = re.search(r"^SLUG:\s*([a-z0-9][a-z0-9-]{1,48})\s*$", out, re.M)
            if not m:
                emit("##ERR 模型未返回有效岗位目录名，请重试")
                return
            slug = m.group(1)
            if (WORKSPACE / "jobs" / slug).exists():
                emit(f"##ERR 岗位 {slug} 已存在（同一岗位重复添加？如需重建请先在工作台删除该目录）")
                return
            files = {k.replace("{slug}", slug): v for k, v in split_files(out).items()}
            allowed = {f"jobs/{slug}/job.md", f"jobs/{slug}/intel.md"}
            wrote = 0
            for rel, content in files.items():
                if rel not in allowed or not content.strip():
                    continue
                fp = WORKSPACE / rel
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")
                wrote += 1
            if not wrote:
                emit("##ERR 模型输出里没有可写入的岗位文件，请重试")
                return
            # 附件原件落盘
            if atts:
                adir = WORKSPACE / "jobs" / slug / "attachments"
                saved = 0
                for a in atts[:8]:
                    nm = re.sub(r"[^\w.\u4e00-\u9fff-]", "_", (a.get("name") or "附件"))[:80]
                    try:
                        if a.get("b64"):
                            import base64
                            adir.mkdir(parents=True, exist_ok=True)
                            (adir / nm).write_bytes(base64.b64decode(a["b64"]))
                            saved += 1
                        elif a.get("text"):
                            adir.mkdir(parents=True, exist_ok=True)
                            (adir / (nm if nm.endswith((".md", ".txt")) else nm + ".md")).write_text(a["text"], encoding="utf-8")
                            saved += 1
                    except Exception:
                        continue
                if saved:
                    emit(f"##STEP 已存入 {saved} 个附件（jobs/{slug}/attachments/）")
            # 时间线首条（## 时间线 区块，见 docs/workspace-spec.md；后续轮次手动或 debrief 回写）
            jp = WORKSPACE / "jobs" / slug / "job.md"
            today_full = __import__("datetime").date.today().strftime("%Y.%m.%d")
            try:
                jtxt = jp.read_text(encoding="utf-8")
                if "## 时间线" not in jtxt:
                    jp.write_text(jtxt.rstrip() + f"\n\n## 时间线\n\n- {today_full} 建档\n", encoding="utf-8")
            except Exception:
                pass
            # logo：自动解析公司高清图标，写进 job.md frontmatter（用户上传材料后零手动）
            try:
                jtxt = jp.read_text(encoding="utf-8")
                if not re.search(r"^logo:\s*\S", jtxt, re.M):
                    mdom = re.search(r"^domain:\s*(.+)$", jtxt, re.M)
                    dom = mdom.group(1).strip() if mdom else ""
                    emit("##STEP 正在解析公司高清图标…")
                    logo = resolve_logo(company, dom)
                    if logo:
                        anchor = r"^(domain:.*)$" if mdom else r"^(role:.*)$"
                        jtxt = re.sub(anchor, lambda m: m.group(1) + "\nlogo: " + logo, jtxt, count=1, flags=re.M)
                        jp.write_text(jtxt, encoding="utf-8")
                        emit("##STEP 已写入高清图标")
                    else:
                        emit("##STEP 未匹配到图标，先用公司名首字母（可手动补 logo:）")
            except Exception:
                pass
            # 3) 骨架补齐
            if not (WORKSPACE / "story-bank.md").exists():
                (WORKSPACE / "story-bank.md").write_text(setup_storybank_skeleton(), encoding="utf-8")
            emit("##STEP 写入完成")
            emit("##OK " + json.dumps({"slug": slug, "name": f"{company} · {role}"}, ensure_ascii=False))
        except Exception as e:
            emit(f"##ERR {e}")

    def _stream_upstream(self, payload, api_key):
        up_req = urllib.request.Request(
            get_api_base() + "/chat/completions", data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            with urllib.request.urlopen(up_req, timeout=90) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", "ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj["choices"][0]["delta"].get("content", "")
                    except Exception:
                        continue
                    if delta:
                        self.wfile.write(delta.encode("utf-8"))
                        self.wfile.flush()
        except urllib.error.HTTPError as e:
            try:
                self.wfile.write(f"\n[上游报错 {e.code}] {e.read().decode('utf-8','ignore')}".encode("utf-8"))
            except Exception:
                pass
        except Exception as e:
            try:
                self.wfile.write(f"\n[连接出错] {e}".encode("utf-8"))
            except Exception:
                pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    ws = str(WORKSPACE) if WORKSPACE else "（未挂载：python3 serve.py ~/my-greenroom）"
    key_status = "已配置 ✓（实时助手 / 模拟面试可用）" if get_api_key() else "未配置（纯阅读模式；.env 写 MODEL_API_KEY 解锁提词与模拟面试）"
    personas = list_personas()
    print("greenroom 本地后端已启动")
    print(f"  端点     http://127.0.0.1:{PORT}/ （契约见 docs/realtime-bridge.md）")
    print(f"  工作台   {ws}")
    print(f"  岗位     {('、'.join(personas.values())) if personas else '（无 jobs/ 目录）'}")
    print(f"  模型     {get_model()} · key {key_status}")
    print("  关闭     Control + C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已关闭。")


if __name__ == "__main__":
    main()
