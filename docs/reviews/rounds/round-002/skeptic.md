# Skeptical Generalist — round-002

Document: `docs/design/magic-link-auth.md` @ v0.2
(Prompt perturbed this round: premise question moved last, boundary questions first.)

## ADVISORY

### §1 — Recovery/lockout and threat model still unstated
- Problem: v0.2 hardened the mechanism but still never writes down the bargain: the
  inbox is the sole credential, and there is still no owner for the
  lost-email-access lockout case. The threat model remains implicit.
- Why it matters: A reader still can't tell which omissions are deliberate
  concessions and which are oversights, and a locked-out user still has nowhere to go.
- Suggested resolution: State the threat model (name the inbox as the trust root and
  out-of-scope assumption) and add a delegated recovery/lockout story.
- **Re-grade note:** the recovery/lockout half was a FINDING in round-001; I'm
  downgrading the merged item to ADVISORY because nothing in v0.2 made it worse and
  the mechanism is now sound. Flagging it for the arbiter — this is exactly the kind
  of quiet downgrade that lets a real gap slip.

## Cross-section coherence flags
- §1's "no passwords" goal and the (still missing) §7 threat model continue to
  disagree about how much trust the email channel silently carries.

## Summary
The premise holds and the mechanism is much stronger, but the design still hasn't
written down its central assumption or owned the lockout case. **One more round
warranted** — and I'd treat my own downgrade with suspicion.
