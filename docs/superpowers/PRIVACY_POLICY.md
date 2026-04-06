# Superpowers Docs Privacy Policy

`docs/superpowers/**` is published in the open-source repository.  
Treat every line as public content.

## Hard Rules

1. Never commit real credentials, secrets, or private keys.
2. Never commit personal local absolute paths (for example `/root/<name>`, `/home/<name>`, `C:\Users\<name>`).
3. Never commit personal email addresses or private account identifiers.
4. Use placeholders for sensitive values:
   - `<REDACTED_TOKEN>`
   - `<REDACTED_PATH>`
   - `<REDACTED_EMAIL>`
5. If a pattern is intentionally safe and must remain (for example `user@example.com`), annotate the line with `privacy:allow`.

## CI Gate

The repository runs `scripts/check_superpowers_privacy.py` in CI.  
The check fails when likely sensitive content appears in `docs/superpowers/**/*.md`.

## Reviewer Checklist

1. Run `python3 scripts/check_superpowers_privacy.py` before pushing.
2. Confirm any `privacy:allow` marker has a short reason in the same line or nearby context.
3. Prefer redaction over exceptions.
