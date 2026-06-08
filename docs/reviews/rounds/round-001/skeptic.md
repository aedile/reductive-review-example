# Skeptical Generalist: Round 001

Target: `docs/design/magic-link-auth.md` (v0.1)

## BLOCKER

### §1-scope note: No threat model means nothing in the doc can be evaluated
- Problem: The doc explicitly defers the threat model ("no stated threat model") while making a series of security-shaped decisions throughout (§3 token, §4 enumeration, §3.4 session). Every "SEEDED FLAW" annotation presumes a threat we never name. Without an adversary model, who are we defending against, what are they capable of, what do they gain, there is no basis on which any token/session/enumeration decision can be judged right or wrong. The other critics (security especially) will each invent their own implicit threat model, and they will not be the same one.
- Why it matters: A design doc that picks an auth mechanism without stating what it defends against cannot be trusted, because "is this secure enough" is unanswerable. Every downstream review becomes an argument about unstated assumptions. This is the load-bearing gap.
- Suggested resolution: Add a §0 Threat Model before §1: name the assets (the account, the session, the email channel), the adversaries (passive network, attacker with the victim's email open, attacker without it, shared-device attacker), and what is explicitly out of scope. Everything else gets evaluated against it.

### §1 / §1-scope note: Account recovery and email-loss lockout is unowned, not just unspecified
- Problem: §1 makes email the *sole* authentication factor ("No passwords"), and §1-scope note admits there is "no account-recovery story if the user loses email access." With magic links, possession of the email account *is* the identity. If the user loses email access (lapsed domain, churned employer, hacked mailbox, closed provider), they are permanently locked out with no path back, and conversely, anyone who gains email access gains the account permanently. This is not an edge case; it is the central consequence of the chosen design, and no section owns it.
- Why it matters: This is the seam that falls between Product (UX of lockout), Security (email-takeover = account-takeover), and Systems (support/recovery flows). Each will assume another owns it. An auth system with no recovery path is not shippable; it generates an unbounded support and trust liability the moment a real user loses inbox access.
- Suggested resolution: Either (a) define a recovery flow and own its security trade-offs explicitly (recovery is usually the weakest link and must be threat-modeled too), or (b) state as an explicit, accepted design constraint that "email access loss = permanent lockout, recovery is out of scope and handled by [X]," and name who owns X. Silence is not acceptable for the system's single point of failure.

## FINDING

### §1: The premise itself is unjustified: why passwordless, why magic links
- Problem: §1 states the goal as "sign in by email link, no passwords" as a given. There is no problem statement. We never learn what problem passwordless solves here, what alternatives were considered (passwords + reset, OAuth/SSO, passkeys/WebAuthn, OTP codes), or why email magic links specifically won. Magic links have well-known downsides (email deliverability latency on the critical login path, cross-device friction per §6.0, phishing-trainability, email-as-SPOF per the BLOCKER above) that may make them the wrong tool depending on the actual user and risk context.
- Why it matters: The whole doc is downstream of this choice. If the premise is wrong, every detailed section is polishing the wrong artifact. A reviewer cannot assess whether the design is good without knowing what it was chosen over and why.
- Suggested resolution: Add a "Why this approach" subsection to §1: state the user/context, the alternatives considered, and the decision criteria. At minimum acknowledge passkeys/OTP as the obvious competitors and why they were rejected.

### §1: No definition of success / no acceptance bar
- Problem: Nowhere does the doc state what "this works" means. There are no success criteria, no target metrics (login success rate, time-to-login, deliverability rate, support-ticket rate), and no failure thresholds. The only quality signal in the doc is the self-deprecating "deliberately weak" changelog note.
- Why it matters: Without a stated bar, convergence is undefined, the panel cannot know when the design is "good enough," and the author cannot know when to ship. "Done" becomes a matter of fatigue, which the protocol (README §5) explicitly forbids.
- Suggested resolution: Add a "Success criteria" section with measurable targets (e.g., median time-to-logged-in, login completion rate, email delivery SLA, acceptable lockout/support rate) and the conditions under which the approach would be abandoned.

### §5: Single delivery channel with no fallback makes auth availability = email availability
- Problem: §5.0 sends the email "and assumes it arrives." Beyond the seeded "no delivery-failure path," the deeper premise problem is that there is *one channel* for the entire auth system. When email is slow (greylisting, queue backlog), filtered (spam, corporate gateways), or down (provider outage), there is no fallback auth path at all, the user simply cannot log in. This couples your product's availability to a third-party email pipeline you don't control.
- Why it matters: This is a systems/product/security seam: deliverability latency is on the *critical login path*, not a background job. An outage of the email provider becomes a total auth outage. No section owns "what is the fallback when the one channel fails."
- Suggested resolution: State the availability dependency explicitly and decide on a fallback (e.g., secondary channel, OTP, or graceful degradation), or accept the coupling explicitly with an SLA expectation on the email provider. At minimum, name the dependency as a first-class risk.

### §6.0: Cross-device link opening is a premise problem, not just a UX gap
- Problem: §6.0 flags "no handling of opening the link on a different device" as a UX flaw, but it is deeper: magic links structurally break when the requesting device and the clicking device differ (request on laptop, email opens on phone; link scanners/preview-fetchers in corporate email pre-click the link). This interacts with §3.2 (link logs you in on click) and §3.4 (session creation), *which* device gets the session? An email security scanner that fetches the URL could consume a single-use token before the human ever clicks.
- Why it matters: This is the intersection of Product (the user's flow) and Security (link pre-fetching / token consumption). It is a known failure mode of the chosen mechanism, and it touches token semantics, not just screen states.
- Suggested resolution: Decide the cross-device model (same-device requirement? code-entry fallback? device-binding the token to the requester?) and address email-scanner pre-fetch explicitly in §3.2/§6.0.

## ADVISORY

### §3.3 / §3.2: Expiry is contradictorily handled
- Problem: §3.2 carries the seeded flaw "no expiry; reusable/replayable," and §3.3 "Expiry" exists as a section but is "(expiry unspecified)." The doc has a section heading promising to define expiry and then declines to. This is scope quietly implied but not delivered.
- Why it matters: A named section that defines nothing reads as an oversight rather than a deliberate deferral, and it will confuse the convergence signal (is §3.3 "done"?).
- Suggested resolution: Either fill §3.3 or mark it explicitly as a known open item with an owner, consistent with how §1-scope note is handled.

### §4.0: Enumeration trade-off is decided without acknowledging the UX cost
- Problem: §4.0 returns distinct messages for registered vs unregistered email (seeded enumeration flaw). The fix (uniform "check your inbox" response) has a real UX cost, users who mistype their email or aren't registered get no feedback. This is a genuine product/security trade-off that the doc neither names nor resolves.
- Why it matters: It is exactly the kind of seam that falls between Security (wants uniformity) and Product (wants helpful errors) where each assumes the other owns the call.
- Suggested resolution: Note the trade-off explicitly and assign the decision, rather than leaving it to be silently resolved by whichever critic is loudest.

### §2.1: Rate-limit absence implies an unowned abuse/cost surface
- Problem: §2.1's seeded flaw is "no limit on requests." Beyond the security angle (enumeration/spam), the unowned consequence is operational: each request sends a real email, so an attacker can use the endpoint to generate cost and to weaponize *your* domain for email-bombing a victim's inbox, making your service the abuse vector against a third party.
- Why it matters: This is a systems/cost and reputation concern (sender reputation, deliverability blacklisting) that sits outside the pure-security framing and that no section owns.
- Suggested resolution: When rate-limiting is specified, scope it to cover cost, sender-reputation, and third-party-victim email-bombing, not only brute-force.

## Cross-section coherence flags
- §3.3 ("Expiry") exists as a section but defers to "(expiry unspecified)," while §3.2 already lists "no expiry" as its flaw, the two sections describe the same gap inconsistently and §3.3 is effectively empty.
- §1 ("No passwords") and §1-scope note (no recovery if email is lost) together create an unresolved contradiction: the design removes the recoverable factor (password) and also declines to provide any other recovery path, so the system has no recovery story by construction. No section reconciles this.
- §5.0 ("assume it arrives") contradicts the implicit availability requirement of §1 (users must be able to sign in): if delivery can silently fail, the stated goal is unmet, but no section flags the dependency as a risk to the goal.
- Numbering is irregular (§4 has only §4.0; §6 jumps; "§1-scope note" is a non-numbered trailing section), which makes "locate every finding to a real §" harder to do reliably and weakens the audit trail the protocol depends on.

## Summary
The doc's fatal gaps are not the per-section seeded flaws but the unowned premises beneath them: there is no threat model, no justification for passwordless/magic-links over alternatives, no account-recovery story for the email-loss lockout that the design's single-factor nature makes inevitable, and no definition of success. These are precisely the seams the specialist lenses will each assume another owns. Another round is clearly warranted, I have multiple BLOCKER and FINDING-level premise gaps and nothing here is close to converged.
