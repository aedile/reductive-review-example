# Round 4: Product / UX critic

Reviewing `docs/design/magic-link-auth.md` v0.4. Fresh full read, in the perturbed
order: positive success landing (§6.0) → the multiple-valid-links user mental model
(§2.2/§3.2) → error/edge states (§6.1) → resend / "didn't get it" (§5.0) →
accessibility and trust signals (§5.1/§6.1) → recovery-enrolment (§7.2/§1).

Verification of the two carried-forward v0.3 ADVISORYs against specific v0.4 text:

- **Positive success landing (was ADVISORY, §6.0).** v0.4 §6.0 now closes with: "On
  success the user lands on the page they originally tried to reach, or a default
  home if none." This is exactly the missing happy-path destination I flagged: the
  deep-link target is preserved, with a stated default fallback. **Resolved.**
- **Recovery-enrolment friction / backfill cohort (was ADVISORY, §7.2/§1).** v0.4
  §7.2 now enforces the recovery precondition **in-scope at first sign-in**: "a
  legacy/migrated account with no recovery channel is prompted to enrol one before a
  session is established; until then it is an explicitly owned, named lockout class,
  not a silent gap." The backfill cohort that was previously a silent gap is now an
  owned, named class with a defined in-flow prompt. The enrolment gate's friction is
  acknowledged and located rather than hidden at the scope boundary. **Resolved** at
  the advisory level (the residual conversion-cost question is now an owned product
  decision, not an undocumented hole).

New-this-version surface stressed (the "up to 5 concurrent links" model, §2.2/§3.2):

- A user who doesn't see the first email and re-requests from a fresh session now
  accumulates **multiple simultaneously-valid emails** in one inbox. The key UX
  question, "which link do I click, and do the older ones still work?", resolves
  cleanly: every live link is independently single-use (§3.2), so **any** of them
  works and there is no wrong choice among live links; clicking a stale/expired one
  routes to the §6.1 "expired → send me a new link" recovery state. The model is
  more forgiving than v0.3's supersession (no "your link was killed" surprise). No
  user-facing dead-end is introduced. One small copy gap remains (ADVISORY below):
  the inbox-clutter / "you may see more than one email" expectation is never set.

Headline: both prior ADVISORYs are resolved against concrete v0.4 text, and the new
concurrent-token model is a net UX improvement that introduces no blocking or
substantive failure. One minor, deferrable copy ADVISORY remains.

---

## BLOCKER

_None._

---

## FINDING

_None. Both prior ADVISORYs are resolved against specific v0.4 text, and a fresh
full read in the perturbed order surfaced no new substantive UX failure. The new
§2.2 concurrent-token model removes the v0.3 supersession surprise without creating
a user-facing dead-end._

---

## ADVISORY

### §5.0 / §5.1: "You may receive more than one email" expectation is not set for the multi-link cohort
- Problem: §2.2 now permits up to 5 concurrently-valid links per account, and §5.0's
  resend "mints an additional token … it never invalidates a prior link." A user who
  re-requests from a fresh session (the exact path §2.2 is designed to serve) will
  find **several near-identical sign-in emails** in their inbox. Nothing in the §5.0
  confirmation copy or the §5.1 email content tells them this is expected, that any
  of the links works, or that older links remain valid until they expire. Today's
  copy ("usually within a minute; check spam/promotions") sets a *latency*
  expectation but not a *multiplicity* expectation.
- Why it matters: Multiple identical-looking auth emails is a known phishing/anxiety
  trigger ("why did I get three of these, is someone attacking my account?") and can
  drive needless support contacts, working against the §1 "lockout/support-ticket
  rate < 0.1%" bar. It is an ADVISORY, not a FINDING, because no path actually fails:
  any link works and a stale one degrades gracefully to §6.1. It is purely an
  expectation-setting / reassurance gap.
- Suggested resolution: One clause in the §5.0 confirmation surface and/or §5.1 email
  trust block, e.g. "If you requested more than once, you may see more than one
  email; any of the links will work, and using one won't break the others." This also
  reinforces the §5.1 "if this wasn't you, ignore" trust posture for the duplicate
  case.

---

## Cross-section coherence flags

- §6.0 success landing ("the page they originally tried to reach, or a default home")
  is consistent with the cross-device split in the same section (confirming device
  gets the session; a different requesting device shows "signed in on another device
you can close this tab"). The happy path and the cross-device path no longer
  leave any device-state undefined.
- §2.2 (no invalidation, ≤5 independent single-use tokens), §3.2 (consuming/expiring
  one has no effect on others), §5.0 (resend "never invalidates a prior link"), and
  §6.1 ("expired"/"already used" each route to a single "send me a new link") are
  mutually consistent end-to-end: the multi-link mental model the user could form is
  the model the system actually implements. The v0.3 resend-vs-supersession tension
  is fully dissolved.
- §4.0 uniform response and §6.1 account-existence-neutral states remain consistent;
  the §6.1 rate-limited hint is still explicitly non-enumerating, so the failure
  surface does not re-open the §4.0 enumeration channel.
- §7.2's in-scope first-sign-in enrolment prompt ("before a session is established")
  is consistent with §1's "account creation … out of scope" framing, the boundary
  is now drawn with the legacy cohort owned on the in-scope side rather than dropped.
- No contradictions found between the UX sections and the security/systems sections
  on this read.

## Summary

v0.4 resolves both carried-forward Product/UX ADVISORYs against concrete, locatable
text: §6.0 now states the positive success landing (deep-link target with default
fallback), and §7.2 now owns the legacy/no-recovery cohort as a named, in-flow
enrolment class rather than a silent scope-boundary gap. The new §2.2 "up to 5
concurrent links" model is, from a UX standpoint, a net improvement, it removes
v0.3's "your link was killed" supersession surprise and creates no user-facing
dead-end, since every live link works and a stale one degrades cleanly to the §6.1
expired state. The only residual item is one deferrable copy ADVISORY (set the
"you may receive more than one email" expectation for the multi-link cohort), which
does not block convergence. **From the Product/UX lens I have nothing material left
to add; another round is not warranted on this axis.**
