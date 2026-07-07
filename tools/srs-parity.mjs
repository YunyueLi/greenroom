#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────
// srs.js 算法对拍：校验 app/srs.js 的 FSRS-4.5 实现与 Telos Python 参考(fsrs.py) 数值一致。
// 金标准由 telos/core/telos_core/fsrs.py 跑出后固化在此（测试自包含，不依赖 telos 在场）。
// 用法：node tools/srs-parity.mjs   （退出码非 0 = 算法漂移）
// 若 srs.js 的 W/算法变更，需重新从 fsrs.py 生成金标准并更新这里。
// ─────────────────────────────────────────────────────────────────────────
import SRS from "../app/srs.js";

const days = [0, 2, 9, 30];
const SEQS = {
  A_all_good: [3, 3, 3, 3],
  B_mixed: [1, 3, 2, 4],
  C_easy_lapse: [4, 1, 3, 3],
};
// 金标准 [stability, difficulty, reps, lapses]（fsrs.py，FSRS-4.5，days=[0,2,9,30]）
const GOLDEN = {
  A_all_good: [[2.4, 4.93, 1, 0], [7.187268, 4.9206, 2, 0], [21.367506, 4.911294, 3, 0], [57.911237, 4.902081, 4, 0]],
  B_mixed: [[0.4, 6.81, 1, 1], [3.40426, 6.7818, 2, 1], [5.694865, 7.605282, 3, 1], [69.048681, 6.717729, 4, 1]],
  C_easy_lapse: [[5.8, 3.99, 1, 0], [1.926782, 5.6928, 2, 1], [13.684, 5.675772, 3, 1], [45.911399, 5.658914, 4, 1]],
};
const EPS = 1e-4;
let fail = 0;

for (const [name, gs] of Object.entries(SEQS)) {
  let c = SRS.newCard();
  gs.forEach((g, i) => {
    c = SRS.review(c, g, days[i]);
    const [es, ed, er, el] = GOLDEN[name][i];
    const ok =
      Math.abs(c.stability - es) < EPS && Math.abs(c.difficulty - ed) < EPS && c.reps === er && c.lapses === el;
    if (ok) {
      console.log(`✓ ${name}[${i}] s≈${es} d≈${ed} reps=${er} lapses=${el}`);
    } else {
      fail++;
      console.error(
        `✗ ${name}[${i}] JS s=${c.stability.toFixed(6)} d=${c.difficulty.toFixed(6)} reps=${c.reps} lapses=${c.lapses} | PY s=${es} d=${ed} reps=${er} lapses=${el}`,
      );
    }
  });
}

// interval 采样（req 0.9 / 0.95）
const checks = [
  ["interval req.9", [1, 5, 20].map((s) => SRS.interval(s, 0.9)), [1.0, 5.0, 20.0]],
  ["interval req.95", [1, 5, 20].map((s) => SRS.interval(s, 0.95)), [0.460563, 2.302814, 9.211255]],
];
for (const [label, got, exp] of checks) {
  got.forEach((v, i) => {
    if (Math.abs(v - exp[i]) < EPS) console.log(`✓ ${label}[${i}]≈${exp[i]}`);
    else { fail++; console.error(`✗ ${label}[${i}] ${v} != ${exp[i]}`); }
  });
}

// cramClamp：到期日不越过面试日（最晚面试前一天）
const c1 = SRS.review(SRS.newCard(), SRS.GOOD, 0); // reps=1, lastReviewDay=0
const dueFree = SRS.dueDay(c1, null);
const dueCram = SRS.dueDay(c1, 3); // 距面试 3 天
console.log(`  dueDay 无面试日=${dueFree}，距面试3天=${dueCram}`);
if (dueCram <= 2) console.log("✓ cramClamp：到期不越过面试日");
else { fail++; console.error("✗ cramClamp 未夹紧到期日"); }

if (fail) {
  console.error(`\n${fail} 处与 Python FSRS-4.5 不一致 —— 算法已漂移。`);
  process.exit(1);
}
console.log(`\n✓ srs.js 与 Python fsrs.py(FSRS-4.5) 数值一致；cramClamp 生效。`);
