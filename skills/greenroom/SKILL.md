---
name: greenroom
description: Interview preparation workbench entry point. Runs the full pipeline from resume + target company + JD to a complete prep workspace (research, experience bank, verbatim scripts, industry brief), or routes to a single step. Use when the user says they have an interview coming up, wants interview prep, uploads a resume with a target job, mentions 面试准备 / 我要面试了 / 帮我准备面试 / 帮我把面试材料全做出来 / 一条龙, or asks "where do I start". Do NOT use for writing resumes from scratch, salary negotiation after offer, or live in-interview assistance.
license: MIT
metadata:
  author: Yunyue Li
  version: "0.3.0"
---

# Greenroom · 候场

入口 skill。两种用法：**全流程**（给齐简历 + 目标公司/岗位/JD，一次生成全套备战材料）或**单步路由**（识别用户处在哪一步，转给专项 skill）。

## 全流程（推荐的默认路径）

用户给出（缺什么问什么，一次问全）：

1. 简历（文本或文件路径）
2. 目标公司 + 岗位名 + JD 原文（或链接）
3. 表达风格偏好（可选：自己的说话样本/过往面试转写，或一句描述，如"沉稳、少修辞"；写进 profile.md 的「风格偏好」节，逐字稿按它调）

然后按序执行，每步落盘后只汇报一行进度，不中途长篇输出：

| 步 | 调用 | 产出 |
|----|------|------|
| 1 | 初始化工作台（见下） | profile.md 骨架 |
| 2 | job-intel | `jobs/<slug>/intel.md`（公司与面试官调研、JD 逐条对照、考题预测） |
| 3 | story-bank | `story-bank.md`（经历卡，含本岗讲法） |
| 4 | industry-brief | `library/<行业-岗位>-通识.md`（行业与岗位参考阅读） |
| 5 | interview-script | `jobs/<slug>/script.md`（可朗读逐字稿） |

收尾：汇报生成清单 + 提示工作台目录位置（Markdown 直接读，或用任一按 docs/workspace-spec.md 实现的客户端打开）；建议面试前跑一次 mock-interview、面试后 24 小时内跑 debrief。这套工作台同时是实时提词后端的取数源（逐字稿 + 调研，见 docs/realtime-bridge.md）。

## 六步方法（单步路由用）

| # | 步骤 | 做什么 | 专项 skill | 产出文件 |
|---|------|--------|-----------|----------|
| 1 | 岗位调研 | JD 拆解、公司/面试官调研、考题预测 | job-intel | `jobs/<slug>/intel.md` |
| 2 | 经历库 | 把真实经历整理成经历卡，按岗选讲法 | story-bank | `story-bank.md` |
| 3 | 逐字稿 | 口语化、可直接朗读的答题稿 | interview-script | `jobs/<slug>/script.md` |
| 4 | 行业通识 | 行业格局、岗位画像、高频概念参考阅读 | industry-brief | `library/*.md` |
| 5 | 模拟面试 | 按面试官背景出题、连续追问、评分 | mock-interview | `jobs/<slug>/rounds/mock-N.md` |
| 6 | 面后复盘 | 复原问答、沉淀本轮要点 | debrief | `jobs/<slug>/rounds/rN-debrief.md` |

贯穿所有步骤的底线：生成内容只用候选人真实给出的经历和数字，数字要带得出出处，给不出准确数字就用定性说法，绝不编。

## 找到或创建工作台

工作台是一个本地文件夹，格式契约见仓库 `docs/workspace-spec.md`。判定顺序：

1. 当前目录或其子目录里找 `profile.md` + `jobs/`（或 frontmatter 带 `type: profile` 的文件）→ 找到即用，向用户确认一句。
2. 找不到 → 问用户工作台在哪；用户说没有 → 走初始化。

### 初始化流程

1. 问清两件事：工作台建在哪个路径；候选人简历（贴文本或给文件路径）。
2. 创建目录骨架：

```
<workspace>/
├── profile.md
├── story-bank.md
├── library/
└── jobs/
```

3. 从简历提取生成 `profile.md`（frontmatter `type: profile`）：履历线（时间倒序）、教育背景、关键数字；用户给了风格偏好就加「风格偏好」节。提取数字时把出处一并记在 profile.md 里（哪份报表/哪次复盘），后续逐字稿要用；用户记不清出处的数字标「待核」。
4. 建议用户在工作台目录 `git init`，私有保存。**提醒：工作台含个人简历与面试材料，永远不要放进公开仓库。**

## 单步路由表

| 工作台状态 | 下一步 |
|-----------|--------|
| 没有 `jobs/<slug>/job.md`（用户提到新岗位） | 建岗位目录 + job.md，然后跑 job-intel |
| 有 job.md、没 intel.md | job-intel |
| story-bank.md 为空或缺该岗位讲法 | story-bank |
| 有调研和经历卡、没 script.md | interview-script |
| library/ 没有该行业岗位的通识 | industry-brief |
| 材料齐了、面试在 48 小时内 | mock-interview |
| 用户说"刚面完" | debrief |

路由方式：直接说明该做哪步、调用对应 skill（插件安装下是 `/greenroom:job-intel` 等；standalone 安装下按 skill 名触发）。如果用户一句话里带了材料（贴了 JD、贴了面试回忆），别走流程问答，直接进对应步骤。

## 姿态约定（贯穿所有步骤）

- **只讲真话，讲到最好**。生成内容时禁止编造用户没有的经历和数字，缺什么就问。
- 用户时间紧。能从工作台文件里读到的信息不要再问一遍。
- 中文用户默认全程中文交付。
