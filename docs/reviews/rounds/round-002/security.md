# Security Adversary: Round 002

Target: `docs/design/magic-link-auth.md` v0.2

Method note: fresh full read, checklist worked in reverse (recovery/lockout →
session fixation → interception → enumeration → token entropy/lifetime). Prior
BLOCKER closures re-derived from the current text, not taken from the changelog.

## BLOCKER

### §7.2: Recovery / lockout path is an unscoped second takeover channel
- Problem: §7.1 correctly names email-inbox control as the trust root, then §7.2
  introduces a *recovery method*, "a second verified channel or support-mediated
  identity check", enrolled "at creation time." That recovery channel is, by
  construction, an alternate way to authenticate as the account, yet it is held to
  none of the adversarial scrutiny the primary path now is. There is no stated
  entropy/possession bar for the "second verified channel," no rate limiting or
  lockout on recovery *attempts*, no statement that a successful recovery rotates
  the session (§3.4) or invalidates outstanding login tokens (§2.2/§3.2), and
  "support-mediated identity check" is precisely the social-engineering surface
  through which most real-world account takeovers occur (the help-desk reset).
- Why it matters: An auth scheme is only as strong as its weakest authentication
  path. As written, an attacker who cannot reach the victim's inbox can pivot to
  the recovery channel: if it is an SMS/secondary email it inherits SIM-swap /
  secondary-inbox compromise with *no* rate limit specified; if it is
  support-mediated it is human-judgement override of the entire token model. The
  round-1 ADVISORY explicitly warned that "any out-of-band recovery channel added
  later becomes the new weakest link and a takeover vector if unscoped now." v0.2
  added the channel but did not scope it, so the warning is now realized as a
  live BLOCKER rather than a deferred concern.
- Suggested resolution: Bring §7.2 inside the threat model. Specify (a) the
  authentication strength required of the second channel, (b) rate limiting and
  lockout on recovery *initiation and verification* attempts mirroring §2.1, (c)
  that support-mediated recovery requires a defined, replay-resistant identity
  proof and is itself logged/alerted (§8), and (d) that a successful recovery
  rotates the session and invalidates all live login tokens. Until the recovery
  path is specified to the same bar as the primary path, the document's "we defend
  against … session fixation / replay" claim does not hold end-to-end.

## FINDING

### §2.1 / §2.2 vs §4.0: Enumeration timing oracle from asymmetric server-side work
- Problem: §4.0 asserts identical copy, status, *and timing* with "no observable
  difference in side effects." But §2.1 and §2.2 describe the registered branch
  doing materially more work than the unregistered branch: for a real account the
  server mints a token (§3.1 CSPRNG + hash write), runs §2.2 idempotency
  (look up and *invalidate* the prior live token, atomic CAS), and enqueues a
  send; for a non-account it must do *none* of that. §2.1 only guarantees the
  rate-limit-exceeded case is dropped "before any email is sent", it says nothing
  about equalizing the account-exists vs. account-absent branches. That divergent
  work is a classic timing oracle, and the §2.2 "coalesce to the in-flight link"
  behavior adds a second-order signal (a real account under repeated submits has
  observably different latency/coalescing behavior than a black hole).
- Why it matters: Enumeration is the precondition for targeting (§7.1 names it as
  defended-against). A uniform message that is contradicted by a measurable timing
  delta leaks exactly the bit §4.0 claims to protect, and does so at scale because
  the rate limits in §2.1 are per-address/per-IP, not global, a distributed prober
  rotates addresses cheaply. The doc currently *asserts* timing parity without any
  mechanism to produce it.
- Suggested resolution: State the mechanism that makes timing constant, not just
  the goal: e.g. perform the token-mint/idempotency/enqueue work asynchronously
  off the request path so the synchronous response is identical for both branches,
  or run a dummy equivalent-cost path for non-accounts. §4.0 should reference that
  mechanism rather than asserting the property.

### §2.2: Idempotency invalidation enables targeted login denial-of-service
- Problem: §2.2 states "Requesting a second link before the first is consumed
  invalidates the first … the most recent request wins." Combined with §2.1's
  per-address limit of 3 requests / 15 min, an attacker who can trigger requests
  for a victim's address (the send path is unauthenticated) can keep invalidating
  the victim's just-delivered link by firing a fresh request, and/or burn the
  victim's own 3-per-15-min budget so the victim cannot get a usable link. The
  link the victim clicks is dead because a later attacker request superseded it.
- Why it matters: This is a denial-of-login against a chosen victim that does not
  require inbox access, outside the §7.1 accepted trust-root assumption. It turns
  the anti-abuse rate limit (§2.1) into the abuse primitive. Round-1's bombing
  finding was closed by rate limiting, but the idempotency rule added in v0.2
  reintroduces an availability attack from a different direction.
