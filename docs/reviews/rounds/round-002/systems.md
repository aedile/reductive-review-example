# Systems Engineer — round-002

Document: `docs/design/magic-link-auth.md` @ v0.2
(Prompt perturbed this round: failure/retry items moved ahead of storage items.)

## FINDING

### §5.0 — Delivery still treated as infallible
- Problem: §5.0 is unchanged: "we send the email and assume it arrives." No retry,
  no recorded outcome, no resend, no failure surface.
- Why it matters: Email is the least reliable hop in the whole flow; a provider
  blip locks users out with no diagnosis and no recovery short of waiting.
- Suggested resolution: Bounded retry with backoff; record the send outcome as a
  metric; expose a neutral failure state and a rate-limited resend (couples with
  the Product finding on the same section).

## ADVISORY

### §3 / §8 — No send/verify metrics; logging hygiene unstated
- Problem: Still nothing emitted across request→send→click→login, and no statement
  that the (now real) token stays out of logs.
- Why it matters: You can't see the abuse spike or delivery regression you don't
  measure; and a real token in a log is a credential at rest.
- Suggested resolution: Counters/timers on the funnel; log only hashes/opaque ids.
  (Merges with the Security advisory on logging.)

## Fresh-read confirmation (not a finding)
- The token state machine is now coherent: issued → consumed (invalidate) / expired
  (§3.2), with skew handled (§3.3) and one-live-token idempotency (§2.2). The
  round-001 concurrency ambiguity is resolved.

## Cross-section coherence flags
- None new.

## Summary
The token lifecycle is sound now; delivery is the remaining systems gap and it's a
real FINDING, not a nicety. **One more round warranted.**
