# Skeptical Generalist — round-001

Document: `docs/design/magic-link-auth.md` @ v0.1

## FINDING

### §1 — No account-recovery / lockout story
- Problem: The entire scheme rests on the user receiving email, and nothing
  addresses what happens when they lose access to that inbox.
- Why it matters: Email is the single point of failure. With passwords there's a
  reset; here, lose the inbox and you lose the account forever, with no owner for
  the recovery path.
- Suggested resolution: Name the lockout case explicitly and delegate recovery
  (second channel or support-mediated check) — even if recovery itself lives
  elsewhere, the dependency must be stated, not assumed away.

## ADVISORY

### §1 — No stated threat model
- Problem: The doc never says what it defends against or what it concedes. The
  biggest concession — "we trust whoever controls the inbox" — is left implicit.
- Why it matters: Without a stated boundary, every reviewer re-derives the trust
  root and reasonable concessions read as oversights.
- Suggested resolution: State the threat model and name the inbox as the explicit
  trust root and out-of-scope assumption.

## Cross-section coherence flags
- §1 promises "no passwords" as the goal but never states the cost: the inbox
  becomes the sole credential. The goal and the (missing) threat model disagree
  about how much trust the email channel is carrying.
- The seam nobody owns: security assumes product handles "lost access," product
  assumes security does, and the doc assigns it to neither.

## Summary
The premise (passwordless) is defensible, but the design quietly bets everything
on the email channel without ever saying so or owning the lockout case. **Another
round is warranted** — start by writing down the bargain you're making.
