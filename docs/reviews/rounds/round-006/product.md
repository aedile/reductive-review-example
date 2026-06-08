# Product / UX — Round 006

Reviewing `docs/design/magic-link-auth.md` at **v0.6**. Fresh full read.
Perturbation honored: started from §6.1 split error-state copy and the §5.0
multi-email confirmation line, then the rest of the user surface.

## Verification of the round-005 FINDING (closed)

My round-005 FINDING was that the single **"already used"** state mislabelled a
recovery-revoked link — a user who had just completed account recovery and then
clicked an old link would read "used" as "someone else used my link" and panic.

v0.6 §6.1 splits the copy into two distinct states:

- **"already used"** is now scoped to "a token *this user consumed*."
- **"revoked by recovery"** is a *distinct* state with its own neutral copy:
  "for your security, links from before your recent account recovery no longer
  work — request a fresh one," explicitly "never labelled 'used,' which for a
  recovery-completing user would falsely read as 'someone used my link.'"

This is exactly the resolution the finding called for, and the rationale is
recorded inline. **Closed.**

Cross-checks on the new copy:
- `revoked` is reachable *only* via recovery (§3.2: "`issued → revoked`
  (terminal; only via recovery, §7.2)"), so any user who sees the "your recent
  account recovery" wording has in fact undergone a recovery on their account.
  The copy is never shown to a user for whom it is false. No new confusion
  introduced.
- The state stays account-existence-neutral (§6.1 framing), so the split does
  not re-open the §4.0 enumeration channel.

The §5.0 multi-email confirmation line is present and coherent: the confirmation
page tells the user they "may receive more than one email if they request again
and that any of the links works until it expires (so they don't hunt for 'the
latest' one)," which matches the no-invalidation model in §2.2. It preempts the
"which of these links do I click?" confusion. **Verified present.**

## BLOCKER
None.

## FINDING
None.

## ADVISORY
None.

## Cross-section coherence flags
- §6.1 ↔ §3.2 ↔ §7.2: the four+ defined error states map cleanly to the token
  state machine; `revoked` copy is gated to the only path that produces it. No
  contradictions.
- §5.0 ↔ §2.2: multi-email confirmation copy is consistent with the
  multiple-concurrent-token / "any link works" model. No dangling references.
- §6.0 ↔ §5.0: cross-device flow, confirm-then-POST consumption, "signed in on
  another device — you can close this tab," and success landing are all defined
  and mutually consistent.

## Summary
The round-005 FINDING is genuinely closed: the error-state copy is split so a
recovery-revoked link gets its own neutral "revoked by recovery" message and is
never mislabelled "already used," and the §5.0 multi-email confirmation line is
in place and coherent with the no-invalidation model. The v0.6 copy edits
introduced no new UX problem — the revoked-by-recovery wording is only ever shown
on a path that actually produced a recovery. The user surface (cross-device,
"didn't get the email," accessibility, trust signals, error/empty/edge states)
is complete with no material gap remaining. **No further round is warranted from
the Product / UX lens — I have nothing material to add.**
