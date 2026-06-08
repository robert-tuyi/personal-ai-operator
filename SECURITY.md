# Security Policy

## Reporting a vulnerability
If you discover a security issue, do not open a public issue.

Please report it privately by contacting the repository owner directly and include:
- a short description of the issue
- steps to reproduce
- affected files or components
- possible impact
- screenshots or logs if helpful

## Response approach
Reported vulnerabilities will be reviewed and acknowledged as soon as possible. Valid issues will be investigated privately and fixed before public disclosure when appropriate.

## Secrets policy
Do not commit:
- API keys
- tokens
- passwords
- private certificates
- production credentials

Use environment variables and keep local secrets in untracked `.env` files only.