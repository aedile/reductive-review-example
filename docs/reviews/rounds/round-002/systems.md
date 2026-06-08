# Round 002: Systems Engineer review

Target: `docs/design/magic-link-auth.md` (v0.2)
Reviewer lens: systems engineering, infrastructure, failure, scale.
Method note: fresh full read of v0.2; prior round-001 closures re-derived from the
current text, not taken from the changelog.

## BLOCKER

### §2.2 / §3.2: "Invalidate the first" has no state and no serialization point
- Problem: §2.2 asserts a hard invariant, "At most one live token exists per
  account; the most recent request wins" and "Requesting a second link before the
  first is consumed **invalidates the first**." But the §3.2 state machine defines
  only two transitions: `issued → consumed` and `issued → expired`. There is no
  `issued → invalidated`/`superseded` state and no transition for the act §2.2
  describes. Nothing in the doc says what serializes two concurrent requests for the
  same account, so "the most recent request wins" is unresolvable: under a real
  race, two mints can each invalidate the other (zero live tokens) or interleave so
  both survive (two live tokens), violating the stated invariant either way.
- Why it matters: The single-live-token invariant is load-bearing for the rest of
  the design, the consume CAS in §3.2 implicitly assumes one canonical token to
  consume, and the §2.1 cost/abuse story assumes mints don't accumulate. An
  invariant with no defining state and no serialization authority is unimplementable
  as written; each engineer will invent a different concurrency model, and the
  failure modes (lost token → user can't log in; surviving stale token → wider
  replay surface) are exactly the ones this scheme is supposed to foreclose. There
  is also a live race between §2.2 invalidation and a §3.2 consume of that same
  token: a click landing concurrently with a re-request can consume a token that
  §2.2 is simultaneously invalidating, with no defined ordering.
- Suggested resolution: Add the missing terminal/non-terminal state to §3.2 (e.g.
  `issued → superseded`) and make supersession a single atomic step under a
  serialization point keyed by account, e.g. a conditional write that invalidates
  any prior `issued` row and inserts the new one in one transaction, or an account-
  scoped lock/uniqueness constraint. State that the consume CAS and the supersede
  step contend on the same row/key so exactly one of {consume, supersede} wins, and
  define the outcome of the loser.

## FINDING

### §8.1 / §5.0: Observability lists a metric the delivery model cannot produce, and omits the one needed to see abuse
- Problem: §8.1 enumerates a `send-failures` counter "enough to detect ... a
  delivery regression." But §5.0 explicitly says delivery is best-effort with **no
  failure surface** (open F3). A counter cannot increment off a signal that, by the
  current delivery model, is never captured, so the §8.1 metric set is partly
  aspirational against §5.0. Separately, §2.1 drops over-limit requests "before any
  email is sent," yet §8.1 has **no counter for rate-limit drops / rejected
  requests**. The brief's explicit goal, "see an abuse spike", depends precisely
  on that drop counter: an enumeration or inbox-bombing run shows up as a spike in
  *rejected* requests, not in `sent`.
- Why it matters: Operators will believe they have delivery-regression visibility
  they do not have (§5.0 emits nothing to count), and the abuse spike the whole
  rate-limit machinery exists to stop is invisible because the rejected-request
  signal is unmetered. The system can be under active attack with every listed
  counter looking nominal.
- Suggested resolution: Add a `rate_limited`/`dropped` counter dimensioned by
  per-address vs per-IP limit, and define alert thresholds on it. Either defer the
  `send-failures` counter until §5.0 defines a failure surface, or note explicitly
  that it is dormant until F3 lands so it isn't read as live coverage.

### §8.2 / §3.2: Retention TTL is undefined and silently breaks replay detection
- Problem: §8.2 says consumed/expired rows are "reaped on a **defined** TTL," but no
  TTL value or basis is actually given, "defined" is asserted, not defined. Worse,
  reaping consumed rows collides with §3.2/§8.1 replay detection: once a consumed
  token's row is reaped, a replayed link hits *no row at all* and is indistinguishable
  from a never-existed/guessed token. So the §8.1 "replay attempts" counter
  under-counts by exactly the reaped population, and the §3.2 fail-closed response
  for a "consumed" token silently degrades to the generic unknown-token path after
  TTL.
- Why it matters: A replay-attempt metric that quietly stops counting after the
  retention window gives false assurance during precisely the slow-and-low replay
  campaign it should catch. It also undercuts the audit trail the retention policy
  claims to balance against. This is a real systems coupling, not a wording nit:
  retention duration and replay observability are the same knob and the doc treats
  them independently.
