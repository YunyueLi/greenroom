---
name: industry-brief
description: Generates industry and role reference reading (行业与岗位通识) for a target job — landscape, role expectations, must-know concepts, high-frequency interview topics, quotable viewpoints with sources — written to the workspace library/ folder. Use when the user asks for 行业通识 / 岗位认知 / 这个行业要懂什么 / 面这个方向需要补什么知识, or as step 4 of the greenroom full pipeline. Do NOT use for company-specific research (use job-intel) or answer scripts (use interview-script).
license: MIT
metadata:
  author: Yunyue Li
  version: "0.3.0"
---

# industry-brief · 行业与岗位通识

为目标岗位生成一份可以反复阅读的参考材料，落在工作台 `library/<行业-岗位>-通识.md`。它解决的问题：候选人对岗位本身能讲清楚，但行业格局、岗位方向的高频概念、面试官默认你该知道的常识有缺口。

## 前置

1. 读 `jobs/<slug>/job.md` 和 `intel.md`（知道行业、岗位方向、面试官背景）。
2. 读工作台 `library/` 里的既有资料；如果用户或产品层提供了额外岗位知识包，可以作为参考，但不得假设公开 core 仓库内存在精选知识库。

## 调研与写作

用 web 搜索补齐，每条硬结论带来源链接，拿不准标「未核实」。结构：

```markdown
---
title: <行业> · <岗位方向> 通识
updated: <date>
---

# <行业> · <岗位方向> 通识

## 行业格局
头部玩家、近 12 个月的关键变化、当前争论点（面试官爱用争论点出题）。

## 岗位画像
这个方向的人日常做什么、用什么衡量产出、和相邻岗位的边界。

## 必须能讲清的概念
8-15 个，每个两三句人话解释 + 一个会被追问的点。

## 高频面试话题
按出现频率排序，每个给出题角度（参考公开面经、官方文档、行业报告和用户已有资料，带来源）。

## 值得引用的观点
3-5 条来自头部从业者公开发言的判断，注明谁说的、哪里说的。面试中引用要消化成自己的话。
```

## 纪律

- 写的是**参考阅读**，不替用户表态；观点都注明出处，候选人自己决定信哪条。
- 篇幅 1500-3000 字，超了就砍：这是考前阅读材料，长到读不完等于没写。
- 通用知识沉淀：如果本次调研产出了与候选人个人无关、无保密风险的通用内容，可以提示用户整理成社区资料或提交到公开 core 允许接收的知识贡献范围。

## 收尾

汇报：写了哪个文件、覆盖了几个概念和话题、引用了几条来源；提示在官方产品、桌面端或兼容客户端的「资料」页阅读。
