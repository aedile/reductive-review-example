# Systems Engineer — round-001

Document: `docs/design/magic-link-auth.md` @ v0.1

## BLOCKER

### §2.1 — Unbounded send path
- Problem: Every request mints and sends. No rate limit, no idempotency, no
  backpressure.
- Why it matters: A modest burst saturates the email provider and our queue; the
  auth path becomes a self-inflicted DoS and a spam-reputation risk.
- Suggested resolution: Rate-limit per address and IP; collapse duplicate
  in-flight requests; one live token per account.

## FINDING

### §5.0 — No delivery-failure path
- Problem: "We send the email and assume it arrives." Email is best-effort; this
  has no retry, no failure surface, no resend.
- Why it matters: Provider hiccups silently lock users out with no diagnosis.
- Suggested resolution: Bounded retry with backoff; record send outcome; expose a
  resend control and a neutral failure state.

### §3.3 — Clock skew undefined once expiry exists
- Problem: Expiry is unspecified (§3.3), and once it exists the design must say
  whose clock decides. Send and verify may run on different hosts.
- Why it matters: Skewed clocks reject valid links or honor stale ones at the
  boundary.
- Suggested resolution: Evaluate expiry against server time with a stated skew
  tolerance.

## ADVISORY

### §3 — No send/verify metrics
- Problem: Nothing emitted for requests, sends, failures, clicks, logins.
- Why it matters: You cannot see an abuse spike or a delivery regression you don't
  measure.
- Suggested resolution: Counters/timers on the full request→login funnel.

### §3 — Token retention unspecified
- Problem: No statement of how long consumed/expired token rows live.
- Why it matters: Unbounded growth and a larger at-rest secret surface.
- Suggested resolution: Store only hashes; define a retention/cleanup window.

## Cross-section coherence flags
- §3.2 has no state machine: "issued / consumed / expired" is implied but never
  defined, so concurrency (a link clicked twice) is undefined behavior.

## Summary
The send path is a BLOCKER under any real load, and delivery is treated as
infallible when it is the least reliable hop. **Another round is warranted** once
the token state machine and send limits exist.
