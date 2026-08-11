# greenroom 仓库说明（给 Claude 的工作约定）

开源 Community Edition：面试准备 skills、岗位知识库、工作台数据契约、本地参考后端和虚构示例工作台。**不含产品界面**——官方产品在 [greenroom.ungetsu.net](https://greenroom.ungetsu.net/)，它的前端、账号同步、托管服务端和品牌资产都不在本仓库。结构见 [README.md](README.md)，数据契约见 [docs/workspace-spec.md](docs/workspace-spec.md)。许可证为 AGPL-3.0；品牌使用见 [TRADEMARK.md](TRADEMARK.md)。

## 改动纪律

- **真实个人数据零进入**：本仓库是公开仓库。任何真实候选人的数字、公司名、口径、面试记录都不允许出现；示例只用 `examples/demo-workspace/` 里的虚构人物（林一帆 / 星澜科技 / 远屿资本）。新增示例内容沿用这套虚构世界观。
- **产品层不进公开仓**：产品界面代码、托管服务端（Worker / 账号 / 同步 / 计量）、品牌资产（图标、字标、分享图）、精选运营内容一律留在私有产品仓。本仓库只放别人拿去自己也能用的那一层。README 里的图标从 greenroom.ungetsu.net 远程加载，不要把图片文件提交进来。
- **格式即接口**：`workspace-spec.md` 里 script.md 的题卡标记（体例行、`**口径**` 等折叠区，逐字稿里每个数字写定口径与出处）被三处同时依赖——skills 的输出模板、任何按契约实现的客户端解析器、`docs/realtime-bridge.md` 的取数约定。改任何一处必须三处同步；契约是对外承诺，改动要当成破坏性变更来对待。
- **服务直连契约**：`serve.py` 与 `docs/workspace-spec.md`「工具取数约定」的 `/workspace/bundle`、`/workspace/file` 两端点保持一致。这两个端点是第三方工具的对接面，签名不能随手改。
- **契约文档不描述特定界面**：workspace-spec 与 realtime-bridge 面向所有实现者，写「客户端」而不是某个具体产品的界面；需要举例时指向官方产品的网址，不要指向本仓库里不存在的文件。
- **中文文案写作**：skills 与文档里的中文遵守 `skills/interview-script/references/style-zh.md` 的禁令（它管的是逐字稿，但「不是…而是 / 恰恰 / 这正是 / 值得一提」这类句式在本仓库所有中文文案里同样禁用）。
- **skill 规范**：frontmatter 用开放标准字段（name / description / license / metadata），name 与目录名一致；description 第三人称、带触发词、带负面排除；SKILL.md 正文 500 行以内，深层内容放 references/。发布前 `claude plugin validate . --strict`（如 CLI 可用）。
- **版本**：发布改动时同步更新 `.claude-plugin/plugin.json` 和 `marketplace.json` 的 version。

## 本地验证

无构建步骤。改了 skills 或契约后至少验证两条路径：

- `./start.sh ~/some-workspace` 起本地后端，`curl http://127.0.0.1:8787/workspace/bundle` 能拿到工作台全文
- `python3 -m py_compile serve.py` 通过；改了 `tools/workspace_codec.py` 后确认它仍能解析 `examples/demo-workspace/`
