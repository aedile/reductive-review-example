# Round 003: Systems Engineer review

Target: `docs/design/magic-link-auth.md` (v0.3)
Reviewer lens: systems engineering, infrastructure, failure, scale.
Method note: fresh full read of v0.3. Per the round-003 perturbation I started from
the supersede/consume concurrency and the §3.2 state machine, then
retention/observability (§8), then delivery/queue (§5), then clock authority (§3.3).
Prior round-002 closures are re-derived from the current v0.3 text below, not taken
from the changelog.

## Re-derivation of the round-002 BLOCKER (§2.2 / §3.2 concurrency + state)

The round-002 BLOCKER had two distinct halves: (a) a consume-vs-supersede race on a
single token with no defined winner, and (b) two concurrent *mints* for the same
account with no serialization point, so the "most recent wins / at most one live
token" invariant was unresolvable.

- Half (a) is **closed by the v0.3 text**: §3.2 now defines `issued → superseded` as a
  real terminal state and states consume and supersede "are both single atomic
  compare-and-set steps that **contend on the same account-keyed row**, so exactly one
  of {consume, supersede} wins; the loser fails closed. Only the consume winner mints a
  session." That is a named serialization point with a defined loser outcome. Re-derived
  against the text, the consume-vs-supersede race is resolved.

- Half (b), mint-vs-mint serialization, is **only conditionally closed**, and the
  condition it rests on is contradicted by §3.1. See the BLOCKER and FINDING below. So
  I am **not** declaring the round-002 concurrency BLOCKER fully closed; the residual is
  re-stated below at the severity the v0.3 text actually earns.

## BLOCKER

### §2.2: Session-scoped supersession directly contradicts the "at most one live token per account" invariant
- Problem: §2.2 opens with the hard invariant "At most one live token exists per
  account," then immediately narrows supersession: "a request that does not carry the
  original request's session context does **not** invalidate an outstanding token." A
  legitimate user routinely makes a second request that carries *no* originating-session
  context: they cleared cookies, switched browsers, are on a different device, or simply
  let the confirmation tab's session expire. By the stated rule that request does not
  supersede the outstanding token, yet it must still mint a token (otherwise the user
  cannot log in). The result is **two live tokens for the same account**, which the very
  first sentence of §2.2 forbids. The two halves of §2.2 cannot both hold.
