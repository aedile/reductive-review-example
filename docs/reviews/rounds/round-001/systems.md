# Round 001 — Systems Engineer review

Target: `docs/design/magic-link-auth.md` (v0.1)
Reviewer lens: systems engineering — infrastructure, failure, scale.

## BLOCKER

### §3.1 — Token generation has no defined storage, indexing, or at-rest model
- Problem: The token is "derived from the current timestamp" and the doc never says what is stored, where, or how it is looked up at verify time. There is no record schema (token, email/user, issued_at, expires_at, state), no index, and no statement of whether the raw token sits at rest. Verification (§3.2) is impossible to implement because there is nothing defined to verify against.
- Why it matters: Without a defined storage/lookup model the verify path is undefined behavior. A timestamp-derived token is also guessable, but the systems failure is more basic: there is no persisted authority a verify can consult, so two requests, a restart, or a multi-host deployment have no agreed source of truth. Any implementation will be invented per-engineer and diverge.
- Suggested resolution: Specify a token record: store only a hash of a high-entropy random token (never the raw token at rest), keyed/indexed for O(1) lookup, with columns for `email`/`user_id`, `issued_at`, `expires_at`, `state`, `consumed_at`. State the datastore and its durability/replication assumptions.

### §3.2 / §3.3 — No state machine; issued/consumed/expired transitions are undefined
- Problem: §3.2 says the link "logs the user in when clicked" and §3.3 leaves expiry "unspecified." There is no issued → consumed → expired state machine, no atomic consume step, and no rule for what a verify does when it encounters an already-consumed or expired token.
- Why it matters: Without an atomic state transition the link is replayable (the seeded flaw) and, worse for systems, two concurrent clicks both succeed because nothing serializes the consume. A verify against an expired or consumed token has no defined response, so behavior is non-deterministic across implementations and across hosts.
- Suggested resolution: Define an explicit state machine with a single atomic compare-and-set on consume (e.g., conditional UPDATE `state='issued' → 'consumed'` returning affected-rows; only the winner mints a session). Define terminal states (consumed, expired, revoked) and the exact response for verifying a token in each.

## FINDING

### §2.1 — Send path is not idempotent and has no de-duplication or coalescing
- Problem: "We immediately generate a login link and email it" on every submit. Combined with the absence of rate limiting (seeded §2.1), each submit mints a new token and sends a new email. There is no idempotency key, no coalescing window, and no statement of how many simultaneously-valid tokens a user may hold.
- Why it matters: A double-clicked form or a retried request mints multiple valid tokens and multiple emails. Many valid tokens per user widens the attack surface and confuses the consume logic (which token wins?). It also multiplies email-path load.
- Suggested resolution: Define a short coalescing window per email (return the same in-flight link / no-op if one was issued within N seconds), and cap the number of concurrently-valid tokens per user (invalidate older on new issue).

### §5.0 — Email delivery is fire-and-forget with no failure path, retry, or provider-outage behavior
- Problem: "We send the email and assume it arrives" (seeded). There is no handling of provider 4xx/5xx, timeouts, bounces, or provider downtime; no retry policy, no dead-letter, no backpressure.
- Why it matters: Email providers fail and rate-limit routinely. Fire-and-forget means silent auth failures (user never receives the link, sees only "check your inbox"), and a synchronous send couples request latency to provider latency — a slow provider stalls the request path. There is no signal that delivery failed.
- Suggested resolution: Send asynchronously via a queue/worker with bounded retries and exponential backoff, classify hard bounces vs transient failures, dead-letter exhausted sends, and surface delivery status to observability. Decouple request acknowledgement from actual delivery.

### §2.1 / §5.0 — No protection of the email path against burst load
- Problem: With no rate limit (seeded §2.1) and synchronous per-request send (§5.0), a burst of requests (organic spike or abuse) translates directly into a burst of provider calls.
- Why it matters: This can exhaust the provider quota, trip provider-side throttling that blocks legitimate mail for all users, and run up cost. The email path becomes a shared failure domain with no shock absorber.
- Suggested resolution: Put sends behind a rate-limited queue with per-recipient and global throttles; shed/queue rather than fan out synchronously; alert on send-rate anomalies.

### §3.x — No observability defined for send or verify
- Problem: The doc specifies no metrics, logs, or traces for either path — no counters for links issued, sends attempted/succeeded/failed/bounced, verifies attempted/succeeded/expired/consumed/invalid, nor latency.
- Why it matters: Without these you cannot detect an abuse spike (the brief's explicit concern), a provider outage, or a verify-failure regression. The system is operationally blind; incidents are discovered by user complaints.
- Suggested resolution: Define a metric set per state transition and per failure class, with alerting thresholds (e.g., send-failure rate, issue-rate per IP/email, verify-failure ratio).

### §3.3 / §3.1 — No token data retention or cleanup policy
- Problem: Expiry is unspecified and there is no statement of how long consumed/expired token records are retained or how they are reaped.
- Why it matters: Token tables grow unbounded, degrading lookup performance and inflating the blast radius of a datastore compromise (more historical secrets at rest). Without a reaper, expired rows accumulate indefinitely.
- Suggested resolution: Define a TTL/retention for each terminal state and a reaping mechanism (DB TTL index or scheduled job). Keep only what audit requires; purge raw tokens immediately on consume.

## ADVISORY

### §3.x — Clock skew between send and verify hosts is unaddressed
- Problem: Token uniqueness/expiry is timestamp-based but no clock authority is named. In a multi-host deployment, the host issuing and the host verifying may disagree on time.
- Why it matters: Skew causes premature expiry or a too-long valid window at the boundary; timestamp-derived tokens also collide if two hosts share a clock tick.
- Suggested resolution: Compute and compare expiry against the datastore's authoritative time (or a single time source), not per-host wall clocks; require NTP. Make uniqueness independent of the clock by using random tokens.

### §6.0 — Cross-device / cross-host verify session continuity unspecified
- Problem: The seeded flaw notes opening the link on a different device isn't handled; from a systems view, session creation (§3.4) on the verify host must work regardless of which host originated the request and which device clicks.
- Why it matters: If session state or the token record is host-local rather than shared, verify on a different host or device fails intermittently behind a load balancer.
- Suggested resolution: Ensure token and session stores are shared/replicated across all request-handling hosts; state that verify is stateless w.r.t. the issuing host.

## Cross-section coherence flags
- §3.2 ("logs the user in when clicked") presumes a verify-against-stored-token step, but §3.1 defines no stored record to verify against — the two sections are mutually incomplete.
- §3.3 (expiry "unspecified") is referenced implicitly by §3.2's reusability flaw; expiry cannot be a token property until §3.1 defines where `expires_at` lives.
- §4.0's "check your inbox" message asserts delivery success that §5.0 cannot guarantee (assume-arrives), so the user-facing response contradicts the actual delivery model.

## Summary
The document defines a flow but omits every load-bearing systems primitive: token storage/lookup, an atomic issued/consumed/expired state machine, send/verify idempotency, delivery-failure handling, observability, and retention. Two findings rise to BLOCKER because the verify path is literally unimplementable as written (no stored authority, no defined transitions), and concurrency/replay are unconstrained. Another round IS warranted — these are material, unresolved gaps, not style notes; I have substantive issues outstanding and nothing here is fit to converge on.
