---
name: greenroom
description: Prepare a complete interview workspace from a resume and target role, or choose the next preparation step when the user needs guidance.
license: AGPL-3.0
metadata:
  author: Yunyue Li
  version: "0.3.1"
---

# Greenroom · 候场

为目标面试准备完整工作台，或根据用户当前需求选择一个专项技能。用户已经指定步骤时直接处理该步骤；不要因其他材料尚未生成而自动扩大任务。

## 选择范围

| 用户目标 | 专项技能 | 主要产出 |
| --- | --- | --- |
| 研究岗位、公司或面试官 | [job-intel](../job-intel/SKILL.md) | `jobs/<slug>/intel.md` |
| 整理真实项目与成果 | [story-bank](../story-bank/SKILL.md) | `story-bank.md` |
| 撰写或修改可朗读答案 | [interview-script](../interview-script/SKILL.md) | `jobs/<slug>/script.md` |
| 补充行业与岗位知识 | [industry-brief](../industry-brief/SKILL.md) | `library/*.md` |
| 进行模拟面试 | [mock-interview](../mock-interview/SKILL.md) | `jobs/<slug>/rounds/mock-N.md` |
| 复盘已结束的真实面试 | [debrief](../debrief/SKILL.md) | `jobs/<slug>/rounds/rN-debrief.md` |

- 用户要求完整备战材料时，读取 [全流程](references/full-preparation.md)。
- 用户未指定下一步时，根据目标岗位已有材料和当前缺口建议一个步骤；临近面试可以建议演练，得到演练请求后再开始问答。
- 优先使用用户指定的工作台。只有需要定位或新建工作台时读取 [工作台准备](references/workspace.md)。不要加载无关岗位或其他候选人的文件。

## 共同约束与完成标准

- 经历和数字仅取自候选人提供的材料；事实不全时明确缺口，不补造。缺少准确数字可以用定性表达；只有阻碍当前产出的问题才需要向用户补问。
- 用户明确的表达风格优先于技能的默认写作习惯。中文请求默认中文交付；事实真实性、隐私与工作台格式契约继续成立。
- 已给出的简历、JD、工作台路径和偏好直接复用，不重复确认。需要补充多个关键输入时一次问清。
- 在已授权范围内完成产出、落盘与相关检查，再汇报文件位置和仍待核实的事实。单步任务只交付对应材料；完整任务按全流程的材料清单核对完成。
- Skill 调用使用当前工具支持的名字；Claude 插件可使用 `/greenroom:job-intel` 等入口。没有调用入口时读取对应技能执行，不虚构调用成功。
