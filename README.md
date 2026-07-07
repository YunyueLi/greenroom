<div align="center">

<img src="icon-512.png" width="104" alt="greenroom">

# greenroom · 候场

**An open-source AI workbench for interview prep.**

*Give it your resume and a target JD. greenroom researches the role, turns your real experience into reusable story cards, writes scripts you can say out loud, runs mock interviews, and carries every debrief into the next round.*

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-111.svg)](LICENSE)
&nbsp;[![Release](https://img.shields.io/github/v/release/YunyueLi/greenroom?style=flat&color=111&label=Release)](https://github.com/YunyueLi/greenroom/releases)
&nbsp;[![Stars](https://img.shields.io/github/stars/YunyueLi/greenroom?style=flat&color=111&label=Stars)](https://github.com/YunyueLi/greenroom)
&nbsp;[![中文](https://img.shields.io/badge/README-中文-111.svg)](README.zh-CN.md)

### [Open the hosted product](https://greenroom.ungetsu.net/) · [Run locally](#run-locally) · [Use the skills](#use-the-skills)

</div>

---

> 候场 - the room where performers wait and prepare before going on stage.

```
resume + target JD -> role research       (company, interviewers, likely questions)
                   -> experience bank    (your facts, one source of truth)
                   -> industry brief     -> speakable scripts
                   -> mock interview     -> coach report
                   -> debrief            -> next-round prep
```

## What it does

- **Builds the full prep kit.** From resume + JD to candidate profile, story bank, role intelligence, industry brief, interview scripts, mock rounds, and debriefs.
- **Writes speakable answers.** Scripts are not outlines; they are first-person answers that keep numbers source-backed and role-specific.
- **Keeps a portable workspace.** Everything lives as Markdown under a simple workspace contract, so agents, local tools, and the web app can read the same files.
- **Includes the product UI.** The community repo ships the single-file web console, local backend, role encyclopedia seeds, Cloudflare Worker reference, and demo workspace.
- **Supports local-first use.** Run it without an account. Add your own OpenAI-compatible model key only when you want live prompts, generation, or mock interviews.
- **Offers a hosted path.** The hosted greenroom adds managed accounts, cloud sync, hosted model access, and the maintained production deployment.

## Run locally

```bash
git clone https://github.com/YunyueLi/greenroom.git
cd greenroom
./start.sh
```

Open the demo from the console, or mount your own workspace:

```bash
./start.sh ~/my-greenroom
```

Optional model access:

```bash
cp .env.example .env
# edit MODEL_API_KEY, MODEL_API_BASE, MODEL_NAME
```

No key is needed for reading, browsing, or the role encyclopedia. A key unlocks live copilot, mock interview, and one-pass setup generation.

## Use the skills

```bash
# Claude Code plugin, versioned updates
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom

# or any agent that supports skills
npx skills add YunyueLi/greenroom
```

Then tell your agent:

> I'm interviewing for the X role at Y. Here is my resume and the JD.

The `greenroom` skill orchestrates `job-intel`, `story-bank`, `industry-brief`, `interview-script`, `mock-interview`, and `debrief`.

## Repo layout

| Path | What |
| --- | --- |
| `app/greenroom.html` | Single-file web console |
| `serve.py` / `start.sh` | Local backend and one-command launcher |
| `skills/` | Agent skills for the prep workflow |
| `docs/workspace-spec.md` | Markdown workspace contract |
| `docs/realtime-bridge.md` | Live copilot / mock interview backend contract |
| `examples/demo-workspace/` | Fictional demo workspace |
| `knowledge/` | Community role encyclopedia seeds |
| `worker/` | Cloudflare Worker reference backend with BYOK/account-aware modes |
| `tools/` | Embedding, demo, and workspace tooling |

## Hosted greenroom

The official hosted product is available at [greenroom.ungetsu.net](https://greenroom.ungetsu.net/). It is the maintained deployment of this project with account sync, managed cloud configuration, production uptime work, and hosted model access.

Self-hosting remains first-class: run the local backend, bring your own model key, or deploy your own Worker/Supabase stack from the public code.

## Design and data

greenroom uses a warm paper surface, high-contrast ink, restrained green, a custom wordmark, and pixel-art role badges. The product is designed for two states: quiet preparation before the interview and low-friction prompting during the interview.

Your local workspace is a folder of Markdown files. Do not commit real resumes, interview material, salary details, private company information, API keys, production logs, or user data.

## License

greenroom Community Edition is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

The greenroom name, logo, wordmark, domain, and confusingly similar product branding are governed by [TRADEMARK.md](TRADEMARK.md).
