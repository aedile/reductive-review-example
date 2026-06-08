# Security Adversary — round-001

Document: `docs/design/magic-link-auth.md` @ v0.1

## BLOCKER

### §3.2 — Link never expires and is replayable
- Problem: The link "logs the user in when clicked" with no expiry and no
  single-use enforcement. A link that leaks (forwarded mail, browser history,
  proxy logs) is a permanent credential.
- Why it matters: One intercepted email = indefinite account access. This is the
  whole ballgame for a takeover.
- Suggested resolution: Single-use token, invalidated server-side on consume, plus
  a short absolute expiry (minutes).

### §3.1 — Token is predictable / low-entropy
- Problem: The token is "derived from the current timestamp so it's unique."
  Unique is not unguessable. Timestamps are low-entropy and partially known.
- Why it matters: An attacker who can approximate send time can brute a small
  space and log in as the victim.
- Suggested resolution: 32 bytes from a CSPRNG, stored hashed; never derived from
  guessable inputs.

### §2.1 — No send rate-limiting
- Problem: A link is generated and emailed on every request with no limit.
- Why it matters: An attacker can bomb a victim's inbox and abuse our sender
  reputation; there is also no backpressure on the auth endpoint.
- Suggested resolution: Per-address and per-IP rate limits with backoff; drop
  excess sends without revealing whether the address exists.

## FINDING

### §4.0 — Account enumeration via response
- Problem: "No account found" vs. "check your inbox" tells an attacker exactly
  which addresses are registered.
- Why it matters: Free user-enumeration oracle; feeds targeted phishing.
- Suggested resolution: One uniform "if an account exists, we've sent a link"
  response with matched timing.

### §3.4 — No session rotation (fixation)
- Problem: "On click we create a session" with no statement that any pre-login
  session id is rotated.
- Why it matters: Classic session fixation — prime the victim's browser, then ride
  their post-login session.
- Suggested resolution: Rotate the session id on successful login; set
  `HttpOnly`/`Secure`/`SameSite`.

## ADVISORY

### §3 — Tokens may leak into logs
- Problem: Nothing says the raw token is kept out of access/error logs.
- Why it matters: A token in a log is a credential at rest in a less-guarded store.
- Suggested resolution: Log only a hash or opaque id; never the raw token.

## Cross-section coherence flags
- §3.1 (timestamp token) and §3.2 (no expiry) compound: a guessable token that
  never dies is worse than either alone.

## Summary
v0.1 is not trustable: it has a guessable, immortal, replayable credential and an
open send path. Three BLOCKERs before anything else matters. **Another round is
clearly warranted.**
