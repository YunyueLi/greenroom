# greenroom 仓库说明（给 Claude 的工作约定）

开源 Community Edition 面试准备系统：公开仓包含可本地运行的 Web 控制台、skills、工作台数据契约、本地后端、岗位百科种子和 Worker 参考实现。结构见 [README.md](README.md)，数据契约见 [docs/workspace-spec.md](docs/workspace-spec.md)。许可证为 AGPL-3.0；品牌使用见 [TRADEMARK.md](TRADEMARK.md)。

## 改动纪律

- **真实个人数据零进入**：本仓库是公开仓库。任何真实候选人的数字、公司名、口径、面试记录都不允许出现；示例只用 `examples/demo-workspace/` 里的虚构人物（林一帆 / 星澜科技 / 远屿资本）。新增示例内容沿用这套虚构世界观。
- **格式即接口**：`workspace-spec.md` 里 script.md 的题卡标记（体例行、`**口径**` 等折叠区，逐字稿里每个数字写定口径与出处）被三处同时依赖——skills 的输出模板、`app/greenroom.html` 的 JS 解析器、`docs/realtime-bridge.md` 的取数约定。改任何一处必须三处同步。
- **示例数据流**：`examples/demo-workspace/` 是源，`app/greenroom.html` 里的 `<!--DEMO:START-->` 块是产物。改了示例后必须跑 `python3 tools/embed-demo.py`。同理 `knowledge/` 是源、`<!--KNOWLEDGE:START-->` 块是产物，改后跑 `python3 tools/embed-knowledge.py`；岗位像素头像 `<!--AVATARS:START-->` 块由 `python3 tools/embed-avatars.py` 生成（DiceBear pixel-art，CC0，构建期需网络），新增/改名岗位后重跑。
- **界面双语**：控制台所有 chrome 文案走 `I18N` 字典（`data-i18n` / `data-i18n-html` / JS 内 `t()`），新增界面文案必须中英双份；工作台内容本身不翻译。
- **服务直连契约**：`serve.py` 与 `docs/workspace-spec.md`「工具取数约定」的 `/workspace/bundle`、`/workspace/file` 两端点保持一致，控制台 `tryServer()` 依赖它。
- **中文文案写作**：skills 与文档里的中文遵守 `skills/interview-script/references/style-zh.md` 的禁令（它管的是逐字稿，但「不是…而是 / 恰恰 / 这正是 / 值得一提」这类句式在本仓库所有中文文案里同样禁用）。
- **skill 规范**：frontmatter 用开放标准字段（name / description / license / metadata），name 与目录名一致；description 第三人称、带触发词、带负面排除；SKILL.md 正文 500 行以内，深层内容放 references/。发布前 `claude plugin validate . --strict`（如 CLI 可用）。
- **版本**：发布改动时同步更新 `.claude-plugin/plugin.json` 和 `marketplace.json` 的 version。

## 本地预览

控制台无前端构建步骤：优先跑 `./start.sh`，或直接开 `app/greenroom.html`。验证三条路径：示例按钮、拖拽文件夹、Chromium 目录选择。
