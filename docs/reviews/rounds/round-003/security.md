# Security Adversary — Round 003

Fresh full read of magic-link-auth.md v0.3. Re-derived from the recovery path and
enumeration/timing first, then interception and the consume mechanism, then the
token/session core last — not from the changelog.

## BLOCKER

None.

The three round-002 BLOCKERs are genuinely closed, re-derived against v0.3 text:

- **Recovery/lockout (was: unaddressed → takeover or dead-end lockout).** §7.2 now
  makes a recovery method *mandatory at account creation* ("no account exists without
  one"), so there is no lockout-by-omission; rate-limits *initiation and verification*
  "mirroring §2.1," so the recovery channel can't be brute-forced or used as an
  unbounded takeover oracle; requires "defined, replay-resistant identity evidence" for
  the support-mediated path, closing the static-data social-engineering route at spec
  altitude; and on success "rotates the session and invalidates all live login tokens,"
  so a recovery can't be chained into a live victim token. The §7.1 defense map now
  routes "recovery abuse → §7.2," so the claim closes end-to-end.
- **Single-live-token invariant (was: idempotency asserted without a state).** §3.2 now
  defines a real `issued → superseded` terminal state, and §2.2/§3.2 serialize consume
  vs supersede as competing atomic CAS steps "contending on the same account-keyed row"
  with the loser failing closed and only the consume winner minting a session. Re-derived:
  two concurrent verifications cannot both mint sessions, and a stale superseded token
  cannot mint one at all.
- **Error/edge states (was: §3.2 referenced a response that didn't exist).** §6.1 now
  enumerates the account-existence-neutral terminal-state responses (expired, already
  used, malformed, rate-limited, wrong-account); §3.2's "defined response in §6.1" now
  resolves.

## FINDING

None.

Re-derived each round-002 FINDING and confirmed closure in v0.3 text:

- Timing parity (§4.0): now produced by a *mechanism* — all account-dependent work
  (mint, supersession, send-enqueue) is async off the request path — not merely asserted.
- Targeted login-denial (§2.2): supersession is scoped to the originating session, so a
  third party cannot kill a victim's delivered link or burn their budget.
- Delivery (§5.0): bounded rate-limited queue, async workers, classified bounces, bounded
  retry, dead-letter into §8.
- Scanner pre-fetch (§6.0): consume is a POST behind a deliberate gesture; GET only
  presents; the §8.1 `send-failures` counter is no longer dormant.
- Token-lookup timing (§3.1): hash-only persistence with index equality as the compare —
  no application-level plaintext compare, so no app-level timing channel.
- Clock authority (§3.3): single datastore clock stamps and checks; the self-contradictory
  v0.2 ±60 s grace is removed, so there is no skew/grace window to exploit.

## ADVISORY

### §7.2 — Recovery rotates the actor's session but does not state it terminates *other* live sessions
- Problem: §7.2 says a successful recovery "rotates the session and invalidates all live
  login tokens." That covers the recovering actor's own session and all outstanding
  *tokens*, but it does not explicitly say it terminates *other already-established
  sessions*. Against the §7.1 "shared/public-device attacker" — who may already hold a
  live session, not just a token — a legitimate recovery would rotate the victim's new
  session yet leave the attacker's pre-existing session live.
- Why it matters: recovery is the user's "kick everyone out and take back the account"
  lever; if it only kills tokens and the actor's own session, an attacker who already
  converted a token into a session survives the recovery. This is the residual edge of
  the otherwise-closed recovery-takeover path, hence advisory not blocker.
- Suggested resolution: extend §7.2 to "invalidates all live login tokens **and all other
  live sessions for the account**," consistent with the existing session-rotation
  primitive in §3.4.

### §4.0 — The account-existence check itself is not explicitly placed off the synchronous path
- Problem: §4.0 argues timing parity because "all account-dependent work (token mint,
  §2.2 supersession, send enqueue) happens asynchronously off the request path." Deciding
  whether to do that work still requires an account-existence lookup. The spec lists the
  *consequences* (mint/supersede/enqueue) as async but does not explicitly say the
  existence determination is also off the synchronous response path.
- Why it matters: if the existence check ran synchronously and its result branched the
  synchronous code (e.g., enqueue-or-not, or a cache hit/miss difference), a residual
  timing channel could re-enumerate accounts despite the uniform message. The current
  wording is in the right spirit but leaves this implicit.
- Suggested resolution: state in §4.0 that the synchronous handler performs *no*
  account-dependent branching — the existence lookup and all downstream work occur on the
  async path — so the synchronous response is constant-time by construction, not just
  constant-message.

## Cross-section coherence flags

- None. §3.2's "defined response in §6.1" resolves; §7.1's defense map references
  (§3.1/§3.2/§4.0/§2.1/§3.4/§7.2) all point at sections that now contain the claimed
  mechanism; §8.1's `send-failures` counter is correctly reconciled with §5.0 now
  defining the failure surface; the §3.3 clock-authority text and the removal of the
  v0.2 ±60 s grace are internally consistent.

## Summary

v0.3 closes all three round-002 BLOCKERs and every round-002 FINDING, verified by
re-deriving against the current text rather than the changelog: recovery is now mandatory,
rate-limited, identity-evidenced, and token-invalidating (§7.2); the single-live-token
invariant has a real `superseded` state with same-row CAS serialization (§2.2/§3.2); and
the error-state response §3.2 depends on now exists (§6.1). The two residuals are genuine
but deferrable — recovery doesn't explicitly kill *other* live sessions (§7.2), and §4.0
places the work but not the existence *check* off the synchronous path — both advisory.
I have no BLOCKER or FINDING to add; from the security lens this document has converged
and another security round is **not** warranted.
