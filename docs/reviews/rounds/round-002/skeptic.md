# Skeptical Generalist: Round 002

Target: `docs/design/magic-link-auth.md` (v0.2)

Fresh full read, perturbed order: started from the acceptance bar, then the seams
between lenses, then premise and recovery. New material this round is §7 (threat
model + recovery ownership) and §8 (observability); those got the hardest look.

## BLOCKER

### §7.2: "Owned by delegating" leaves the actual lockout case unowned for the common account
- Problem: §7.2 claims to own the email-loss lockout by requiring that "an account
  needing a fallback **must enrol** a recovery method ... at creation time." Read
  literally, enrolment is conditional ("an account *needing* a fallback") and
  therefore optional. The design's single point of failure is precisely the user
  who did *not* enrol a second channel and then loses inbox access, the default,
  highest-volume case. For that user there is still no path back: the doc has moved
  the lockout one step upstream (to an enrolment that may never have happened)
  rather than resolving it. "We own it by delegating it" delegates to a step the
  spec does not make mandatory and does not define a behavior for when it is skipped.
- Why it matters: This was the round-001 BLOCKER (email-loss lockout is unowned).
  The revision *names* the problem but does not close it: the modal user is still
  permanently lockable-out by construction, which is the exact ship-stopping
  condition the prior round flagged. An auth system whose primary recovery story is
  "you should have opted in earlier" has no recovery story for the people who need
  it most.
- Suggested resolution: State explicitly and bindingly what happens for an account
  with **no** enrolled fallback that loses email access. Either (a) make a recovery
  channel **mandatory at account creation** (no account exists without one), or
  (b) accept "no fallback enrolled ⇒ permanent lockout" as a stated, owned product
  constraint and name who absorbs the resulting support/trust liability. Conditional
  "must" is not ownership.

## FINDING

### §7.2: The recovery mechanism is the new weakest link and is left un-threat-modeled
- Problem: §7.2 offers two recovery methods, "second verified channel" or
  "support-mediated identity check", and specifies neither. In any possession-based
  auth scheme the recovery path is typically the weakest link (it is, by definition,
  the way to get in *without* the primary factor). §7.1's threat model says nothing
  about the recovery path at all: it lists what the primary flow defends against but
  is silent on attacks against recovery (support-desk social engineering, SIM-swap
  if the second channel is SMS, recovery-channel takeover). An attacker who cannot
  beat the magic link simply attacks the support-mediated check instead.
- Why it matters: Adding a recovery mechanism without threat-modeling it can make the
  system *less* secure than having none, you have introduced a parallel
  authentication path and declined to defend it. This is the seam between Security
  (recovery is an attack surface) and Product/Support (recovery is a UX/ops flow);
  §7 currently sits in the gap.
- Suggested resolution: Bring recovery inside the §7.1 threat model. State the
  adversary against the recovery path, the assurance level each recovery method
  provides, and why it is acceptable. If support-mediated check is offered, define
  what identity evidence is required so it is not just "support decides."

### §1 / §7.1: Still no definition of success / acceptance bar
- Problem: The changelog concedes "success criteria remain open," and no section
  defines what "this works" means, no target login-completion rate, time-to-login,
  email-delivery SLA, or acceptable lockout/support rate. The threat model (§7.1)
  now defines the *security* bar qualitatively, but there is no operational or
  product acceptance bar anywhere.
- Why it matters: Without a stated bar, convergence is undefined (README §5): the
  panel cannot know when the design is good enough and "done" collapses to fatigue,
  which the protocol forbids. This was a round-001 FINDING and remains genuinely
  open, not merely deferred-with-owner.
- Suggested resolution: Add measurable success criteria (median time-to-logged-in,
  login completion rate, delivery SLA, acceptable lockout/support-ticket rate) and
  an explicit abandon condition.

### §5 / §6.0: Single-channel availability and cross-device remain open premise gaps, not just UX gaps
- Problem: §5.0 still treats delivery as best-effort with email as the sole channel
  (F3 open), and §6.0 leaves cross-device + scanner pre-fetch undefined (F4 open).
  These are correctly flagged as open in the doc, so I note rather than re-litigate, 
  but I want it on the record that both are *premise* problems, not deferrable
  polish: with one channel, auth availability == email availability (a third-party
  dependency on the critical login path), and the scanner-prefetch case in F4
  interacts with the §3.2 single-use atomic consume, a preview-fetcher can win the
  CAS and consume the token before the human clicks, which is a token-semantics bug,
  not a screen-state bug.
