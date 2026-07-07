# Changelog

All notable changes to greenroom. Versions track `.claude-plugin/plugin.json`.

## v0.39.0 — 2026-07
**Community Edition is now the public product surface.** The public repository is no longer positioned as a narrow open-core shell. It now carries the runnable web console, local backend, skills, workspace contract, role encyclopedia seeds, Worker reference backend, demo workspace, and product documentation as the greenroom Community Edition.

- License changed to AGPL-3.0 so the project can be broadly useful while discouraging closed hosted clones.
- README / README.zh-CN now lead with product value, quick start, local run, skills install, and hosted/self-hosted paths instead of a defensive boundary explanation.
- Removed `OPEN_CORE.md` and the old MIT core license file; updated plugin metadata, contribution rules, app footer, worker docs, and design/product notes to match the public Community Edition model.
- Production deployment details remain outside the public repo. Public Worker config uses placeholders for user-owned Cloudflare/D1 resources.

## v0.38.1 — 2026-07
**Open-core boundary formalized.** greenroom is now documented as an open-core project: the workspace contract, skills, local reference runtime, and fictional demo workspace are MIT core; the hosted app, Cloudflare Worker API, account/sync, desktop product, curated knowledge, and brand assets are proprietary product-layer materials. Added `OPEN_CORE.md`, `TRADEMARK.md`, `CONTRIBUTING.md`, and `licenses/MIT.txt`; updated README, plugin metadata, app copy, manifest text, and worker docs to remove the old "whole product is MIT" framing.

## v0.38.0 — 2026-06
**Live-assistant standby screen redesigned — one centered column, settings in a grouped card.** The "ready to listen" lobby was top-aligned with a tall empty void below it, and its three setting rows used label-left / control-right with a large dead gap between label and pill. Now the card is vertically centered in the viewport (the leftover space becomes a symmetric frame instead of a hole), and the persona selector, the settings group, and the primary button all share one width with flush left/right edges. The three binary settings (trigger / detail / audio) move into a single inset-grouped card — iOS-style: label left, content-sized segmented control right, hairline dividers between rows — so the bounded card edge removes the dead gap. Segmented controls now keep a constant font weight across states; selection is shown by the raised thumb and ink color alone, so toggling no longer shifts layout. Scoped entirely to the lobby — the in-stage gear panel is unchanged.

## v0.37.7 — 2026-06
**Owner usage dashboard.** New admin-gated worker endpoint `GET /admin/usage` (caller's JWT email must be in `ADMIN_EMAILS`) returns per-user / per-endpoint call + token totals plus the entitlement list. New standalone `admin.html` (owner-only — reuses your existing app login in the same browser, no separate sign-in) renders it: headline totals, per-endpoint and per-user tables, relative token bars, the entitlement list, and a live cost estimate driven by a ¥/1M-tokens input. Real token usage was already recorded per call (v0.37.0); this just surfaces it.

## v0.37.6 — 2026-06
**An `unlimited` entitlement tier — truly no cap.** Distinct from `pass` (a high but finite ceiling): an `unlimited` entitlement makes the gate skip the quota check entirely (`lim = Infinity`), so a call is never blocked. Usage is still recorded for cost visibility. For owner / comp / internal accounts — `UPDATE entitlement SET tier='unlimited' WHERE user_id='you@example.com'`.

## v0.37.5 — 2026-06
**Grant a Pass by email, not just user id.** The quota gate now matches an `entitlement` row by the caller's user id OR their JWT email (`SELECT … WHERE user_id=? OR user_id=?`). This lets an operator comp an account *before* its first login — e.g. `INSERT INTO entitlement (user_id,tier) VALUES ('you@example.com','pass')`. The email comes from the signature-verified token, so it can't be spoofed.

## v0.37.4 — 2026-06
**Never ask a hosted user to register their own Supabase.** The account page's manual Supabase-URL / anon-key form is now **self-host only**. On a hosted deploy — where the backend's `/public-config` declares a cloud — the account page shows the normal one-account sign-in (email / magic link / Google / GitHub); if the operator hasn't finished cloud setup yet (anon key not set), it shows a brief "cloud almost ready · retry" card instead of the config form. `grAdoptHostedCloud()` records the hosted cloud config, and `renderAccount()` branches on it so a consumer never sees server-registration fields.

## v0.37.3 — 2026-06
**BYOK is off the consumer happy path — hidden when a managed key already covers the user.** Settings now leads with a model-connection status line; the API-key field (BYOK), model override, backend URL, and self-host folder picker all move under an **Advanced · own key / self-host** disclosure. It's collapsed by default when the backend reports a managed key (so signed-in hosted users never see "paste your API key"), and auto-expands when there's no managed key (self-host / core / no backend), where BYOK is required. Nothing was removed — open-core stays honest: bringing your own key or self-hosting is always one click away, it just no longer clutters the default experience.

## v0.37.2 — 2026-06
**The landing page opens the real app (not just the demo), and hosted login needs zero per-user setup.**
- `index.html`: the primary CTA is now **Open the app** → `app/greenroom.html` (sign in / your own workspace); the live demo is a secondary button. Previously every CTA pointed at `?demo`, so there was no way into the actual product from the landing page.
- On a hosted deploy the app adopts the backend's **public** Supabase config (`GET /public-config` on the worker → `{sb_url, sb_anon}`) when nothing is configured locally, so any visitor can sign in without pasting Supabase credentials. Dormant until `SUPABASE_ANON_KEY` is set as a Worker secret; self-host / local deploys are unaffected (endpoint absent → skipped), and an already-configured workspace is never overwritten. The anon key is public by design (it ships in every Supabase web client; RLS guards the data).

## v0.37.1 — 2026-06
**Free allowance is a per-account lifetime total, not a daily reset.** The gate now sums a user's all-time calls per endpoint against `FREE_*` (was: today's calls). Per-day rows are still recorded for cost/time-series analytics; only the quota check changed. A new account gets one fixed taste of each feature, then Pass or BYOK — no daily refill. Console message dropped "today" accordingly.

