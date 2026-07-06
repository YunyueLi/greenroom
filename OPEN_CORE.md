# greenroom Open Core

greenroom has two layers: a portable open core and an official hosted product.
The public core is meant to be reusable; the official product is not licensed
for cloning, resale, or competing hosted deployment.

## Core

The greenroom core is licensed under MIT. It includes:

- the workspace contract in `docs/workspace-spec.md`
- the realtime bridge contract in `docs/realtime-bridge.md`
- the Claude skills in `skills/`
- the local reference runtime in `serve.py`
- the fictional demo workspace in `examples/demo-workspace/`
- narrow tooling used to read/write the workspace contract, such as
  `tools/workspace_codec.py`

The core lets another agent or local tool generate the same kind of interview
workspace without depending on the official hosted app.

## Product

The greenroom product layer is proprietary and all rights are reserved. It
includes:

- the hosted web app and product UI
- account, sync, metering, and hosted model-proxy flows
- Cloudflare Worker code and hosted service configuration
- the desktop app
- premium or curated role knowledge, playbooks, and operational content
- brand assets, icons, wordmarks, screenshots, and product visual design

Product-layer files are maintained outside the public core repository unless a
file is explicitly published under a separate license. Historical availability
of a product file in an older release does not change the license of future
versions.

## Public Positioning

Use "greenroom core", "Community Edition", or "reference implementation" for
the open layer. Do not describe the public layer as a crippled edition. The
core should be useful on its own, while the official product provides a hosted,
polished, synced experience.

## Contributions

Community contributions are welcome for the open-core layer:

- skills and prompt references
- workspace contract improvements
- local reference runtime fixes
- fictional demo data
- docs that help others build compatible tools

Product-layer changes are handled by the product owner. Pull requests that
modify proprietary product files may be closed or treated as suggestions unless
there is a separate written agreement.

## Compatibility

Projects may truthfully describe themselves as "compatible with greenroom
core" if they implement the public workspace contract. They may not imply that
they are the official greenroom product or use reserved brand assets without
permission.
