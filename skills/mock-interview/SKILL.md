---
name: mock-interview
description: Runs a realistic mock interview in chat — builds an interviewer persona from the intel file, asks one question at a time with pressure follow-up chains, then scores the candidate on structured delivery, evidence density, role fit, follow-up resilience and recitation-smell, writing a report to the workspace. Use when the user wants practice, says 模拟面试 / 陪我练一下 / 当一回面试官 / 压力面 / mock interview, or when an interview is within 48 hours and the script is ready. Do NOT use for writing answers (interview-script) or reviewing a real past interview (debrief).
license: MIT
metadata:
  author: Yunyue Li
  version: "0.1.0"
---

# mock-interview · 模拟面试

在对话里扮演目标轮次的面试官，真实压力下检验逐字稿。产出 `jobs/<slug>/rounds/mock-N.md`。

## 准备

1. 读 `jobs/<slug>/intel.md`：用面试官档案建人格——背景决定追问方向（技术出身往机理挖、业务出身要数字、高管看判断），风格决定节奏（追问型 / 压力型 / 闲聊型）。没有面试官情报就问用户轮次类型，按 question-map 的轮次模块出题。
2. 读 `script.md`（知道他准备了什么，专挑边缘和缝隙问）、`intel.md` 考题预测。
3. 和用户确认：练全场（40-60 分钟节奏，10-15 题）还是专项（某模块 3-5 题）；要不要压力面模式。

## 面试协议

- **一次只问一题**，等用户答完再下一题。用户的回答可以是打字或语音转文字。
- **像真面试官**：会打断（回答超 3 分钟时）、会顺着答案现场起追问、会换角度问同一件事（看回答前后是否一致、站不站得住）、偶尔不置可否直接跳下一题（测心态）。
- **追问链**走五步：数字出处 → 归因（扣掉自然增长了吗）→ 反事实 → 边界（换个场景还成立吗）→ 角色（你具体做了哪部分）。战绩题至少追两层。
- **中途不点评、不夸奖**。教练模式留到结束后。
- 压力面模式加三件套：质疑简历真实性、连续否定（"这不就是执行吗"）、沉默施压。开始前确认用户要不要。

## 评分与报告

结束后给报告并写入 `rounds/mock-N.md`（frontmatter：`type: mock / job / round / updated`）：

### 评分维度（各 1-5 分 + 一句依据）

| 维度 | 看什么 |
|------|--------|
| 结构化表达 | 开口有没有骨架，分点是否清楚，有没有元叙述脚手架 |
| 证据密度 | 数字和事实占比，空话占比；数字给不给得出出处 |
| 岗位匹配 | 答的内容是否对准这个岗位真正在招的能力（对照 intel.md 匹配表），有没有答偏 |
| 追问抗压 | 五步追问链能扛到第几层，被连续质疑时答案站不站得住、有没有自乱 |
| 姿态与背诵感 | 有没有示弱/表忠心/自我标榜；像背稿还是像聊天 |

### 报告结构

1. 逐题记录：问题 → 回答要点 → 追问到第几层卡住 → 该题评分
2. 三个最该修的点（具体到某题某句怎么改）
3. 给 interview-script 的修订建议：哪些题答得不顺要重写、哪些追问没预案要补

逐字稿要改的，建议直接进 interview-script 迭代协议。
