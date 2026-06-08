# Round 007: the decorrelated review (capstone)

This round is different in kind, and that is the entire point.

Rounds 001 to 006 were the frozen panel: four adversarial lenses, all the same model
in different roles, looping to convergence. They converged at round 006: 0 BLOCKER,
0 FINDING, unanimous "nothing material to add." Then we did the thing
[`FAILURE-MODES.md`](../FAILURE-MODES.md) says is the real escape from correlated-error
blind spots: we ran reviewers of a **different kind**. A security domain expert with a
fresh context and a hostile brief, plus the non-LLM [`executable critic`](../EXECUTABLE-CRITIC.md).

The security reviewer found **BLOCKER-class issues the six-round panel never raised.**
Not restatements of logged items: genuinely new attack surface the all-LLM panel shared
a blind spot on. The pattern is clear in hindsight: the panel polished the token *state
machine* to a high gloss and never seriously attacked what happens to the token *once it
leaves the database as a URL*, or the send pipeline *pointed outward as a weapon*.

This is not the example failing. This is the example's thesis (W3, W7, W2 in
`FAILURE-MODES.md`: shared blind spots are real, recall is unobservable, decorrelate with
a different kind of reviewer) demonstrated on its own converged artifact. A correlated
panel reported "done"; a decorrelated lens reopened it in one pass.

## New findings against v0.6 (none logged in rounds 001 to 006)

### BLOCKER, §3.1 / §5.1: the token travels in a URL and leaks out of band
- Problem: the secret rides in the emailed URL and in the §6.0 confirm page's address
  bar. It leaks via the `Referer` header to any third-party subresource on the confirm
  page, into browser history (and cloud history sync, relevant to the §7.1
  shared/public-device adversary), and into corporate "safe links" rewriters and CDN
  access logs. POST-to-consume (§6.0) stops a scanner *consuming* the token; it does
  nothing to stop it being *logged*.
- Why it matters: every path defeats "only the inbox holder can consume" without touching
  the inbox, which is exactly the trust root §7.1 accepts and therefore waves past.
- Direction: `Referrer-Policy: no-referrer` on the confirm page; strip the token from the
  URL on load (`history.replaceState`); prefer an opaque claim id exchanged server-side;
  forbid third-party subresources on the confirm page.

### BLOCKER, §2.1 / §5.0: the send pipeline is an outward-pointing weapon
- Problem: §2.2 removed all invalidation so "a third party cannot kill a victim's link,"
  and resend mints more tokens. But the recipient mailbox is a finite, attacker-targetable
  resource the spec never models. Per-IP limits are bypassable with rotating IPs; there is
  no per-recipient cooldown, no "stop sending me these" off-switch, and by design no way to
  invalidate. That is a sustained email-bombing primitive aimed at a real person, and a
  reflection/amplification vector that burns your own sender reputation (breaking the §1
  delivery SLA for everyone). The §2.2 anti-targeting choice, praised across three rounds,
  *created* a strictly worse targeted-harassment surface.
- Direction: per-recipient send suppression when prior links are unconsumed; a "this
  wasn't me / stop" control that suppresses *sends* (compatible with non-invalidation of
  *tokens*); monitor outbound send-to-distinct-recipient ratios in §8.1.

### FINDING, §2.1 / §4.0: the async "parity mechanism" relocated the enumeration oracle
- Moving account-dependent work off the synchronous path does not delete it. Email
  *arrival* is a perfect existence oracle for anyone who can observe the mailbox; the
  §2.1 limiter is account-keyed (only real accounts mint, so rate-limit state and missed-
  coalesce duplicates leak existence). §4.0 should claim "no added HTTP-side oracle," not
  "enumeration prevented."

### FINDING, §7.2: recovery enrolment is bootstrapped from the inbox it is meant to backstop
- First-sign-in enrolment is inbox-gated (§7.2 admits this), so an attacker with brief
  inbox access enrols *their own* independent recovery channel and gains persistence that
  survives the victim regaining the inbox. Separately, recovery-initiation is rate-limited
  on a *separate* counter and revokes *all* live tokens, so it is a fresh targeted-login-
  denial vector, the very thing §2.2 was contorted to prevent.

### FINDING, §6.0 / §3.4: POST-to-consume is not CSRF protection
- "POST not GET" defeats prefetch, not CSRF. The confirm POST needs its own origin-bound
  anti-CSRF token (unspecified), and login-CSRF (tricking a victim into consuming an
  attacker's token, logging them into the attacker's account) is not addressed by session
  rotation.

### FINDING, §8: logging hygiene protects the wrong surface
- Hashing the token in *your* logs is good, but the real leak surface (Referer, history,
  link-host logs) is outside your logging discipline; §8 should drive a URL/header hygiene
  requirement, not just redaction. Retained tombstones also form a per-account activity
  timeline.

### ADVISORIES
- §3.3: the ≤5 s NTP bound assumes NTP is *honest*; a spoofed/asymmetric time source
  extends the replay window and is not in the threat model.
- §3.4: `SameSite=Lax` has app-wide CSRF consequences post-login the spec implies are
  handled.
- §6.0: "land on the page you originally tried to reach" is an open-redirect sink unless
  validated against a same-origin allowlist.

The executable critic, by contrast, found nothing new: it can only test the claims the
panel already chose to encode, so it shares the panel's *agenda* even though it is
decorrelated in *execution*. That is the precise limit stated in `EXECUTABLE-CRITIC.md`:
a decorrelated *checker* corroborates selected claims; a decorrelated *reviewer of a
different kind* is what finds the unasked questions.

## The lesson, which is the whole repo in one round

The descent converged honestly against the panel it had. It was still wrong, because the
panel shared blind spots and recall is unobservable. "Converged" meant "no objection
survived *these four correlated lenses*," never "correct." We are **not** revising v0.6
to silence these (it is a fictional teaching artifact, and chasing one more correlated
panel past them would just relocate the lesson). We are logging them, in the open, as the
strongest evidence this repo can offer for its own central claim: if you want correctness
and not just convergence, change the *kind* of reviewer, and put a human (or a real
domain expert, or a tool that runs) where the shared blind spots do the most damage. And
know when to stop: the loop ends when no material objection survives a round, but
releasing with the remaining limits logged is a human call, not a proof.
