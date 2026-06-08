# Security Adversary: Round 006 (target: magic-link-auth.md v0.6)

Fresh full read of v0.6, end to end, not a delta skim. Per the round-006
perturbation I started from the §7.2 recovery step ordering (revoke-then-terminate)
and re-derived whether the reorder closes the round-005 race (F19) cleanly, then
worked back out to enumeration/timing and the token core. I also re-verified the
other v0.6 edits, the split §6.1 error-state copy (F20) and the small §8/§5
clauses, for newly introduced issues, rather than trusting the changelog.

## BLOCKER

None.

## FINDING

None.

## ADVISORY

### §7.2/§3.2: Revoke-then-terminate closes the round-005 gap; the residual rests on consume being a single visible unit
- Problem: The reorder is correct. Step (1) revokes every `issued` row via the
  account-scoped index on the primary, each transition contending with consume on
  that one row; step (2) then sweeps other sessions and rotates. The safety argument
  holds **on the premise that a consume which wins its CAS makes its minted session
  durably visible as part of the same consume unit**, i.e., there is a happens-before
  from "consume wins CAS" to "session exists," and step (1) fully completes before
  step (2) begins. Under those two premises the only sessions extant when the sweep
  enumerates are from consumes that won *before* their row was revoked (hence before
  revoke-completion, hence before the sweep starts), so the sweep catches them, and no
  *new* consume can win after revoke-completion because every row is already `revoked`.
  §3.2 already frames consume as "a single atomic compare-and-set ... Only the consume
  winner mints a session," which supplies the first premise, and §7.2's "in this order"
  plus "then" supplies the second. So this is closed, but the closure is load-bearing
  on those two premises, not on the prose alone.
- Why it matters: If a future edit ever decoupled session-mint from the consume CAS
  (e.g., enqueued session creation asynchronously after the CAS), a session could
  become visible *after* the sweep enumerates yet from a consume that won *before*
  revoke-completion, re-opening exactly the F19 gap the reorder just closed. As
  written, v0.6 does not do this.
- Suggested resolution: None required for v0.6. Optionally note in §3.2 that
  session-mint is synchronous-with / part of the winning CAS unit (not a deferred
  step), to fence the future edit that would re-open F19.

### §3.1/§7.2: `revoked` remains reachable only through the full recovery-authorization gate (guardrail, carried)
- Problem: Carried from round-005. The account-scoped index makes bulk-`revoke` a
  cheap, account-wide primitive; v0.6 keeps its only trigger bound to "a successful
  recovery," and recovery initiation/verification are rate-limited and locked out
  mirroring §2.1 *and* gated by an independent channel or support-mediated identity
  check (§7.2). The strength of this subsystem therefore rests on recovery
  *authorization*, not the rate limit. v0.6 does not expose any inbox-only self-serve
  path to `revoked`.
- Why it matters: A future "revoke my other links" button gated only by inbox control
  would hand an inbox-only attacker a victim-link-killing primitive, re-opening the
  targeted-login-denial hole §2.2's no-invalidation model exists to close.
- Suggested resolution: None required. Optionally state explicitly that `revoked` is
  reachable *only* through full recovery authorization and never an inbox-only path.

## Cross-section coherence flags

- **F19 (ordering) is closed and coherent.** §7.2 now states the sequence explicitly
  ("in this order, (1) ... then (2) ..."), names *why* the order carries the property
  ("revoking first fences any further consume ... revoking *after* the sweep would
  leave that gap open"), and ties the revoke to the §3.1 account-scoped index writing
  **on the primary** (A25). Consistent with §3.2's single-row contention and with
  §7.1's end-to-end claim. No dangling reference.
- **F20 (copy split) is closed and account-existence-neutral.** §6.1 now separates
  `already used` ("a token *this user consumed*") from a distinct `revoked by recovery`
  state with its own neutral copy ("links from before your recent account recovery no
  longer work"), explicitly never labelled "used." All §6.1 states are only reachable
  *after* a valid token is presented, which already implies the account exists, so
  the split discloses nothing across the §4.0 existence boundary. The one
  enumeration-sensitive state, `rate-limited`, is still rendered only as a
  non-confirming hint, so §4.0 parity is intact. §6.1 remains the exact set §3.2 refers
  to ("the defined response in §6.1"); no dangling reference.
- **A25-A28 folded cleanly:** revoke on the primary (§7.2); `revoked` reap TTL = 7 days
  alongside consumed=7d/expired=24h, with `terminal_at` defined for revoked (§8.2);
  clock-offset warns at **≥ 3 s**, strictly below the §3.3 ≤ 5 s NTP bound, giving the
  gauge headroom to be a true leading indicator (§8.1); multi-email line added to the
  displayed §5.0 confirmation copy and consistent with §2.2/§5.0's "any of the links
  works." None of these introduced a new channel.
- **Token core re-derived from scratch:** ≥128-bit CSPRNG token, not derived from
  observable input (§3.1); hash-only at rest on a per-token hash-keyed row, index
  equality *is* the comparison so no app-level timing channel (§3.1); single atomic
  CAS consume on the linearizable primary, replay fails closed, second click loses the
  CAS (§3.2); absolute `expires_at` value comparison with a single named ≤5 s skew
  window (§3.3); session id rotated on consume, consume is POST so GET/prefetch can't
  mutate (§3.4/§6.0). Replay surface bounded by single-use + 10-min expiry + ceiling of
  5 (§2.2). No regression from any v0.6 edit.

## Summary

The two round-005 findings are both closed and *proven* against the v0.6 text, not
assumed: F19's revoke-then-terminate reorder closes the consume-in-the-gap race (the
sweep catches any session a just-in-time consume created, and post-revoke no new
consume can win), and F20's copy split stops a recovery-completing user from being told
their link was "already used," all without re-opening the §4.0 enumeration boundary.
The four folded advisories (primary-side revoke, `revoked` reap TTL, ≥3 s clock-offset
warn, multi-email confirmation copy) introduced no new attack path. The two ADVISORYs
above are forward-looking guardrails for future edits, not open defects. Another round
is **NOT** warranted on security grounds, I have nothing material to add; the design
is converged for this lens.
