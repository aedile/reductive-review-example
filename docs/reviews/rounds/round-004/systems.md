# Round 004 — Systems Engineer review

Target: `docs/design/magic-link-auth.md` (v0.4)
Reviewer lens: systems engineering — infrastructure, failure, scale.
Method note: fresh full read of v0.4, end to end. Per the round-004 perturbation I
started from the bounded-multiple-token concurrency and the §3.2 token-hash-keyed
consume, then §3.3 absolute `expires_at` + NTP bound, then retention/observability
(§8), then delivery (§5). Each round-003 item below is re-derived from the current
v0.4 text and pointed at specific sentences — not taken from the changelog.

## Re-derivation of the round-003 BLOCKER and findings (do they actually close?)

**Round-003 BLOCKER — §2.2 single-live-token invariant vs session-scoped supersession.**
CLOSED by v0.4. §2.2 no longer asserts a single-live-token invariant at all. The
opening line is now "A new request **never invalidates an existing token.** Up to **5**
concurrently-valid, **independently single-use** tokens may exist per account." A
grep of the whole doc finds no surviving "at most one live token" / "most recent
wins" / "supersede" assertion outside §2.2's own explanatory note and the changelog.
The contradiction is dissolved by deleting one horn (the invariant), not by papering
over it: the targeted-login-denial property the round-002/003 fix was protecting is
explicitly preserved ("a third party cannot kill a victim's link, and a user who
re-requests from a fresh session simply gets an additional working link"). The replay
surface is re-bounded coherently by single-use consumption + 10-min expiry + the
per-account cap. This is a real close, not a re-grade.

**Round-003 FINDING — §3.1/§3.2 account-keyed vs token-hash-keyed serialization.**
CLOSED by v0.4. §3.2 now states consume is "a single atomic compare-and-set on **the
token's own hash-keyed row** (`issued → consumed`) — the same row §3.1 resolves at
verify time, so lookup and the state transition contend on exactly one row by
construction." The "account-keyed row" language is gone everywhere. Because
supersession (the only operation that was inherently account-scoped) has been removed,
there is no second operation that needed to serialize on a different key, so the
two-different-keys race the round-003 finding identified cannot arise. Mint-vs-mint
serialization — the conditionally-open half from round-003 — is also resolved: tokens
are now independent per-token rows, so concurrent mints do not contend at all, and
§2.2 correctly says count is bounded by the §2.1 rate limit rather than by any
per-account uniqueness CAS. Internally consistent.

**Round-003 FINDING — §3.3 single-clock-domain assumption.**
CLOSED by v0.4. §3.3 now: "At mint we compute and persist an **absolute `expires_at`**
(mint time + 10 min, stamped by the primary). Expiry is the value comparison
`now() ≥ expires_at`." This is exactly the value-vs-value fix the round-003 finding
recommended: the read-side clock dependency is removed because expiry is no longer
`now() > issued_at + 10m` evaluated against a possibly-different node's clock. The
residual skew is named and bounded ("NTP-synced within a stated bound of **≤ 5
seconds**, which is the only skew window in the system"), and the doc explicitly notes
this replaces the v0.3 single-clock claim. Real close.

**Round-003 ADVISORY — §8.1 queue depth / dead-letter metrics.** CLOSED. §8.1 now
carries "a **send-queue depth gauge** with a high-water alert and a **dead-letter-rate**
counter, so saturation is visible *before* sends start failing."

**Round-003 ADVISORY — §8.2 tombstone time field for non-consumed terminal states.**
CLOSED. §8.2 generalizes the field to "**`terminal_at`** — the time the token entered
its terminal state, defined for consumed *and* expired," and the reap-ordering rule
("never before `expires_at` + the replay-observation window") now has a uniform basis.

## BLOCKER

_None._

## FINDING

### §7.2 / §3.1 — "invalidates all live login tokens" on recovery has no enumeration path under the hash-keyed-only storage model
- Problem: §7.2 requires that "a **successful recovery rotates the session, terminates
  the account's other active sessions, and invalidates all live login tokens.**" Under
  the new multi-token model an account can hold up to 5 live, independent token rows.
  But §3.1 specifies storage as "a **per-token row** keyed/indexed by that hash," and
  §3.2 reinforces that consume resolves a token solely "by construction" via that hash.
  Nothing in v0.4 states a secondary **account-id index** on token rows. With only a
  hash index and a token value that is "**not** derived from any observable input,"
  there is no described way to *enumerate* all of an account's live tokens at recovery
  time in order to invalidate them. The single-token v0.3 design hid this — there was at
  most one token to kill and it was reachable on the account row — but the v0.2/v0.4
  move to per-token hash-keyed rows removes the account handle, and the recovery
  requirement silently assumes it still exists.
- Why it matters: Recovery is the in-scope defense against an inbox-compromise / lost-
  device adversary (§7.1, §7.2), and "invalidates all live login tokens" is one of its
  three load-bearing actions. If the storage model literally cannot find the other live
  tokens, a successful recovery rotates the session and kills other sessions but leaves
  up to 4 attacker-minted links still consumable for the rest of their 10-minute
  window — exactly the post-recovery foothold the action is meant to remove. This is a
  data-model gap that the multi-token decision (§2.2) introduced and §7.2 did not
  re-derive against.
- Suggested resolution: State the index that makes bulk invalidation possible — e.g.
  per-token rows carry an indexed `account_id` (or `account_id_hash`) column, and
  recovery performs an account-scoped CAS that moves all `issued` rows for that account
  to a terminal `revoked` state. Then §3.1's "keyed/indexed by that hash" should say the
  *primary* lookup is by hash while an account-scoped secondary index exists for
  invalidation, so §7.2's "all live login tokens" is literally executable.

## ADVISORY

### §2.2 — "coalesce to the in-flight send" needs an in-flight key that is not specified
- Problem: §2.2 says "Repeated submits within a short window **coalesce to the in-flight
  send** (no duplicate email) without invalidating anything." Coalescing requires
  detecting that a send is already in flight for this address/account — i.e. a short-TTL
  per-address (or per-account) in-flight marker that the request path checks before
  enqueuing. v0.4 never states where that marker lives or its key, and it must be
  consistent with §4.0's constraint that account-existence work happens off the
  synchronous path (so the coalesce check cannot itself become an account-existence
  oracle on the synchronous response).
- Why it matters: Low stakes for correctness — the worst case of a missed coalesce is a
  duplicate email, which §2.1's rate limit already bounds and §2.2 explicitly tolerates
  ("without invalidating anything"). But left unspecified it is an easy place to
  accidentally reintroduce a timing/existence signal, or to do the dedup on the
  synchronous path and violate §4.0's constant-time parity. Worth one sentence.
- Suggested resolution: Note that coalescing is a best-effort dedup keyed on a short-TTL
  in-flight marker evaluated **off the synchronous path** (consistent with §4.0), and
  that a missed coalesce degrades only to a duplicate send bounded by §2.1 — never to a
  parity or correctness violation.

### §3.3 / §5.0 — NTP ≤ 5 s bound is named but not enforced or alerted on
- Problem: §3.3 makes the ≤ 5 s NTP skew "the only skew window in the system" and the
  correctness of `now() ≥ expires_at` rests on it, but nothing in §8.1 monitors clock
  offset across app/datastore nodes. A silently drifting node (NTP daemon dead, VM
  clock-step) violates the named bound undetected.
- Why it matters: Low probability, but when the only remaining skew guarantee is a
  stated bound rather than a value comparison, an unmonitored bound is the failure mode
  — a drifted node judges tokens expired-early or live-late with no guardrail (the v0.2
  grace is gone by design). This is an observability gap, not a logic flaw.
- Suggested resolution: Add a node-clock-offset gauge with an alert at a fraction of the
  5 s bound to §8.1, so a drift that would invalidate the §3.3 premise is visible before
  it affects token decisions.

## Cross-section coherence flags
- §7.2 ("invalidates all live login tokens") vs §3.1/§3.2 (per-token rows keyed only by
  hash, no account index): the recovery action assumes an account-scoped enumeration the
  storage model does not provide — see FINDING. This is the one place the otherwise-clean
  multi-token refactor (§2.2) left a dangling assumption in a section that was not
  re-derived against it.
- §2.2 (coalesce to in-flight send) and §4.0 (all account-dependent work off the
  synchronous path) are compatible but the coalesce key/placement is unstated — see
  ADVISORY; flagging only so the dedup is not implemented on the synchronous path.
- §2.2's "5 concurrently-valid tokens" cap and §2.1's "≤ 3 per address / 15 min" are
  consistent (rate limit + 10-min expiry keep the live count well under 5), and §2.2
  correctly attributes the bound to §2.1 rather than to a separate enforced cap. No
  contradiction; noting it because the two numbers could look like competing limits.

## Summary
v0.4 genuinely closes the round-003 BLOCKER and both round-003 findings, verified
against specific text: the single-live-token invariant and supersession are deleted in
favor of up to 5 independent single-use tokens (§2.2), which dissolves the
contradiction while keeping targeted-denial closed; consume now serializes on the
token's own hash-keyed row with lookup and transition on the same row by construction
(§3.2), closing the key-mismatch finding; and expiry is now a value comparison against
an absolute `expires_at` stamped at mint with a named ≤ 5 s NTP bound (§3.3), closing
the clock-domain finding. The multi-token refactor did, however, leave one section
un-re-derived: §7.2's "invalidates all live login tokens" has no enumeration path under
§3.1's hash-keyed-only storage — a substantive recovery-side gap (FINDING), plus two
low-stakes ADVISORYs (unspecified coalesce key; unmonitored NTP bound). **Another round
is warranted:** one open FINDING remains (the recovery-invalidation enumeration gap),
which under the protocol blocks convergence; the two ADVISORYs alone would not.
