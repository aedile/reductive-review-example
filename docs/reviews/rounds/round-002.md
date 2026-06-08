# Round 002 — Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.2**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-002/{security,systems,product,skeptic}.md`
- **Prompts perturbed** this round (each critic's checklist reordered) per the
  anti-rubber-stamp guard.
- **Verdict:** **Closing.** Not converged — 4/4 critics still request another round.

## Counts (after de-duplication)

| Severity | Round 001 | Round 002 | Δ |
|----------|:--------:|:--------:|:--:|
| BLOCKER  | 3 | **0** | −3 |
| FINDING  | 7 | **2** | −5 |
| ADVISORY | 5 | **4** | −1 |

## FINDINGs (substantive; should fix)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F2 | §3.4 | No session rotation (fixation) | Security |
| F3 | §5.0 | No delivery-failure path / "didn't get it" | Systems, Product |

## ADVISORYs (worth noting)

| # | § | Title | Raised by | Note |
|---|-----|-------|-----------|------|
| A6 | §6.0 | Cross-device guidance thin | Product | re-graded from F5 |
| A7 | §6.1 | Error/edge + accessibility undefined | Product | re-graded from F6 |
| A8 | §1/§7 | Recovery/lockout + threat model unstated | Skeptic | re-graded from F7 (+A5) |
| A9 | §8 | Logging hygiene + no send/verify metrics | Security, Systems | merges A1+A3 |

## Arbiter decisions

**1. The BLOCKER→0 drop is real, and I checked.** Per the guard, a collapse gets
scrutiny, not applause. The Security critic re-derived each BLOCKER fix from v0.2
rather than trusting the changelog (replay fails closed, send is rate-limited, token
is CSPRNG, response is uniform). The drop reflects work, not fatigue. Recorded.

**2. Three findings were downgraded to advisory — and I am not letting that stand
as "deferred."** Product downgraded F5 (cross-device) and F6 (error/a11y); Skeptic
downgraded F7 (recovery/lockout). Each downgrade is *defensible* — with the BLOCKERs
gone, these are quality gaps, not trust blockers — and **each critic flagged its own
downgrade for me**, which is the protocol working as intended. But "advisory" must
not become "ignore." Decision: **A6, A7, and A8 are scheduled into the v0.3 revision
alongside the two findings.** Softening severity changed the label, not the
obligation.

**3. No genuine disagreement to adjudicate.** F3 was raised by Systems and Product
on the same section (§5.0); one delivery-failure + resend design closes both. A9
merges the Security and Systems logging/metrics advisories.

## Required revisions for v0.3

1. **§3.4** — Rotate the session id on successful login; state cookie flags. (F2)
2. **§5.0** — Bounded send retry with backoff; record outcome; neutral failure
   state; rate-limited resend with a latency expectation. (F3)
3. **§6.0** — State cross-device support explicitly and surface it on the
   confirmation page. (A6 — promoted back into scope)
4. **§6.1** — Enumerate error/empty/edge states with neutral copy; commit to WCAG
   AA with a plain-text email fallback. (A7 — promoted back into scope)
5. **§7 (new)** — State the threat model (inbox as trust root and out-of-scope
   assumption) and a delegated recovery/lockout story. (A8 — promoted back into scope)
6. **§8 (new)** — Send/verify metrics; state that raw tokens are never logged. (A9)
7. **Changelog** — append the v0.3 entry.

That leaves only genuinely-deferrable polish for round 3. Re-review v0.3 with a
fresh full read and perturbed prompts, and treat any sudden "nothing to add" with
suspicion.