- Suggested resolution: State the actual TTL per terminal state, and make it long
  enough to cover the replay-detection window (retain a minimal consumed-token
  tombstone, hash + consumed_at + state, past row purge so replays are still
  classifiable as replay, not unknown). Note the ordering guarantee: reaping must
  never run before expiry + replay-observation window.

### §5.0: Delivery is still synchronous/best-effort: request latency coupled to the provider, no burst absorber
- Problem: §5.0 remains "We send the email" with the F3 caveat (no retry, no failure
  surface, no resend, single channel). From a systems standpoint, beyond the missing
  retry/failure-surface that F3 names, the doc still does not decouple the request
  acknowledgement from the provider call. A synchronous send ties request-path
  latency to provider latency, and a burst of (rate-limit-passing) requests fans out
  directly into provider calls with no queue/throttle between them.
- Why it matters: A slow or throttling provider stalls the request path for all
  users; a legitimate spike just under the rate limits can trip provider-side
  throttling that blocks mail globally and runs up cost. The email path is a shared
  failure domain with no shock absorber. Rate limits (§2.1) cap *who* may request,
  not the instantaneous fan-out to the provider.
- Suggested resolution: When F3 is addressed, send asynchronously via a bounded,
  rate-limited queue/worker (per-recipient + global throttle), decouple the user
  acknowledgement from actual delivery, classify hard-bounce vs transient, and
  dead-letter exhausted sends into the §8 observability surface. Track this as the
  systems half of F3, not just its UX half.

## ADVISORY

### §3.3: "±60s skew tolerance" contradicts "single authoritative datastore time"
- Problem: §3.3 says expiry is evaluated against "the datastore's authoritative
  server time, never a client-supplied time," and *also* adds "a small fixed ±60
  seconds skew tolerance for issuance/validation host differences." If every expiry
  check reads the one datastore clock, there is no issuance/validation host clock to
  differ, the ±60s tolerance has no host-skew to absorb under its own stated model.
  The two halves of the sentence describe two different time authorities.
- Why it matters: On a 10-minute token, ±60s makes the effective window 9-11 min, 
  benign in magnitude, but the inconsistency signals an unsettled design: if
  issued_at is stamped by an app host while expiry is checked against datastore time,
  the authority is *not* in fact single, and the real skew to worry about is app-host
  vs datastore, which the ±60s doesn't clearly target.
- Suggested resolution: Pick one. If the datastore stamps both issued_at and
  evaluates expiry, drop the ±60s clause as unnecessary. If app hosts stamp
  issued_at, say so and justify the tolerance against app-host-vs-datastore skew
  (and require NTP on app hosts).

### §3.1: "O(1) keyed lookup" + "constant-time compare" are partly redundant as stated
- Problem: §3.1 says the stored hash is "keyed for O(1) lookup" *and* that we
  "compare in constant time." A keyed/indexed lookup by hash already performs the
  equality match inside the index; a separate constant-time compare matters only if
  the implementation fetches a candidate row and then compares secrets in
  application code. The doc doesn't say which, so the timing-safety guarantee is
  ambiguous.
- Why it matters: Minor, but if lookup is a plain indexed equality on the hash, the
  "constant-time compare" is doing nothing and may give false assurance; if it is
  fetch-then-compare, the lookup is not the O(1)-by-key path described. Implementers
  should know which model holds so the timing property is real.
- Suggested resolution: State the lookup model explicitly, e.g. "index on the hash;
  the index equality is the comparison, no plaintext-token compare occurs", or, if
  fetching then comparing, keep the constant-time compare and say so.

## Cross-section coherence flags
- §2.2 ("invalidates the first," "at most one live token") names a transition that
  §3.2's state machine does not contain, see BLOCKER. The two sections disagree on
  what states a token can occupy.
- §8.1 lists `send-failures` while §5.0 (open F3) provides no failure surface to
  source it; §8.1 omits a rate-limit-drop counter while §2.1 is the section doing the
  dropping, the observability section and the sections it observes are out of sync.
- §8.2 retention and §8.1/§3.2 replay detection are coupled (reaped consumed rows
  become unclassifiable replays) but written as independent, see FINDING.
- §3.3 internally splits between "single datastore time authority" and "±60s host
  skew tolerance", see ADVISORY.

## Summary
v0.2 genuinely closes the round-001 BLOCKERs I can re-derive from the text: token
storage is now hash-at-rest with keyed lookup (§3.1), and the consume path is a real
atomic CAS (§3.2). But the new idempotency invariant (§2.2) introduces a state and a
concurrency-serialization gap the §3.2 state machine does not back, which I rate a
BLOCKER, and the new observability/retention section (§8) ships metrics that its own
delivery and retention models can't produce or that silently degrade, plus the
clock-authority text contradicts itself. Another round IS warranted: there is one
ship-stopping concurrency/state gap and three substantive findings outstanding, none
of them style.
