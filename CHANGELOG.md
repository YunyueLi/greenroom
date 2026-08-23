# Changelog

All notable changes to the greenroom open layer — the skills, the role knowledge
base, the workspace contract, and compatible file-format tools. Versions track
`.claude-plugin/plugin.json`.

Product-layer history (the hosted interface, accounts and sync, the hosted
service backend, brand assets) is kept with the product and is not tracked here.

## v0.42.0 — 2026-08
**Breaking — the open layer no longer ships a local HTTP runtime.** The public
contract remains a portable Markdown file format; compatible tools read files
chosen by the user instead of probing a loopback server.

- **Removed:** `serve.py`, `start.sh`, and the server-only `Makefile` targets.
- **Removed from the release bundle:** the local server and launcher.
- **Contract narrowed:** `docs/workspace-spec.md` now specifies direct file
  access only; `docs/realtime-bridge.md` shows filesystem integration without
  HTTP endpoints, wildcard CORS, or localhost auto-discovery.
- **Product boundary clarified:** the repository contains Skills, public role
  knowledge, the Markdown contract, examples, and compatible file tools. It is
  not a local or self-hosted edition of Greenroom.

## v0.41.0 — 2026-08
**Breaking — the model-served endpoints are withdrawn. The public repository is now a set of agent skills plus a data contract.** Anything that needs a model to run belongs to the hosted product, and running a model on a user's behalf was never the part of this project that anyone could pick up and reuse. What remains is that reusable layer: seven skills your own agent runs, a 27-group role knowledge base, the workspace contract, and a read-only reference server.

- **Removed from `serve.py`:** `POST /api/answer` (live prompting), `POST /api/mock` (interviewer persona and coach report) and `POST /api/setup` (one-pass workspace generation), along with everything they needed to run; also `POST /api/ping` (model key liveness check) and `POST /api/fetch-jd`, the model key and model-name lookup, the upstream streaming proxy, and the BYOK request headers. No `POST` route remains, and no `.env` is read anywhere in this repository.
- **Removed:** `.env.example`. `start.sh` no longer creates a `.env` or asks for a key, and `docs/realtime-bridge.md` no longer documents model configuration.
- **`GET /config` now returns `{"personas": {...}}` only.** The `has_key` and `model` fields reported model state and are gone. A client that used `has_key` for capability detection will find the field missing; that is intended, since the open layer no longer advertises model access.
- **Kept unchanged:** the workspace read endpoints `GET /workspace/bundle` and `GET /workspace/file`, plus `GET /api/resolve-logo`. Third-party clients read a workspace through these, and interoperability is the point of publishing a contract.
- **`docs/realtime-bridge.md` is now a read-integration guide**, retitled 工作台取数对接: the two ways to read a workspace, the CORS requirement, and the boundary. The live-prompting system prompt, the endpoint protocols and the prompt-engineering notes are gone. `docs/workspace-spec.md` absorbed the `/config` shape and the CORS rule, and dropped its own summary of how a live prompter assembles context.
- **The skills are untouched.** `mock-interview` still plays the interviewer with pressure follow-ups and scores the round; `interview-script` still writes speakable answers. They run through your own agent, which is what a skill is — only the server endpoints that happened to share those names are gone.
- **Earlier releases stand.** Every version through v0.40.1 was published under AGPL-3.0, and this change does not retract a grant already made. It governs what ships from here on.
- **License framing corrected.** The seven `SKILL.md` files still carried `license: MIT` in their frontmatter while `LICENSE`, `plugin.json` and `marketplace.json` all said AGPL-3.0. v0.40.0 claimed the framing was unified and missed these seven; they now read AGPL-3.0, and `CONTRIBUTING.md` no longer allows a per-file exception. This corrects a stale declaration rather than relicensing anything: copies already obtained under the earlier declaration keep the terms they were given.

## v0.40.0 — 2026-08
**The public repository is now the skills-and-contract layer; the interface belongs to the product.** The single-file web console, its landing page and routing config, the Cloudflare Worker backend, the cloud-sync docs and the brand assets were all withdrawn from this repository. What remains is the layer that is useful to anyone on its own terms: seven agent skills, a 27-role knowledge base, the workspace contract, and a zero-dependency reference backend.

- **Removed:** `app/greenroom.html` and `app/srs.js`; `index.html`, `404.html`, `_headers`, `_redirects` and `scripts/build-pages.sh` (all of which existed only to publish the console); the three `tools/embed-*.py` data-embedding scripts and `tools/srs-parity.mjs`; `worker/`; `docs/cloud-sync.md` and `docs/supabase-keepalive.sql`; all icons, wordmarks, the social image and `site.webmanifest`; `DESIGN.md` and `PRODUCT.md`.
- **`serve.py` is now a backend, not a page server.** The console routes are gone; `GET /` returns the endpoint index. The workspace read endpoints (`/workspace/bundle`, `/workspace/file`), `/config` and the three model endpoints are unchanged — the contract in `docs/realtime-bridge.md` still holds.
- **The workspace contract now reads as a contract.** `docs/workspace-spec.md` and `docs/realtime-bridge.md` describe what any conforming client does instead of what one particular interface does, and no longer point at files that live outside this repository.
- **License framing unified on AGPL-3.0.** The core was described as MIT in one place and shipped as AGPL-3.0 in another; AGPL-3.0 is the answer, and the role knowledge base is explicitly part of the open layer.
- **Both READMEs rewritten** around the new positioning, with the hosted product as the linked destination rather than something this repository contains.

