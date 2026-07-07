# greenroom Worker backend

A stateless [Cloudflare Worker](https://developers.cloudflare.com/workers/)
backend for greenroom web deployments. It is the cloud-side equivalent of
`serve.py`'s HTTP API, with one difference: it keeps **no workspace on disk**.

Use it for your own hosted/self-hosted instance, or read it as the reference
implementation for the API contract in `../docs/realtime-bridge.md`.

- **Live prompting** (`/api/answer`, `/api/mock`) builds the prompt from the `ws` payload the browser sends with each request (resume / transcript / JD / intel / names) — exactly the contract in [`../docs/realtime-bridge.md`](../docs/realtime-bridge.md).
- **Add a job** (`/api/setup`) takes the candidate's resume + company/role/JD **plus any extra notes and attached files**, asks the model to generate the workspace files, and **returns them** in a final `##OK {files}` line. The browser saves them into its local blocks, which auto-sync to the signed-in account. Nothing is written server-side.

So a signed-in user, on any device, with no local backend, can paste a resume
and job description, optionally add notes/files, generate a workspace, and sync
it through their account.

## Endpoints

| Method | Path | Body / query | Returns |
|---|---|---|---|
| `GET` | `/config` | — | `{has_key, model, personas:{}, cloud:true}` |
| `POST` | `/api/ping` | — | `{ok, model, sample}` (key/connectivity check) |
| `POST` | `/api/answer` | `{question, persona, detail, history, ws}` | streamed plaintext prompt |
| `POST` | `/api/mock` | `{persona, stage, history, round, style, lang, minutes, ws}` | streamed plaintext |
| `POST` | `/api/setup` | `{company, role, jd, notes, resume_text, attachments[]}` | line stream: `##STEP …` then `##OK {ok,name,slug,files}` |

`personas` is empty on purpose — in the cloud the workspace lives in the user's account, so the console drives the role list from its own loaded workspace, not from the backend.

## Deploy

```sh
cd worker
npx wrangler deploy
# set the model key as a SECRET (never in wrangler.jsonc vars):
npx wrangler secret put MODEL_API_KEY        # paste your DeepSeek / OpenAI-compatible key
```

`MODEL_API_BASE` (default `https://api.deepseek.com`) and `MODEL_NAME` (default `deepseek-v4-flash`) are plain vars in `wrangler.jsonc` — point them at any OpenAI-compatible endpoint.

Local dev: `npx wrangler dev`, with the key in a `.dev.vars` file (`MODEL_API_KEY=sk-…`).

## Two ways to supply the model key

1. **Server key (zero friction for users):** set `MODEL_API_KEY` as a Worker secret. Every signed-in user can generate jobs and run live prompting without their own key. You pay for the model calls — this is the model for a paid hosted tier.
2. **BYOK (bring your own key):** leave the secret unset. The browser sends the user's own key as `X-Greenroom-Key` (set in the console's settings; stored only in their browser). `X-Greenroom-Model` overrides the model per request.

CORS is open (`*`) and the preflight allows `Content-Type, X-Greenroom-Key, X-Greenroom-Model`, so the hosted page (a different origin) can call it directly.

## How the app reaches the worker

The console stores the backend URL in Settings. For local use, `serve.py` is the
default backend. For a hosted/self-hosted deployment, deploy this Worker and set
the console backend URL to your Worker route or custom domain.

## Auth & metering

With a server-side `MODEL_API_KEY`, every call is billed to that key — so the hosted endpoint must know **who** is calling and cap usage. That turns on automatically once you set **`SUPABASE_URL`** as a Worker secret:

```sh
npx wrangler d1 create greenroom-meter          # then put the id in wrangler.jsonc d1_databases
npx wrangler d1 execute greenroom-meter --remote --file=schema.sql
npx wrangler secret put SUPABASE_URL             # https://<your-ref>.supabase.co  (pins the JWT issuer)
npx wrangler secret put SUPABASE_ANON_KEY        # your project's anon (public) key — lets the hosted app sign users in with zero setup
npx wrangler deploy
```

- **Zero-setup login.** `GET /public-config` returns `{sb_url, sb_anon}` from `SUPABASE_URL` + `SUPABASE_ANON_KEY`. The hosted app fetches it on boot when nothing is configured locally and uses it to sign users in — so visitors never paste Supabase credentials. Both values are public by design (the anon key ships in every Supabase web client; RLS guards the data). Empty until `SUPABASE_ANON_KEY` is set, in which case the app just falls back to its own settings.

- **Auth.** `/api/answer`, `/api/mock`, `/api/setup` require the caller's Supabase access token in `Authorization: Bearer …` (the console attaches it automatically when signed in). The worker verifies it against `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` (ES256/RS256, cached) and checks `iss`/`exp` — no shared JWT secret to manage. Invalid/absent token → `401 {error:"login"}`.
- **Metering.** Cloudflare D1 (`schema.sql` → `usage`, `entitlement`). Each call increments a per-user/day/endpoint counter (the gate currency) and records real model token usage (`prompt_tokens`/`completion_tokens` via `stream_options.include_usage`) for cost attribution / usage-based billing.
- **Quota.** Free tier = per-endpoint **lifetime** limits per account (the gate sums all-time calls, not a daily reset), set as `wrangler.jsonc` vars: `FREE_ANSWER` (30), `FREE_SETUP` (2), `FREE_MOCK` (10). Over limit → `402 {error:"quota",used,limit,tier}`. The `PASS_*` vars are the paid-Pass limits.
- **BYOK bypasses quota.** A signed-in user who sets their own key (`X-Greenroom-Key`) is never metered — they pay their own model cost.

**Grant a Pass** (Phase-2 payment integration writes this; until then, comp manually):

```sh
npx wrangler d1 execute greenroom-meter --remote \
  --command "INSERT INTO entitlement (user_id,tier,expires) VALUES ('<supabase-user-uuid-or-email>','pass','2026-12-31') ON CONFLICT(user_id) DO UPDATE SET tier='pass', expires='2026-12-31'"
```

`user_id` may be the Supabase user UUID **or an email** — the gate matches either, so you can comp an account before its first login (the email is read from the signature-verified JWT). Use `expires` `NULL` for a permanent grant.

Without `SUPABASE_URL` the worker stays **open / ungated**. That is fine for a
private BYOK or self-host deploy, but do not expose a server `MODEL_API_KEY`
publicly in that mode. The free allowance is a lifetime total per account. D1
counter pre-increments are best-effort (`waitUntil`), so heavy concurrency can
over-grant slightly; token usage records are the source of truth for real cost.
