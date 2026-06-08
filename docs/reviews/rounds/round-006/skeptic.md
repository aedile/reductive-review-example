# Skeptical Generalist: Round 6

Fresh full read of `magic-link-auth.md` v0.6. Per this round's perturbation I
started from the v0.6 deltas (recovery reordering §7.2, split revoked copy §6.1,
the small §8.1/§8.2 clauses) and checked each for a *new* seam before sweeping
premise/scope, the success bar, and recovery soundness one final time.

## BLOCKER

None.

## FINDING

None.

## ADVISORY

### §7.2 / §6.1: "revoke before sweep" leaves a sub-skew window where the recovering user's own fresh link can be self-revoked, but the copy still reads correctly

- Problem: Recovery (1) revokes all `issued` tokens, then (2) terminates other
  sessions and rotates. If the recovering user requested a *new* magic link
  moments before completing recovery (e.g. the "request a fresh one" affordance
  from a revoked-link error in §6.1), that fresh token is `issued` and will be
  swept to `revoked` by step (1). The user then clicks their just-requested link
  and correctly lands on the §6.1 "revoked by recovery" copy, which is the
  *right* security outcome (no link minted before recovery completes should
  survive) but produces a "request another link, again" loop the doc does not
  name as an expected, benign state.
- Why it matters: Purely a UX edge, not a security or correctness gap, the
  ordering is exactly what §7.2 intends and the split copy from the v0.6 edit
  handles the labelling correctly, so no mislabelling seam was introduced. It is
  worth a one-line acknowledgement that the first post-recovery link request is
  the clean path, not the immediately-pre-recovery one.
- Suggested resolution: Optional. Add half a sentence to §7.2 or §6.1 noting that
  links requested before recovery completed are intentionally revoked and the
  user should request a fresh one *after* recovery; defer if word budget is tight.

## Cross-section coherence flags

- §7.2 ordering vs §3.2 CAS contention: the revoke step "each row's transition
  contending with consume on that one row" is consistent with §3.2's per-row
  hash-keyed CAS on the primary. Revoke and consume race on the same single row;
  whichever wins, the other fails closed. No seam, the two sections describe the
  same atomic primitive from two directions and agree.
- §6.1 revoked copy vs §3.2 terminal-state contract: §3.2 routes any terminal
  state to §6.1; §6.1 now enumerates `revoked by recovery` as a distinct state.
  The v0.5 dangling-state risk is fully closed; no new dangling reference.
- §8.2 revoked reap (7 days) vs §8.2 tombstone: a token revoked before its 10-min
  `expires_at` is reaped at 7 days, well past `expires_at` + replay window, and
  its tombstone (hash + state + `terminal_at`) keeps a post-revoke replay
  classifiable. The `terminal_at` definition explicitly covers `revoked`.
  Consistent.
- §8.1 clock-offset warn (≥3 s) vs §3.3 skew bound (≤5 s): warn strictly inside
  the tolerated bound, so a drift that would corrupt `now() ≥ expires_at` is
  caught with headroom. No seam between the observability and expiry lenses.
- Premise/scope (§1) vs recovery (§7.2): §1 names the lockout class, the success
  bar gates a recovery-path review on the lockout/support metric, and §7.2 owns
  the precondition imported from out-of-scope account creation and enforces it
  in-scope at first sign-in. The seam the generalist exists to find, recovery as
  the case no specialist owns, is explicitly assigned and instrumented. Nothing
  falls between security, systems, and product here.

## Summary

The three v0.6 edits (recovery reordering, split revoked copy, the §8 clauses)
are internally consistent and introduced no new seam; the reordering closes the
prior gap without opening another, and the split copy resolves the mislabelling
cleanly. Premise, success bar, and recovery soundness all survive a fresh
adversarial pass, the only residual item is one benign UX edge re-graded to
ADVISORY (deferrable). I have nothing material to add and another round is not
warranted; I report convergence.
