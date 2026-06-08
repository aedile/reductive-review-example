# Round 002: Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.2**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-002/{security,systems,product,skeptic}.md`
- **Prompts perturbed** this round (each critic's checklist reversed/reordered).
- **Verdict:** **Closing on the original BLOCKERs, but not converged.** The three
  round-001 BLOCKERs are genuinely closed (re-derived from the text by Security and
  Systems, not taken on faith), but the v0.2 revision *introduced three new
  BLOCKERs*. 4/4 critics request another round.

## Counts (after arbitration and de-duplication)

| Severity | Round 001 | Round 002 |
|----------|:--------:|:--------:|
| BLOCKER  | 3 | 3 |
| FINDING  | 11 | 9 |
| ADVISORY | 4 | 5 |

The headline is **not** "3 → 0 blockers." It is "3 original blockers closed, 3 new
ones opened by the fixes." This is the descent behaving honestly: a revision can add
surface. Raw panel output was 5 BLOCKER / 12 FINDING / 8 ADVISORY before merge.

## Re-derived confirmations (round-001 BLOCKERs: checked, not assumed)

- **B1 (token entropy)**: closed: ≥128-bit CSPRNG, hash-at-rest, constant-time
  compare (§3.1). Confirmed by Security and Systems independently.
- **B2 (replay/state machine)**: closed: explicit issued→consumed/expired machine
  with atomic CAS on consume, 10-min TTL (§3.2). Confirmed.
- **B3 (session fixation)**: closed for the primary path: id rotated, `HttpOnly`/
  `Secure` cookies (§3.4). Confirmed.

## NEW BLOCKERs (3): introduced or left unresolved by v0.2

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| B4 | §7.2 | Recovery path is unsound: enrolment is *optional* so the default user is still lockable-out, **and** the recovery channel is unscoped / un-threat-modeled (the new weakest link) | Skeptic, Security |
| B5 | §2.2/§3.2 | Single-live-token invariant has no backing state and no serialization point; it races with the §3.2 consume | Systems |
| B6 | §6.1/§3.2 | Consumed/expired/malformed token has no defined user-facing state; §3.2's normative "defined response (see §6.1)" dangles into an empty section, unimplementable and user-stranding | Product |

## FINDINGs (9)

| # | § | Title | Raised by | New? |
|---|-----|-------|-----------|:----:|
| F12 | §2.1/§4.0 | Enumeration timing oracle, §4.0 asserts timing parity the §2.1/§2.2 work contradicts; no mechanism given | Security | new |
| F13 | §2.2 | Targeted login-denial, a third party can invalidate the victim's live link / burn their request budget | Security | new |
| F14 | §8 | Observability lists `send-failures` §5.0 can't emit, omits a rate-limit-drop counter, and row-reaping silently breaks replay detection | Systems | new |
| F3 | §5.0 | Delivery failure / resend / "didn't get it" path; also still synchronous with no burst absorber | Product, Systems | carried |
| F4 | §6.0 | Cross-device + email-scanner pre-fetch can consume the single-use token; reconcile with §3.2 | Product, Security, Skeptic | carried |
| F5 | §6.0 | Confirmation / success / per-step copy undefined | Product | carried |
| F6 | §5/§6 | Accessibility of email and pages unspecified | Product | carried |
| F7 | §5 | Email trust / anti-phishing signals undefined | Product | carried |
| F10 | §1 | No success criteria / acceptance bar | Skeptic | carried |

## ADVISORYs (5)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A5 | §3.3 | ±60s skew is symmetric (extends effective lifetime) and contradicts the "single authoritative clock" claim | Security, Systems |
| A7 | §3.1 | "O(1) keyed lookup" + "constant-time compare" are ambiguous together, state the lookup model | Systems |
| A8 | §2.1 | A legitimately rate-limited user gets no non-enumerating hint they're throttled | Product |
| A10 | §7.1 | Threat model is a defense list; it never names assets or adversaries, so omissions can't be checked | Skeptic |
| A11 | §1/§7.1 | "Layer a second factor (out of scope)" walks back the §1 premise; scope the design to the low-assurance segment explicitly | Skeptic |

## Arbiter adjudications

1. **B4 merges two angles into one blocker.** Security attacks the recovery *channel*
   (unscoped, un-rate-limited, support-desk social engineering); the Skeptic attacks
   the recovery *enrolment* (conditional "must" ⇒ optional ⇒ default user still
   lockable). Same section, same root: v0.2 *named* the round-001 lockout finding
   without *closing* it and added an unguarded path doing so. One BLOCKER, two
   required fixes.
2. **Product's §5.0 "no resend" BLOCKER → FINDING (F3).** Genuinely user-stranding,
   but the document's *trust* hinges on B4-B6; the resend gap is a high-priority
   completeness FINDING, not a trust blocker. Recorded over Product's objection.
3. **Product's §6.1 BLOCKER upheld (B6), on implementability, not just UX.** The
   decisive factor isn't "bad UX"; it's that §3.2 makes a *normative* reference to a
   response §6.1 does not contain. The state machine is unimplementable as written.
4. **A5/A7 (clock skew, lookup model) stay advisory**: real inconsistencies, low
   stakes; fold into the v0.3 cleanup, don't gate on them.

## Required revisions for v0.3

v0.3 must close all three new BLOCKERs and, since the remaining findings are all
legitimate and mostly mechanical, close them too, leaving round 3 to verify, not to
discover:

1. **§7.2 (B4)**: Make a recovery channel **mandatory at account creation** (no
   account without one) *or* state "no fallback ⇒ permanent lockout" as an owned
   constraint with a named owner. Bring recovery **inside §7.1**: assurance bar for
   the second channel, rate-limit + lockout on recovery attempts, defined identity
   proof for support-mediated recovery, and "successful recovery rotates the session
   and invalidates live tokens."
2. **§3.2/§2.2 (B5)**: Add an `issued → superseded` transition; make supersession a
   single atomic, account-keyed step that contends on the same row as the consume CAS,
   so exactly one of {consume, supersede} wins; define the loser's outcome.
3. **§6.1 (B6)**: Define every terminal/error state (expired, already-used,
   malformed, rate-limited, wrong-account) as concrete, account-existence-neutral copy
   with a "send me a new link" recovery action. This is the response §3.2 points to.
4. **§5.0 (F3)**: Bounded async retry with backoff behind a throttled queue; recorded
   send outcome; neutral failure state; rate-limited resend; latency + spam guidance.
5. **§6.0 (F4)**: Require a deliberate user gesture to consume (GET *presents* a
   "confirm sign-in" button; **POST consumes**) so scanner pre-fetch can't burn the
   token; define the cross-device outcome (device that confirms gets the session).
6. **§4.0 (F12)**: State the *mechanism* for timing parity (do the token-mint /
   idempotency / enqueue work off the synchronous response path), don't just assert it.
7. **§2.2 (F13)**: Scope idempotency/invalidation so a third-party request can't kill
   the victim's live token (originating-session-scoped, or a small bounded set of
   independent single-use tokens).
8. **§8 (F14)**: Add a `rate_limited`/dropped counter; mark `send-failures` dormant
   until F3 lands; retain a minimal consumed-token tombstone past row-reap so replays
   stay classifiable; state the actual TTLs.
9. **§6/§5 (F5, F6, F7)**: Per-step copy; WCAG AA + multipart email with readable
   plaintext link; sender identity / single first-party link domain / SPF-DKIM-DMARC /
   "we'll never ask for your password."
10. **§1 (F10, A11)**: Measurable success criteria (time-to-login, completion rate,
    delivery SLA, acceptable lockout/support rate, abandon condition); scope the design
    to the low-assurance consumer segment explicitly.
11. **Cleanups (A5, A7, A8, A10)**: Resolve the skew/clock contradiction; state the
    lookup model; add a non-enumerating "still waiting?" hint; give §7.1 an
    asset/adversary list.

Re-review v0.3 with a fresh full read and prompts perturbed a third time.
