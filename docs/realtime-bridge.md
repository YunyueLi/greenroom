# 实时提词工具对接（realtime bridge）

Greenroom 是赛前准备工具。如果你另外在用实时提词类工具（面试中转写对方语音、生成提示），工作台可以作为它的**受控上下文源**——重点是只喂它你准备过的材料，让提词器从逐字稿里取材，不替你编造。

## 上下文组装契约

实时工具的 system prompt 按这个顺序组装，输出规则在前，逐字稿（取材库）在后，岗位调研可选作第二段：

```
你是 <候选人名> 的实时答题提词器。他正在面：<公司 · 岗位>。

# 输出规则
1. 开口即答案，第一人称，用他的口吻
2. 第一行给 ≤25 字、能直接开口的起手句
3. 其余给要点，不写完整段落
4. 任何数字、职级、时间、项目细节，只能用下方逐字稿和岗位调研里出现过的；没有就提示「这个数字稿里没有」，不要编

==================== 逐字稿知识库 ====================
<jobs/<slug>/script.md 全文>
==================== 知识库结束 ====================
```

逐字稿本身已经把每个数字的口径和出处写定（见 `docs/workspace-spec.md` 的 script.md 契约），所以提词器只要严守「只用稿里出现过的」这一条，就不会当场说出一个没准备过的数字。

## 两种取数方式

**方式一：HTTP 直读工作台（推荐自建工具用）**。后端实现 `GET /workspace/bundle` 与 `GET /workspace/file?path=`（契约见 `docs/workspace-spec.md`「工具取数约定」），客户端即可自动直连、免选文件夹；同一个 bundle 也够提词后端组装上下文。仓库自带的 `serve.py` 是参考实现。

**方式二：程序直读工作台文件（伪代码）**：

```python
from pathlib import Path

WS = Path("~/my-greenroom").expanduser()

def build_context(slug: str) -> str:
    script = (WS / "jobs" / slug / "script.md").read_text(encoding="utf-8")
    return PROMPT_TEMPLATE.format(script=script)
    # 可选：把 jobs/<slug>/intel.md 作为第二段加进去（面试官信息、考题预测）
```

岗位切换 = 换 slug 重读，不需要在工具里硬编码任何一套材料。逐字稿解析规则见 `docs/workspace-spec.md` 的 script.md 契约。

## 提词后端协议

一个提词客户端负责转写与呈现，取数与生成交给后端。客户端典型形态：双引擎转写（本地
FunASR WebSocket 优先、回退 Chrome Web Speech）、手动或静音自动触发、流式渲染（起手句
高亮、加粗要点、口径行标记）、追加快捷指令、手动打字兜底。后端地址由客户端决定（同源
优先，其次 `http://127.0.0.1:8765`）。

**仓库自带参考实现：`serve.py`**——挂载工作台并在 `.env` 配好 `MODEL_API_KEY` 即全功能（persona 自动扫 `jobs/` 目录，逐字稿/JD/情报全部按 workspace-spec 契约实时读盘；`MODEL_API_BASE`/`MODEL_NAME` 支持任意 OpenAI 兼容接口）。自建后端实现以下三个接口即可：

```
GET /config
→ {"has_key": true, "model": "deepseek-v4-flash", "personas": {"<jobs 目录名>": "<公司 · 岗位>", ...}}

POST /api/answer        # body 为 JSON 字符串；客户端不带自定义 header（CORS 简单请求，免预检）
  {"question": "...", "persona": "<key>", "detail": "brief|detail", "history": [{role, content}, ...]}
→ 流式 text/plain（直接 write 模型增量文本）

POST /api/mock          # 模拟面试，两阶段
  {"stage": "interview", "persona": "<key>", "round": "hr|biz|director|cross|final",
   "style": "gentle|standard|tough", "lang": "zh|en", "minutes": 30, "history": [...]}
  # 面试官人格：system prompt 由 resume.md + jobs/<key>/job.md + intel.md 组装；
  # history 首条为 {"role":"user","content":"[开始面试]"}；面试官在结束时输出单独一行 [面试结束]
  {"stage": "report", "persona": "<key>", "history": [完整问答]}
  # 教练报告：评分（结构 / 证据密度 / 时长 / 背诵感）+ 修订建议；
  # 数字类回答对照 jobs/<key>/script.md，提醒本场说出但稿里没有的数字
→ 均为流式 text/plain

POST /api/setup         # 不依赖 Claude 的工作台生成（serve.py 参考实现）
  {"company": "...", "role": "...", "jd": "...", "notes": "?", "resume_text": "?",
   "resume_pdf_b64": "?", "replace_resume": false}
→ 流式 text/plain 按行：##STEP 进度 / ##OK {"slug","name"} / ##ERR 信息
  # 生成 resume.md+profile.md（契约格式）、jobs/<slug>/job.md+intel.md（模型知识首稿，
  # 建议后续用 job-intel skill 做带 web 检索的深度版）、story-bank 骨架
```

后端责任：按本文上方契约从工作台组装 system prompt（输出规则 + 逐字稿），代理模型流式接口、藏 key。响应头带 `Access-Control-Allow-Origin: *`；建议同时实现 `OPTIONS`（204 + CORS 头）兼容带 JSON header 的客户端。转写若用本地 FunASR：WebSocket 端口 8766，客户端发 `start` 后推 16kHz 单声道 Int16 PCM，服务端回 `{"text": "增量文本"}`。

客户端侧（v0.4.0 起）：实时助手视图为视口内布局——提词卡内部滚动、流式自动跟随（用户上翻即暂停跟随），转写区与操作条固定不被顶走；「输入设备」可选（deviceId 透传 FunASR 采集链，回声消除/降噪/自动增益显式关闭，配合 BlackHole 一类环回设备），带电平实测按钮；「悬浮窗」用 Document Picture-in-Picture 把问题+提词镜像到一个置顶小窗（可拖到摄像头正下方，Chrome 116+）。

## 实现建议（来自一个真实的自建提词器）

- **手动触发优于 VAD 自动触发**：外放场景下自动触发会把自己的声音也当成问题。
- **多轮历史**只保留最近 ~12 轮，system prompt 里的逐字稿不变、靠 KV cache 摊薄成本。
- 逐字稿全文塞 system prompt 在 60 题量级是可行的；更大的库再考虑按题切块检索。
- 模型选低延迟档（首 token 时间优先于推理深度），提词场景要的是 2 秒内出起手句。
- **思考模式必须显式关掉**：新一代模型（如 deepseek-v4-flash）普遍默认开 thinking，首字前静默推理 4-6 秒——提词等于废了。OpenAI 兼容接口加 `"thinking": {"type": "disabled"}`（实测 TTFT 从 ~5s 回到 <1s）。

## 立场

提词器最大的实际风险是**当场说出一个你从没准备过、随口编的数字**。把上下文严格限定在你写过的逐字稿里、并要求「稿里没有就别编」，解决的就是这个。至于要不要在面试里用实时工具，自己判断；Greenroom 的主张始终是赛前把准备做透，临场工具只兜底、不代答。