## v0.39.0 — 2026-07
**Positioned as a Community Edition rather than a narrow core.** License changed to AGPL-3.0 so the project can be broadly useful while discouraging closed hosted clones. Both READMEs moved from a defensive boundary explanation to product value, quick start and skills install. (The scope described in this release was narrowed again in v0.40.0.)

## v0.38.1 — 2026-07
**Open-core boundary first formalized.** Added `TRADEMARK.md` and `CONTRIBUTING.md`, and documented which layer is which: the workspace contract, skills, local reference runtime and fictional demo workspace on the open side; the hosted app, service backend, account and sync, and brand assets on the product side.

## v0.26.0 — 2026-06
**Job folders never silently lose a file, and pre-round prep becomes a contract type.** `docs/workspace-spec.md` gains the `round-prep` type and a no-silent-drop guarantee: any unrecognized `.md` inside a job folder must be surfaced rather than discarded. The demo workspace gains a `round-prep` example.

## v0.25.0 — 2026-06
**Breaking — the claim-ledger skill and the cross-round claims log were removed.** Tracking whether your wording stayed consistent across rounds didn't earn its complexity: real interviewers don't diff your answers across rounds, and the ledger pulled focus from the actual deliverable.
- **skills:** deleted `claim-ledger`; the suite is now **7 skills** (the `greenroom` orchestrator plus `job-intel`, `story-bank`, `interview-script`, `industry-brief`, `mock-interview`, `debrief`). The anti-fabrication rule — a number carries its source, never invent one — stays; that is honesty, not ledger-keeping.
- **`serve.py`:** dropped the `claims.md` injection and the coach's reconciliation pass; mock coaching scores four content dimensions (structure / evidence / role-fit / follow-up resilience). Kept *only use numbers that appear in the script*.
- **docs & examples:** `claims.md` removed from the workspace contract and the demo workspace; `docs/realtime-bridge.md` no longer defines a claims contract.

## v0.23.0 — 2026-06
**AI and product playbooks upgraded to the deeper scaffold.** All nine Algorithm·AI roles (LLM / CV / RecSys / Search / NLP / Speech / ML / Risk / AD-perception) rewritten to the responsibilities + 6-probe mental models + 5-axis watershed + Bloom-tagged must-knows structure, and the eight remaining product roles back-filled to the same scaffold with their numbers re-verified. Every role went through deep-write then adversarial calibration; calibration caught real errors, including a fabricated watch-time metric and several stale benchmarks. **New AI industry brief** covering the 2026 landscape as its own industry, separate from the Algorithm·AI function axis.

## v0.22.0 — 2026-06
**Deeper playbook scaffold.** Role entries gain a top-level core-responsibilities block; mental models follow a 6-probe cognitive-task-analysis checklist including the often-missed self-calibration probe; the watershed renders as a 5-axis strong-vs-weak table decidable on the spot; must-knows carry Bloom-level tags separating the fail line from the expert line. The core-tension line became optional, since it degrades into generic "speed vs quality" outside design and product roles. First technical-role playbook (Game Client Programmer) lands as the golden sample. Section labels renamed to plain Chinese.

## v0.21.0 — 2026-06
**Segment-level industry briefs.** An industry file can carry `## 细分导读：<segment>` sections with the same fields as the industry brief, so a selected segment gets its own reading instead of falling back to the whole industry. Ships with a Game brief under Internet.

## v0.20.0 — 2026-06
**World-class playbook format, and the first verticals written to it.** Role entries adopt a two-tier 怎么想 / 怎么考 structure — mental models, benchmarks, canonical cases, two-sided open debates, and the watershed between strong and weak candidates — distilled to an insider bar: non-obvious, actionable, fact-checked. The nine product-management roles are rewritten to this bar, and the game-design family lands its first seven playbooks, each adversarially calibrated against authoritative sources with a `来源` line.

## v0.19.0–v0.19.1 — 2026-06
**Time became part of the contract.** Story cards carry an optional `**时间**：<org> · <span>` line; `library/` docs surface relative freshness from their `updated:` date, falling back to a date parsed from the filename (a 20xx year prefix is required so version strings aren't mistaken for dates). Documented in `docs/workspace-spec.md`; the `story-bank` skill template updated to match.

## v0.16.0 — 2026-06
**Four more industries**, filling gaps surfaced by research: Energy & Environment, Agriculture & Food, Travel & Hospitality, Legal Services. Plus clinical roles added to Healthcare. 15 industries, 155 role playbooks.

## v0.15.0 — 2026-06
**Sports & Entertainment industry** (esports, sports, talent agency, live shows) with event ops, club manager, team analyst, caster, talent agent, show producer and sports marketing.

## v0.14.0 — 2026-06
**Roles encyclopedia rebuilt to a higher standard.** The function axis was redefined into 11 mutually-exclusive groups, each with a primary-deliverable boundary rule: AI·Data split into Algorithm·AI and Data; Consulting·HR·Legal split into Strategy·Consulting and People·Legal·Admin. Role library went from 60 to 128 base and specialized roles, with every industry's segments filled out.

## v0.13.0–v0.13.1 — 2026-06
**Function × industry as a composition model.** Functions are base roles; industries are a context layer with their own briefs. Any combination produces content, so there are no empty cells. Added Consumer Retail.

## v0.8.0–v0.9.2 — 2026-06
**`serve.py` became a full reference backend** — `/api/answer`, `/api/mock`, `/config` and `/api/setup`, with personas auto-discovered from `jobs/`. Workspace generation from a resume plus a pasted JD needs no agent in the loop.

## v0.1.0–v0.7.x — 2026-06
**Initial release.** Eight skills covering the full prep pipeline, the Markdown workspace data contract, and the role knowledge base with its industry-and-function model.
