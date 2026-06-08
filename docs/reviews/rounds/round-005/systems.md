# Round 005 — Systems Engineer

Fresh full read of magic-link-auth.md v0.5. Re-derived from the new
`account_id` secondary index + account-scoped revoke (§3.1/§3.2/§7.2)
outward, not from the changelog.

## Round-004 FINDING — disposition

My round-004 FINDING was that recovery's "invalidate all live tokens" had
**no enumeration path**: rows were keyed only by token hash, and at recovery
time the raw tokens are unknown (recovery is not triggered from a token), so
there was no operation that could *find* an account's live rows to revoke.

This is **closed in text**:

- §3.1 now states each row "also carries an indexed `account_id`; this
  **account-scoped secondary index** exists so recovery (§7.2) can enumerate
  and revoke an account's live tokens — the primary verify path still goes
  only by hash." That gives recovery a key it actually holds (the account_id
  of the recovering, authenticated user) and explicitly preserves the
  hash-only verify path, so the index does not become a second lookup channel
  on the hot path.
- §3.2 adds the `issued → revoked` terminal transition ("only via recovery,
  §7.2"), so the enumerated rows have a defined terminal state.
- §7.2 wires it: "invalidates all live login tokens — the last via the §3.1
  account-scoped index, moving every `issued` row for the account to
  `revoked` in one account-scoped operation."

The enumeration gap is genuinely resolved. However, the v0.5 edit that
closed it introduced a **new ordering race** between session-termination and
token-revocation (see FINDING §7.2 below).

## BLOCKER

(none)

## FINDING

### §7.2 — Session-termination ordered before token-revocation re-opens the post-recovery foothold the revoke was meant to close

- Problem: §7.2 specifies the recovery effects in this order: "rotates the
  session, **terminates the account's other active sessions, and invalidates
  all live login tokens**." Tokens are revoked *after* sessions are
  terminated. The whole point of the §3.1 index + account-scoped revoke is
  that an attacker may hold a live, attacker-minted token at recovery time
  (§7.1 names "attacker *with* the victim's inbox"). If that attacker
  consumes their still-`issued` token in the window **after** session
  termination runs but **before** revoke reaches that row, the consume-CAS
  (§3.2, `issued → consumed`) succeeds and mints a fresh session — and that
  session post-dates the termination sweep, so it is never terminated. The
  closing claim "so no attacker-minted link survives recovery" then does not
  hold: the *link* is consumed, but the *session it minted* survives.
- Why it matters: this is exactly the foothold the v0.5 edit set out to
  remove. The narrow interleaving (consume landing between the two recovery
  steps) is small but is the single most security-relevant moment in the
  protocol — it is the moment an attacker is being evicted. The current
  ordering is backwards for closing it.
- Suggested resolution: order revoke **before** session termination, OR make
  the two steps one logical fence: revoke-all-tokens first (so no further
  consume can mint), *then* terminate sessions (which now also kills any
  session a just-in-time consume created). State the ordering explicitly;
  "rotates, terminates sessions, and invalidates tokens" reads as a set, but
  the safety property depends on the sequence.

## ADVISORY

### §7.2 / §3.2 — "one account-scoped operation" leaves per-row vs. all-rows atomicity unspecified against the linearizable consume CAS

- Problem: §3.2's consume is a CAS on **one** hash-keyed row on "the primary /
  a linearizable path." §7.2's revoke is "one account-scoped operation" over
  **N** rows resolved via a secondary index, held "to the primary-path bar."
  Whether that bulk update is a single linearization point for the whole set,
  or N independently-serialized row updates, is not stated. The per-row
  serialization is sufficient for *each* row's consume-vs-revoke contention
  (the loser sees a non-`issued` state and fails closed), so the property is
  defensible — but only the FINDING-§7.2 ordering fix makes the *set*-level
  guarantee airtight. Worth naming the atomicity model so a reader does not
  assume a global snapshot the store may not provide. Secondary-index reads
  are also frequently non-linearizable by default; "held to the primary-path
  bar" should be read as "enumerate and write on the primary," not "read the
  index off a replica."
- Why it matters: leaving it implicit invites an implementation that
  enumerates against a stale index replica and misses an in-flight `issued`
  row.
- Suggested resolution: one sentence stating revoke enumerates and writes on
  the primary, and that each row's transition contends with consume on that
  same single row (mirroring §3.2's "contend on exactly one row").

### §8.2 — Revoked rows have no stated reap TTL

- Problem: §8.2 gives reap TTLs for `consumed` (7 days) and `expired` (24 h)
  but not for `revoked`, even though §3.2 made `revoked` a first-class
  terminal state and §8.2 itself now defines `terminal_at` "for consumed,
  expired, *and* revoked." A terminal state with a tombstone but no row-reap
  rule is an unbounded-growth corner for accounts that recover repeatedly.
- Why it matters: minor capacity/cleanliness gap, not a safety issue — the
  tombstone keeps replays classifiable regardless.
- Suggested resolution: state a reap TTL for `revoked` (treating it like
  `consumed`, 7 days, is the natural choice since both are
  deliberately-terminated live tokens), or say revoked rows follow the
  consumed TTL.

### §8.1 — Clock-offset gauge alert threshold relative to the 5 s bound is unstated

- Problem: §8.1's node-clock-offset gauge "alerts when any app/datastore node
  drifts toward the §3.3 ≤ 5 s NTP bound." "Toward" has no number. If it
  alerts only at 5 s, the alert fires when correctness is already at risk
  (§3.3's `now() ≥ expires_at` decision can already be wrong by the time you
  are paged); the gauge's stated purpose ("caught before it affects tokens")
  requires a margin below 5 s.
- Why it matters: an alert at the failure boundary is a lagging indicator, not
  the leading one §8.1 claims it to be — consistent in spirit with the
  send-queue high-water gauge, which does have margin built in.
- Suggested resolution: name a warn threshold strictly below the bound (e.g.
  alert at ≥ 3 s of measured offset), so remediation has headroom before the
  5 s window is exhausted.

## Cross-section coherence flags

- §3.1 ↔ §7.2: enumeration index and revoke operation now agree; the
  round-004 dangling "invalidate all live tokens" reference is resolved.
- §3.2 ↔ §7.2 ↔ §6.1: the new `revoked` state is consistently surfaced —
  §6.1's "already used (consumed or revoked-by-recovery)" covers it, and
  §3.2's "any terminal state returns the defined response in §6.1" still
  holds. No dangling reference.
- §7.2 internal: the effect ordering (terminate-sessions-then-revoke-tokens)
  contradicts the section's own closing claim "no attacker-minted link
  survives recovery" — flagged as FINDING §7.2.
- §3.2 ↔ §8.2: `terminal_at` is now defined for all three terminal states,
  but §8.2's reap-TTL list omits `revoked` — flagged as ADVISORY.

## Summary

My round-004 FINDING (no enumeration path for recovery-time token
invalidation) is genuinely closed: the §3.1 `account_id` secondary index
gives recovery a key it actually holds, §3.2 adds the `revoked` terminal
transition, and §7.2 composes them, all while preserving the hash-only verify
path and per-row consume CAS. The closing edit, however, introduced a new
ordering race in §7.2 — sessions are terminated *before* tokens are revoked,
so a consume landing between those two steps mints a session that escapes the
termination sweep, defeating the very foothold the revoke was added to
remove. **Another round is warranted** to fix the §7.2 step ordering (one
FINDING); the three ADVISORYs (revoke atomicity model, revoked-row reap TTL,
clock-offset alert margin) may be folded in or deferred.
