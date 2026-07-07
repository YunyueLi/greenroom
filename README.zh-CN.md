<div align="center">

<img src="icon-512.png" width="104" alt="greenroom">

# greenroom · 候场

**开源 AI 面试准备工作台。**

*给它你的简历和目标 JD。greenroom 调研岗位，把真实经历整理成可复用的经历卡，写出能直接说出口的逐字稿，跑模拟面试，再把每一轮复盘喂给下一轮。*

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-111.svg)](LICENSE)
&nbsp;[![Release](https://img.shields.io/github/v/release/YunyueLi/greenroom?style=flat&color=111&label=Release)](https://github.com/YunyueLi/greenroom/releases)
&nbsp;[![Stars](https://img.shields.io/github/stars/YunyueLi/greenroom?style=flat&color=111&label=Stars)](https://github.com/YunyueLi/greenroom)
&nbsp;[![English](https://img.shields.io/badge/README-English-111.svg)](README.md)

### [打开官方托管版](https://greenroom.ungetsu.net/) · [本地运行](#本地运行) · [使用 skills](#使用-skills)

</div>

---

> 候场 - 演员上台之前等待和准备的房间。

```
简历 + 目标 JD -> 岗位调研   （公司、面试官、可能的考题）
              -> 经历库     （你的事实，一份底座，按岗位换角度）
              -> 行业通识   -> 逐字稿（按口语标准写）
              -> 模拟面试   -> 教练报告
              -> 复盘       -> 下一轮准备
```

## 它做什么

- **一次备齐全套材料。** 从简历和 JD 出发，生成候选人档案、经历库、岗位情报、行业通识、逐字稿、模拟面试和复盘。
- **写能直接说出口的答案。** 不是要点提纲，而是第一人称口语稿；数字有出处，讲法按岗位换角度。
- **保留可迁移工作台。** 所有材料按公开契约存成 Markdown，agent、本地工具和 Web App 读的是同一份工作台。
- **包含产品界面。** 公开仓包含单文件 Web 控制台、本地后端、岗位百科种子、Cloudflare Worker 参考实现和示例工作台。
- **本地优先。** 不登录也能跑。只有实时提词、生成和模拟面试需要你自己的 OpenAI 兼容模型 key。
- **也有托管路径。** 官方 greenroom 提供账号、云同步、托管模型能力和持续维护的生产部署。

## 本地运行

```bash
git clone https://github.com/YunyueLi/greenroom.git
cd greenroom
./start.sh
```

在控制台里打开示例，或挂载你自己的工作台：

```bash
./start.sh ~/my-greenroom
```

可选模型配置：

```bash
cp .env.example .env
# 编辑 MODEL_API_KEY、MODEL_API_BASE、MODEL_NAME
```

阅读、浏览和岗位百科不需要 key。实时助手、模拟面试和一键生成工作台需要模型 key。

## 使用 skills

```bash
# Claude Code 插件，版本化更新
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom

# 或任何支持 skills 的 agent
npx skills add YunyueLi/greenroom
```

然后告诉 agent：

> 我要面试 Y 公司的 X 岗位，这是我的简历和 JD。

`greenroom` skill 会编排 `job-intel`、`story-bank`、`industry-brief`、`interview-script`、`mock-interview` 和 `debrief`。

## 仓库结构

| 路径 | 是什么 |
| --- | --- |
| `app/greenroom.html` | 单文件 Web 控制台 |
| `serve.py` / `start.sh` | 本地后端和一键启动脚本 |
| `skills/` | 面试准备流水线 skills |
| `docs/workspace-spec.md` | Markdown 工作台契约 |
| `docs/realtime-bridge.md` | 实时助手 / 模拟面试后端契约 |
| `examples/demo-workspace/` | 虚构示例工作台 |
| `knowledge/` | 社区岗位百科种子 |
| `worker/` | Cloudflare Worker 参考后端，支持 BYOK / 账号模式 |
| `tools/` | 嵌入、示例和工作台工具 |

## 官方托管版

官方托管产品在 [greenroom.ungetsu.net](https://greenroom.ungetsu.net/)。它是这个项目的维护部署，提供账号同步、托管云配置、生产可用性维护和托管模型能力。

自部署仍是一等路径：可以跑本地后端、带自己的模型 key，也可以基于公开代码部署自己的 Worker / Supabase 栈。

## 设计和数据

greenroom 使用暖纸底、高对比墨色、克制绿色、自定义 wordmark 和岗位像素工牌头像。它服务两个状态：面试前安静准备，面试中低干扰提词。

本地工作台是一组 Markdown 文件。不要提交真实简历、真实面试材料、薪资信息、公司机密、API key、生产日志或用户数据。

## License

greenroom Community Edition 使用 GNU Affero General Public License v3.0。见 [LICENSE](LICENSE)。

greenroom 名称、logo、wordmark、域名和容易混淆的产品品牌使用由 [TRADEMARK.md](TRADEMARK.md) 管理。
