# Product / UX Review: Round 001

Target: `docs/design/magic-link-auth.md` v0.1
Critic: Product / UX

## BLOCKER

### §6.0 / §6.1: Cross-device open is undefined and silently breaks the core flow
- Problem: §6.0 only describes "User clicks the link and is logged in," and explicitly notes (parenthetically) that opening the link on a different device is not handled. The most common real-world pattern is request-on-phone / open-on-laptop (or vice versa), or the link opening in the device's default browser rather than the in-app webview the request came from. The spec defines no behavior for this. Combined with §3.4 ("On click we create a session"), the session is created in whatever browser opened the link, which may not be the device/browser the user is actually trying to sign in on. The user ends up logged in nowhere useful and stuck.
- Why it matters: This is not an edge case; it is a primary path. Email is frequently opened on a different device or app than where the login was initiated. If the spec is silent, the implementation will pick an arbitrary behavior that strands a large fraction of users with no recovery and no explanation. The entire premise of the feature ("sign in by clicking a link we send") fails for these users.
- Suggested resolution: Specify the cross-device contract explicitly. Either (a) require the link to log in the device/browser that opens it and clearly tell the requesting device "Signed in on another device, you can close this tab," or (b) use a same-device-preferred flow with a fallback code (e.g., show a short numeric/OTP code the user can type into the original device). Define what each device's screen shows in both same-device and cross-device cases.

### §6.1: Error / empty / edge states are entirely unspecified
- Problem: §6.1 states outright that error, empty, and edge states are unspecified. There is no defined screen or copy for: expired link, already-used link, malformed/tampered link, link clicked while already logged in, link for an account that no longer exists, or a rate-limited request. A user who clicks an old or reused link sees undefined behavior.
- Why it matters: These states are guaranteed to occur (users sit on emails, click twice, forward links, click stale links from days ago). Without defined states the user hits a raw error or a blank page with no path forward, the single most common cause of abandoned logins. An auth flow with undefined failure states cannot be trusted to ship.
- Suggested resolution: Enumerate every terminal state and define, for each, (1) what the page shows, (2) plain-language copy explaining what happened, and (3) the recovery action (typically a "Send me a new link" button that returns to §2.1). At minimum cover: expired, already-used, invalid/malformed, account-not-found-at-click-time, and already-authenticated.

