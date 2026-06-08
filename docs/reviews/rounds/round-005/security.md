# Security Adversary: Round 005 (target: magic-link-auth.md v0.5)

Fresh full read of v0.5. Per the round perturbation I started from the new
`account_id` secondary index, the `revoked` state, and bulk-revoke (§3.1/§3.2/§7.2),
then the linearizable-CAS clause (§3.2), then re-derived enumeration/timing and the
token core from scratch rather than trusting the changelog.

## BLOCKER

None.

## FINDING

None.

## ADVISORY

### §3.1/§7.2: Account-scoped index is a bulk-revoke lever; confirm it is gated, not just rate-limited
- Problem: The new `account_id` secondary index makes "move every `issued` row for
  the account to `revoked` in one operation" cheap. The doc binds the *trigger* to
  "a successful recovery," and §7.2 rate-limits and locks out recovery initiation/
  verification "mirroring §2.1." That is sufficient to stop a third party who lacks
  the independent recovery channel. The residual note is only that the strength of
  this whole subsystem now rests entirely on recovery *authorization* (the second
  independent channel or the support-mediated check), not on the rate limit, a rate
  limit alone would merely slow a bulk-revoke DoS, not prevent it.
- Why it matters: If a future edit ever let bulk-revoke fire on anything weaker than
  full recovery auth (e.g., a "revoke my other links" self-serve button gated only
  by inbox control), it would hand an inbox-only attacker a victim-link-killing
  primitive, re-opening exactly the targeted-login-denial hole that §2.2's
  no-invalidation model was built to close. As written, v0.5 does not do this; the
  trigger is correctly bound to recovery. This is a guardrail note, not a defect.
- Suggested resolution: None required for v0.5. Optionally, state explicitly that
  `revoked` is reachable *only* through the full recovery-authorization gate and
  never through an inbox-only self-serve path, to fence off the future edit.

### §3.1/§8.2: Secondary index does not store plaintext tokens (confirmed; note for durability)
- Problem: The `account_id` index references the same per-token rows, which persist
  only the token *hash* (§3.1), so compromise or accidental logging of the index
  yields no usable tokens, and §8.2 already forbids logging raw tokens. Nothing to
  fix; recorded so a later schema change that denormalizes a plaintext token onto the
  index row would be caught.
- Why it matters: The whole at-rest story depends on "hash only, everywhere a token
  is referenced." The new index is a second place tokens are referenced.
- Suggested resolution: None. v0.5 is consistent.

## Cross-section coherence flags

- `revoked` state is coherent end to end: introduced §3.2 (terminal, recovery-only),
  surfaced to users as "already used" in the account-existence-neutral set §6.1,
  reaped/tombstoned with `terminal_at` defined for revoked in §8.2, and produced by
  the §7.2 bulk operation. No dangling reference.
- Linearizable-CAS clause (§3.2) is consistent with the stale-replica presentation
  path (§6.0) and the single-row contention claim (§3.1): lookup and transition
  contend on one hash-keyed row on the primary; a replica GET only presents and
  cannot mint a session. No contradiction.
- The §3.1 "primary verify is by hash only; the account-scoped index exists solely
  for recovery enumeration" split is internally consistent and does not re-open a
  timing/enumeration channel, the index is never consulted on the synchronous
  request or verify path. Consistent with §4.0.
- Live-token bound: §2.2 attributes the bound to §2.1 with a hard ceiling of 5 as a
  belt-and-suspenders guard, and §3.2 keeps tokens independent (no supersession).
  The targeted-login-denial closure from v0.4 is preserved.

## Summary

I re-derived the token core (≥128-bit CSPRNG, hash-at-rest, atomic single-use CAS,
absolute 10-min expiry, ≤5 s named NTP bound), the enumeration/timing surface (async
off-path lookup §4.0, non-enumerating rate-limited hint §6.1, off-path coalescing
§2.2), and the v0.5 additions (account-scoped index, `revoked` state, linearizable
CAS, recovery-triggered bulk-revoke) from scratch. The v0.5 edits close the
round-004 post-recovery-foothold finding without opening a new attack path: bulk-
revoke is correctly bound to full recovery authorization, the index stores only
hashes, and the linearizable-CAS clause closes the read-replica race rather than
creating one. Two ADVISORYs above are guardrail notes for future edits, not open
defects. Another round is NOT warranted on security grounds, I have nothing
material to add; the design is converged for this lens.
