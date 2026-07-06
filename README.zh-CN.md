# greenroom core

**用于生成可迁移面试准备工作台的开源底层。**

greenroom core 把简历和目标岗位转成一个本地 Markdown 工作台：岗位调研、经历卡、行业通识、可直接说出口的逐字稿、模拟面试和面后复盘。公开仓库只保留可复用的协议、skills、本地参考运行时和虚构示例；官方托管产品是单独维护的产品层。

[打开官方产品](https://greenroom.ungetsu.net/) ·
[English README](README.md) ·
[开源边界](OPEN_CORE.md) ·
[工作台契约](docs/workspace-spec.md)

## 公开仓包含什么

| 路径 | 作用 | 许可证 |
| --- | --- | --- |
| `skills/` | 面试准备流水线 Claude / agent skills | MIT core |
| `docs/workspace-spec.md` | 可迁移 Markdown 工作台契约 | MIT core |
| `docs/realtime-bridge.md` | 本地实时助手和模拟面试 API 契约 | MIT core |
| `serve.py` | 工作台文件夹的本地参考运行时 | MIT core |
| `examples/demo-workspace/` | 虚构示例工作台 | MIT core |
| `tools/workspace_codec.py` | 工作台辅助工具 | MIT core |

## 安装 skills

```bash
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom
```

也可以把 `skills/*` 复制到任何兼容的 agent 环境。

然后告诉 agent：

> 我要面试 `<公司>` 的 `<岗位>`，这是我的简历和 JD。

`greenroom` skill 会编排全流程，并把材料写进一个工作台文件夹。

## 运行 core runtime

```bash
python3 serve.py ~/my-greenroom
```

运行时暴露：

- `GET /config`
- `GET /workspace/bundle`
- `GET /workspace/file?path=...`
- `POST /api/answer`
- `POST /api/mock`
- `POST /api/setup`

在工作台 `.env` 里加入 `MODEL_API_KEY=sk-...` 后，可以用任意 OpenAI 兼容模型接口解锁实时答题和模拟面试。

## 工作流

```
简历 + 目标 JD
  -> 岗位调研
  -> 经历库
  -> 行业通识
  -> 逐字稿
  -> 模拟面试
  -> 面后复盘，喂给下一轮
```

工作台本质上是一组 Markdown 文件，所以可读、可迁移。官方产品在同一套 core 契约上增加账号、同步、产品级 UI、托管模型能力和精选知识。

## 许可证

greenroom 是 open-core 项目。

- Core 文件使用 MIT。见 [licenses/MIT.txt](licenses/MIT.txt)。
- 官方托管产品和品牌单独治理。见 [OPEN_CORE.md](OPEN_CORE.md) 和 [TRADEMARK.md](TRADEMARK.md)。