- Why it matters: This is the same invariant the round-002 BLOCKER was about, and the
  v0.3 fix for the *targeted-login-denial* sub-problem (scoping supersession to the
  session) reopens the *single-live-token* invariant it was supposed to preserve.
  Whichever way an implementer resolves it, a stated guarantee breaks: if they honor
  "at most one live token," a third party (or the user's own new session) can again kill
  an outstanding link (re-opening the denial path §2.2 claims to close); if they honor
  session-scoping, the single-live-token invariant, which §3.2's consume model and the
  §2.1 cost story both lean on, is false. The doc currently asserts both.
- Suggested resolution: Pick a coherent rule and make the invariant match it. The
  defensible version is: supersession is *always* account-scoped (most recent mint wins,
  contending on the account-keyed row), and the anti-denial property is provided not by
  refusing to supersede but by §2.1 rate limits + the fact that an attacker who can mint
  for the victim's account already triggers only a uniform response and cannot read the
  link. If session-scoping is genuinely wanted, restate the invariant as "at most one
  live token *per originating session*" and re-derive the §2.1 cost/accumulation story
  and §3.2 consume model against *multiple* concurrently-live tokens per account.

## FINDING

### §3.1 / §3.2: Verify-time lookup is token-hash-keyed but the serialization point is an "account-keyed row"; the doc never reconciles them
- Problem: §3.1 specifies the lookup model as a hash-indexed token column, "the hash
  column is indexed; the index equality *is* the comparison", i.e. verify resolves a
  token by its hash and gets a token-keyed row. §3.2 then says consume and supersede
  "contend on the same **account-keyed row**." These are two different keys. Consume is
  reached only via the token-hash lookup of §3.1 (the user presents a token, not an
  account id), so consume naturally operates on the *token* row; supersession is
  inherently account-scoped. The doc never states the storage model that makes "the same
  account-keyed row" true for *both* operations, e.g. whether the token state lives on a
  single per-account row, or on per-token rows with a separate account-scoped lock that
  consume must also take.
- Why it matters: The "exactly one of {consume, supersede} wins" guarantee in §3.2 is
  only true if consume and supersede actually serialize on the *same* row/key. If consume
  CASes a token-keyed row while supersede CASes an account-keyed row, they do not contend
  at all and both can succeed, exactly the lost-token / surviving-stale-token failure the
  round-002 BLOCKER identified, now reintroduced through an under-specified data model.
  This is also what makes mint-vs-mint (half (b) above) only conditionally resolved: it is
  serialized only under the single-per-account-row reading, which §3.1 does not support.
- Suggested resolution: State the storage/serialization model explicitly. Either (i) one
  row per account holding the current token hash + state, so the §3.1 hash index and the
  §3.2 account-keyed contention are the same row (verify looks up by hash, but the row is
  account-unique), or (ii) per-token rows plus an account-scoped uniqueness/lock that
  *both* consume and supersede must acquire, and say consume takes it. Then re-derive
  "contend on the same account-keyed row" so it is literally true for consume.

### §3.3: "Single authoritative clock = the datastore's time" assumes a single-node/single-primary datastore that the doc never constrains
- Problem: §3.3 now removes the ±60 s grace and rests entirely on "a **single
  authoritative clock**, the datastore's time, for both `issued_at` and the expiry
  check ... one clock stamps and checks, there is no host-skew window." That is only true
  if the *same* datastore node's clock both stamps `issued_at` and evaluates the expiry
  predicate. Real datastores at this tier are commonly replicated: if `issued_at` is
  stamped on the primary and the expiry check (`now() > issued_at + 10m`) runs against a
  read replica, or in a multi-primary / multi-region deployment, `now()` is a
  *different* node's clock, with replication lag and independent NTP discipline. The
  "single clock" premise then quietly fails and the host-skew window §3.3 claims to have
  eliminated reappears between datastore nodes.
- Why it matters: The whole v0.3 simplification (deleting the tolerance) is justified by
  the single-clock claim. If the deployment reads expiry off a replica, a token can be
  judged expired early or live late by the replica-vs-primary skew, and there is now *no*
  tolerance to absorb it, the v0.2 grace was removed. The design traded an explicit (if
  contradictory) tolerance for an implicit topology assumption that is not stated as a
  constraint, so an implementer on a replicated store inherits a skew bug with no
  guardrail.
- Suggested resolution: Make the topology an explicit requirement: the expiry predicate
  and `issued_at` stamp MUST be evaluated by the same clock domain, i.e. evaluate expiry
  on the primary (or compute it as a stored absolute `expires_at` written at mint time and
  compared by whatever node, so the comparison is value-vs-value, not clock-vs-clock).
  Computing and persisting `expires_at` at mint removes the read-side clock dependency
  entirely and is the cleaner fix.

## ADVISORY

### §5.0 / §8.1: Bounded queue has no saturation/depth or dead-letter-rate metric, so "a burst can't take out delivery" is unobservable until it already has
- Problem: §5.0 absorbs bursts in a "bounded, rate-limited queue" and dead-letters
  exhausted sends into §8; §8.1 now has `sent`, `send-failures` (live), and rate-limit
  drops. But there is no counter/gauge for **queue depth / saturation** or **dead-letter
  rate**. A bounded queue under sustained burst backs up and then sheds or blocks; the
  first observable symptom in the current metric set is `send-failures` climbing, i.e.
  after delivery is already degrading.
- Why it matters: The brief's "does a burst take out delivery" and "see an abuse spike"
  both want a *leading* indicator. Queue depth rising is the early warning; DLQ rate is the
  confirmed-loss signal. Without them an operator sees nominal counters until sends start
  failing.
- Suggested resolution: Add a queue-depth gauge with a high-water alert and a
  dead-letter-rate counter to §8.1, alongside the existing send-failures/rate-limit-drop
  counters.

### §8.2: Tombstone schema (`hash + state + consumed_at`) has no timestamp for superseded/expired tokens
- Problem: §8.2 retains a tombstone of "hash + state + consumed_at" past row-reap for the
  replay-observation window. `consumed_at` exists only for the consume path; superseded and
  expired tokens have no consume timestamp, so their tombstones carry a null time field and
  the reap-ordering rule ("never before expiry + replay-observation window") has no
  per-tombstone basis to evaluate for those states.
- Why it matters: Minor, but a replayed *superseded* link (a real §6.1 case) should stay
  classifiable for the same window as a replayed consumed one; with no terminal-time field
  the window can't be computed uniformly across terminal states.
- Suggested resolution: Generalize the tombstone time field to `terminal_at` (the time the
  token entered its terminal state) so consumed/superseded/expired all carry a basis for the
  reap-ordering guarantee.

## Cross-section coherence flags
- §2.2 sentence 1 ("at most one live token exists per account") contradicts §2.2's
  session-scoped supersession rule for any legitimate new-session request, see BLOCKER.
- §3.1 (token-hash-indexed lookup → token row) vs §3.2 ("contend on the same account-keyed
  row") disagree on what key the state transitions serialize on; the "exactly one wins"
  guarantee depends on reconciling them, see FINDING.
- §3.3 asserts a single datastore clock without constraining the datastore to a single
  clock domain (replica/multi-primary), and the v0.2 tolerance that would have masked the
  gap was removed, see FINDING.
- §5.0's bounded queue and §8.1's metric set are out of sync: the queue can saturate but no
  §8.1 signal makes saturation visible before failure, see ADVISORY.

## Summary
v0.3 genuinely closes most of round-002: consume-vs-supersede now has a real terminal
state and a named CAS contention point (§3.2), the clock text no longer self-contradicts
(±60 s removed, §3.3), retention TTLs/tombstone/reap-ordering are stated (§8.2), the
rate-limit-drop and now-live send-failures metrics exist (§8.1), and delivery is async via
a bounded retrying queue (§5.0). But the v0.3 fix to the *targeted-denial* sub-problem
reopened the single-live-token invariant it was meant to protect (§2.2 self-contradicts, 
BLOCKER), and the §3.2 "same account-keyed row" guarantee is undercut by §3.1's
token-hash-keyed lookup with no reconciling data model (FINDING), plus a topology-dependent
clock assumption that the removed tolerance no longer covers (FINDING). **Another round is
warranted:** there is one ship-stopping invariant contradiction and two substantive
findings outstanding, none of them style.
