# greenroom core

**Open-source interview-prep core for building a portable preparation workspace.**

greenroom core turns a résumé and target role into a local Markdown workspace:
role research, experience cards, industry reading, spoken interview scripts,
mock interviews, and debriefs. The public repository contains the reusable
contract and agent skills. The official hosted product lives separately.

[Open official product](https://greenroom.ungetsu.net/) ·
[中文 README](README.zh-CN.md) ·
[Open-core policy](OPEN_CORE.md) ·
[Workspace spec](docs/workspace-spec.md)

## What Is Public

| Path | Purpose | License |
| --- | --- | --- |
| `skills/` | Claude / agent skills for the prep pipeline | MIT core |
| `docs/workspace-spec.md` | Portable Markdown workspace contract | MIT core |
| `docs/realtime-bridge.md` | Local live-copilot and mock-interview API contract | MIT core |
| `serve.py` | Reference local runtime for a workspace folder | MIT core |
| `examples/demo-workspace/` | Fictional demo workspace | MIT core |
| `tools/workspace_codec.py` | Workspace helper utilities | MIT core |

## Install Skills

```bash
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom
```

Or copy `skills/*` into any compatible agent environment.

Then tell the agent:

> I am interviewing for `<role>` at `<company>`. Here is my résumé and the JD.

The `greenroom` skill orchestrates the pipeline and writes a workspace folder.

## Run The Core Runtime

```bash
python3 serve.py ~/my-greenroom
```

The runtime exposes:

- `GET /config`
- `GET /workspace/bundle`
- `GET /workspace/file?path=...`
- `POST /api/answer`
- `POST /api/mock`
- `POST /api/setup`

Add `MODEL_API_KEY=sk-...` to `.env` in your workspace to enable live answer
generation and mock interviews with an OpenAI-compatible model provider.

## Workspace Flow

```
résumé + target JD
  -> job intel
  -> story bank
  -> industry brief
  -> spoken scripts
  -> mock interview
  -> debrief for the next round
```

The workspace stays readable and portable because it is just Markdown. The
official product adds hosted accounts, sync, product-grade UI, managed model
access, and curated knowledge on top of the same core contract.

## License

greenroom is open core.

- Core files are MIT-licensed. See [licenses/MIT.txt](licenses/MIT.txt).
- The official hosted product and brand are governed separately. See
  [OPEN_CORE.md](OPEN_CORE.md) and [TRADEMARK.md](TRADEMARK.md).