- Suggested resolution: Decide and state the precedence carefully: either scope
  idempotency/invalidation to the *same originating session/request* (so a
  third-party request cannot kill the victim's live token), or allow a small bounded
  set of concurrently-valid tokens with independent single-use, rather than
  "most recent globally wins." Note the interaction with the §6.0 F4 cross-device
  case, where requester and clicker legitimately differ.

## ADVISORY

### §3.3: ±60s skew tolerance is symmetric and extends effective token lifetime
- Problem: §3.3 sets a "±60 seconds" tolerance against authoritative server time.
  The negative direction means a token can validate up to ~60s *after* its nominal
  10-minute expiry, so effective max lifetime is 11 minutes, and the tolerance is
  double the ≤30s the round-1 ADVISORY suggested. The justification given is
  "issuance/validation host differences," but if expiry is evaluated against the
  *datastore's* authoritative time (as the same sentence states), issuance and
  validation read the same clock and no validation-side grace is needed at all.
- Why it matters: Any grace window is replay surface. The stated rationale and the
  stated single-clock authority are in slight tension, if there is one
  authoritative clock, the validation-side +60s grace is unjustified and only
  enlarges the window an intercepted/archived link remains usable.
- Suggested resolution: Either drop validation-side grace to zero (single
  authoritative clock makes it unnecessary) or, if multi-host issuance genuinely
  skews the *stored* issuance timestamp, apply tolerance only to issuance and cap
  it at ≤30s, and say so explicitly.

### §3.4: SameSite=Lax permits the cross-site GET that consumes the token
- Problem: §3.4 sets `SameSite=Lax`. The consume action is reached by a top-level
  GET navigation from the mail client (cross-site), which Lax intentionally allows
that is required for the link to work. But it also means the consume endpoint
  must not rely on cookie SameSite for CSRF protection, and a GET that mutates
  state (issued→consumed) is itself prefetch/scanner-sensitive (the §6.0 F4
  email-scanner pre-fetch case). The doc rotates the session correctly but does not
  state that consumption is CSRF-safe or that the GET-consume is guarded against
  automated prefetch.
- Why it matters: The session-fixation fix (re-derived: rotation is genuinely
  present and closes fixation, confirmed) is sound, but a state-mutating GET that
  any link-fetcher can trigger interacts with the still-open F4 pre-fetch issue;
  flagging here so the two are reconciled together rather than fixed in isolation.
- Suggested resolution: Note that consume must tolerate the §6.0 F4 prefetch model
  (e.g. require an explicit user gesture / POST-confirm step before the atomic CAS,
  or a one-time interstitial), and confirm CSRF posture independent of SameSite.

## Cross-section coherence flags
- §4.0 *asserts* timing/side-effect parity that §2.1+§2.2 *describe mechanisms
  contradicting* (asymmetric token-mint/invalidate/enqueue work). The property and
  the procedure disagree; see FINDING above.
- §3.3 states a single authoritative datastore clock *and* a ±60s host-skew
  tolerance in the same breath, if the clock is single and authoritative, the
  validation-side tolerance is self-contradicting. See ADVISORY.
- §7.1 claims the panel "defend[s] against … session fixation" and §3.4 backs that
  for the *primary* path, but §7.2's recovery path is outside that guarantee, the
  threat-model claim overstates coverage until §7.2 is scoped (BLOCKER).
- §2.2's "most recent request wins / invalidates the first" collides with the
  still-open §6.0 F4 cross-device path, where the requester and the clicker
  legitimately differ; the two cannot both be satisfied as currently written and
  must be designed together.

## Re-derived confirmations (prior BLOCKERs, checked against current text: not on faith)
- §3.1 token entropy: ≥128-bit CSPRNG, not derived from any observable input,
  stored only as a keyed hash with constant-time compare. The round-1
  timestamp-forgery BLOCKER is genuinely closed.
- §3.2 single-use/replay: explicit issued→consumed/expired state machine with an
  atomic compare-and-set on consume and a 10-min TTL; only the race winner mints a
  session. The round-1 "permanently replayable" BLOCKER is genuinely closed (modulo
  the §3.3 grace-window ADVISORY).
- §3.4 session fixation: pre-login id discarded, fresh server-issued id, HttpOnly /
  Secure cookies. The round-1 fixation BLOCKER is genuinely closed for the primary
  path (caveats: SameSite ADVISORY above; recovery path BLOCKER separate).

## Summary
The three round-1 BLOCKERs are genuinely closed (re-derived from the text, not the
changelog), but the v0.2 revision introduced new surface: an unscoped recovery /
lockout channel (§7.2) that is a second, unguarded authentication path and a live
BLOCKER, plus two FINDINGs where the new anti-abuse machinery created an
enumeration timing oracle (§2.1/§2.2 vs §4.0) and a targeted login-denial primitive
(§2.2 invalidation). With one open BLOCKER and two open FINDINGs, another round is
clearly warranted, I have material objections remaining and the recovery path in
particular must be brought inside the threat model before the document can be
trusted end-to-end.
