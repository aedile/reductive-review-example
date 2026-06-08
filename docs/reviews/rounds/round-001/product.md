# Product / UX — round-001

Document: `docs/design/magic-link-auth.md` @ v0.1

## FINDING

### §6.0 — Cross-device open is undefined
- Problem: "User clicks the link and is logged in" assumes one device. The most
  common real flow is request-on-phone, open-on-laptop, and the doc is silent on it.
- Why it matters: If login secretly requires the same device/session that
  requested, a huge fraction of users silently fail with no explanation.
- Suggested resolution: State that login completes in whatever browser opens the
  link, and say so on the confirmation page.

### §6.1 — Error, empty, and accessibility states undefined
- Problem: §6.1 explicitly leaves error/empty/edge and accessibility unspecified.
  No expired-link page, no "already used," no malformed-link state, no a11y bar.
- Why it matters: The unhappy paths are most of real usage; undefined means each
  one ships as a raw stack trace, and excluded users can't complete login at all.
- Suggested resolution: Enumerate the states with neutral copy; commit to WCAG AA
  for emails and pages, including a plain-text email fallback.

### §5.0 — No "I didn't get the email" path
- Problem: Delivery is assumed (§5.0); there is no resend, no latency expectation,
  no spam guidance.
- Why it matters: "Nothing arrived" is the single most common magic-link support
  ticket; with no path, the user is simply stuck.
- Suggested resolution: A rate-limited resend, a stated "arrives within a minute,
  check spam," and a neutral failure message.

### §4.0 — Enumerating copy
- Problem: Telling the user "no account found" both leaks existence (security) and
  dead-ends a legitimate user who typoed their address.
- Why it matters: Worse UX *and* worse security from the same copy.
- Suggested resolution: Uniform "if an account exists, we've sent a link," which
  also nudges the typo'd user to recheck their address.

## ADVISORY

### §5 — Email copy and trust signals unspecified
- Problem: Nothing defines what the email says or how a user knows it's really us.
- Why it matters: Unbranded auth mail reads as phishing; users won't click, or
  will click anything.
- Suggested resolution: Specify sender, subject, and trust signals; descriptive
  link text.

## Cross-section coherence flags
- §4.0 is owned by both us and security; the same copy decision resolves both.

## Summary
The happy path is one sentence and the unhappy paths — cross-device, "no email,"
errors, accessibility — are absent, which is where users actually live. **Another
round is warranted.**
