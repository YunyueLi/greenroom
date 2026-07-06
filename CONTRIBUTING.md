# Contributing to greenroom

greenroom is open core. Contributions are welcome in the core layer and are
reviewed against the workspace contract, privacy rules, and product boundary.

## Good Contribution Areas

- `skills/`
- `docs/workspace-spec.md`
- `docs/realtime-bridge.md`
- `serve.py`
- `examples/demo-workspace/`
- reference docs for building compatible tools

Product-layer files such as `app/`, `worker/`, `workers/`, `desktop/`, `brand/`,
and hosted service configuration are proprietary. Changes to those files may be
closed or treated as product suggestions unless the maintainer has agreed to a
separate contribution path.

## License

By contributing to an MIT-licensed core file, you agree to license your
contribution under the MIT License. Contributions to files with another
explicit license follow that file's license.

You also confirm that you have the right to submit the contribution and that it
does not include confidential employer, candidate, interview, or customer data.

## Privacy

Do not commit real interview material, private resumes, salary information,
company confidential information, user account data, API keys, or production
logs. Demo data must stay fictional and consistent with
`examples/demo-workspace/`.

## Product Boundary

The open core should remain useful, portable, and local-first. The official
hosted product adds account sync, metering, cloud model access, polished UI,
desktop distribution, premium knowledge, and brand presentation.
