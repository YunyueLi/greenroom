# Changelog

## v0.39.0

Public repository converted to **greenroom core / Community Edition**.

- Kept the MIT core: workspace contract, realtime bridge contract, Claude skills, local reference runtime, fictional demo workspace, and workspace helper tools.
- Moved official hosted product assets out of the public tree: web app UI, landing page implementation, Cloudflare Worker API, desktop app, brand assets, icons, curated role encyclopedia, and operational product files.
- Rewrote README, license policy, contribution guide, repository instructions, and release packaging around the open-core boundary.
- Updated `serve.py` so the public runtime no longer requires a bundled product UI. It now exposes a core status page plus the workspace/model bridge APIs.

## v0.38.0

Open-core boundary formalized in documentation.

- Added `OPEN_CORE.md`, `TRADEMARK.md`, `CONTRIBUTING.md`, and `licenses/MIT.txt`.
- Clarified that the reusable core is MIT-licensed while official product UI, hosted service implementation, account sync, metering, curated knowledge, and brand assets are proprietary.
