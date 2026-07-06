---
name: debrief
description: Post-interview review — reconstructs the Q&A from transcript or memory, captures interviewer intel and next-round forecasts, and turns the round into a revision list for the script. Use when the user says they just finished an interview, 刚面完 / 复盘一下 / 面试录音转文字给你 / 这轮被问了什么, or pastes an interview transcript or recollection. Do NOT use for practice sessions (mock-interview) or pre-interview research (job-intel).
license: MIT
metadata:
  author: Yunyue Li
  version: "0.1.0"
---

# debrief · 面后复盘

每轮真实面试后 24 小时内做一次（记忆衰减很快）。产出 `jobs/<slug>/rounds/rN-debrief.md`：把这一轮固化成下一轮能用的东西——问答复原、面试官情报、下轮预测、逐字稿修订清单。

## 输入采集

最好的输入是录音转写。没有就引导回忆倾倒，按这个顺序问（一次 2-3 个问题，别审讯）：

1. 从进场开始按时间顺序过：第一个问题是什么？你怎么答的？
2. 每个问题：面试官当时的反应（追问了？点头？记笔记？换话题？）
3. 哪几题答得不顺、答完自己不满意，或被追问到答不上来？
4. 面试官透露了什么：团队情况、岗位实情、下轮安排、他自己的背景
5. 反问环节你问了什么、对方答了什么

明确告诉用户：记不清的就说记不清，复原里会标「不确定」，比硬凑可靠。

## 产出 rN-debrief.md

frontmatter：`type: debrief / job: <slug> / round: N / updated: <date>`。四个部分：

### 1. 问答复原

按时间顺序，`**Q:**` / `**A:**`（A 记要点和关键原话）。不确定处标 `（不确定）`。面试官的反应用括号注在对应位置。

### 2. 面试官情报更新

观察到的风格（追问型？要数字型？）、在意什么（哪个话题追了三层）、他主动透露的信息（团队/方向/他的背景）。回写进 `intel.md` 的面试官档案。

### 3. 下轮预测与建议

- 本轮剧透的下轮信息：谁面、考什么（面试官经常顺嘴说"下一轮会让你聊聊 X"——这是最高价值情报）
- 本轮暴露的弱点 → 下轮大概率重点核查的点
- 给 interview-script 的修订清单：哪些题答得不顺要重写、下轮要新增什么题

### 4. 待办

按优先级列 3-5 条（核实什么、补什么材料、改什么稿、跟猎头确认什么）。

## 收尾

汇报：复原了几题、面试官情报更新了什么、下轮预测、建议的下一步（通常是按修订清单回 interview-script 改稿）。
