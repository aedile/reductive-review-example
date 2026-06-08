# Round 005 — Product / UX review of magic-link-auth.md (v0.5)

Fresh full read. Started from the multi-email expectation and the user's mental
model (multiple valid links; the revoked-by-recovery "already used" state), then
error/edge states, resend, accessibility/trust.

## BLOCKER

_None._

## FINDING

### §6.1 — "Already used" copy mislabels a link the user never used (new v0.5 edit)

- Problem: v0.5 folded the new `revoked` state into the existing **"already used
  (consumed or revoked-by-recovery)"** bucket, served by one piece of copy. But
  these are two different user realities. A link a user *consumed* truly was "used."
  A link *revoked by recovery* was never used by this user — it was killed as a
  side effect of the account-recovery they just performed (§7.2 invalidates all
  live tokens). Telling that user "this link was already used" is factually wrong
  from their vantage point, and in a recovery context it reads as **"someone else
  used my link"** — the single most alarming possible message right after a
  security event.
- Why it matters: The user most likely to click a stale original-email link
  *after* recovery is the user who just did recovery (they had two emails open —
  the recovery flow and the original sign-in link). For that exact user, "already
  used" implies compromise and predictably generates a support contact — the
  precise outcome §1's `lockout/support-ticket rate < 0.1%` success metric exists
  to suppress. The doc collapses two states with materially different correct copy
  into one string for terseness, and the merged string is wrong for the revoked
  case.
- Suggested resolution: Separate the copy (the state machine already distinguishes
  `consumed` from `revoked`, §3.2, so no new state is needed). For the
  revoked-by-recovery case, say something like "For your security, links from
  before your recent account-recovery no longer work — request a fresh one," with
  the same "send me a new link" action. Keep account-existence neutrality: this
  copy is only reachable by presenting a real (now-revoked) token, so it does not
  reopen §4.0 enumeration. If the author insists on a single string, it must at
  minimum **not** assert "used"; "no longer valid — get a new link" is neutral to
  both sub-cases. As written, "already used" is the wrong word for half the states
  it covers.

## ADVISORY

### §5.0 — Multi-email expectation is in the spec but not yet in the user-facing copy

- Problem: This is the residual of round-004's advisory. v0.5 correctly records
  internally that a user "may receive **more than one email**" (§2.2) and that
  resend "never invalidates a prior link" (§5.0). But the **displayed** copy on the
  confirmation page (§5.0) still only sets a latency/spam expectation and offers
  resend/re-enter — it does not tell the user that re-requesting produces an
  *additional* working link and that **any** of the links they receive will work.
- Why it matters: A user who clicks resend (or requests from a second device) now
  has 2+ emails in their inbox. Without a "you may receive more than one link — any
  of them works" cue, the natural mental model is "the new one supersedes the old —
  I must use the latest," and a user who clicks the older email gets a *valid*
  login but with lingering doubt, or hunts for "the right" email. This is mild
  confusion, not a failure (the link still works), which is why it stays ADVISORY —
  but it is the unfinished half of the prior round's note: the mechanism changed,
  the copy didn't catch up.
- Suggested resolution: Add one line to the §5.0 confirmation/resend copy, e.g.
  "Requested more than once? You may get more than one email — any of the links
  will work until it expires." This closes the loop between §2.2's mechanism and
  what the user sees.

## Cross-section coherence flags

- §3.2 ↔ §6.1: §3.2 keeps `consumed` and `revoked` as distinct terminal states and
  says verifying a terminal token "returns the defined response in §6.1." §6.1 then
  *merges* `consumed` and `revoked` into one user-facing "already used" string. The
  state machine distinguishes them but the UX flattens them — that is the FINDING
  above; the dangling expectation is that §6.1 honor the distinction §3.2 preserves.
- §2.2 ↔ §5.0: internally consistent (multi-email + non-invalidating resend), but
  neither §2.2 nor §5.0 surfaces that fact in displayed copy — the ADVISORY above.
- No contradictions found in cross-device flow (§6.0), trust signals/accessibility
  (§5.1, §6.1), rate-limited rendering (§6.1/§4.0), or wrong-account handling.

## Summary

The only material UX item is the FINDING: the v0.5 edit that folded the new
`revoked` state into the existing "already used" copy mislabels, for the
recovery-completing user, a link they never used — exactly the cohort §1's
support-ticket metric targets. The multi-email mental-model gap from round 004 is
partly closed (spec acknowledges it) but the user-facing copy still doesn't, so it
remains as one ADVISORY. Because an open FINDING stands, **another round is
warranted** — I do not yet have nothing material to add; the FINDING needs one copy
split (or a neutral re-word) before this critic converges.
