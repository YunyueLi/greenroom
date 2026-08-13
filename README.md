
</think>

<div align="center">

<img src="https://greenroom.ungetsu.net/icon-512.png" width="96" alt="greenroom">

# greenroom · 候场

**Interview prep that ends in words you can actually say.**

*Seven agent skills, a 27-role knowledge base, and an open Markdown workspace format. Hand an agent your resume and a target JD — get role intel, a sourced story bank, speakable scripts, mock rounds, and debriefs that feed the next round.*

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-111.svg)](LICENSE)
&nbsp;[![Release](https://img.shields.io/github/v/release/YunyueLi/greenroom?style=flat&color=111&label=Release)](https://github.com/YunyueLi/greenroom/releases)
&nbsp;[![Stars](https://img.shields.io/github/stars/YunyueLi/greenroom?style=flat&color=111&label=Stars)](https://github.com/YunyueLi/greenroom)
&nbsp;[![中文](https://img.shields.io/badge/README-中文-111.svg)](README.zh-CN.md)

### **[Open the app →](https://greenroom.ungetsu.net/)**&nbsp;&nbsp;·&nbsp;&nbsp;[Install the skills](#install-in-30-seconds)&nbsp;&nbsp;·&nbsp;&nbsp;[Read the spec](docs/workspace-spec.md)

</div>

---

> 候场 — the room where performers wait and prepare before going on stage.

```
resume + target JD ─→ role research      (company, interviewers, likely questions)
                   ─→ story bank         (your facts, one source of truth)
                   ─→ industry brief     ─→ speakable scripts
                   ─→ mock interview     ─→ coach report
                   ─→ debrief            ─→ next-round prep
```

## Why this one

**It writes answers, not outlines.** Most prep tools hand you bullet points and leave the hardest part — turning them into sentences under pressure — to you. greenroom writes the sentences.

**Every number carries its own definition.** A script line never states a figure without recording how it was counted and where it came from, so a follow-up question lands on something you can defend instead of something you improvised.

```markdown
	上线到现在，自助解决率从 31% 做到 52%，客服人力成本降了 18%。

**数字出处**
- 解决率 31%→52%，统计口径=未转人工且 24h 未重复进线（被追问时主动给口径）
```

**Your prep is a folder you own.** Plain Markdown under a published contract. No lock-in, no export button — the files are already yours, and any tool that reads the spec can read them.

## Install in 30 seconds

```bash
# Claude Code plugin, versioned updates
/plugin marketplace add YunyueLi/greenroom
/plugin install greenroom@greenroom
```

```bash
# or any agent that supports skills
npx skills add YunyueLi/greenroom
```

Then say:

> I'm interviewing for the AI PM role at Acme next Tuesday. Here's my resume and the JD.

The `greenroom` skill runs the pipeline and writes a workspace folder. Say "just the scripts" or "run a mock" and it routes to one step instead.

## The skills

| Skill | What it does |
| --- | --- |
| `greenroom` | Entry point — runs the full pipeline, or routes to a single step |
| `job-intel` | Deconstructs the JD, researches company and interviewers, forecasts the next round |
| `story-bank` | Mines your real experience into reusable story cards with sourced numbers |
| `industry-brief` | Writes the industry and role reading you need before you can sound informed |
| `interview-script` | Turns all of it into first-person answers you can read out loud |
| `mock-interview` | Plays the interviewer with pressure follow-ups, then scores the performance |
| `debrief` | Reconstructs the round you just finished into a revision list for the script |

## What it writes

```
my-greenroom/
├── profile.md                  candidate profile
├── resume.md                   resume as Markdown, the fact source
├── story-bank.md               story cards, repackaged per role type
├── library/                    industry briefs, research, reference reading
└── jobs/<company-role>/
    ├── job.md                  the JD, plus a timeline of the process
    ├── intel.md                company, interviewers, question forecast
    ├── script.md               the verbatim script
    └── rounds/                 prep notes, mock reports, debriefs
```

A fictional example workspace lives in [`examples/demo-workspace/`](examples/demo-workspace/) — real format, invented people.

## The role knowledge base

[`knowledge/`](knowledge/) holds 27 roles across industries and functions: high-frequency questions, role fundamentals, follow-up patterns. It contains no candidate data and is safe to read, fork, and contribute to. The `industry-brief` skill checks it first, so the more complete it gets, the faster every new user starts.

## Build on it

The workspace format is a published contract, not an internal detail. Anything that reads it works with everything else that reads it.

| | |
| --- | --- |
| [`docs/workspace-spec.md`](docs/workspace-spec.md) | File layout, frontmatter, the `script.md` card format, the HTTP read endpoints |
| [`docs/realtime-bridge.md`](docs/realtime-bridge.md) | Contract for live-prompting and mock-interview backends |
| [`serve.py`](serve.py) | Zero-dependency reference backend — Python standard library only |

```bash
git clone https://github.com/YunyueLi/greenroom.git
cd greenroom
./start.sh ~/my-greenroom      # serves the workspace over HTTP on :8765
```

No API key is needed to read a workspace. Add an OpenAI-compatible key in `.env` to unlock live prompting, mock interviews, and one-pass generation.

## The hosted app

**[greenroom.ungetsu.net](https://greenroom.ungetsu.net/)** is the official product: the full interface, accounts and cloud sync, hosted model access, and a maintained deployment. It reads and writes the same workspace format documented here, so nothing you build against the spec is wasted.

## What's here and what isn't

**Here**, under AGPL-3.0: the skills, the role knowledge base, the workspace contract, the reference backend, the demo workspace. Run it, fork it, build compatible tools on it.

**Not here**: the product interface, accounts and cloud sync, the hosted service backend, and the brand assets. Those belong to the official product.

## Privacy

Your workspace is a folder on your machine. Never commit real resumes, interview material, salary figures, private company information, API keys, or production logs — to this repository or any other public one.

## License

greenroom Community Edition is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

The greenroom name, logo, wordmark, domain, and confusingly similar product branding are governed by [TRADEMARK.md](TRADEMARK.md).
