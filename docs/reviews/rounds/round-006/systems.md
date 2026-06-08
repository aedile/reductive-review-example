# Systems Engineer: Round 006 review of magic-link-auth.md (v0.6)

Fresh full read of v0.6 completed. This round I started from the reordered §7.2
revoke/terminate sequence and its primary-write/atomicity, then §8 retention/metrics,
then re-derived the token core (§3).

## BLOCKER

None.

## FINDING

None.

My round-005 FINDING, the §7.2 terminate-before-revoke ordering race, is closed.
Proof against specific text:

- §7.2 (lines 198-206) now sequences recovery **"in this order"**: (1) **revoke all
  live login tokens** via the §3.1 account-scoped index, "enumerating and writing **on
  the primary** and moving every `issued` row to `revoked`, each row's transition
  contending with consume on that one row"; then (2) "**terminates the account's other
  active sessions and rotates the session.**"
- The doc states the mechanism explicitly: "revoking first fences any further consume,
  and the subsequent session sweep then also kills any session a just-in-time consume
  created in the gap, so **no attacker-minted link or session survives recovery**
  (revoking *after* the sweep would leave that gap open)."
- The atomicity is load-bearing and grounded: each revoke is a primary-side state write
  on the same hash-keyed row that §3.2's consume CAS contends on. So for any token, the
  revoke and a racing consume serialize on one row, either revoke wins (link dead) or a
  just-in-time consume wins, and the *subsequent* session sweep reaps the session that
  late consume minted. There is no longer an interval in which a consume completes after
  the sweep with its tokens still live. The race I flagged is gone.

## ADVISORY

None material. The two v0.6 retention/metrics edits were checked specifically and
introduce nothing:

- **§8.2 revoked reap TTL.** `revoked: 7 days` row reap plus a retained tombstone
  (`hash + state + terminal_at`) past reap. A revoked token's `terminal_at` (the revoke
  instant) can fall *before* its `expires_at`, but the reap guard is keyed on
  "`expires_at` + the replay-observation window," not on `terminal_at`, so a revoked row
  is never reaped earlier than an otherwise-identical expired/consumed row, and a replayed
  revoked link stays classifiable via the tombstone. Conservative and correct; no
  under-retention hole.
- **§8.1 clock-offset ≥3 s warn.** The per-node offset gauge warns at ≥3 s, "strictly
  below the §3.3 ≤5 s NTP bound … caught with headroom before it affects tokens." 3 s < 5 s
  leaves a 2 s margin against the only named skew window. Consistent with §3.3's framing
  of ≤5 s as an absolute per-node bound against the NTP reference (not a pairwise figure),
  so the `now() ≥ expires_at` decision is protected. No contradiction.

## Cross-section coherence flags

- §7.2 ↔ §3.2 ↔ §3.1: the new `revoked` terminal state, the account-scoped secondary
  index, the hash-keyed primary CAS, and the revoke-before-sweep ordering interlock
  consistently. §3.2 lists `issued → revoked (terminal; only via recovery, §7.2)`; §7.2
  uses exactly that transition on the primary; §3.1's account-scoped index is the
  enumeration path. No dangling references.
- §8.1 ≥3 s ↔ §3.3 ≤5 s: consistent (advisory above).
- §8.2 reap guard ↔ §3.3 expiry / replay-observation window: consistent.
- Token core (§3.1-§3.4) re-derived end to end, ≥128-bit CSPRNG, hash-only at rest,
  index-equality comparison (no app-level timing channel), absolute `expires_at` stamped
  by primary, single atomic CAS, session rotation, unchanged and sound. No regressions
  from the v0.6 edits.

## Summary

My round-005 ordering-race FINDING is closed against specific §7.2 text, with the
atomicity correctly anchored to the §3.2 single-row CAS, and the two v0.6 retention/metrics
edits (revoked reap TTL §8.2, clock-offset ≥3 s §8.1) introduce nothing material. I have
re-derived the token core and find no residual BLOCKER, FINDING, or material ADVISORY.
**Another round is not warranted, I have nothing material to add.**
