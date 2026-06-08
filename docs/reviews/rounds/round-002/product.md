# Product / UX — round-002

Document: `docs/design/magic-link-auth.md` @ v0.2
(Prompt perturbed this round: "didn't get the email" moved to the top of the list.)

## FINDING

### §5.0 — No "I didn't get the email" path
- Problem: Delivery is still assumed (§5.0). No resend, no latency expectation, no
  spam guidance. (Same section as the Systems finding; one fix serves both.)
- Why it matters: "Nothing arrived" is the most common magic-link support ticket;
  with no path the user is simply stuck and we never learn it failed.
- Suggested resolution: Rate-limited resend, "arrives within a minute, check spam,"
  and a neutral failure message.

## ADVISORY

### §6.0 — Cross-device guidance still thin
- Problem: §6.0 still describes only single-device click-and-login; the
  phone→laptop case isn't stated.
- Why it matters: It very likely *works* (the token carries the authority), so this
  is no longer a correctness blocker — but an unguided user who switches devices is
  left unsure it worked.
- Suggested resolution: One sentence stating login completes in whatever browser
  opens the link, surfaced on the confirmation page.
- **Re-grade note:** raised as a FINDING in round-001; downgraded to ADVISORY on a
  fresh read now that the security BLOCKERs are closed and the core flow is sound.

### §6.1 — Error/empty/edge + accessibility states still undefined
- Problem: §6.1 is unchanged; the unhappy-path states and the a11y bar are still
  unspecified.
- Why it matters: Real, but the happy path is coherent, so this reads as a quality
  gap rather than a trust blocker at v0.2.
- Suggested resolution: Enumerate states with neutral copy; commit to WCAG AA with
  a plain-text email fallback.
- **Re-grade note:** also a round-001 FINDING, downgraded to ADVISORY this round.

## Cross-section coherence flags
- §4.0's uniform response is good for security but means the typo'd-address user
  gets no "did you mean…"; acceptable, but note the trade-off.

## Summary
The one material UX gap left is the delivery/"didn't get it" path (§5.0); the
device and error-state items are now quality advisories. **One more round
warranted** — and the arbiter should sanity-check my two downgrades.
