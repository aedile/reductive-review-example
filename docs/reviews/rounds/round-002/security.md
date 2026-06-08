# Security Adversary — round-002

Document: `docs/design/magic-link-auth.md` @ v0.2
(Prompt perturbed this round: checklist reordered, session items moved first.)

## FINDING

### §3.4 — Session id still not rotated on login
- Problem: §3 now has a strong token, but §3.4 still just "creates a session" with
  no statement that a pre-login session id is discarded and reissued.
- Why it matters: Session fixation survives the token fix — an attacker who plants a
  known session id before login rides the authenticated session afterward.
- Suggested resolution: Rotate the session id on successful login; set
  `HttpOnly`/`Secure`/`SameSite`.

## ADVISORY

### §3 — Confirm raw token is kept out of logs
- Problem: Now that the token is a real 32-byte secret (§3.1), logging it anywhere
  is a credential at rest. The doc still doesn't say it's excluded.
- Why it matters: A high-entropy token in an access log is as good as the link.
- Suggested resolution: State that only the hash/opaque id is logged.

## Fresh-read confirmation (not a finding)
- B1/B3 resolved: token is CSPRNG, single-use, expiring (§3.1–§3.2); replay now
  fails closed. B2 resolved: §2.1 rate limits the send path. F1 resolved: §4.0 is
  uniform. I re-derived each rather than trusting the changelog.

## Cross-section coherence flags
- None new. §2.2 (one live token) and §3.2 (single-use) are consistent.

## Summary
The credential is fixed; the one material security gap left is session fixation at
§3.4. **One more round warranted** — I expect to converge once rotation lands.
