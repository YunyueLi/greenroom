/**
 * greenroom cloud worker — stateless backend for the hosted web app.
 *
 * Mirrors serve.py's HTTP API (/config, /api/ping, /api/answer, /api/mock, /api/setup)
 * but holds NO workspace on disk:
 *   - live prompts (/api/answer, /api/mock) are built from the `ws` payload the client
 *     sends with each request (resume / transcript / jd / intel / candidate & persona name);
 *   - /api/setup generates the workspace files and RETURNS them in a `##OK {files}` line
 *     for the client to save into its blocks (which auto-sync to the user's cloud account).
 *
 * Model key: env.MODEL_API_KEY (a Worker secret) OR per-request BYOK header X-Greenroom-Key.
 * Base / model: env.MODEL_API_BASE (default DeepSeek), env.MODEL_NAME. Any OpenAI-compatible API.
 *
 * Contract source of truth: ../serve.py + ../docs/realtime-bridge.md + ../docs/workspace-spec.md.
 */

const DEFAULT_BASE = "https://api.deepseek.com";
const DEFAULT_MODEL = "deepseek-v4-flash";      // live prompting (/api/answer) — speed
const DEFAULT_MODEL_PRO = "deepseek-v4-pro";    // generation (/api/setup) & mock (/api/mock) — quality
const PLACEHOLDER_KEY = "sk-your-own-key-here";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Greenroom-Key, X-Greenroom-Model",
};
const ENC = new TextEncoder();

function srvCfg(env) {
  const base = (env.MODEL_API_BASE || env.DEEPSEEK_API_BASE || DEFAULT_BASE).replace(/\/+$/, "");
  const model = env.MODEL_NAME || env.DEEPSEEK_MODEL || DEFAULT_MODEL;
  const modelPro = env.MODEL_NAME_PRO || DEFAULT_MODEL_PRO;
  let key = (env.MODEL_API_KEY || env.DEEPSEEK_API_KEY || env.OPENAI_API_KEY || "").trim();
  if (key === PLACEHOLDER_KEY) key = "";
  return { base, model, modelPro, key };
}
// tier: "flash" (live, fast) | "pro" (generation / mock, higher quality). Header X-Greenroom-Model overrides both.
function pickKey(req, env, tier) {
  const c = srvCfg(env);
  let hk = (req.headers.get("X-Greenroom-Key") || "").trim();
  if (hk === PLACEHOLDER_KEY) hk = "";
  const key = hk || c.key;
  const hm = (req.headers.get("X-Greenroom-Model") || "").trim();
  const model = hm || (tier === "pro" ? c.modelPro : c.model);
  return { key, model, base: c.base };
}
function txt(body, status = 200, ctype = "text/plain; charset=utf-8") {
  return new Response(body, { status, headers: { ...CORS, "Content-Type": ctype, "Cache-Control": "no-store" } });
}
function jsonResp(obj, status = 200) {
  return txt(JSON.stringify(obj), status, "application/json; charset=utf-8");
}
async function respSnippet(resp, limit = 500) {
  if (!resp || !resp.body) return "";
  const reader = resp.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (size < limit) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      size += value.byteLength;
    }
  } catch (e) {}
  return new TextDecoder().decode(concatBytes(chunks, Math.min(size, limit))).slice(0, limit);
}
function concatBytes(chunks, size) {
  const out = new Uint8Array(size);
  let off = 0;
  for (const c of chunks) {
    const slice = c.slice(0, Math.max(0, size - off));
    out.set(slice, off);
    off += slice.byteLength;
    if (off >= size) break;
  }
  return out;
}
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
async function supabaseKeepalive(env) {
  const sup = (env.SUPABASE_URL || "").replace(/\/+$/, "");
  const anon = (env.SUPABASE_ANON_KEY || "").trim();
  if (!sup || !anon) return { ok: false, error: "cloud-not-configured" };
  const restHeaders = { apikey: anon, Authorization: "Bearer " + anon, Accept: "application/json" };
  const checks = [
    {
      name: "rpc-touch",
      optional: true,
      url: sup + "/rest/v1/rpc/gr_touch_keepalive",
      init: { method: "POST", headers: { ...restHeaders, "Content-Type": "application/json" }, body: "{}" },
    },
    { name: "rest-read", url: sup + "/rest/v1/gr_profile?select=user_id&limit=1", init: { headers: restHeaders } },
    { name: "auth-settings", url: sup + "/auth/v1/settings", init: { headers: { apikey: anon, Accept: "application/json" } } },
  ];
  const results = [];
  for (const check of checks) {
    let last = null;
    for (let attempt = 1; attempt <= 4; attempt++) {
      try {
        const resp = await fetch(check.url, { ...(check.init || {}), cf: { cacheTtl: 0 } });
        last = { name: check.name, status: resp.status, ok: resp.ok, attempt };
        if (resp.ok) break;
        last.body = await respSnippet(resp);
        if (check.optional && resp.status === 404) break;
      } catch (e) {
        last = { name: check.name, status: 0, ok: false, attempt, error: ((e && e.message) || e).toString().slice(0, 200) };
      }
      await sleep(5000 * attempt);
    }
    results.push(last);
  }
  const touch = results.find((r) => r && r.name === "rpc-touch");
  const read = results.find((r) => r && r.name === "rest-read");
  const auth = results.find((r) => r && r.name === "auth-settings");
  const ok = !!((touch && touch.ok) || (read && read.ok)) && !!(auth && auth.ok);
  return { ok, at: new Date().toISOString(), results };
}
function thinkingPatch(base) {
  return base.includes("deepseek") ? { thinking: { type: "disabled" } } : {};
}
function today() {
  return new Date().toISOString().slice(0, 7); // YYYY-MM
}
function todayFull() {
  return new Date().toISOString().slice(0, 10).replace(/-/g, "."); // YYYY.MM.DD
}

