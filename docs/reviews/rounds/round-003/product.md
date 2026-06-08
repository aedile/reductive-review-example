# Product / UX — round-003

Document: `docs/design/magic-link-auth.md` @ v0.3
(Prompt perturbed: started from accessibility, then error states, then cross-device.)

## (no BLOCKER / FINDING / ADVISORY)

## Fresh-read confirmation (proving the drop, per the guard)
- **A6 closed:** §6.0 now states login completes in whatever browser opens the link
  and surfaces it on the confirmation page — the phone→laptop case is explained.
- **A7 closed:** §6.1 enumerates expired / used / malformed / rate-limited /
  delivery-failed / wrong-account states with neutral copy, and commits to WCAG AA
  with a plain-text email fallback.
- **F3/§5.0 closed:** the "didn't get it? resend" control with a latency
  expectation is present.
- I re-read each page/state described rather than trusting that "promoted to v0.3"
  meant "done."

## Summary
The unhappy paths that were missing in rounds 1–2 are now defined, accessible, and
explained. **Nothing material to add.**
