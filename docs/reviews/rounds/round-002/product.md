# Round 2: Product / UX critic

Reviewing `docs/design/magic-link-auth.md` v0.2. Fresh full read, starting from
accessibility / trust signals, then the "didn't get the email" path and error/edge
states, then the cross-device flow.

Headline: the security and systems spine of the doc was genuinely hardened in v0.2
(CSPRNG single-use token, atomic consume, expiry, session rotation, rate-limiting,
uniform response, threat model). But the entire user-facing surface, §5 Delivery,
§6 User experience, remains a stub. The prior UX FINDINGs were not resolved; they
were re-labelled as parenthetical "OPEN FINDING" notes inside otherwise-empty
sections. A flag is not a resolution. From a Product/UX standpoint this document
still does not describe a usable product.

---

## BLOCKER

### §6.1: Consumed/expired/malformed token has no defined user-facing state at all
- Problem: §3.2 says verifying a consumed or expired token "fails closed with a
  defined response (see §6.1, still open)." §6.1 is a placeholder that defines
  nothing, it is a parenthetical admitting F5/F6 are "still unspecified." So the
  one normative cross-reference the token state machine depends on points at empty
  space. There is no defined copy, no next action, no page, for: expired link,
  already-used link, malformed/truncated token, or rate-limited request. These are
  not rare paths, with a 10-minute expiry (§3.2) and "second request invalidates
  the first" (§2.2), expired and consumed-link landings are the *common* failure
  modes of normal use.
- Why it matters: A user who clicks a stale or superseded link is the single most
  frequent error case in any magic-link system. With nothing defined, the
  implementer ships a raw 4xx, a blank page, or a generic "error," and the user is
  stranded with no path back to signing in. This is the difference between a product
  and a security primitive. It also blocks §3.2 from being implementable as written,
  since §3.2 explicitly defers its response definition here.
- Suggested resolution: Define each terminal/error state as a concrete page with
  (a) plain-language explanation, (b) a single obvious recovery action, almost
  always a "Send me a new link" button that re-enters §2.1, and (c) no leakage of
  account existence (must stay consistent with §4.0). At minimum: expired, already
  used, invalid/unrecognized link, and rate-limited. Until §6.1 contains these,
  §3.2's "defined response" is undefined.

