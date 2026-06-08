# Skeptical Generalist — Round 003

Target: `docs/design/magic-link-auth.md` (v0.3)

Fresh full read, perturbed order: started from the success criteria / acceptance
bar, then recovery-path soundness, then premise/scope, then the seams between
lenses. My standing job is the boundaries nobody owns and the assumptions the
specialists each assume someone else checks.

## Disposition of my prior round-002 BLOCKER (honest re-open attempt)

Prior BLOCKER: §7.2 recovery enrolment was conditional ("an account *needing* a
fallback **must** enrol"), so the default user who never enrolled was still
lockable-out by construction — the headline round-001 lockout, named but not closed.

v0.3 §7.2 now reads: a recovery method "is **mandatory at account creation** — no
account exists without one — so the default user is not lockable-out by omission."
The conditional "needing a fallback" language is gone; this adopts my suggested
resolution (a) verbatim in intent. I tried to re-open the by-omission lockout and
**cannot**: under this text there is no account without a recovery channel, so the
omission case it described no longer exists. The threat-model gap I raised as a
FINDING is also addressed: §7.2 rate-limits recovery initiation/verification
mirroring §2.1, requires "defined, replay-resistant identity evidence" for
support-mediated recovery, logs/alerts it (§8), rotates the session and invalidates
all live tokens on success, and holds the path "to the same bar as the primary
path"; §7.1 adds the recovery-targeting adversary and the `recovery abuse → §7.2`
defense mapping. **I am releasing the BLOCKER.** What remains is an enforceability/
ownership seam (below), which is a FINDING, not the old ship-stopper.

## BLOCKER

None. The round-002 BLOCKER is genuinely closed, not merely renamed.

## FINDING

### §7.2 / §1 — The lockout fix is enforced entirely inside a process §1 declares out of scope
- Problem: The single load-bearing sentence that closes the lockout BLOCKER is "a
  recovery method ... is **mandatory at account creation** — no account exists
  without one." But §1 lists "account creation" under **Out of scope**. So the
  invariant the whole §7 recovery story rests on ("no account exists without a
  recovery channel") is asserted by this doc but enforced by a process this doc
  explicitly does not own or specify. Nothing in scope verifies the invariant
  actually holds at runtime; it is a precondition imported from elsewhere and then
  relied on as if proven here. Relatedly, the present-tense invariant says nothing
  about accounts that predate the requirement (legacy/migrated accounts with no
  recovery channel) — whether they are blocked, back-filled, or grandfathered into
  the old lockout is undefined.
- Why it matters: This is exactly the seam my lens is for: Security treats "recovery
  is mandatory" as a given and threat-models forward from it; Product/Systems treat
  account creation as out of scope and never confirm the precondition is enforced.
  If creation can mint an account without a recovery channel (a bug, a legacy path,
  a partner-provisioned account), the lockout BLOCKER silently reopens with no
  in-scope control catching it. A guarantee whose enforcement lives in an explicitly
  out-of-scope process is an assumption, not a defense.
- Suggested resolution: State the invariant as a **hard precondition this design
  depends on** and name where it is enforced (e.g., "account-creation, though out of
  scope here, MUST reject account creation without an enrolled recovery channel; this
  design assumes that contract and does not function safely without it"). Add one
  line on legacy/no-recovery accounts: either they cannot authenticate until a
  channel is enrolled, or they are an explicitly accepted, owned lockout class.

### §2.2 / §3.2 / §5.0 — Single-live-token invariant, session-scoped supersession, and resend collide for the lost-tab user
- Problem: Three stated properties do not compose cleanly. §3.2: "**at most one live
  token exists per account.**" §2.2: supersession is "**scoped to the originating
  session** ... a request that does not carry the original request's session context
  does **not** invalidate an outstanding token," and "repeated submits within a
  **short window** coalesce to the in-flight link." §5.0: resend is "coalesced per
  §2.2." Now take the ordinary legitimate user who closes the original tab (losing
  the originating session context) and, after the short coalesce window but before
  the 10-minute token expiry, re-requests from a fresh session. That request (a)
  cannot supersede (no originating-session context, by §2.2's anti-targeting rule),
  and (b) is outside the coalesce window, so what happens is undefined: either a
  second live token is minted — **violating §3.2's "at most one" invariant** — or the
  request is dropped/refused, **stranding a legitimate user** who is now waiting on an
  email they may not be able to retrieve, with no in-scope way to get a fresh link.
- Why it matters: The §2.2 session-scoping was introduced to stop a *third party*
  killing a victim's link; it correctly distinguishes attacker from owner only while
  the owner holds the original session. The instant the owner loses that context
  (closed tab, new device, cleared session) they become indistinguishable from the
  attacker under §2.2's own rule, and the design has no defined branch for them. This
  is the seam between Security (don't let others supersede), Systems (exactly-one-live
  invariant), and Product (lost-tab resend must work) — each assumes another resolved
  it. The 10-minute expiry minus the "short window" is the live gap.
- Suggested resolution: Define the non-originating-session re-request explicitly.
  Options: treat a re-request as superseding only when accompanied by a fresh
  proof-of-control of the *same address* (re-entry of the address is already
  required), accepting that an attacker cannot supply that for an address they don't
  control; or define that a second live token may coexist and reconcile that against
  §3.2's invariant (state the real invariant, e.g., "at most one live token *per
  originating session*"); or state that lost-tab users must wait out expiry and own
  that as a UX cost. Pick one and make §2.2/§3.2/§5.0 agree.

## ADVISORY

### §1 — Acceptance bar is now real, but the abandon condition covers only one of four criteria
- Problem: The success criteria are genuine and measurable (time-to-logged-in,
  completion rate, delivery SLA, lockout/support rate) — this closes my round-002
  FINDING. But the stated **abandon condition** triggers only on completion rate
  (< 90% after delivery/resend addressed). The lockout/support-ticket rate (< 0.1%)
  is the metric most directly tied to the recovery design that dominated two review
  rounds, and it has no abandon/escalation trigger. A design can hit its completion
  target while quietly running a 5% support-driven-lockout rate and never trip a bar.
- Why it matters: The metric that measures whether the lockout fix actually worked in
  production is the one with no consequence attached. Convergence on paper does not
  guarantee the bar means anything operationally.
- Suggested resolution: Attach a trigger to the lockout/support-rate criterion too
  (e.g., breach for N consecutive periods escalates a recovery-path review), or state
  why only completion rate gates the abandon decision.

### §7.1 / §7.2 — Recovery-channel assurance is asserted equal to email, but the trust-root assumption can undercut it
- Problem: §7.2 says the recovery path is "held to the same bar as the primary path,"
  and §7.1's accepted trust root is "we do not defend against an attacker who already
  controls the user's inbox." If a permitted "second verified channel" happens to be
  reachable by an inbox-controlling attacker (e.g., a recovery email at the same
  provider, or a forwarded/shared mailbox — which §7.1 notes "inherit this"), the
  same-bar claim and the recovery threat model both quietly degrade for that
  configuration. The doc requires "a second verified channel" but never requires it
  be *independent* of the primary email channel.
- Why it matters: The recovery path is the by-design way in without the primary
  factor; if it can collapse onto the same trust root, the parity claim is weaker than
  stated for exactly the population (shared/forwarded inboxes) §7.1 already flags as
  weakest.
- Suggested resolution: Add an independence requirement: the second channel must not
  be reachable solely via control of the primary email account; shared/forwarded-
  inbox accounts fall to the support-mediated path, not a same-provider second email.

## Cross-section coherence flags
- §2.1 vs §6.1: §2.1 says over-limit requests are "accepted at the UI layer (so the
  response can't enumerate)," yet §6.1 lists "rate-limited" as a defined visible
  state. These are reconciled in practice — §6.1's visible artifact is a
  *non-enumerating hint* ("check spam before re-requesting"), not a hard
  "you are rate-limited" — but a reader can take §6.1's bare label "rate-limited" as
  a confirmable state that would re-open the enumeration channel §4.0 closes. Worth
  one clause making explicit that the §6.1 rate-limited state renders as the
  non-enumerating hint, never as a throttle confirmation.
- §3.2 vs §6.0: the round-002 coherence flag (scanner pre-fetch winning the atomic
  consume CAS) is genuinely closed: §6.0 now requires a deliberate POST gesture and a
  GET only presents, so a preview-fetcher cannot consume. Confirmed by reading §6.0
  against §3.2, not assumed.
- §1 vs §7.2: the round-002 "fewer moving parts vs needs a second channel" tension is
  now reconciled — §1 scopes the design to low-assurance consumer sign-in and frames
  the recovery channel as the owned cost of recoverability rather than a contradiction.
  Closed.

## Summary
v0.3 genuinely closes my round-002 BLOCKER: recovery is now mandatory-at-creation
(not conditional), threat-modeled, rate-limited, session-rotating, and held to the
primary-path bar — I tried to re-open the by-omission lockout against the specific
text and could not. Success criteria are now real and measurable. What remains is not
the old ship-stopper: one FINDING that the lockout fix's load-bearing invariant is
enforced inside an explicitly out-of-scope process (and silent on legacy accounts),
and one FINDING that §2.2/§3.2/§5.0 don't compose for the lost-tab/new-session
re-request — a logic seam that either violates the single-live-token invariant or
strands a legitimate user. Both are FINDINGs, not BLOCKERs; with two open FINDINGs the
objection surface is not yet at zero, so **another round is warranted** — but it is a
narrow one, and I expect convergence next round if these two seams are closed.
