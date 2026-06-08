# Round 001 — Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.1**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-001/{security,systems,product,skeptic}.md`
- **Verdict:** **Far from done.** Not converged — 4/4 critics request another round.

## Counts (after de-duplication)

| Severity | Count |
|----------|:-----:|
| BLOCKER  | 3 |
| FINDING  | 7 |
| ADVISORY | 5 |

Raw critic output overlapped (enumeration and the send path were each raised by
two lenses). The arbiter merges duplicates into one finding attributed to both.

## BLOCKERs (must fix before v0.2 can be trusted)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| B1 | §3.2 | No expiry / replayable link | Security, Systems (state machine) |
| B2 | §2.1 | No send rate-limiting | Security, Systems |
| B3 | §3.1 | Predictable / low-entropy token | Security |

## FINDINGs (substantive; should fix)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F1 | §4.0 | Account enumeration via response | Security, Product |
| F2 | §3.4 | No session rotation (fixation) | Security |
| F3 | §5.0 | No delivery-failure path | Systems, Product |
| F4 | §3.3 | Clock skew undefined once expiry exists | Systems |
| F5 | §6.0 | Cross-device open undefined | Product |
| F6 | §6.1 | Error/empty/edge + accessibility undefined | Product |
| F7 | §1 | No account-recovery / lockout story | Skeptic |

## ADVISORYs (worth noting; may defer)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A1 | §3 | Tokens may leak into logs | Security |
| A2 | §5 | Email copy / trust signals unspecified | Product |
| A3 | §3 | No send/verify metrics | Systems |
| A4 | §5 | Link branding unspecified | Product |
| A5 | §1 | Threat model unstated | Skeptic |

## Arbiter decisions

There was no real disagreement on severity this round; the work is in
**prioritization**, not adjudication. Decisions:

- **v0.2 closes all three BLOCKERs.** The token is the credential, so B1+B3 are
  one coherent rewrite of §3; B2 is the send path. Nothing else is trustworthy
  until these land.
- **Fold F1 (enumeration) into v0.2 as well.** It is cheap — a single uniform
  response (§4.0) closes it — and it was raised by two lenses. No reason to carry it.
- **Carry F2–F7 to subsequent rounds.** They are real and will be tracked to
  closure; they are not ship-stoppers and several (F4 clock-skew) only become
  concrete *after* the v0.2 token rewrite exists.
- **Advisories logged, none actioned this round.** A1 and A3 will be revisited once
  the token has real entropy (an entropy-free token in a log is moot).
- **Anti-rubber-stamp note:** this is round 1, so there is no prior round to
  rubber-stamp. The guard to watch from here is the opposite — a future sudden
  collapse to zero. Recorded so round 2 checks it.

## Required revisions for v0.2

1. **§3.1** — Replace the timestamp-derived token with 32 bytes from a CSPRNG;
   store only its hash. (B3)
2. **§3.2** — Make the token single-use, invalidated server-side on consume, with a
   short absolute expiry (10 min). (B1)
3. **§3.3** — As a consequence of adding expiry, state that expiry is evaluated
   against server time with a fixed skew tolerance. (pre-empts F4)
4. **§2.1 / §2.2** — Rate-limit sends per address and per IP with backoff; one live
   token per account (idempotency). (B2)
5. **§4.0** — Single uniform "if an account exists, we've sent a link" response with
   matched timing. (F1)
6. **Changelog** — append the v0.2 entry recording the above.

After these, re-review v0.2 with a fresh full read and **perturbed** prompts.