// ============ auth (Supabase JWT) + metering (Cloudflare D1) ============
// Gating activates only when env.SUPABASE_URL is set (a Worker secret). Without it the
// worker stays an open BYOK proxy — the self-host / fork default, unchanged behaviour.

function b64urlBytes(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const bin = atob(s), u = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
  return u;
}
function b64urlStr(s) { return new TextDecoder().decode(b64urlBytes(s)); }

let _jwks = { url: null, keys: null, at: 0 };
async function getJwks(jwksUrl) {
  const now = Date.now();
  if (_jwks.keys && _jwks.url === jwksUrl && now - _jwks.at < 3600000) return _jwks.keys;
  const r = await fetch(jwksUrl, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) throw new Error("jwks " + r.status);
  const j = await r.json();
  _jwks = { url: jwksUrl, keys: j.keys || [], at: now };
  return _jwks.keys;
}
function algParams(alg) {
  if (alg === "ES256") return { imp: { name: "ECDSA", namedCurve: "P-256" }, ver: { name: "ECDSA", hash: "SHA-256" } };
  if (alg === "RS256") return { imp: { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, ver: { name: "RSASSA-PKCS1-v1_5" } };
  return null;
}
// Verify a Supabase access token (ES256/RS256 via JWKS). Returns {userId,email} or null.
async function verifyUser(req, env) {
  const sup = (env.SUPABASE_URL || "").replace(/\/+$/, "");
  if (!sup) return null;
  const m = (req.headers.get("Authorization") || "").match(/^Bearer\s+(.+)$/i);
  if (!m) return null;
  const parts = m[1].trim().split(".");
  if (parts.length !== 3) return null;
  let head, pl;
  try { head = JSON.parse(b64urlStr(parts[0])); pl = JSON.parse(b64urlStr(parts[1])); } catch (e) { return null; }
  if (!pl || !pl.sub) return null;
  if (pl.exp && Math.floor(Date.now() / 1000) >= pl.exp) return null;
  if (pl.iss && pl.iss !== sup + "/auth/v1") return null;
  const ap = algParams(head.alg);
  if (!ap) return null;
  try {
    const keys = await getJwks(sup + "/auth/v1/.well-known/jwks.json");
    const jwk = keys.find((k) => k.kid === head.kid) || keys[0];
    if (!jwk) return null;
    const ck = await crypto.subtle.importKey("jwk", jwk, ap.imp, false, ["verify"]);
    const ok = await crypto.subtle.verify(ap.ver, ck, b64urlBytes(parts[2]), ENC.encode(parts[0] + "." + parts[1]));
    if (!ok) return null;
  } catch (e) { return null; }
  return { userId: pl.sub, email: pl.email || "" };
}

function dayKey() { return new Date().toISOString().slice(0, 10); } // YYYY-MM-DD (UTC)
function freeLimits(env) { return { answer: +(env.FREE_ANSWER || 30), setup: +(env.FREE_SETUP || 2), mock: +(env.FREE_MOCK || 10) }; }
function passLimits(env) { return { answer: +(env.PASS_ANSWER || 3000), setup: +(env.PASS_SETUP || 50), mock: +(env.PASS_MOCK || 600) }; }
// Admin = JWT email in ADMIN_EMAILS (comma-separated). Gates the usage dashboard endpoint.
function isAdmin(env, user) {
  const list = (env.ADMIN_EMAILS || "").toLowerCase().split(",").map((s) => s.trim()).filter(Boolean);
  return !!(user && user.email && list.includes(user.email.toLowerCase()));
}

async function incCall(env, userId, ep) {
  if (!env.DB) return;
  try {
    await env.DB.prepare(
      "INSERT INTO usage (user_id,day,endpoint,calls,tok_in,tok_out) VALUES (?,?,?,1,0,0) " +
      "ON CONFLICT(user_id,day,endpoint) DO UPDATE SET calls=calls+1"
    ).bind(userId, dayKey(), ep).run();
  } catch (e) {}
}
async function addTokens(env, userId, ep, tin, tout) {
  if (!env.DB || (!tin && !tout)) return;
  try {
    await env.DB.prepare(
      "INSERT INTO usage (user_id,day,endpoint,calls,tok_in,tok_out) VALUES (?,?,?,0,?,?) " +
      "ON CONFLICT(user_id,day,endpoint) DO UPDATE SET tok_in=tok_in+excluded.tok_in, tok_out=tok_out+excluded.tok_out"
    ).bind(userId, dayKey(), ep, tin | 0, tout | 0).run();
  } catch (e) {}
}

// One round-trip auth + quota check. Returns {resp} to short-circuit, or {user,meter}.
// meter=true → record token usage for this call (counts against quota); meter=false →
// BYOK / ungated / login-only (no quota). Pre-increments the call counter via waitUntil.
async function gate(req, env, ep, ctx) {
  if (!env.SUPABASE_URL) return { user: null, meter: false }; // ungated (self-host / fork)
  const user = await verifyUser(req, env);
  if (!user) return { resp: jsonResp({ error: "login", message: "请登录后使用托管服务" }, 401) };
  let hk = (req.headers.get("X-Greenroom-Key") || "").trim();
  if (hk === PLACEHOLDER_KEY) hk = "";
  if (hk) return { user, meter: false }; // BYOK pays its own model cost → skip quota
  if (!env.DB) return { user, meter: false }; // gated but no store → login-only
  const day = dayKey();
  let tier = "free", used = 0;
  try {
    const res = await env.DB.batch([
      env.DB.prepare("SELECT tier,expires FROM entitlement WHERE user_id=? OR user_id=?").bind(user.userId, user.email || ""),
      env.DB.prepare("SELECT SUM(calls) AS total FROM usage WHERE user_id=? AND endpoint=?").bind(user.userId, ep),
    ]);
    // entitlement may be keyed by user_id (uuid) OR by email — the latter lets you grant a tier
    // before a user's first login (email comes from the signature-verified JWT, so it can't be forged).
    const _erows = (res[0].results || []).filter((r) => !r.expires || r.expires >= day);
    if (_erows.some((r) => r.tier === "unlimited")) tier = "unlimited";      // owner / comp — no cap at all
    else if (_erows.some((r) => r.tier === "pass")) tier = "pass";           // paid Pass — high finite cap
    const u = res[1].results && res[1].results[0];
    used = (u && u.total) || 0; // lifetime total across all days, not per-day
  } catch (e) {}
  const lim = tier === "unlimited" ? Infinity : (tier === "pass" ? passLimits(env) : freeLimits(env))[ep];
  if (used >= lim) return { resp: jsonResp({ error: "quota", endpoint: ep, used, limit: lim, tier }, 402) };  // never blocks when unlimited
  ctx.waitUntil(incCall(env, user.userId, ep));
  return { user, meter: true };
}
// Wrap a gate result into a per-call usage recorder (or null when not metering).
function usageRecorder(g, env, ep, ctx) {
  if (!g.meter || !g.user) return null;
  return (u) => { if (u) ctx.waitUntil(addTokens(env, g.user.userId, ep, u.prompt_tokens || 0, u.completion_tokens || 0)); };
}

async function modelComplete({ base, key, model }, messages, { temperature = 0.3, max_tokens = 4000, onUsage = null } = {}) {
  const payload = { model, messages, stream: false, temperature, max_tokens, ...thinkingPatch(base) };
  const r = await fetch(base + "/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + key },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const b = await r.text();
    throw new Error("upstream " + r.status + ": " + b.slice(0, 300));
  }
  const obj = await r.json();
  if (onUsage && obj.usage) { try { onUsage(obj.usage); } catch (e) {} }
  return (obj.choices && obj.choices[0] && obj.choices[0].message && obj.choices[0].message.content) || "";
}

// stream upstream SSE → plaintext deltas (the client reads response.body as text)
function streamModel({ base, key, model }, messages, { temperature = 0.3, max_tokens = 800 } = {}, onUsage = null) {
  const payload = { model, messages, stream: true, temperature, max_tokens, stream_options: { include_usage: true }, ...thinkingPatch(base) };
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const up = await fetch(base + "/chat/completions", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: "Bearer " + key },
          body: JSON.stringify(payload),
        });
        if (!up.ok || !up.body) {
          const b = await up.text();
          controller.enqueue(ENC.encode("\n[上游报错 " + up.status + "] " + b.slice(0, 300)));
          controller.close();
          return;
        }
        const reader = up.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          let i;
          while ((i = buf.indexOf("\n")) >= 0) {
            const line = buf.slice(0, i).trim();
            buf = buf.slice(i + 1);
            if (!line.startsWith("data:")) continue;
            const data = line.slice(5).trim();
            if (data === "[DONE]") {
              controller.close();
              return;
            }
            try {
              const obj = JSON.parse(data);
              const delta = obj.choices && obj.choices[0] && obj.choices[0].delta && obj.choices[0].delta.content;
              if (delta) controller.enqueue(ENC.encode(delta));
              if (obj.usage && onUsage) { try { onUsage(obj.usage); } catch (e) {} }
            } catch (e) {}
          }
        }
        controller.close();
      } catch (e) {
        try { controller.enqueue(ENC.encode("\n[连接出错] " + ((e && e.message) || e))); } catch (_) {}
        controller.close();
      }
    },
  });
  return new Response(stream, { headers: { ...CORS, "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
}

// ---------------- live prompting prompt (ported from serve.py build_system_prompt, fed by ws) ----------------
function buildAnswerPrompt(ws, detail) {
  const name = (ws && ws.candidateName) || "候选人";
  const persona = (ws && ws.personaName) || "目标岗位";
  const transcript = (ws && ws.transcript) || "（该岗位还没有逐字稿：先跑 /greenroom:interview-script 生成）";
  const lengthRule =
    detail === "brief"
      ? "长度以把这道题答透为准——有逐字稿就把那题的完整内容给足（数字、机制、论证一个不丢），可以讲到 1–2 分钟；别为了精炼牺牲质量。第一句必须是能照着直接念出口的话（提词从开头读起，新内容只往下接）。"
      : "给完整版本，可以讲到约 2 分钟，多铺一层细节、机制或例子。";
  return `你是${name}的实时面试答题搭子。他正在面：${persona}。他会把面试官刚问出口的话原样打给你，你唯一的任务：立刻给一段「能直接念出口」的第一人称回答。他边看边念，所以要快、要短、像真人说话。

# 输出规则（最重要）
1. 开口即答案，第一人称，用他的口吻。没有任何前言（不要「好的」「这个问题在考察…」「建议你…」「以下是」）。
2. 第一行写 \`【这么起】\` 再跟一句能立刻开口的缓冲话（≤25 字）：给结论预告或复述要点，让他扫一眼先讲出去、争取思考时间；别把核心数字塞在这句里。
3. 之后分点给骨架，分点数量按内容定、把内容讲全，每点是可直接念的整句，**关键词加粗**方便他跳读。
4. ${lengthRule}他打「短」就压成 20–30 秒一句话版；打「深」或「展开」给完整版。
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
${transcript}
==================== 知识库结束 ====================`;
}

const ROUND_FOCUS = {
  hr: "HR 轮：动机与稳定性（为什么离开上家、为什么是我们、职业规划）、薪酬期望、文化匹配。",
  biz: "业务面：简历项目深挖（数字怎么来的、个人贡献、失败复盘）、岗位专业题、实际工作场景题。",
  director: "高管面：判断力与方向感（行业判断、方法论迁移、带人带事）、和老板风格的匹配。",
  final: "终面：价值观、长期主义、综合素质，外加对前几轮疑点的复核。",
  cross: "交叉面：来自相邻团队的面试官（非直接用人方），考察通用能力与协作——拿一个候选人不熟的业务场景看他怎么拆、跨团队冲突怎么处理、方法论能不能离开熟悉领域还成立；对岗位专业细节问得少，对思维质量和真诚度盯得紧。",
};
const STYLE_DESC = {
  gentle: "温和耐心，多给候选人台阶，但关键处仍会确认细节。",
  standard: "专业标准，节奏适中，该追问就追问。",
  tough: "严苛压迫式：对每个数字和说法刨根问底，三层追问起步，对含糊回答直接点破，不留情面。",
};
function buildMockInterviewerPrompt(ws, round, style, lang, minutes) {
  const persona = (ws && ws.personaName) || "目标岗位";
  const resume = (ws && ws.resume) || "（无简历，按候选人口述提问）";
  const jd = (ws && ws.jd) || "";
  const intel = (ws && ws.intel) || "";
  const langRule = lang === "en" ? "全程用英文提问。" : "全程用中文提问。";
  return `你是一位资深面试官，正在面试候选人应聘：${persona}。${ROUND_FOCUS[round] || ROUND_FOCUS.biz}
风格：${STYLE_DESC[style] || STYLE_DESC.standard}
这是一场约 ${minutes} 分钟的${lang === "en" ? "英文" : "中文"}面试。${langRule}

规则：
- 一次只问一个问题，像真人面试官那样自然、口语，别报菜单式列清单。
- 顺着候选人上一句答的内容追问，盯数字、盯个人贡献、盯逻辑漏洞；答得含糊就追。
- 别替候选人答、别给评价或建议，只提问与简短回应（「了解」「嗯，那…」）。
- 开场先自然寒暄一句再进入第一题；临近时间用一道收口题结束。

==================== 候选人简历 ====================
${resume}
${jd ? "\n==================== 目标岗位 JD ====================\n" + jd : ""}
${intel ? "\n==================== 岗位情报（面试官背景知识）====================\n" + intel : ""}
==================== 结束 ====================`;
}
function buildMockCoachPrompt(ws) {
  const persona = (ws && ws.personaName) || "目标岗位";
  return `你是一位面试教练。下面是候选人面试「${persona}」的完整记录。给一份简洁的复盘报告（Markdown）：
1. 五维评分（每项 1–5 + 一句理由）：表达清晰度、专业深度、结构化、真诚可信、岗位匹配。
2. 三个最该改的点（具体、可操作，引用记录里的原话）。
3. 一句话总评。
不堆砌、不灌水、不写「总而言之」这类套话。`;
}

// ---------------- /api/setup generation (returns files; ported from serve.py) ----------------
const SETUP_RESUME_SYS = `你负责把候选人的简历原文转写成 greenroom 工作台的两个 Markdown 文件。只输出文件内容，用标记分隔，不加任何解释。

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

规则：忠实转写、零编造；日期一律「YYYY.MM – YYYY.MM」（在职用「至今」）；条目标题必须是「公司｜岗位｜日期」三段式（全角｜）；教育经历放「## 教育经历」分区。`;

const SETUP_JOB_SYS = `你负责为 greenroom 面试准备工作台生成一个新岗位的档案。只输出文件内容，用标记分隔，不加任何解释。

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

规则：JD 原文一字不动；公司信息凭真实知识、宁缺毋滥；考题必须扣 JD 和简历的交集。`;

function splitFiles(text) {
  const out = {};
  let cur = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const m = line.match(/^===FILE:(.+?)===$/);
    if (m) { cur = m[1].trim(); out[cur] = []; continue; }
    if (line === "===END===") { cur = null; continue; }
    if (cur !== null) out[cur].push(raw);
  }
  const files = {};
  for (const k of Object.keys(out)) files[k] = out[k].join("\n").trim() + "\n";
  return files;
}
function storyBankSkeleton() {
  return `---\ntype: story-bank\nupdated: ${today()}\n---\n\n# 经历库\n\n> 真实经历整理成经历卡：事实和数字只有一份、都标出处，讲法按岗位选。用 /greenroom:story-bank 生成，或手写。\n`;
}

function handleSetup(req, env, body, onUsage) {
  const company = (body.company || "").trim();
  const role = (body.role || "").trim();
  const jd = (body.jd || "").trim();
  if (!company || !role || !jd) return txt("缺少 公司 / 岗位 / JD", 400);
  const { key, model, base } = pickKey(req, env, "pro");
  if (!key) return txt("未配置模型 key（在设置里填你的 key，或给 Worker 配 MODEL_API_KEY）", 401);
  const srv = { key, model, base };
  const resumeText = (body.resume_text || "").trim();
  const notes = (body.notes || "").trim();
  const atts = Array.isArray(body.attachments) ? body.attachments.slice(0, 8) : [];

  const stream = new ReadableStream({
    async start(controller) {
      const emit = (s) => controller.enqueue(ENC.encode(s + "\n"));
      try {
        const files = {};
        // 1) resume → resume.md + profile.md（提供了简历文本才转写）
        if (resumeText) {
          emit("##STEP 正在转写简历（契约格式 + 候选人档案）…");
          const out = await modelComplete(srv, [
            { role: "system", content: SETUP_RESUME_SYS },
            { role: "user", content: `（今天日期：${today()}，updated 字段用它）\n\n` + resumeText.slice(0, 20000) },
          ], { onUsage });
          const f = splitFiles(out);
          for (const rel of ["resume.md", "profile.md"]) if (f[rel]) files[rel] = f[rel];
          if (!files["story-bank.md"]) files["story-bank.md"] = storyBankSkeleton();
        }
        // 2) job → jobs/<slug>/job.md + intel.md（补充信息一并喂进生成）
        emit("##STEP 正在生成岗位档案与调研底稿…");
        const attTexts = atts
          .filter((a) => a && a.text)
          .map((a) => `## 附件：${(a.name || "附件").slice(0, 80)}\n${String(a.text).slice(0, 6000)}`);
        const extra = (notes || "") + (attTexts.length ? "\n\n" + attTexts.join("\n\n") : "");
        const resumeForJd = (resumeText && files["resume.md"]) || resumeText || "（暂无）";
        const user =
          `（今天日期：${today()}，updated 字段用它）\n公司：${company}\n岗位：${role}\n\n# JD\n${jd.slice(0, 12000)}` +
          `\n\n# 补充信息\n${extra || "无"}\n\n# 候选人简历（用于 JD 拆解对照）\n${String(resumeForJd).slice(0, 8000)}`;
        const out = await modelComplete(srv, [
          { role: "system", content: SETUP_JOB_SYS },
          { role: "user", content: user },
        ], { max_tokens: 5000, onUsage });
        const sm = out.match(/^SLUG:\s*([a-z0-9][a-z0-9-]{1,48})\s*$/m);
        if (!sm) { emit("##ERR 模型未返回有效岗位目录名，请重试"); controller.close(); return; }
        const slug = sm[1];
        const jf = splitFiles(out);
        const allowed = [`jobs/${slug}/job.md`, `jobs/${slug}/intel.md`];
        let wrote = 0;
        for (const k of Object.keys(jf)) {
          const rel = k.replace(/\{slug\}/g, slug);
          if (allowed.indexOf(rel) < 0 || !jf[k].trim()) continue;
          files[rel] = jf[k];
          wrote++;
        }
        if (!wrote) { emit("##ERR 模型输出里没有可写入的岗位文件，请重试"); controller.close(); return; }
        // 时间线首条（## 时间线 区块：控制台岗位页渲染）
        const jrel = `jobs/${slug}/job.md`;
        if (files[jrel] && files[jrel].indexOf("## 时间线") < 0) {
          files[jrel] = files[jrel].replace(/\s*$/, "") + `\n\n## 时间线\n\n- ${todayFull()} 建档\n`;
        }
        // 附件文本原件留档（pdf/二进制留给自部署；云端先存文本）
        for (const a of atts) {
          if (a && a.text && a.name) {
            const nm = String(a.name).replace(/[^\w.一-鿿-]/g, "_").slice(0, 80);
            const fn = /\.(md|txt)$/i.test(nm) ? nm : nm + ".md";
            files[`jobs/${slug}/attachments/${fn}`] = String(a.text);
          }
        }
        emit("##OK " + JSON.stringify({ ok: true, name: `${company} · ${role}`, slug, files }));
        controller.close();
      } catch (e) {
        emit("##ERR " + ((e && e.message) || e));
        controller.close();
      }
    },
  });
  return new Response(stream, { headers: { ...CORS, "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" } });
}

// ---------------- router ----------------
export default {
  async scheduled(controller, env, ctx) {
    const result = await supabaseKeepalive(env);
    console.log(JSON.stringify({ event: "supabase_keepalive", cron: controller.cron, ...result }));
  },
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    const url = new URL(request.url);
    const route = url.pathname;

    if (request.method === "GET") {
      if (route === "/" || route === "/config") {
        const c = srvCfg(env);
        return jsonResp({ has_key: !!c.key, model: c.model, model_pro: c.modelPro, personas: {}, cloud: true });
      }
      // Public Supabase config for the hosted app so login works with zero per-user setup.
      // Both values are PUBLIC by design (anon key ships in every Supabase web client; RLS guards data).
      // Empty until SUPABASE_ANON_KEY is set as a secret → the app then falls back to its own config.
      if (route === "/public-config") {
        return jsonResp({ sb_url: env.SUPABASE_URL || "", sb_anon: env.SUPABASE_ANON_KEY || "" });
      }
      if (route === "/keepalive") {
        const result = await supabaseKeepalive(env);
        return jsonResp(result, result.ok ? 200 : 502);
      }
      // Owner usage dashboard data (admin-gated). Returns per-user / per-endpoint call + token totals.
      if (route === "/admin/usage") {
        const u = await verifyUser(request, env);
        if (!u) return jsonResp({ error: "login" }, 401);
        if (!isAdmin(env, u)) return jsonResp({ error: "forbidden" }, 403);
        if (!env.DB) return jsonResp({ error: "no-store" }, 500);
        const usage = await env.DB.prepare(
          "SELECT user_id, endpoint, SUM(calls) AS calls, SUM(tok_in) AS tok_in, SUM(tok_out) AS tok_out, MAX(day) AS last_day FROM usage GROUP BY user_id, endpoint"
        ).all();
        const ent = await env.DB.prepare("SELECT user_id, tier, expires FROM entitlement").all();
        return jsonResp({ usage: usage.results || [], entitlement: ent.results || [], free: freeLimits(env), pass: passLimits(env) });
      }
      return txt("greenroom cloud worker", 200);
    }

    if (request.method !== "POST") return txt("not found", 404);

    let body = {};
    try { body = (await request.json()) || {}; } catch (e) { body = {}; }

    if (route === "/api/ping") {
      const { key, model, base } = pickKey(request, env, "flash");
      if (!key) return jsonResp({ ok: false, error: "未填 key" });
      try {
        const sample = await modelComplete({ key, model, base }, [{ role: "user", content: "只回两个字：正常" }], { temperature: 0, max_tokens: 16 });
        return jsonResp({ ok: !!sample, model, sample: (sample || "").slice(0, 40) });
      } catch (e) { return jsonResp({ ok: false, error: ((e && e.message) || e).toString().slice(0, 160) }); }
    }

    if (route === "/api/answer") {
      const question = (body.question || "").trim();
      if (!question) return txt("empty question", 400);
      const g = await gate(request, env, "answer", ctx);
      if (g.resp) return g.resp;
      const { key, model, base } = pickKey(request, env, "flash");
      if (!key) return txt("未配置模型 key", 401);
      const messages = [{ role: "system", content: buildAnswerPrompt(body.ws || {}, body.detail || "brief") }];
      for (const h of (body.history || []).slice(-12)) {
        const c = (h && h.content || "").trim();
        if ((h.role === "user" || h.role === "assistant") && c) messages.push({ role: h.role, content: c });
      }
      messages.push({ role: "user", content: question });
      return streamModel({ key, model, base }, messages, { temperature: 0.3, max_tokens: 800 }, usageRecorder(g, env, "answer", ctx));
    }

    if (route === "/api/mock") {
      const g = await gate(request, env, "mock", ctx);
      if (g.resp) return g.resp;
      const { key, model, base } = pickKey(request, env, "pro");
      if (!key) return txt("未配置模型 key", 401);
      const ws = body.ws || {};
      const history = body.history || [];
      let messages, max_tokens;
      if (body.stage === "report") {
        const qa = history.filter((h) => h && h.content).map((h) => (h.role === "assistant" ? "面试官：" : "候选人：") + h.content).join("\n\n");
        messages = [{ role: "system", content: buildMockCoachPrompt(ws) }, { role: "user", content: "完整面试记录如下，请出报告：\n\n" + qa }];
        max_tokens = 2000;
      } else {
        messages = [{ role: "system", content: buildMockInterviewerPrompt(ws, body.round || "biz", body.style || "standard", body.lang || "zh", body.minutes || 30) }];
        for (const h of history.slice(-40)) {
          const c = (h && h.content || "").trim();
          if ((h.role === "user" || h.role === "assistant") && c) messages.push({ role: h.role, content: c });
        }
        max_tokens = 500;
      }
      return streamModel({ key, model, base }, messages, { temperature: 0.5, max_tokens }, usageRecorder(g, env, "mock", ctx));
    }

    if (route === "/api/setup") {
      const g = await gate(request, env, "setup", ctx);
      if (g.resp) return g.resp;
      return handleSetup(request, env, body, usageRecorder(g, env, "setup", ctx));
    }

    return txt("not found", 404);
  },
};
