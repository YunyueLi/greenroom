# greenroom core 仓库说明

Open-core 面试准备系统：公开仓只维护 MIT core；官方 Web、Worker、桌面端、品牌资产、精选岗位知识和线上产品体验在私有产品层维护。结构和授权边界见 [README.md](README.md)、[OPEN_CORE.md](OPEN_CORE.md)，数据契约见 [docs/workspace-spec.md](docs/workspace-spec.md)。

## 改动纪律

- **真实个人数据零进入**：本仓库是公开 core。任何真实候选人的数字、公司名、口径、面试记录都不允许出现；示例只用 `examples/demo-workspace/` 里的虚构人物（林一帆 / 星澜科技 / 远屿资本）。新增示例内容沿用这套虚构世界观。
- **格式即接口**：`workspace-spec.md` 里 script.md 的题卡标记（体例行、`**口径**` 等折叠区，逐字稿里每个数字写定口径与出处）被 skills、`serve.py`、`docs/realtime-bridge.md` 和兼容客户端共同依赖。改任何一处必须同步契约文档和相关 skill 模板。
- **公开仓不放产品层**：不要新增 `app/`、`worker/`、`workers/`、`desktop/`、`brand/`、图标/wordmark、营销落地页或精选知识库。此类内容进入私有产品仓。
- **服务直连契约**：`serve.py` 与 `docs/workspace-spec.md`「工具取数约定」的 `/workspace/bundle`、`/workspace/file`、`/config`、`/api/answer`、`/api/mock` 保持一致。
- **中文文案写作**：skills 与文档里的中文遵守 `skills/interview-script/references/style-zh.md` 的禁令（它管的是逐字稿，但「不是…而是 / 恰恰 / 这正是 / 值得一提」这类句式在本仓库所有中文文案里同样禁用）。
- **skill 规范**：frontmatter 用开放标准字段（name / description / license / metadata），name 与目录名一致；description 第三人称、带触发词、带负面排除；SKILL.md 正文 500 行以内，深层内容放 references/。发布前尽量运行 `claude plugin validate . --strict`（如 CLI 可用）。
- **版本**：发布改动时同步更新 `.claude-plugin/plugin.json` 和 `marketplace.json` 的 version。

## 本地预览

公开仓只有 core runtime：

```bash
python3 serve.py ~/my-greenroom
```

状态页在 `http://127.0.0.1:8787/`。官方产品 UI 不从公开仓启动。
