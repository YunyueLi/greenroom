# Contributing to greenroom

greenroom is an open-source Community Edition under AGPL-3.0. Contributions are
welcome when they make the local-first interview-prep workflow more useful,
portable, and trustworthy.

## Good Contribution Areas

- `skills/` workflow improvements
- `docs/workspace-spec.md` and compatible workspace tooling
- `serve.py`, `start.sh`, and local runtime fixes
- `knowledge/` community role encyclopedia entries based on public,
  non-confidential sources
- `examples/demo-workspace/` fictional demo data
- tools that read or write the workspace contract from other editors and agents

The hosted product UI, its brand assets, and the hosted service backend are not
part of this repository. Contributions that require them belong in a bug report
instead of a pull request.

## License

By submitting a contribution, you agree that your contribution is licensed under
the GNU Affero General Public License v3.0. Everything in this repository ships
under that license, including the skills and their reference material; no file
carries a separate license.

You also confirm that you have the right to submit the contribution.

## Privacy

Do not commit real interview material, private resumes, salary information,
company confidential information, user account data, API keys, production logs,
or screenshots containing personal data. Demo data must stay fictional and
consistent with `examples/demo-workspace/`.

## Product Direction

The public repository should remain useful on its own. The skills, the role
knowledge base, the workspace contract, and the reference read server must keep
working end to end without an account, without an API key, and without the
hosted service. Hosted greenroom adds the product UI, managed accounts, cloud
sync, and everything that runs on a model — live prompting during the interview,
the mock-interview and one-pass generation endpoints; the open project stays a
complete, portable toolkit on its own terms.

## Brand

Forks and compatible tools should use their own names and visual identity. See
`TRADEMARK.md` for the brand policy.
