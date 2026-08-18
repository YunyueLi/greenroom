---
name: job-intel
description: Deconstructs a job description and builds interview intelligence — JD-to-evidence matching, company and product research, interviewer profiling, recruiter-vs-team discrepancy checks, and next-round question forecasting. Use when the user shares a JD or job link, names a company they will interview with, asks to analyze a position (拆解 JD / 分析这个岗位 / 查一下这家公司 / 面试官是谁 / 下一轮会考什么), or after a round when the next interviewer is known. Do NOT use for writing the answer script itself (use interview-script) or post-interview review (use debrief).
license: AGPL-3.0
metadata:
  author: Yunyue Li
  version: "0.1.0"
---

# job-intel · 岗位情报

把一个岗位变成一份可备战的情报文件 `jobs/<slug>/intel.md`。原则：**证据驱动**——匹配结论必须能指到候选人材料里的具体证据，查不到的就写查不到，不编。

## 前置

1. 定位工作台（找 `profile.md` + `jobs/`；没有则建议先跑 greenroom 入口 skill 初始化）。
2. 没有 `jobs/<slug>/job.md` 就先建：slug 用小写连字符（如 `acme-ai-pm`），frontmatter 含 `type: job / company / role / status / source`，正文放 JD 原文。
3. 读 `profile.md`、`story-bank.md`，作为匹配分析的证据池。

## 产出 intel.md 的六个部分

### 1. JD 逐条匹配表

JD 的每条要求一行，证据只能来自工作台材料：

| JD 要求（原文） | 我的证据 | 匹配度 | 风险/缺口 | 面试策略 |
|----------------|----------|--------|-----------|----------|
| （逐条抄原文） | 指向具体项目和数字；无则写「材料未见直接证据」 | ✅强 / ⚠️中 / ❌弱 | 会被追问什么 | 有证据→用哪个经历卡哪个角度；无证据→怎么正面回应缺口 |

表后给一段判断：这个岗位真正在招什么人（JD 措辞背后的核心诉求，通常 1-2 条，其余是装饰）。

### 2. 公司与产品

用 web 搜索补齐：公司近况（融资/组织变化/战略转向）、目标产品的当前状态、竞品格局、近期公开发言（创始人/业务负责人访谈是考题富矿）。每条结论带来源链接；搜不到的写「未核实」。

### 3. 面试官档案（拿到名字就做，价值极高）

- 背景：履历、做过什么方向、公开内容（博客/播客/演讲/社交账号）。
- **风格推断**：技术出身→会往机理追问；业务出身→要结果和数字；投资背景→看判断和盘子大小。
- **prefer 什么人**：从其背景推断雷区与加分项（例：面试官自己是某背景出身，慎打「我比你懂你的领域」的牌；面试官明确说过喜欢无包袱的人，就少打资历牌）。
- 给出 2-3 条具体打法调整建议，写明推断依据，标注置信度。

### 4. 双轨核对：猎头描述 vs 实际岗位

猎头/HR 描述的岗位和业务团队实际在招的岗位经常有出入（汇报线、职级、是负责人还是组员）。把两边说法并排列出，差异处标 ⚠️，列出该向谁核实什么问题。差异本身就是反问环节的好问题。

### 5. 下轮考题预测

依据：JD 关键词、面试官背景、本轮面试官透露的信息（debrief 里常有下轮剧透）、该公司公开面经（带来源）。输出 5-10 个预测题，按概率排序，每题一行注明预测依据。这份清单直接喂给 interview-script 和 mock-interview。

### 6. 渠道情报

面经、社区帖子、内部消息，逐条带来源和日期，可信度分级（一手/二手/传闻）。

## 写入约定

- frontmatter：`type: intel / job: <slug> / updated: <date>`。
- 调研中发现的硬数字（公司估值、产品数据）只是背景情报，逐条带来源；查不到的写「未核实」，不替公司编数字。
- 发现 JD 或情报与用户既有材料冲突（例：用户准备讲的方向公司刚砍掉），单独列一节「⚠️ 冲突提醒」。
- 全部写完后更新 `job.md` 的 `status` 和 `updated`。

## 触发后的最小流程

用户只给了一个 JD 没说别的 → 建 job.md → 跑六部分 → 汇报匹配表的强弱结论 + 考题预测 top3 + 建议的下一步（通常是 story-bank 或 interview-script）。
