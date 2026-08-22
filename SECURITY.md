# Security Policy

## Supported code

Security fixes target the current `main` branch. Generated media, third-party model repositories, model weights, checkpoints, external services, and local environments are outside this repository and must be assessed under their own policies and licenses.

## Reporting a vulnerability

Do not open a public issue for a vulnerability or include credentials, private media, or a working exploit in public discussion.

Use the repository's **Security → Advisories → New draft security advisory** flow when it is available. If that private channel is unavailable, contact the maintainer through the [Arnon-hs GitHub profile](https://github.com/Arnon-hs) and request a private channel without disclosing sensitive details publicly.

Include:

- affected commit and component;
- impact and realistic attack prerequisites;
- minimal reproduction or evidence;
- suggested mitigation, if known;
- whether the issue affects a third-party model or service.

The project targets acknowledgment within 7 days and an initial assessment within 30 days. These are best-effort targets, not an SLA. Please allow coordinated remediation before public disclosure.

## Security boundaries

- Credentials belong only in local environment variables and must never be committed.
- Model and media downloads require an explicit user action.
- Postiz creates private drafts; it does not publish automatically.
- The LAN status server is unauthenticated and binds to loopback by default. Expose it to a trusted LAN only when required.
- Generated output must receive human review for safety, originality, and third-party rights.