- Why it matters: These two open items are the load-bearing seams between Systems
  (availability), Security (token consumption by a non-human fetcher), and Product
  (the actual user journey). They must be closed before the design can be trusted,
  and their resolution may feed back into §3.2/§5, so they are not safely
  end-of-queue.
- Suggested resolution: When closing F3/F4, explicitly state the availability
  dependency/SLA and the cross-device model, and reconcile scanner pre-fetch against
  the §3.2 atomic consume (e.g., require a human-interaction confirm step, or
  GET-safe pre-validation + POST-to-consume).

## ADVISORY

### §7.1: Threat model states defenses and one assumption but never names assets or adversaries
- Problem: §7.1 lists threats defended-against and one accepted assumption (attacker
  controls the inbox), which is a real improvement. But a threat model conventionally
  also names the **assets** (the account, the live session, the email channel) and
  the **adversaries** by capability (passive network observer, attacker-with-inbox,
  attacker-without-inbox, shared/public-device attacker). The current text is a
  defense list, not an adversary model; e.g., the passive-network and
  shared/public-device adversaries are never positioned even though §3.4's
  cookie/session choices are decisions against them.
- Why it matters: A defense list can look complete while silently omitting an
  adversary class. Naming assets and adversaries is what lets a reader check the
  list for *omissions* rather than just reading the items present.
- Suggested resolution: Prepend a one-line asset list and an adversary-by-capability
  list to §7.1, then map each listed defense to the adversary it counters.

### §7.1: "Layer a second factor (out of scope)" quietly walks back the §1 premise
- Problem: §1 sells magic links because email possession "is already the de-facto
  recovery factor, so making it the primary factor removes a moving part." §7.1 then
  says high-assurance accounts "should layer a second factor (out of scope)." If a
  meaningful class of accounts needs a second factor, the "removes a moving part"
  justification holds only for the low-assurance segment, which should be stated as
  the explicit scope of the whole design, not surfaced as an aside in the threat
  model.
- Why it matters: It is a mild premise/scope-creep seam: the doc's central rationale
  (§1) and its threat model (§7.1) imply different intended audiences, and neither
  names the boundary.
- Suggested resolution: In §1, scope the design to the low-assurance / low-frequency
  consumer segment explicitly, and state that higher-assurance use is out of scope
  and why, so §7.1's aside is a consequence of a stated boundary, not a new one.

## Cross-section coherence flags
- §7.2 vs §1: §1 frames email-as-primary as *removing* a moving part; §7.2 then
  requires enrolling a *second* channel for any account that wants a fallback, 
  re-introducing the moving part for the case that matters. The two sections are not
  contradictory but the doc never reconciles "fewer moving parts" with "you need a
  second channel to be recoverable."
- §7.2 vs §3.2: §3.2's single-use atomic consume is asserted as a clean property, but
  the still-open F4 scanner-prefetch case (§6.0) means a non-human fetcher can be the
  CAS winner, §3.2 and §6.0 describe the same token lifecycle with incompatible
  optimism. Flagging so the eventual F4 fix is reconciled back into §3.2.
- Numbering is now regular and the prior §3.3 empty-placeholder coherence flag from
  round-001 is genuinely closed (§3.3 now defines server-time authority + ±60s skew).
  Confirmed by reading, not assumed.

## Summary
The v0.2 revision genuinely closed the round-001 token/session/expiry BLOCKERs and
the numbering/empty-section coherence flags, and the new §7 is a real improvement
over silence. But the headline round-001 BLOCKER, the email-loss lockout, is named
rather than resolved: §7.2's recovery enrolment is conditional/optional, so the
default user is still lockable-out by construction, and the recovery path it
introduces is itself un-threat-modeled (the new weakest link). Success criteria
remain genuinely undefined. Another round is warranted: I am carrying one BLOCKER
(§7.2 unowned default-lockout) and three FINDINGs, so the objection surface is not
yet at zero and I have material to add.