### §5.0: No "I didn't get the email" path exists (no resend, no latency expectation, no spam guidance, no failure surface)
- Problem: §5.0 is the single sentence "We send the email," followed by a note that
  delivery is "best-effort, no retry, no failure surface, no resend, and email is
  the sole channel." From the user's side this means: after submitting their
  address they see "If an account exists... we've sent a sign-in link" (§4.0) and
  then, nothing. No stated expectation of how long it should take, no resend
  control, no "check spam/promotions" guidance, no surfacing of a send failure.
  Email delivery fails or delays for a meaningful fraction of real traffic
  (greylisting, spam foldering, provider throttling, typo'd address).
- Why it matters: "I didn't get the email" is the top support ticket and the top
  silent-abandonment cause for passwordless auth. Because §4.0 deliberately gives an
  identical response whether or not the account exists, a user who typo'd their
  address gets the *same* reassuring "we've sent a link" and then waits forever with
  zero recourse. With no resend and email as the sole channel, a single delivery
  failure is a hard lockout for that session with no self-service exit. This is a
  product-defining gap, not a polish item.
- Suggested resolution: The confirmation screen must set a latency expectation
  ("usually within a minute"), give spam/promotions-folder guidance, and offer a
  resend control gated to the §2.1 rate limits (and consistent with §2.2 idempotency
resend should coalesce/replace, not stack). Provide a visible "wrong address?
  re-enter it" affordance so a typo is recoverable without abandoning. Note: this
  overlaps the carried-forward F3, but F3 frames it as a delivery-engineering issue;
  the *user-facing* recourse is independently required and is currently absent.

---

## FINDING

### §6.0 / §5.0: Confirmation and success states are undefined; the user is told nothing actionable
- Problem: The only described UX is §6.0 "User clicks the link and is logged in" and
  the §4.0 confirmation string. There is no spec for what the request screen, the
  confirmation screen, or the post-login landing look like or say. A confused or
  distracted user gets no guidance on what to do next at any step except the single
  confirmation sentence.
- Why it matters: Copy clarity at each step is what keeps a non-technical user
  moving. "We've sent a link" with no follow-through (how long? what if it doesn't
  come? what happens after I click?) leaves the user guessing. The happy path being
  a one-liner means the actual screens will be invented ad hoc by whoever implements.
- Suggested resolution: Specify the copy and primary action for each step: request,
  confirmation (incorporating the §5.0 latency/resend items), click-success landing,
  and what "logged in" lands the user on (the page they were trying to reach, or a
  default). Tie success to the success criteria the changelog admits are still open.

### §5/§6: No accessibility requirements for either the email or the pages
- Problem: The brief calls out accessibility of both emails and pages, contrast,
  focus order, link text, plain-text email fallback. The current doc states none of
  this. §5.0 does not require a plain-text alternative part (many clients and
  screen-reader users render text/plain), and §6 defines no page-level a11y baseline.
- Why it matters: A magic-link email that is HTML-only, or whose link is an opaque
  "click here," fails for screen-reader and text-client users, i.e., it excludes
  users from the *only* way to sign in. An error/confirmation page with no defined
  focus management or contrast baseline excludes the same users from recovery. With
  email as the sole channel (§5.0), an inaccessible email is a total lockout for the
  affected user, not a degraded experience.
- Suggested resolution: Require a multipart email with a meaningful plain-text part
  whose link is a full, readable URL (not "click here"); require descriptive link
  text in the HTML part; and state a page a11y baseline (WCAG AA contrast, keyboard
  focus order, focus moved to the result heading on error/success pages, no
  reliance on color alone to convey state).

### §5: No trust / anti-phishing signals defined for the email
- Problem: The brief explicitly asks whether the email is "obviously from us and
  obviously not phishing." §5 says nothing about sender identity, from-address,
  what the link domain is, or any in-email anti-phishing affordance. Magic-link
  emails are a prime phishing template precisely because they train users to "click
  the link in the login email."
- Why it matters: If the legitimate email has no consistent, recognizable trust
  markers, users cannot distinguish it from a phishing clone, and the whole scheme
  rests on the user clicking a link in an email. This directly undermines the
  security posture §7 worked to establish: §7 defends the token, but the human is
  the soft target and §5 leaves them unguided.
- Suggested resolution: Specify the from-name and from-domain, require the visible
  link to point at a single known first-party domain (no redirectors/tracking
  wrappers that obscure the destination), require authentication (SPF/DKIM/DMARC
  alignment) be stated as a delivery requirement, and consider a recognizable
  per-account cue. State plainly what the email will and will not ask the user to do
  (e.g., "we will never ask for your password").

### §6.0: Cross-device flow and scanner pre-fetch are still undefined (F4 carried forward, not resolved)
- Problem: §6.0 carries F4 as an open note: request-on-phone / open-on-laptop, plus
  email-scanner pre-fetch consuming the single-use token, are "still undefined."
  This is acknowledged but unresolved. The interaction with §3.2 (single atomic
  consume) and §2.2 (one live token) makes this concrete and dangerous: a corporate
  mail scanner or link-preview bot that GETs the link will *consume* the only live
  token before the human clicks, and the human then lands on the §6.1 "already used"
  state, which itself is undefined (see BLOCKER above).
- Why it matters: Scanner pre-fetch is not a tail case; Outlook/Defender, Proofpoint,
  Slack/iMessage unfurlers, and antivirus link-checkers routinely fetch URLs in
  email. If a GET consumes the token, a large share of users get a "link already
  used" landing they never triggered, with no recovery defined. Cross-device is also
  a primary real-world flow (read mail on phone, work on laptop) and the doc does
  not say whether the session is established on the clicking device or handed back.
- Suggested resolution: Make token consumption require a deliberate user action
  (POST on a confirmation page, or a GET that only *presents* a "Confirm sign-in"
  button rather than consuming) so pre-fetch cannot burn the token. Define the
  cross-device outcome explicitly: the device that completes confirmation is the one
  that gets the session; state what the requesting device shows if it is a different
  device. This closes F4 rather than restating it.

---

## ADVISORY

### §2.1 / §6.1: Rate-limited request has no user-facing explanation
- Problem: §2.1 silently drops over-limit requests (correctly, to avoid enumeration),
  and §4.0 returns the same reassuring message regardless. A user who legitimately
  hits the 3-per-15-min limit (e.g., kept retrying because the email was slow, see
  §5.0 gap) is told "we've sent a link" and gets nothing, with no hint that they are
  throttled.
- Why it matters: This is a genuine usability trap created by an otherwise-correct
  security choice. It is hard to surface without leaking enumeration signal, so it is
  an advisory rather than a blocker, but it deserves a deliberate decision.
- Suggested resolution: Consider a soft, non-enumerating hint after repeated submits
  in a session ("Still waiting? Links can take a minute; check spam before
  re-requesting"), which steers the user without confirming throttle state.

### §7.2: Recovery enrolment at account creation has UX cost not acknowledged
- Problem: §7.2 owns the lockout case by requiring a fallback (second channel or
  support-mediated check) be enrolled "at creation time." That is sound, but it adds
  friction to the very first interaction and the doc does not consider whether
  forcing it at creation harms conversion or what happens to existing accounts with
  no fallback enrolled.
- Why it matters: A hard requirement at signup is a product decision with drop-off
  consequences; "at creation time" also leaves the migration/backfill cohort
  undefined.
- Suggested resolution: State whether fallback enrolment is blocking at signup or
  promptable later, and define the path for accounts that predate the requirement.

---

## Cross-section coherence flags

- §3.2 references §6.1 for the "defined response" to consumed/expired tokens, but
  §6.1 is an empty placeholder. This is a dangling normative reference: a section
  the state machine relies on does not yet contain the thing it points to.
- §4.0 (identical response whether or not an account exists) and the missing §5.0
  resend/recovery path together create a dead end for a mistyped address: the user
  is reassured a link was sent and has no way to discover or correct that it wasn't.
  These two sections are individually defensible but jointly trap the user.
- §2.2 idempotency ("most recent request invalidates the first") and the absent
  resend UX (§5.0) interact: any resend feature added later must coalesce/replace,
  and the doc should pre-state that so resend and idempotency don't contradict.
- The changelog and front-matter both honestly state delivery UX, cross-device,
  error/accessibility, trust signals, and success criteria "remain open." That is
  accurate self-reporting, but it confirms that the bulk of the Product/UX surface
  is still unbuilt, not that it is resolved.

## Summary

v0.2 made real progress on the security/systems core, and the carried-forward UX
items are honestly flagged rather than hidden, but flagging is not resolving. Every
material Product/UX surface (delivery recourse, error/edge states, accessibility,
trust signals, cross-device, success copy) remains undefined, and §3.2's normative
reference to §6.1 dangles into an empty section. Two of these (undefined
consumed/expired user state, and the absent "didn't get the email" path) are
ship-stopping from a user's perspective. Another round is clearly warranted; I have
substantial material to add and nothing here is yet resolved on the UX axis.
