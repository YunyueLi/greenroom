<div align="center">

<img src="https://greenroom.ungetsu.net/icon-512.png" width="96" alt="greenroom">

# greenroom · 候场

**把面试准备做到能张口说出来为止。**

*七个 agent 技能包、160+ 岗位的知识库、一套开放的 Markdown 工作台格式。把简历和目标 JD 交给 agent，拿回岗位情报、带出处的经历库、可朗读的逐字稿、模拟面试和复盘——复盘再喂给下一轮。*

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-111.svg)](LICENSE)
&nbsp;[![Release](https://img.shields.io/github/v/release/YunyueLi/greenroom?style=flat&color=111&label=Release)](https://github.com/YunyueLi/greenroom/releases)
&nbsp;[![Stars](https://img.shields.io/github/stars/YunyueLi/greenroom?style=flat&color=111&label=Stars)](https://github.com/YunyueLi/greenroom)
&nbsp;[![English](https://img.shields.io/badge/README-English-111.svg)](README.md)

### **[打开线上版 →](https://greenroom.ungetsu.net/)**&nbsp;&nbsp;·&nbsp;&nbsp;[装上技能包](#三十秒装好)&nbsp;&nbsp;·&nbsp;&nbsp;[读格式契约](docs/workspace-spec.md)

</div>

---

> 候场——上台之前，演员等待和准备的那个房间。

```
简历 + 目标 JD ─→ 岗位调研      （公司、面试官、可能考什么）
              ─→ 经历库        （你的事实，只有一份底本）
              ─→ 行业通识      ─→ 可朗读的逐字稿
              ─→ 模拟面试      ─→ 教练报告
              ─→ 面后复盘      ─→ 下一轮备战
```

## 为什么用这个

**它写的是答案，不是提纲。** 多数准备工具给你几条要点，剩下最难的一步——临场把要点变成完整句子——还是留给你。greenroom 把句子写出来。

**每个数字都带着自己的口径。** 逐字稿里出现一个数，同时写清它怎么算的、从哪来。被追问的时候，接住的是一个站得住的说法，不是当场编的。

```markdown
　　上线到现在，自助解决率从 31% 做到 52%，客服人力成本降了 18%。

**数字出处**
- 解决率 31%→52%，统计口径=未转人工且 24h 未重复进线（被追问时主动给口径）
```

**你的准备是一个属于你的文件夹。** 纯 Markdown，格式公开写明。没有锁定，也不需要导出——文件本来就在你手上，任何读得懂契约的工具都能读它。

## 三十秒装好

```bash
# Claude Code 插件，可版本化更新
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom
```

```bash
# 或者任何支持 skills 的 agent
npx skills add YunyueLi/greenroom
```

然后直接说：

> 下周二面 Acme 的 AI 产品经理，这是我的简历和 JD。

`greenroom` 入口技能会跑完整条流水线，写出一个工作台文件夹。说「只要逐字稿」或者「陪我练一轮」，它就只跑那一步。

## 七个技能包

| 技能包 | 做什么 |
| --- | --- |
| `greenroom` | 入口——跑完整流程，或者按需路由到某一步 |
| `job-intel` | 拆 JD、查公司和面试官、预测下一轮考题 |
| `story-bank` | 把你的真实经历挖成可复用的经历卡，数字带出处 |
| `industry-brief` | 写这个行业和岗位的通识，补到能聊得像内行 |
| `interview-script` | 把上面所有材料变成第一人称、能念出口的答案 |
| `mock-interview` | 当面试官出题追问，练完给评分和教练报告 |
| `debrief` | 把刚面完那一轮还原出来，转成逐字稿的修订清单 |

## 它会写出什么

```
my-greenroom/
├── profile.md                  候选人档案
├── resume.md                   简历的 Markdown 转写，事实底本
├── story-bank.md               经历卡，按岗位类型换讲法
├── library/                    行业通识、调研、参考阅读
└── jobs/<公司-岗位>/
    ├── job.md                  JD 原文，附岗位进程时间线
    ├── intel.md                公司、面试官、考题预测
    ├── script.md               逐字稿
    └── rounds/                 备战稿、模拟报告、面后复盘
```

[`examples/demo-workspace/`](examples/demo-workspace/) 是一份完整的示例工作台：格式是真的，人物是虚构的。

## 岗位知识库

[`knowledge/`](knowledge/) 收了 160+ 个岗位条目，分在 27 个行业与职能分组里：高频题、岗位通识、追问模式。它不含任何候选人数据，可以放心读、放心 fork、放心贡献。`industry-brief` 技能包生成通识时会先查这里，攒得越全，每个新用户冷启动越快。

## 在它上面搭东西

工作台格式是对外公开的契约，不是内部实现细节。读同一份契约的工具之间天然互通。

| | |
| --- | --- |
| [`docs/workspace-spec.md`](docs/workspace-spec.md) | 目录结构、frontmatter、`script.md` 题卡格式、HTTP 取数端点 |
| [`docs/realtime-bridge.md`](docs/realtime-bridge.md) | 怎么把工作台接进你自己的工具：HTTP 直读，或者直接读盘 |
| [`serve.py`](serve.py) | 工作台取数端点的零依赖参考实现，只用 Python 标准库 |

```bash
git clone https://github.com/YunyueLi/greenroom.git
cd greenroom
./start.sh ~/my-greenroom      # 在 :8765 上把工作台开成 HTTP 接口
```

读工作台不需要 API key，也不需要账号。本地服务只把工作台读出来，交给任何按契约实现的客户端。

## 线上版

**[greenroom.ungetsu.net](https://greenroom.ungetsu.net/)** 是官方产品：完整界面、账号与云同步、托管模型能力（面试中的实时提词、模拟面试、一次生成工作台）、持续运维的正式部署。它读写的就是这里写明的同一套工作台格式，所以你照契约做的东西不会白做。

## 这里有什么，没有什么

**有的**，按 AGPL-3.0 授权：技能包、岗位知识库、工作台契约、取数参考服务、示例工作台。拿去跑、拿去改、拿去做兼容工具都可以。

**没有的**：产品界面、账号与云同步、托管服务端及其模型端点（实时提词、模拟面试评分、一次生成工作台）、品牌资产。这些属于官方产品。`mock-interview` 技能包照旧可以在你自己的 agent 里跑完整一轮模拟面试。

## 隐私

工作台是你本机上的一个文件夹。真实简历、面试材料、薪资数字、公司内部信息、API key、生产日志——不要提交到这个仓库，也不要提交到任何别的公开仓库。

## 许可证

greenroom Community Edition 按 GNU Affero General Public License v3.0 授权，见 [LICENSE](LICENSE)。

greenroom 名称、logo、wordmark、域名和容易混淆的产品品牌使用由 [TRADEMARK.md](TRADEMARK.md) 管理。