## v0.37.0 — 2026-06
**Per-user auth + metering on the cloud worker — the hosted tier is no longer an open key proxy.** Gating activates whenever `SUPABASE_URL` is set as a Worker secret; without it the worker stays an open BYOK proxy (the self-host default, unchanged).
- **Auth:** every call to `/api/answer`, `/api/mock`, `/api/setup` must carry the caller's Supabase access token (`Authorization: Bearer …`). The worker verifies it against the project's JWKS (ES256/RS256, cached) and pins the issuer — no shared secret to manage. No valid token → `401 {error:"login"}`.
- **Metering:** a Cloudflare D1 store (`worker/schema.sql`: `usage` + `entitlement`) records per-user/day/endpoint call counts **and real model token usage** (`stream_options.include_usage`), so the hosted key's spend is attributable per user and usage-based billing is possible later.
- **Quota:** free tier gets per-endpoint daily limits (`FREE_ANSWER` 30 / `FREE_SETUP` 2 / `FREE_MOCK` 10 — all `wrangler.jsonc` vars, tune freely). Over limit → `402 {error:"quota",used,limit,tier}`. A paid Pass (`entitlement.tier='pass'`) lifts to the `PASS_*` limits. **BYOK bypasses quota entirely** — bring your own key, no limits, ever.
- **Console:** requests now attach the Supabase bearer (and refresh it if it's within 5 min of expiry); `401`/`402` responses surface as a plain-language message ("sign in" / "daily free limit reached — upgrade or add your own key") instead of a raw error. Signed-out local serve.py use is unchanged (no token → simple request).
- `serve.py` preflight now allows the `Authorization` header too.

## v0.36.0 — 2026-06
**A real cloud backend: paste a résumé + a JD in the browser, get a workspace — no files, no local server.** New stateless Cloudflare Worker (`worker/`) that mirrors `serve.py`'s API for the hosted web app but keeps nothing on disk:
- `/api/answer` & `/api/mock` build their prompts from the `ws` payload the browser sends with each request, so live prompting and mock interviews work with zero server-side state.
- `/api/setup` takes the candidate's résumé + company/role/JD **plus any extra notes and attached files**, has the model generate the workspace files, and returns them in a `##OK {files}` line. The console saves them into its blocks, which auto-sync to the signed-in account — so adding a job is just pasting text, and it lands on every device. No folder to pick, no server to run.
- Model key is a Worker secret (`MODEL_API_KEY`) for a zero-friction hosted tier, or BYOK via `X-Greenroom-Key`. Any OpenAI-compatible endpoint (`MODEL_API_BASE` / `MODEL_NAME`).
- Console: the add-a-job flow routes to the worker whenever a keyed backend is configured (and applies the returned files into the workspace + cloud), falling back to the offline minimal builder only when there's no backend at all.
- Deploy in `worker/README.md` (`wrangler deploy` + `wrangler secret put MODEL_API_KEY`).

## v0.35.1 — 2026-06
**Signed in means your account is the workspace — the demo never leaks in.** Two fixes so a logged-in user never sees the fictional example jobs (云梭 / 星澜 / 远屿) as if they were their own:
- Boot order: a signed-in cloud user now loads their cloud workspace authoritatively and never falls back to the backend's example bundle. An empty account shows the "add your first job" onboarding — not the demo.
- The live copilot's role picker reflects the loaded workspace (your jobs), no longer the backend's auto-scanned `/config` personas — so a backend that happens to serve the examples can't override your account. Signed-out self-hosted users still get the backend personas as before.
- Loading a real workspace (folder picker / server bundle) while signed in auto-syncs it up to your account, so after a one-time seed it's there on every device.
- Also folded in: standby card trimmed to title + one line (dropped the eyebrow and second sentence); removed the red dot on the mic (the black↔white toggle + running timer + status dot already signal recording).

## v0.35.0 — 2026-06
**Live copilot: the mic becomes the recording.** A focused craft pass on the in-session screen, grounded in how end/recording controls behave across ChatGPT Advanced Voice (mic and end on opposite bottom corners), Google Meet (the red leave button cornered away from the mic on purpose), screen recorders (a small stop indicator at the edge, not a central button), and HIG/Material destructive-action rules (away from frequent actions, red, extra spacing).
- **The one control at bottom center is an ink-black circular microphone with a blinking red recording dot and a running timer** — recording is the whole metaphor. Tap it to pause (it flips to a white outline, dot off, "已暂停 · 点继续"); tap to resume. Pause keeps the session alive (engine muted, stage stays); only End leaves. Webspeech auto-restart now respects the paused flag.
- **Every control is a true circle.** Settings stays top-right; font size moves into the gear sheet so the top bar is just status + role + gear + End. **End** is a quiet red circle that fills red and shows a "再点一下结束" tooltip on first tap — confirm-to-end, so a mid-interview mis-tap can't drop the session.
- The prompt stays the centered hero; the interviewer transcript is a quiet strip just above the mic. Verified recording / paused / end-confirm on desktop and at 375px, long-answer no-clip, console-clean.

## v0.34.0 — 2026-06
**Live copilot, rebuilt around the one thing that matters: the words you read.** Researched first (Doubao / ChatGPT Advanced Voice / Gemini Live / Siri edge-glow on the voice side; iFlytek 听见 / Feishu & Tencent Meeting captions / Otter / Google Meet on the transcription side), then redesigned. The old screen was a control panel — a status row of tags, the prompter, a transcript panel, and an 11-control toolbar all on screen at once. Now it's two states:
- **Standby** (not listening yet): one calm centered card — role picker + trigger / detail / audio as refined segmented controls + a single ink Start button. Set it once; never touch it mid-interview.
- **Live** (listening): the prompt is the whole screen. The top bar carries only a status dot, the role, font size, a gear, and Stop — everything else (trigger/detail/audio, floating window, copy, clear, audio setup) collapses into the gear sheet. The interviewer transcript drops to a quiet 1–2 line caption strip pinned at the bottom, no speaker labels or timestamps (it's 1:1). The prompt keeps its anchored-top, never-auto-scroll reading behavior.
- Mobile: the caption wraps so the transcript gets its own line; the gear opens as a bottom sheet; the strip clears the home indicator.
- Verified standby / live / gear across desktop and 375px, console-clean, with state switching, two-way-synced settings, and persona echo all confirmed.

## v0.33.0 — 2026-06
**Mobile, properly.** Below 760px the seven-item top nav (which used to wrap and scroll awkwardly on a phone) gives way to a fixed **bottom tab bar** — the pattern every top mobile product uses (telos `apptabs`, iOS HIG Tab Bars, Material 3 Navigation bar). Four primary destinations (总览 / 简历 / 岗位百科 / 实时助手) plus a **更多** tab that opens a bottom sheet for the rest (经历库 / 资料 / 模拟面试 / 方法论) — the combo pattern NN/g measures as the highest-performing navigation for 6+ destinations (a scrollable strip or a buried hamburger both lose discoverability). Active state is color + filled-icon only — never a weight change, so there's no layout shift. The bar carries `env(safe-area-inset-bottom)` for the home indicator and hides entirely during an immersive live/mock session so the interview surface stays one screen.
- **Settings → bottom sheet on mobile.** The centered modal re-anchors to the bottom below 760px: rounded top corners, a drag handle, 40% scrim, slide-up, safe-area bottom padding, footer pinned (Material 3 Bottom sheets / Apple HIG Sheets). Desktop is unchanged — still a centered modal.
- The live copilot's sticky bottom dock now clears the home indicator on a phone; the account screen stays a focused single card with no tab bar.
- Researched first (top mobile products + iOS HIG + Material 3 + Linear/Geist/Rauno craft rules), then built. Verified at 375px and on desktop, console-clean, with active-state sync and the 更多 sheet behavior confirmed.

## v0.32.1 — 2026-06
**Mock setup now speaks the same language as the rest of the app.** The full-bleed split (v0.32.0) was the odd one out — every other screen (Overview, Live, etc.) is content on the paper background in the standard page width, with white cards and `.sect-t` section labels, no full-bleed surface and no page-title bar. Rebuilt the setup to match: it's a normal scrolling page (footer and all), with two white cards in the standard width — left **岗位** (the job list), right **面试设置** (the four segmented rows + ink Start) — each headed by a `.sect-t` label, and a **历史模拟** section below. Two columns on desktop, stacked on mobile. Only the live interview itself stays viewport-locked to one screen; the setup scrolls like any other page.

## v0.32.0 — 2026-06
**Mock setup: full-bleed split that fills the screen.** The centered ~480px card left too much dead space around it. Replaced it with a master-detail split that fills the viewport: a top title bar, then a left **job roster** panel (label + scrollable job list + a quiet history strip pinned at the bottom) and a right **config** panel (the four segmented rows + the ink Start button), divided by a hairline. The two panels carry the layout edge-to-edge instead of huddling in the middle. Desktop = side-by-side (left ~38% capped 460px, right flexes); below 760px it stacks into one scrolling column. Reuses the refined job rows and segmented controls from v0.31.

## v0.31.1 — 2026-06
**Mock setup: typography & spacing polish.** A craft pass on the new setup panel (Geist/Linear/Rauno rules): unified the two section-label styles to one treatment (mono 11px / .1em — they were 10.5 vs 11), snapped the vertical rhythm to a consistent scale (20px zone gaps, 12px setting rows, 4px job rows), card radius 16→14 with more even padding, job role title 14→15px (the primary content earns the weight; company stays a quiet mono label), segment text 12.5→13px. Mobile gets denser gutters (smaller paddings/gaps, 12px segments) so the whole panel sits comfortably within one viewport with ~65px to spare; the job list only scrolls internally past ~6 roles.

## v0.31.0 — 2026-06
**Mock-interview setup, redesigned from research.** Retired the poker-fan job picker (it crushed the middle cards and never sat right) for a calm, one-screen setup panel — grounded in how top products do "pick → configure → start" (Final Round AI / Character.AI logo cards, Apple HIG & Material 3 segmented controls, Linear/Geist/Rauno craft: one radius family, one hairline, ≤2 weights, color rationed to a single ink accent, no weight-change-on-select).
- A single ~480px paper card, vertically centered: Fraunces title → **vertical job list** → four **segmented** setting rows → one ink **Start** → a mono caption echoing the choice.
- **Job list:** one row per saved job = logo + company (mono) + full role title (no truncation of the differentiator beyond a graceful ellipsis); selected = ink hairline ring + filled dot (weight unchanged). Long Chinese role titles finally have horizontal room. List caps at ~5 rows then scrolls internally so the panel always fits one viewport.
- **Settings:** refined segmented controls — warm inset track + white thumb for the selected segment, equal-width segments. Round (5) / style (3) / duration (4) / language (2). Segment labels shrink on ≤480px so the 5-option round never truncates.
- **CTA:** one full-width ink button (the only filled element) + a mono caption ("小红书 · 业务面 · 标准 · 30 min · 中文") — the Duolingo-style "here's what you're about to start" confirmation.
- Verified one-screen, no horizontal scroll, no clipping, console-clean at 375 and desktop with 2–6 jobs.

## v0.30.1 — 2026-06
**Mock-interview setup: fixed the poker-fan visuals.** Two bugs. (1) The selected job card got a z-index near 300, above the Settings modal (z-index 100) — so it poked through the overlay. (2) The fanned cards overlapped so hard that the back cards showed only ragged, mid-word text tails. Fixes: `.mk-fan` now establishes its own stacking context (`isolation:isolate`) with a small local z-index range, so cards can never paint above modals/menus; the fan spread is viewport-aware (the whole hand fits its container — no edge clipping, no horizontal scroll on mobile, verified at 2–6 cards × 375/desktop), rotation is gentler, and role text clamps to two lines.

## v0.30.0 — 2026-06
**No more "open a workspace" — you only ever hand over a résumé + JD.** Dropped the folder-centric entry model from the default UI. A normal user signs in (their workspace syncs back) or starts from a résumé + JD; they never "open," "reopen," or drag in a workspace folder. The folder *is* the on-disk storage / export / git format — backend only, and only relevant if you self-host.
- **top bar:** removed the **Open workspace** button.
- **start page:** the hero is now two actions — **New from résumé + JD** and **Sign in** — over a quiet *demo · method* link row. Removed *Reopen last workspace*, *Open a local folder*, and the drag-a-folder hint. The three explainer cards were rewritten off the old "install skills → one folder is everything → serve.py auto-connects" story onto the product flow (sign in or start → auto-generated set → one surface); the skills-install code box left the app start (it lives on the landing page + README).
- **self-host:** the local-folder picker moved into **Settings → Advanced** as a clearly-labeled self-host affordance. serve.py still auto-connects with no action; a remembered folder still auto-reconnects on boot. The source-status chip is now purely informational (it only offers a manual reconnect in server mode).

## v0.29.0 — 2026-06
**A real account page — sign in, sync, done.** The cloud-sync login moved out of a cramped corner of the settings dialog into a dedicated `#/account` view, rebuilt to match the project's paper aesthetic. A person icon in the top bar (with a green dot when you're signed in) opens it.
- **console (`app/greenroom.html`):** the account view has three states — **signed out** (a serif title, a 登录/注册 segmented toggle, email + password with a show/hide toggle, a forgot-password link, a full-width primary button, an "或" divider, then magic-link + Google + GitHub buttons, and a back link); **signed in** (a "my account" card with avatar initial, email, sync status, *Sync now* and *Sign out*); and **not configured** (an inline Supabase URL + anon-key form). Tab switching preserves the typed email/password; the password show/hide flips in place.
- **auth:** adds password reset (`/auth/v1/recover`) and OAuth redirect (`/auth/v1/authorize?provider=…`) on top of the existing email+password and magic-link flows — all hand-rolled against Supabase GoTrue REST, no SDK. Friendly mapped error messages (wrong password, already registered, rate limited, …).
- **start page declutter:** the hero dropped from five stacked buttons to two primaries (**New from résumé + JD**, **See the demo**) plus a quiet link row (sign in · open a local folder · methodology). The settings dialog's cloud section is now a one-line link to the account page.
- Google/GitHub buttons require enabling those providers in your Supabase project; email magic-link and password work out of the box. Bilingual throughout.

## v0.28.0 — 2026-06
**Brand identity: a real icon, favicons, an OG image and a PWA manifest.** greenroom gets its own mark — a backstage dressing-room door ajar with a warm glow and a gold star (the green room before you walk on stage), on the brand-green field.
- **Icon set:** `icon.svg` master (squircle) plus a full-bleed `brand/icon-square.svg`, rasterized to `favicon-32.png`, `apple-touch-icon.png` (180), and maskable `icon-192/512.png` — all reproducible via `brand/build-icons.sh` (headless Chrome, no extra deps).
- **Social + PWA:** a 1200×630 `og.png` (mark + wordmark + tagline) wired into the landing's Open Graph and Twitter card; `site.webmanifest` with maskable icons and theme color; favicon links and `theme-color` added to `index.html` `<head>`.
- **Console + README:** `app/greenroom.html` carries the mark as an inline data-URI favicon (resolves from any serve root); both README headers now show it.

## v0.27.0 — 2026-06
**Closed roles sink into a collapsed section instead of cluttering the overview.** Once a role's `status` is `closed`, it leaves the active grid and drops into a folded **Closed / 已关闭** area at the bottom of the overview — collapsed by default, with a count.
- **console (`app/greenroom.html`):** the overview partitions roles into active vs. closed. Active roles render in the grid as before; closed roles move into a native `<details>` disclosure below (zero-JS toggle, dimmed cards). The headline **Active roles / 在投岗位** stat — plus the script-question and round totals — now counts active roles only, matching its own label. Two new bilingual i18n keys (`sect_closed`, `ov_all_closed`) and an all-closed fallback line for the active grid.
- **demo:** the demo workspace gains a closed role (云梭智能) so the folded section is visible under `?demo`.

**Rounds are now a vertical timeline.** The Rounds tab moved from a flat list of cards to a dated timeline — each round sits on a rail node colored by kind (green Debrief / amber Prep / neutral Mock · Doc), with the date on the left and the card to the right.
- **console (`app/greenroom.html`):** rounds render as a `.rtimeline` — a left date column + a connecting rail with per-kind dots, and the expandable card beside it. Cards are collapsed by default (a tap-to-open disclosure with an animated caret); the date stays on one line down to mobile. Reuses the existing Debrief/Prep/Mock/Doc kinds and colors — no new strings.

## v0.26.0 — 2026-06
**The console no longer silently drops job files, and pre-round prep gets a first-class card.** The job view recognized only five file types (job / intel / script / debrief / mock); any other `.md` in a job folder — a pre-round battle-plan, a stray note — was parsed and then thrown away with no warning. Now nothing vanishes.
- **console (`app/greenroom.html`):** `buildWorkspace` keeps every unrecognized `.md` instead of discarding it. New `round-prep` type renders as a **Prep / 备战** card in Rounds (amber, distinct from the green Debrief card), sorted before that round's debrief and open by default when it's the latest; any other unknown type falls back to a neutral **Doc / 材料** card. Robust round-number parse (`R2` → 2). Two new bilingual i18n keys (`rk_prep`, `rk_doc`).
- **docs & examples:** `workspace-spec.md` documents the `round-prep` type and the no-silent-drop guarantee; the demo workspace gains a `round-prep` example so the Prep card shows under `?demo`.

## v0.25.0 — 2026-06
**Breaking — removed the claim-ledger skill and the cross-round "claims log" feature, product-wide.** Tracking whether your wording stays consistent across rounds was a premise that didn't earn its complexity: real interviewers don't diff your answers across rounds, and keeping a ledger pulled focus from the actual deliverable. greenroom now centers squarely on getting your whole interview kit ready — job intel, story bank, say-it-out-loud scripts, a 155-role encyclopedia, mock interviews with coaching, and live prompting.
- **skills:** deleted `claim-ledger`; the suite is now **7 skills** (greenroom orchestrator + job-intel / story-bank / interview-script / industry-brief / mock-interview / debrief). Stripped claim/ledger references from the remaining skills and both plugin manifests. The anti-fabrication rule — *numbers carry their source, never invent one* — stays; that's honesty, not ledger-keeping.
- **console (`app/greenroom.html`):** removed the Claims view, its route, parser, CSS, command-palette entries, the overview drift banner, the export-redlines path, and ~21 orphaned i18n keys. Landing copy and the realtime/mock blurbs no longer mention a ledger.
- **backend (`serve.py`):** dropped the `claims.md` injection, the ⚠️ redline reminder, and the coach's口径-reconciliation pass; mock coaching now scores four content dimensions (structure / evidence / role-fit / follow-up resilience). Kept *only use numbers that appear in the script*.
- **docs & examples:** `claims.md` removed from `workspace-spec.md` and the demo workspace; `realtime-bridge.md` no longer defines a claims/redline contract.

## v0.24.1 — 2026-06
- **Audio-source toggle moved into the control bar.** The Speaker / System pill now sits inline next to Trigger and Detail (short labels 外放 / 系统) instead of being tucked inside the audio panel — one row, three consistent switches. The panel keeps the device dropdown, status hint and BlackHole setup steps; picking System with no virtual device detected toasts and opens that panel (deferred past the click so the outside-click handler doesn't immediately re-close it).

## v0.24.0 — 2026-06
- **Live copilot settings are now segmented toggles instead of dropdowns.** Trigger (Manual / Auto) and Detail (Brief / Full) became inline segmented pills in the control bar — one tap to switch, no dropdown to open. Their values moved from the `<select>` DOM into `LV.mode` / `LV.detail` state.
- **New audio-source toggle: Speaker vs System audio.** A segmented pill at the top of the audio panel switches between picking the interviewer up through the microphone (zero setup, but catches your own voice) and routing system audio through a virtual device (cleanest). System mode auto-detects a loopback device (BlackHole / Loopback / VB-Audio / Stereo Mix / aggregate / …) and selects it; if none is found it shows the one-time BlackHole setup steps (now revealed only in system mode) or lets you pick manually. The device dropdown and the pill stay in sync, and on Web Speech a note reminds you it only uses the OS default input.

## v0.23.4 — 2026-06
- **Live copilot answer no longer snaps from raw text to formatted on completion.** While streaming it showed raw text (literal `**`, the `【这么起】` marker, blank-line gaps under `white-space:pre-wrap`); the moment generation finished it reflowed into compact formatted HTML — a jarring jump. The stream now renders progressively through the same `lvRenderAnswer` formatter, so bold, the highlighted lead and compact spacing appear as text arrives. `lvFmt` also renders an unclosed trailing `**…` as in-progress bold, so the actively-streaming label doesn't briefly flash literal asterisks.

## v0.23.3 — 2026-06
- **Live copilot's "let it hear only the interviewer" panel is now a centered modal.** It was a bottom-right popover capped at `62vh`, so the audio/BlackHole setup steps scrolled out of view. It now opens as a centered dialog over a dimmed backdrop (`88vh`, content fits without scrolling), closes on backdrop-click and Esc.
- **Fix: the panel's 收起 (Close) button did nothing.** The button carried the `lv-qk` class, so `lvInit`'s `$$('.lv-qk')` binding overwrote its inline `onclick` with the quick-action handler — clicking it fired "ask a question first" instead of closing. Given a dedicated class and handler; Esc now closes the modal without also clearing the prompter.

## v0.23.2 — 2026-06
- **Bug-hunt sweep across parsers, the live copilot, mock interview and the roles encyclopedia.**
  - *Markdown:* `inline()` no longer rewrites `**bold**` / links inside `` `code` `` spans (e.g. `` `npm i **pkg**` `` rendered correctly), via a single-pass alternation.
  - *Frontmatter:* `splitFrontmatter` now tolerates CRLF (Windows-authored files kept their frontmatter) and no longer mistakes a leading `---` thematic break for frontmatter — which had silently eaten the body up to the next `---` (data loss).
  - *Story bank sort:* `whenSortKey` no longer treats any string containing `今` (e.g. 如今/今后) as "present", and anchors the 4-digit-year match so `工号 20245` no longer reads as year 2024.
  - *Story bank parse:* a card whose heading is the file's last line (no trailing newline) no longer loses the last character of its title.
  - *Live copilot:* clearing (Esc / 清空) while an answer is still streaming no longer leaves `generating` stuck true — the prompter was bricked for the rest of the session. A merge clicked mid-stream no longer drops the merged question and corrupts the next-merge anchor.
  - *Mock interview:* the round timer no longer leaks when you navigate away mid-session (the clock now resumes on return); the FunASR socket is captured before nulling so its deferred `close()` actually runs; the grading report re-acquires its node each chunk so it still renders after navigating away and back.
  - *Roles encyclopedia:* four medical roles (CRA / MSL / RA / bioinformatics engineer) carried function-axis names retired in v0.14.0, so they dropped out of every function filter and showed a dead label — remapped to current axes. Function-chip counts now match the grid's empty-cell fallback, and that fallback now honors the selected segment filter.

## v0.23.1 — 2026-06
- **Fix: clicking a transcript question in the TOC bounced to the landing page.** The script (逐字稿) table-of-contents links were plain `<a href="#q-N">` anchors. Because the whole console is hash-routed, clicking one set `location.hash` to `#q-N`, which matches no route and fell through to the start view. The links now scroll via `jumpQ()` without touching the route hash (matching the library TOC's `jumpHeading` pattern); `.stoc a` gains `cursor:pointer` for the now href-less anchors.

## v0.23.0 — 2026-06
- **AI & product playbooks upgraded to the deeper scaffold.** All nine Algorithm·AI roles (LLM / CV / RecSys / Search / NLP / Speech / ML / Risk / AD-perception) are rewritten to the CWF + 6-probe mental models + 5-axis watershed + Bloom-tagged must-knows structure, and the eight remaining Product roles (functional / strategy / data / B2B / monetization / head-of-product / growth / globalization) are back-filled to the same scaffold with their 2026 numbers re-verified. Every role was produced by the deep-write → adversarial-calibration workflow (all atBar, sources attached); calibration caught real errors — DeepSeek-R1 date, GRPO model count, OneRec's fabricated watch-time metric, stale SaaS/eCPM/retention benchmarks.
- **New AI industry brief.** 人工智能 (AI) lands as its own industry, ordered first and separate from the Algorithm·AI *function* axis — covering the 2026 landscape (foundation-model oligopoly, infra layer, the burn-vs-revenue tension and circular financing), per-function differences, and five segments (foundation models / AI apps / AI Infra / AIGC / embodied AI). Function × AI composes like any other industry pairing.

## v0.22.0 — 2026-06
- **Deeper playbook scaffold.** Role entries gain a top-level **Core responsibilities** (CWF) block; mental models follow a 6-probe cognitive-task-analysis checklist (incl. the often-missed self-calibration probe); the watershed renders as a **5-axis table** (strong vs weak, decidable on the spot); must-knows carry **Bloom-level** tags (fail-line vs expert-line). A portrait's **core-tension** line is now optional — kept for design/product roles, dropped where it degrades into generic "speed vs quality". Parser/renderer/CSS/i18n updated, fully backward-compatible with existing entries.
- **ID-badge redesign.** The role detail's lanyard card is rebuilt to a real employee-badge layout (logo · photo · name · dept / function / ID · barcode); the long role description moved out of the card into the body.
- **First technical-role playbook.** Game Client Programmer lands under Internet as the golden sample for the game-programming family, produced by the deep-write → adversarial-calibration workflow (atBar, sources attached).
- **Plain-language labels.** Renamed abstract section labels to plain Chinese: 战例→经典案例, 悬案→行业争论, 分水岭→强弱分界, 追问链→追问方向 (心智模型 / 基准线 / 前沿 kept).

## v0.21.0 — 2026-06
- **Segment-level industry briefs.** An industry file can carry `## 细分导读：<segment>` sections (same fields as the industry brief). When that segment is selected, the console swaps the industry-brief card for a segment-specific one with its own reading page — shipping with a Game brief under Internet. Falls back to the industry brief when a segment has none.
- **Removed the in-page role search** added in v0.20.0: the top-right command palette (⌘F) already searches roles, so the dedicated box was redundant.

## v0.20.0 — 2026-06
- **In-page role search.** The roles encyclopedia gets a search box above the filter chips: it matches roles by name, English title, one-liner and insider vocabulary, plus industries by name and segment — scoped to the encyclopedia, with the global ⌘F palette kept separate. Only the result grid re-renders, so the box never loses focus.
- **World-class playbook format + first verticals.** Role entries adopt a two-tier "怎么想 / 怎么考" (how they think / how they test it) structure — mental models, benchmarks, canonical cases, two-sided open debates, and the watershed between strong and weak candidates — distilled to an insider bar (non-obvious, actionable, fact-checked). The nine product-management roles are rewritten to this bar, and the game-design family lands its first seven playbooks (systems / numerical / combat / level / gameplay / monetization / narrative designer), each adversarially calibrated against authoritative sources with a `来源` line.

## v0.19.1 — 2026-06
- **Reading freshness now fires on date-named files.** When a `library/` doc has no `updated:` frontmatter, the date is parsed from its filename (`…_2026.06.10.md`, `…-2026-06.md`; a 20xx year prefix is required so version strings like `V5.1` aren't mistaken for dates). Intel notes named by date light up their freshness pill and newest-first sort without needing frontmatter.

## v0.19.0 — 2026-06
- **Time on the card walls.** Story cards now carry an optional `**时间**：<org> · <span>` line that renders as a context anchor under the title (where & when, at a glance) and unlocks a **By time / By story** sort toggle — no second timeline, the resume view already owns that. Reading docs (`library/`) surface relative freshness from their `updated:` date ("3 days ago", flagged red past six months) and sort newest-first within each group; undated reference material is untouched. Contract documented in `docs/workspace-spec.md`; `story-bank` skill template updated.

## v0.18.0 — 2026-06
- **Automatic high-resolution company logos.** Add a job (or upload materials via `/api/setup`) and greenroom resolves a crisp official icon on its own — no manual URL hunting. The ladder: App Store official icon (512px, via the iTunes search API) → Clearbit → site `apple-touch-icon` → Google favicon → DuckDuckGo → letter monogram. App Store hits require **domain corroboration** (the developer's site domain or vendor name must match the job's domain) so a generic name like "Converge" can't pull in an unrelated app's icon. The console resolves client-side too (iTunes via JSONP, favicon guarded by a 32px minimum to reject Google's 404 globe placeholder), and `/api/setup` writes the resolved URL straight into `job.md`. New `/api/resolve-logo` endpoint in `serve.py`.

## v0.17.0 — 2026-06
- **Live demo + landing page.** A polished `index.html` deployed to static hosting; the console auto-loads the embedded demo workspace via `?demo`, so visitors land straight in the full product on fictional data — nothing uploaded.

## v0.16.0 — 2026-06
- **Four more industries** filling the gaps surfaced by research: Energy & Environment (solar/wind, storage, carbon & ESG, power, environmental), Agriculture & Food, Travel & Hospitality, Legal Services. Plus clinical roles (clinician, nurse, clinical pharmacist) added to Healthcare. 15 industries, 155 role playbooks.

## v0.15.0 — 2026-06
- **Sports & Entertainment industry** (esports, sports, talent agency, live shows) with esports event ops, club manager, team analyst, caster, talent agent, show producer, sports marketing. Added Game Producer.

## v0.14.0 — 2026-06
- **Roles encyclopedia rebuilt to highest standard.** Function axis redefined into 11 mutually-exclusive groups, each with a primary-deliverable boundary rule (hover to see it): split AI·Data → Algorithm·AI + Data, split Consulting·HR·Legal → Strategy·Consulting + People·Legal·Admin. Role library 60 → 128 base+specialized; every industry's segments filled out.

## v0.13.0–v0.13.1 — 2026-06
- **Function × industry as a composition model (A×B).** Functions are base roles; industries are a context layer with hardcore briefs. Any combination produces content — no empty cells. Added Consumer Retail (incl. beauty). Lanyard badge clip fixed to actually thread through the card hole.

## v0.10.0–v0.12.0 — 2026-06
- Resume life timeline v2 (proportional bands + content cards + leader lines). Orthogonal function × industry filtering with live-linked counts. Live copilot role switcher as an anchored menu. Experience bank profile-card removed.

## v0.8.0–v0.9.2 — 2026-06
- `serve.py` upgraded to a full reference backend (`/api/answer` + `/api/mock` + `/config` + `/api/setup`); personas auto-discovered from `jobs/`. No-Claude "Add role" screen generates the workspace from a dropped resume + pasted JD. Job timelines.

## v0.6.0–v0.7.x — 2026-06
- Mock-interview view (interviewer persona + coach report with claim reconciliation). Roles encyclopedia with DiceBear pixel-art ID badges. Reading anchor for the live prompter; screen-share safety notice. Single-stage immersive mock setup.

## v0.1.0–v0.5.0 — 2026-06
- Initial release: 8 skills (the full prep pipeline) + the claim ledger mechanism + a single-file local-first console (overview, resume, experience bank, library, roles, live copilot) + the workspace data contract. Bilingual UI.
