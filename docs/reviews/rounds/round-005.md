# Round 005 — Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.5**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-005/{security,systems,product,skeptic}.md`
- **Prompts perturbed** a fifth time.
- **Verdict:** **Two findings from convergence.** Security and Skeptic converged
  (each proving its prior items closed). Systems and Product each hold **one** finding
  — and both findings were *introduced by the v0.5 edits themselves*. Not converged.

## Counts (after arbitration and de-duplication)

| Severity | R001 | R002 | R003 | R004 | R005 |
|----------|:----:|:----:|:----:|:----:|:----:|
| BLOCKER  | 3 | 3 | 1 | 0 | 0 |
| FINDING  | 11 | 9 | 3 | 1 | 2 |
| ADVISORY | 4 | 5 | 7 | 6 | 5 |

Per-lens: Security 0/0/2, Skeptic 0/0/0, Systems 0/1/3, Product 0/1/1.

## Proven closures (re-derived against v0.5)

- **F18 (recovery enumeration)** — closed: §3.1 `account_id` secondary index gives
  recovery a key it holds; §3.2 adds the `revoked` terminal state; §7.2 composes them,
  hash-only verify path preserved (Systems re-derived).
- Round-004 advisories on the cap framing, legacy-enrolment trust boundary, etc. —
  closed (Skeptic re-derived both of its advisories against the exact text).

## FINDINGs (2) — both introduced by the v0.5 edits

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F19 | §7.2 | Recovery terminates sessions *before* revoking tokens — an attacker who consumes a still-`issued` token in the gap mints a session that post-dates the termination sweep and survives recovery | Systems |
| F20 | §6.1 | The v0.5 edit folded `revoked` into the "already used" copy — telling a recovery-completing user a link they never used was "already used" reads as "someone used my link," generating exactly the support contact §1's metric targets | Product |

**Arbiter:** Both upheld as FINDINGs. Both are mechanical and both are *my own v0.5
edits' fault* — the ordering finding from making the revoke an afterthought clause,
the copy finding from merging two states for terseness. This is the descent's final
lesson in miniature: even cleanup edits at round five introduced regressions, which is
exactly why the loop doesn't stop until the panel re-reads and *proves* clean.

## ADVISORYs (5)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A25 | §7.2/§3.2 | State that revoke enumerates and writes **on the primary** (secondary-index reads can be stale), each row's transition contending with consume on that one row | Systems |
| A26 | §8.2 | `revoked` has a `terminal_at` but no reap TTL — unbounded growth for repeat-recovery accounts | Systems |
| A27 | §8.1 | The clock-offset gauge alerts "toward" the 5 s bound with no number; needs a margin (e.g. ≥3 s) to be a leading indicator | Systems |
| A28 | §5.0 | The multi-email fact is in the spec but not in the displayed confirmation copy ("you may get more than one email — any works") | Product |
| A29 | §2.2/§3.2 | (Security) two guardrail notes for future edits — keep the cap/rate-limit relationship and the linearizable-CAS explicit | Security |

## Required revisions for v0.6 (surgical — the end of the descent)

1. **§7.2 (F19)** — Reorder: **revoke all live tokens first** (fencing further
   consumes), **then** terminate other sessions and rotate (catching any session a
   just-in-time consume created). State that the sequence, not the set, carries the
   safety property.
2. **§6.1 (F20)** — Split the copy: `consumed` → "already used"; `revoked-by-recovery`
   → a distinct, neutral "for your security, links from before your recent account
   recovery no longer work — request a fresh one." Both keep the "send me a new link"
   action and §4.0 neutrality.
3. **Advisories (A25–A28)** — one clause each: revoke on the primary (A25); `revoked`
   reap TTL = 7 days (A26); clock-offset warn at ≥3 s (A27); add the multi-email line to
   the §5.0 confirmation copy (A28).

Re-review v0.6 with a fresh full read and prompts perturbed a sixth time. The two
findings are narrow; convergence is expected — but it must be **proven**, and the v0.6
edits must not introduce a seventh-round regression.
