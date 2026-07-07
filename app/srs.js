/* ═══════════════════════════════════════════════════════════════════════
   srs.js — FSRS-4.5 间隔重复引擎 + 面试倒计时调度

   纯算法移植自 Telos：telos/core/telos_core/fsrs.py 与 web/lib/telos/engine.ts，
   逐行同构（DSR 模型、17 权重、grade 1..4）。无 DOM 依赖。

   双用途：
     · 浏览器：作为 IIFE 内联进 app/greenroom.html 的 <!--SRS--> 块（tools/embed-srs.py），
       挂到 window.SRS。
     · Node：被 tools/srs-parity.mjs require，与 Python fsrs.py 对拍验证算法一致。

   面试场景特化（Telos 没有、Greenroom 独有）：
     · cramClamp —— 复习日不越过面试日；临近面试抬高目标记忆保持率（90%→95%→97%）。
       面试要的是「到当天全部新鲜」，不是长期最优间隔。

   ⚠️ 改 W / 算法需与 telos fsrs.py、engine.ts 同步（tools/srs-parity.mjs 会对拍）。
   ═══════════════════════════════════════════════════════════════════════ */
(function (root) {
  "use strict";

  // ── FSRS-4.5 常量（与 fsrs.py 完全一致）──
  var DECAY = -0.5;
  var FACTOR = 19 / 81; // == 0.9 ** (1 / DECAY) - 1
  var W = [
    0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49,
    0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61,
  ];
  var AGAIN = 1, HARD = 2, GOOD = 3, EASY = 4;

  function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

  // 回忆概率：距上次复习 elapsed 天后还记得的概率
  function retrievability(stability, elapsedDays) {
    if (stability <= 0) return 0;
    return Math.pow(1 + (FACTOR * Math.max(0, elapsedDays)) / stability, DECAY);
  }
  // 间隔：记忆保持率衰减到 req 所需的天数（req=0.9 时 ≈ stability）
  function interval(stability, req) {
    if (req == null) req = 0.9;
    return (stability / FACTOR) * (Math.pow(req, 1 / DECAY) - 1);
  }

  function initStability(g) { return Math.max(0.1, W[g - 1]); }
  function initDifficulty(g) { return clamp(W[4] - W[5] * (g - 3), 1, 10); }
  function nextDifficulty(d, g) {
    var target = initDifficulty(EASY);
    var nd = d - W[6] * (g - 3);
    nd = W[7] * target + (1 - W[7]) * nd; // 均值回归
    return clamp(nd, 1, 10);
  }
  function stabilityAfterRecall(d, s, r, g) {
    var hard = g === HARD ? W[15] : 1;
    var easy = g === EASY ? W[16] : 1;
    return s * (1 + Math.exp(W[8]) * (11 - d) * Math.pow(s, -W[9]) * (Math.exp(W[10] * (1 - r)) - 1) * hard * easy);
  }
  function stabilityAfterLapse(d, s, r) {
    var sf = W[11] * Math.pow(d, -W[12]) * (Math.pow(s + 1, W[13]) - 1) * Math.exp(W[14] * (1 - r));
    return Math.min(sf, s); // 遗忘绝不增加 stability
  }

  function newCard() {
    return { stability: 0, difficulty: 0, reps: 0, lapses: 0, lastReviewDay: 0, state: "new" };
  }

  // 复习一张卡：返回更新后的卡（grade 1..4 = Again/Hard/Good/Easy；day = 整数日序号）
  function review(card, grade, day) {
    var g = Math.trunc(grade), s, d, lapses;
    if (card.reps === 0 || card.state === "new") {
      s = initStability(g);
      d = initDifficulty(g);
      lapses = g === AGAIN ? 1 : 0;
    } else {
      var elapsed = Math.max(0, day - card.lastReviewDay);
      var r = retrievability(card.stability, elapsed);
      d = nextDifficulty(card.difficulty, g);
      if (g === AGAIN) {
        s = stabilityAfterLapse(d, card.stability, r);
        lapses = card.lapses + 1;
      } else {
        s = stabilityAfterRecall(d, card.stability, r, g);
        lapses = card.lapses;
      }
    }
    return { stability: Math.max(0.1, s), difficulty: d, reps: card.reps + 1, lapses: lapses, lastReviewDay: day, state: "review" };
  }

  // ── 面试倒计时调度（Greenroom 特化）──
  var DAY_MS = 86400000;
  function today() { return Math.floor(Date.now() / DAY_MS); }
  // YYYY.MM.DD / YYYY-MM-DD → 日序号；解析失败返回 null
  function dayFromDateStr(str) {
    var m = String(str || "").match(/(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})/);
    if (!m) return null;
    var t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
    return Math.floor(t / DAY_MS);
  }
  // 临近面试抬高目标保持率：越近要求记得越牢
  function reqRetention(daysToInterview) {
    if (daysToInterview == null) return 0.9;
    if (daysToInterview <= 2) return 0.97;
    if (daysToInterview <= 7) return 0.95;
    return 0.9;
  }
  // 卡的下次到期日序号。daysToInterview 给定时：到期日不越过面试日（最晚面试前一天），
  // 且用抬高后的保持率缩短间隔 —— 保证面试当天每张都还新鲜。
  function dueDay(card, daysToInterview) {
    if (card.reps === 0 || card.state === "new") return card.lastReviewDay; // 新卡立即到期
    var req = reqRetention(daysToInterview);
    var iv = Math.max(1, Math.round(interval(card.stability, req)));
    if (daysToInterview != null && daysToInterview > 0) {
      iv = Math.min(iv, Math.max(1, daysToInterview - 1)); // cramClamp：别越过面试日
    }
    return card.lastReviewDay + iv;
  }
  function isDue(card, todayDay, daysToInterview) {
    if (card.reps === 0 || card.state === "new") return true;
    return dueDay(card, daysToInterview) <= todayDay;
  }

  // ── 稳定 ID（复习进度按此键存，不随渲染顺序漂移）──
  function slugify(s) {
    return String(s || "").trim().toLowerCase()
      .replace(/^经历卡[:：]\s*/, "")
      .replace(/\s+/g, "-")
      .replace(/[^\w一-龥-]/g, "")
      .slice(0, 48);
  }
  function cardId(card) { return "sb:" + slugify(card && (card.id || card.title)); }
  function questionId(jobSlug, q) { return "q:" + jobSlug + "#" + (q && q.n); }

  // ── 复习状态存取（localStorage gr_srs = { [id]: Card }）──
  var KEY = "gr_srs";
  function loadStore() {
    try { return JSON.parse(root.localStorage.getItem(KEY) || "{}") || {}; }
    catch (e) { return {}; }
  }
  function saveStore(m) {
    try { root.localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) {}
  }
  function getCard(store, id) { return (store && store[id]) || newCard(); }
  // 评分并持久化；返回更新后的卡
  function grade(id, g) {
    var m = loadStore();
    m[id] = review(getCard(m, id), g, today());
    saveStore(m);
    return m[id];
  }

  var API = {
    DECAY: DECAY, FACTOR: FACTOR, W: W,
    AGAIN: AGAIN, HARD: HARD, GOOD: GOOD, EASY: EASY,
    retrievability: retrievability, interval: interval, review: review, newCard: newCard,
    today: today, dayFromDateStr: dayFromDateStr, reqRetention: reqRetention,
    dueDay: dueDay, isDue: isDue,
    slugify: slugify, cardId: cardId, questionId: questionId,
    loadStore: loadStore, saveStore: saveStore, getCard: getCard, grade: grade,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = API; // Node（测试）
  root.SRS = API; // 浏览器
})(typeof window !== "undefined" ? window : globalThis);