### §5.0: No "I didn't get the email" path
- Problem: §5.0 says "We send the email and assume it arrives," and flags the absence of a delivery-failure path. There is no resend control, no stated delivery-latency expectation, no spam-folder guidance, and no handling for bounced/undeliverable mail. The confirmation screen (implied by §4.0's "check your inbox") is a dead end if the email never shows up.
- Why it matters: Email delivery routinely fails, delays by minutes, or lands in spam. With no passwords and no recovery story, the email is the only way in, so a missing email is a total lockout, not an inconvenience. "Check your inbox" with no follow-up is the #1 abandonment point for magic-link flows.
- Suggested resolution: On the "check your inbox" screen, specify: a "Resend email" action (with the request-throttling from the security side respected and surfaced as a countdown, not a silent failure), an expected-arrival hint ("usually within a minute"), explicit spam-folder guidance, a "wrong email? change it" affordance, and a defined behavior when the address bounces (tell the user the address looks undeliverable rather than leaving them waiting forever).

## FINDING

### §4.0: Result copy is ambiguous and the two outcomes are not described as user-facing screens
- Problem: §4.0 gives two outcomes, "no account found" vs "check your inbox", but only as message strings, not as defined screens with next actions. "No account found" leaves the user with no path (no link to sign up, no way to retry a typo'd address). "Check your inbox" doesn't say which inbox/address, how long to wait, or what to do next (that gap is the §5.0 BLOCKER, but the copy itself is also underspecified here).
- Why it matters: A user who fat-fingers their email gets "no account found" and is stuck with no obvious correction or signup route. A user on the success screen has no guidance. Both are common, and both produce silent drop-off.
- Suggested resolution: Define each result as a screen: success screen echoes the exact address the link was sent to and offers "edit address" + "resend"; the not-found screen offers "try a different email" and a route to sign up. (Note: the account-enumeration concern in §4.0 is a security matter; reconciling that with UX clarity is a cross-section item flagged below.)

### §6.1: Accessibility of pages and emails is unspecified
- Problem: §6.1 explicitly defers accessibility. There are no requirements for: HTML email plus a plain-text fallback, descriptive link text (vs. a bare "click here" or a raw token URL), color contrast, keyboard focus order on the request and result pages, screen-reader labeling of the email field and submit button, or error-message association with the input.
- Why it matters: If the email is HTML-only, plain-text and some screen-reader/email clients render an empty or broken message and the user can't find the link. Bare-URL or "click here" link text is hostile to screen-reader users. An inaccessible auth flow excludes users from the product entirely, there is no password alternative to fall back on.
- Suggested resolution: Add accessibility requirements: multipart email (HTML + plain text) with the actual link visible as text, descriptive link/button text, WCAG AA contrast on both pages, visible focus states, labeled form fields, and programmatically associated error messages.

### §5.0 / §3.x: Email trust signals and anti-phishing content are undefined
- Problem: Nothing in §5 (Delivery) or §3 (The token) specifies the email's content or sender presentation: no defined From name/address, no subject line, no statement that the email will name the user's account/product, no "if you didn't request this, ignore it" line, and no guidance to help the user distinguish a legitimate login email from a phishing lookalike. A login link in an email is exactly the shape of a phishing attack.
- Why it matters: Magic-link emails train users to click links to log in, which is precisely the behavior phishers exploit. Without explicit trust signals (recognizable sender, clear purpose, expiry statement, "you requested this" framing), cautious users won't trust the email (and abandon) while incautious users are conditioned to click malicious lookalikes.
- Suggested resolution: Specify the email's trust-bearing content: clear From identity, descriptive subject, a line stating the login was requested and from roughly where/when if available, a visible expiry ("this link expires in N minutes"), and an "if this wasn't you, ignore this email" line. Make the legitimate email recognizably distinct.

## ADVISORY

### §2.1: No feedback during request submission
- Problem: §2.1 says "User submits their email. We immediately generate a login link and email it." No loading/pending state, double-submit handling, or client-side validation of the email format is described.
- Why it matters: On a slow connection a user may double-tap submit (triggering duplicate emails) or assume nothing happened. A typo'd-but-syntactically-valid address silently goes nowhere.
- Suggested resolution: Define a pending state, disable the submit control after the first tap, and validate email syntax client-side before submission.

### §1-scope note: No account-recovery story leaves users permanently locked out
- Problem: The scope note flags that there is no recovery story if the user loses access to their email. With no passwords and email as the sole factor, losing email access is an unrecoverable lockout.
- Why it matters: Users change jobs, lose mailbox access, or mistype their address at signup. Permanent lockout with no support path is a real product failure, even if rarer than the daily paths above.
- Suggested resolution: At minimum, document the intended recovery path (support escalation, secondary contact, or an alternate factor) even if out of scope for v1, so the product team knows the gap is acknowledged rather than missed.

## Cross-section coherence flags

- §4.0 vs. security intent: §4.0's distinct "no account found" vs "check your inbox" messages are explicitly seeded as an account-enumeration flaw. The UX desire (clear feedback for a typo'd/unregistered address) directly conflicts with the security need (uniform response). These two requirements must be reconciled in one place, likely a single neutral "if an account exists, we've sent a link" message, rather than left contradictory across sections.
- §3.4 ("On click we create a session") vs §6.0 (cross-device gap): the session is created wherever the link is opened, but §6.0 never reconciles this with the device the user requested from. These two sections must agree on which device ends up authenticated.
- §3.2/§3.3 (no expiry / reusable link) vs §5/§6 (no email expiry messaging or used-link state): the token model and the user-facing copy/states are inconsistent, the email can't truthfully state an expiry the token doesn't have, and §6.1's missing "used/expired link" states stem directly from §3's undefined expiry. Resolve the token lifecycle first, then make the email copy and result screens match it.

## Summary

The document defines only the happy path and explicitly defers every failure, cross-device, accessibility, and trust-signal concern that determines whether real users actually get in. The three BLOCKERs (undefined cross-device open, entirely unspecified error/edge states, and no "didn't get the email" path) each independently strand a large share of users with no recovery, and the §4.0 enumeration-vs-clarity tension is left contradictory across sections. Another round is clearly warranted, this document is far from convergence on the UX axis, and I have substantial material outstanding.

Counts: 3 BLOCKER, 3 FINDING, 2 ADVISORY.
