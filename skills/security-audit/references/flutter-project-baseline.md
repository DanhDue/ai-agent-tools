# Flutter Project Baseline — Security

House rules that go **beyond** the `SEC-FLUTTER-*` rules in `SKILL.md`. Hardcoded credentials,
HTTPS/pinning, PII in logs, secure storage and cryptography are already covered there — do not
re-check them here.

## Network client configuration

Every Dio/HTTP client must set explicit connection and receive timeouts. A client with no
timeout can hang a financial flow indefinitely with no user-visible failure.

## Error surfacing

Stack traces and raw exception text must never reach the UI. Map failures to a domain error type
and render a safe message — a leaked stack trace exposes package structure and internal paths.

## Input validation

- Validate every user input on the client (length, format, allowed character set), and again
  server-side where a server exists.
- Local database access (Drift / sqflite) must use parameterized queries. String-concatenated
  SQL is a finding even against a local database.
