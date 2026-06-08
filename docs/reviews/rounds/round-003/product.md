# Round 3: Product / UX critic

Reviewing `docs/design/magic-link-auth.md` v0.3. Fresh full read, in the perturbed
order: cross-device confirm flow (§6.0) → error/edge states (§6.1) → the "didn't get
the email" path (§5.0) → accessibility and trust signals (§5.1/§6.1).

Verification of the six carried-forward UX items (delivery recourse, error/edge
states, accessibility, trust signals, cross-device, success copy), each against the
specific v0.3 text:

- **Error/edge states (was BLOCKER).** §6.1 now enumerates expired, already used
  (consumed or superseded), malformed/unrecognized, rate-limited, and wrong-account,
  each "with plain-language copy and a single 'send me a new link' action," and
  closes §3.2's dangling reference ("This is the response §3.2 refers to"). The state
  machine no longer points at empty space. **Resolved.**
- **"Didn't get the email" path (was BLOCKER).** §5.0 now states a latency
  expectation ("usually within a minute; check spam/promotions"), a resend control
  "gated to the §2.1 limits and coalesced per §2.2," a "wrong address? re-enter it"
  affordance, and a send-failure surface ("we couldn't send your link right now").
  All four sub-items I called for are present and cross-consistent. **Resolved.**
- **Cross-device + scanner pre-fetch (was FINDING).** §6.0 requires a deliberate
  gesture: GET only *presents* a "Confirm sign-in" page, a POST consumes; pre-fetch
  cannot burn the token; the confirming device gets the session; the requesting
  device shows "signed in on another device, you can close this tab." This closes
  F4 concretely rather than restating it. **Resolved.**
- **Accessibility (was FINDING).** §5.1 multipart with a plain-text part whose link
  is "a full, readable URL, never a bare 'click here'"; §6.1 WCAG 2.1 AA, contrast,
  keyboard focus order, focus moved to result heading on error/success, no
  color-only state. **Resolved.**
- **Trust / anti-phishing signals (was FINDING).** §5.1 consistent from-name, single
  first-party link domain (no redirector/tracking wrappers), SPF/DKIM/DMARC as a
  delivery requirement, visible expiry, "if this wasn't you, ignore," and "we will
  never ask for your password." **Resolved.**
- **Success / step copy (was FINDING).** Request → confirmation (§5.0) → confirm
  gesture (§6.0) → cross-device close-tab message (§6.0) → error states (§6.1) are
  now each given copy or a defined surface. Largely resolved; one residual gap on the
  *positive* success landing (ADVISORY below).

The two prior ADVISORYs: the rate-limited hint is now in §6.1; the recovery-enrolment
UX cost is acknowledged in §1's scope framing but its conversion/backfill UX is still
not addressed (re-stated as ADVISORY below).

Headline: every prior BLOCKER and FINDING is genuinely resolved with specific,
locatable text, not a flag. The user-facing surface now describes a usable product.
What remains is two ADVISORYs, a defined-but-unspecified positive success landing,
and the unaddressed recovery-enrolment friction, neither of which is ship-stopping.

---

## BLOCKER

_None. Both prior BLOCKERs (§6.1 error states, §5.0 delivery recourse) are resolved
in v0.3 with concrete, cross-referenced text._

---

## FINDING

_None. All five prior FINDINGs are resolved against specific v0.3 text (see
verification above). No new material FINDING surfaced on a fresh full read._

---

## ADVISORY

### §6.0: Positive success landing (what the confirming device lands on) is still unspecified
- Problem: §6.0 defines the cross-device *split* well: the confirming device gets the
  session, the requesting device gets "signed in on another device, you can close
  this tab." But it does not say what the confirming device lands on after the POST
  succeeds, the originally-requested ("deep link") destination, or a default
  account home. Every failure/edge state in §6.1 now has copy, yet the single most
  common outcome (a successful same-device sign-in) has no stated landing.
