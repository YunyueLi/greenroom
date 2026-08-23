# greenroom 仓库说明（给 Claude 的工作约定）

开源 Community Edition：面试准备 skills、岗位知识库、工作台数据契约、兼容工具和虚构示例工作台。**本仓库不含产品界面、可部署后端或任何靠模型跑起来的服务**：实时提词、模拟面试接口、一次生成工作台都在官方产品 [greenroom.ungetsu.net](https://greenroom.ungetsu.net/)，它的前端、账号同步、托管服务端和品牌资产同样不在本仓库。结构见 [README.md](README.md)，数据契约见 [docs/workspace-spec.md](docs/workspace-spec.md)。许可证为 AGPL-3.0；品牌使用见 [TRADEMARK.md](TRADEMARK.md)。

## 改动纪律

- **真实个人数据零进入**：本仓库是公开仓库。任何真实候选人的数字、公司名、口径、面试记录都不允许出现；示例只用 `examples/demo-workspace/` 里的虚构人物（林一帆 / 星澜科技 / 远屿资本）。新增示例内容沿用这套虚构世界观。
- **产品层不进公开仓**：产品界面代码、托管服务端（Worker / 账号 / 同步 / 计量）、靠模型跑起来的能力及其全部提示词（实时提词、模拟面试接口、一次生成工作台）、品牌资产（图标、字标、分享图）、精选运营内容一律留在私有产品仓。本仓库只放别人拿去自己也能用的那一层。README 里的图标从 greenroom.ungetsu.net 远程加载，不要把图片文件提交进来。
- **格式即接口**：`workspace-spec.md` 里 script.md 的题卡标记（体例行、`**口径**` 等折叠区，逐字稿里每个数字写定口径与出处）被两处同时依赖：skills 的输出模板，以及任何按契约实现的客户端解析器。改任何一处必须两处同步；契约是对外承诺，改动要当成破坏性变更来对待。
- **不提供本地运行时**：本仓库不包含 HTTP 服务、回环端口或可部署产品后端。兼容工具应让使用者显式选择工作台目录，并直接按 `docs/workspace-spec.md` 读取 Markdown 文件；不要重新加入自动探测 localhost、通配 CORS 或后台服务。
- **契约文档不描述特定界面**：workspace-spec 与 realtime-bridge 面向所有实现者，写「客户端」而不是某个具体产品的界面；需要举例时指向官方产品的网址，不要指向本仓库里不存在的文件。这两份文档都不写提示词、不写模型参数。
- **中文文案写作**：skills 与文档里的中文遵守 `skills/interview-script/references/style-zh.md` 的禁令（它管的是逐字稿，但「不是…而是 / 恰恰 / 这正是 / 值得一提」这类句式在本仓库所有中文文案里同样禁用）。
- **skill 规范**：frontmatter 用开放标准字段（name / description / license / metadata），name 与目录名一致；description 第三人称、带触发词、带负面排除；SKILL.md 正文 500 行以内，深层内容放 references/。发布前 `claude plugin validate . --strict`（如 CLI 可用）。
- **版本**：发布改动时同步更新 `.claude-plugin/plugin.json` 和 `marketplace.json` 的 version。

## 本地验证

无构建步骤。改了 skills 或契约后至少验证两条路径：

- `python3 tools/workspace_codec.py examples/demo-workspace` 的 round-trip 自测通过
- 改了 `tools/workspace_codec.py` 或工作台契约后，运行 `python3 tools/workspace_codec.py examples/demo-workspace --emit`，确认结构化输出仍能生成
