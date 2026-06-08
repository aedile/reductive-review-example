# Round 004 — Skeptical Generalist

Fresh full read of `magic-link-auth.md` v0.4. Perturbed entry order: legacy-account /
out-of-scope enforcement → recovery-channel independence → premise/scope & success bar →
inter-lens seams. Primary task: honestly re-test my two round-003 FINDINGs and try to
re-open them.

## Re-test of round-003 FINDINGs (did v0.4 actually close them?)

**(1) Lockout invariant enforced inside out-of-scope account-creation + silent on legacy
accounts — CLOSED.** v0.4 §7.2 no longer hides the obligation inside a process it has
disclaimed. It does two distinct things and names both: (a) states the import as a *hard
contract* — "account creation MUST reject creating an account without a recovery channel,
and this design does not function safely otherwise" — and (b) closes the legacy gap
*in-scope*: "a legacy/migrated account with no recovery channel is prompted to enrol one
**before a session is established**; until then it is an explicitly owned, named lockout
class, not a silent gap." §1 also now surfaces the precondition import explicitly ("this
design depends on a precondition it imports from it — see §7.2") rather than leaving it
buried. The previously-silent population (legacy accounts) is now owned at a concrete
enforcement point. I cannot re-open this as a FINDING; the residual is the *enrolment
ceremony*, demoted to ADVISORY below.

**(2) Lost-tab / new-session composition seam — CLOSED.** This was a seam created by the
v0.3 "single live token + supersession" model: re-requesting from a fresh session
contradicted either victim-protection or new-device support. v0.4 §2.2 deletes
supersession entirely — "A new request **never invalidates an existing token**," up to 5
"independently single-use" tokens coexist — and states the exact composition outcome: "a
user who re-requests from a fresh session simply gets an additional working link," while
"a third party cannot kill a victim's link." §3.2 confirms "There is no supersession …
Tokens are independent: consuming or expiring one has no effect on the others." The two
horns that made this a contradiction are gone by construction. No residual at FINDING
level.

Both prior findings are genuinely resolved against specific, load-bearing text — this is
not a collapse-to-zero by fatigue. What remains are ADVISORYs only.

## BLOCKER

_None._

## FINDING

_None._ The seams I probed hardest — legacy enrolment authority, recovery-channel
independence at enrolment, and the cap-vs-rate-limit interaction — each resolve inside an
explicitly stated boundary (the §7.1 trust root or the §2.1 limiter) rather than falling
through it. I could not manufacture a material gap without contradicting the doc's own
stated scope.

## ADVISORY

### §7.2 — Authority held during legacy first-sign-in enrolment is left implicit
- Problem: The legacy fix enrols a recovery channel "before a session is established."
  At that moment the user has proven exactly one factor — inbox control — and holds no
  session. The doc does not say what authenticates the enrol-and-verify step, nor that an
  attacker controlling a legacy inbox could enrol *their own* independent channel during
  this window.
- Why it matters: A reader could mistake "independent recovery channel" for protection
  against inbox compromise. It is not, here: enrolment is gated only by inbox control, so
  recovery independence buys nothing for a legacy account whose inbox is already owned at
  first sign-in.
- Suggested resolution: One sentence in §7.2 noting that legacy enrolment authority is
  inbox-control only and therefore inherits the §7.1 trust root (inbox compromise is
  out of scope) — making the boundary explicit rather than inferred. No mechanism change.

### §2.2 / §2.1 — The "5 concurrent" cap may be unreachable given the rate limit + expiry
- Problem: §2.2 caps concurrent live tokens at 5, but §2.1 allows ≤3 mints per address
  per 15 min and §3.2/§3.3 expire tokens at 10 min. With coalescing of in-flight sends,
  it is not obvious any address can actually hold 5 simultaneously-live tokens.
- Why it matters: A cap that the limiter + expiry already make unreachable is dead text;
  a future reader may tune one constant without seeing it can never bind. Harmless today,
  but it muddies which control is actually bounding the replay surface.
- Suggested resolution: Either state that the cap is a belt-and-suspenders ceiling the
  rate limit normally keeps slack, or reconcile the two constants so the binding control
  is unambiguous. Defer-able.

## Cross-section coherence flags
- Expiry value is now consistent across §2.2 ("10-minute expiry"), §3.2 ("expire 10
  minutes after mint"), §3.3 ("mint time + 10 min"), and §5.1 email copy ("expires in 10
  minutes"). No dangling state-machine references: §3.2's "defined response" resolves to
  §6.1, and §6.1 confirms "This set is the response §3.2 refers to."
- §1's success/abandon bar and §7.2's recovery design are now mutually load-bearing: the
  lockout/support-rate metric (<0.1%) explicitly gates a recovery-path review, so the
  metric that measures the recovery design actually triggers action. No contradiction.
- §7.1 defenses table maps each adversary to a section (recovery abuse → §7.2; the
  inbox-controlling attacker is an *accepted assumption*, not a defended-against one),
  and §7.2 holds the recovery path "to the primary-path bar … so §7.1's claims hold
  end-to-end." The lenses agree on who owns the inbox-compromise boundary; it no longer
  falls between security and recovery.

## Summary
v0.4 closes both of my round-003 FINDINGs against specific text: the legacy/out-of-scope
lockout class is now explicitly owned and enforced in-scope at first sign-in (§7.2/§1),
and the lost-tab/new-session composition seam is dissolved by dropping supersession for
independent single-use tokens (§2.2/§3.2). I tried to re-open both and could not without
contradicting the doc's own stated boundaries. Two ADVISORYs remain (implicit enrolment
authority; a possibly-unreachable concurrency cap), neither of which blocks trust in the
document. **I have nothing material to add and do not believe another round is warranted
from my lens; the two residual ADVISORYs may be deferred.**