- Why it matters: This is the success-copy item, and it is the one step still left to
  the implementer. A user who clicked the link to reach a specific page (the typical
  reason they were asked to sign in) will be dropped on whatever default the
  implementer happens to pick, losing their intended destination, measurable against
  the §1 "median time-to-logged-in < 60 s" bar. It is an advisory, not a finding,
  because the recovery surfaces are all defined; only the happy-path destination is
  unstated.
- Suggested resolution: One sentence in §6.0: on successful consume, land the user on
  the originally-requested destination if one was carried through the flow, else a
  stated default; confirm the deep-link target is preserved across the
  request→email→confirm round-trip (and note that the email link must therefore carry
  or reference that return target).

### §7.2 / §1: Recovery-enrolment friction and the pre-existing-account cohort still not addressed as a UX concern
- Problem: §7.2 makes a recovery method "mandatory at account creation, no account
  exists without one." This correctly closes the lockout hole (a security/systems
  win), but the UX consequence I raised before is still not addressed: forcing a
  second verified channel at signup adds first-interaction friction with conversion
  cost, and the doc says nothing about accounts that predate this requirement (the
  backfill cohort) or whether enrolment is blocking vs. promptable. §1 scopes account
  creation as "out of scope," which is a reasonable boundary but also means this UX
  cost is now neither owned here nor anywhere visible.
- Why it matters: A hard gate at signup is a product decision with drop-off
  consequences, and a backfill cohort with no recovery channel is a population that
  the §7.2 "no account without one" invariant silently doesn't cover. Advisory
  because it sits at the §1 scope boundary and does not invalidate the auth flow
  itself.
- Suggested resolution: A single clause stating that enrolment-flow UX and the
  migration/backfill path for pre-existing accounts are owned by the (out-of-scope)
  account-creation spec, and that §7.2's invariant is enforced for that cohort via a
  defined backfill prompt, so the boundary is explicit rather than a silent gap.

---

## Cross-section coherence flags

- §5.0's resend control is stated as "gated to the §2.1 limits and coalesced per
  §2.2," and §2.2 supersession is "scoped to the originating session." These are now
  mutually consistent: a user's own resend carries the originating session and so
  coalesces to the in-flight link rather than stacking, the prior
  resend-vs-idempotency contradiction is closed.
- §6.0 (deliberate POST-to-consume, GET only presents) and §3.2/§3.4 (atomic consume,
  POST consumption, no bare-GET mutation) now agree: the UX gesture and the state
  machine describe the same single consume step. No dangling reference remains; §6.1
  explicitly states "This is the response §3.2 refers to."
- §4.0 uniform response and §6.1 account-existence-neutral error states are
  consistent, the error pages do not leak account existence, and the §6.1
  rate-limited hint is explicitly "non-enumerating," preserving the §4.0 posture into
  the failure surface. The prior §4.0-vs-§5.0 dead-end-for-a-typo trap is closed by
  the §5.0 "wrong address? re-enter it" affordance.
- No contradictions found between the UX sections and the security/systems sections
  on this read.

## Summary

v0.3 resolves every prior Product/UX BLOCKER and FINDING with specific, locatable
text rather than a flag: §6.1 now defines all error/edge states and closes §3.2's
dangling reference; §5.0 supplies the full "didn't get the email" recourse; §6.0
defines the cross-device deliberate-consume flow defeating scanner pre-fetch; and
§5.1/§6.1 supply trust signals and WCAG 2.1 AA accessibility for both email and
pages. The collapse to zero BLOCKER/FINDING is earned, not a rubber-stamp, each
resolution is pinned to text above. Only two non-blocking ADVISORYs remain (the
positive success landing in §6.0 and the recovery-enrolment friction/backfill cohort
at the §1/§7.2 boundary), neither of which blocks convergence. **From the Product/UX
lens I have nothing material left to add; another round is not warranted on this
axis.**
