# Round 001 — Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.1**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-001/{security,systems,product,skeptic}.md`
- **Verdict:** **Far from done.** Not converged — 4/4 critics request another round.

## Counts (after arbitration and de-duplication)

| Severity | Count |
|----------|:-----:|
| BLOCKER  | 3 |
| FINDING  | 11 |
| ADVISORY | 4 |

Raw, the panel returned 10 BLOCKER / 16 FINDING / 10 ADVISORY across four files —
heavily overlapping, and with genuine disagreement on severity. The arbiter's job
this round is mostly **adjudication**, recorded below.

## BLOCKERs (3) — must fix before v0.2 can be trusted

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| B1 | §3.1 | Timestamp-derived token, no at-rest hashing — forgeable credential | Security, Systems |
| B2 | §3.2/§3.3 | No expiry, no single-use, no atomic state machine — replayable + unimplementable verify | Security, Systems |
| B3 | §3.4 | No session rotation on login — session fixation | Security |

These three each independently yield account takeover, and they chain with F1/F2
into an unauthenticated-takeover path. Undisputed.

## FINDINGs (11) — substantive; should fix

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F1 | §2.1 | No send rate-limiting / idempotency / burst protection | Security, Systems, Skeptic |
| F2 | §4.0 | Account enumeration via differential response | Security, Product, Skeptic |
| F3 | §5.0 | Delivery failure unhandled; no "didn't get it" path; single-channel availability | Product, Systems, Security, Skeptic |
| F4 | §6.0 | Cross-device open undefined (incl. email-scanner pre-fetch consuming a single-use token) | Product, Security, Skeptic |
| F5 | §6.1 | Error / empty / edge states undefined | Product |
| F6 | §6.1 | Accessibility of emails and pages unspecified | Product |
| F7 | §5/§3 | Email trust signals / anti-phishing content undefined | Product |
| F8 | §1 | No stated threat model | Skeptic, Security |
| F9 | §1 | Account recovery / email-loss lockout is unowned | Skeptic, Product, Security |
| F10 | §1 | No success criteria / acceptance bar | Skeptic |
| F11 | §3 | No observability/metrics and no token-retention policy | Systems |

## ADVISORYs (4)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A1 | §3.3 | Clock-skew authority undefined once expiry exists | Security, Systems |
| A2 | §2.1 | No request-submission feedback / double-submit guard / client validation | Product |
| A3 | §3.3 | §3.3 is an empty placeholder; section numbering irregular (weakens the audit trail) | Skeptic |
| A4 | §1 | Premise unjustified — no rationale for magic links over passkeys/OTP | Skeptic |

## Arbiter adjudications (where the panel disagreed)

1. **Cross-device (F4): Product graded BLOCKER, Security/Skeptic FINDING → resolved
   FINDING.** It strands real users and has a security edge (scanner pre-fetch), but
   it cannot be designed until the B1/B2 token rewrite exists. It is a FINDING that
   the v0.2 token work must not foreclose, not an independent ship-blocker.
2. **Threat model (F8): Skeptic graded BLOCKER, Security graded ADVISORY → resolved
   FINDING, and required for v0.2.** The Skeptic is right that without it the other
   findings have no acceptance bar; Security is right that a missing threat model is
   not itself a takeover. Landing in the middle: it is a FINDING, and it is pulled
   into v0.2 scope because several other gradings depend on it.
3. **Recovery/lockout (F9): Skeptic BLOCKER, Product FINDING, Security ADVISORY →
   resolved FINDING.** An accepted, *stated and owned* "recovery is delegated to X"
   is a sufficient resolution; the defect is silence, not the absence of a built
   recovery flow. FINDING.
4. **Product's §6.1 and §5.0 BLOCKERs → downgraded to FINDING (F3, F5).** Real and
   user-stranding, but the document's *trust* hinges on the auth core (B1–B3); the
   UX-completeness gaps are substantive findings, not trust blockers.
5. **Premise justification (Skeptic FINDING) → downgraded to ADVISORY (A4).** The
   passwordless choice is defensible; documenting the alternatives is good practice,
   not material to trust.

No averaging: each contested item is decided and the reasoning recorded.

## Required revisions for v0.2

The arbiter does **not** scope v0.2 to "everything." It closes the BLOCKERs and the
findings that are unambiguous, security-adjacent, or prerequisite to grading the
rest; it carries the UX-completeness and premise findings to round 2.

1. **§3.1** — CSPRNG token ≥128 bits, stored only as a hash, constant-time compare. (B1)
2. **§3.2/§3.3** — Single-use with atomic compare-and-set consume; short absolute
   expiry; defined issued/consumed/expired terminal states. (B2)
3. **§3.3** — Evaluate expiry against server time with a small stated skew tolerance;
   fill the empty placeholder. (A1, A3)
4. **§3.4** — Rotate session id on login; set `HttpOnly`/`Secure`/`SameSite`. (B3)
5. **§2.1/§2.2** — Per-address + per-IP rate limits with backoff; one live token per
   account (idempotency/coalescing). (F1)
6. **§4.0** — Uniform "if an account exists, we've sent a link" response, matched
   timing, no side-effect leak. (F2)
7. **§7 (new)** — State the threat model (inbox as trust root, out of scope) and
   **own** the recovery/lockout dependency by delegating it explicitly. (F8, F9)
8. **§8 (new)** — Send/verify metrics and a token-retention/reaping policy; raw
   tokens never logged. (F11)
9. **§1** — One-line rationale for the passwordless choice; regularize numbering. (A4, A3)
10. **Changelog** — append the v0.2 entry.

**Carried to round 2:** F3 (delivery UX), F4 (cross-device), F5 (error states),
F6 (accessibility), F7 (trust signals), F10 (success criteria), A2 (request feedback).

Re-review v0.2 with a fresh full read and **perturbed** prompts.
