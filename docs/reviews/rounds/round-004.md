# Round 004: Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.4**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-004/{security,systems,product,skeptic}.md`
- **Prompts perturbed** a fourth time.
- **Verdict:** **One finding from convergence.** Security, Product, and Skeptic all
  converged (0 BLOCKER / 0 FINDING, each proving its prior items closed against the
  text and failing to re-open them). Systems holds **one** FINDING. Per the
  termination rule, one open FINDING blocks convergence, so not yet done, but close.

## Counts (after arbitration and de-duplication)

| Severity | R001 | R002 | R003 | R004 |
|----------|:----:|:----:|:----:|:----:|
| BLOCKER  | 3 | 3 | 1 | 0 |
| FINDING  | 11 | 9 | 3 | 1 |
| ADVISORY | 4 | 5 | 7 | 6 |

Per-lens: Security 0/0/2, Product 0/0/1, Skeptic 0/0/2, Systems 0/1/2.

## Proven closures (re-derived against v0.4, not the changelog)

- **B7 (supersession vs invariant)**: closed: §2.2 deletes the single-live-token
  invariant and supersession outright; a grep finds no surviving "at most one" /
  "supersede" assertion. Targeted-login-denial stays closed (nothing invalidates).
  Confirmed by Systems *and* Skeptic, each re-deriving.
- **F15 (key mismatch)**: closed: consume now contends on the token's own hash-keyed
  row; supersession (the only account-scoped op) is gone (Systems).
- **F16 (clock domain)**: closed: absolute `expires_at` stamped at mint; value
  comparison; named ≤5 s NTP bound (Systems).
- **F17 (legacy / out-of-scope enforcement)**: closed: precondition stated as a hard
  contract *and* enforced in-scope at first sign-in for legacy accounts (Skeptic,
  re-derived; could not re-open).
- Round-003 advisories on queue/DLQ metrics and the `terminal_at` tombstone, closed.

## FINDING (1)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F18 | §7.2/§3.1 | "Successful recovery invalidates all live login tokens," but §3.1's hash-keyed-only per-token storage gives no path to *enumerate* an account's live tokens, so up to 4 attacker-minted links survive recovery for their 10-min window | Systems |

**Arbiter:** upheld as FINDING (not BLOCKER, recovery still rotates the session and
kills other sessions; the residual is the un-revoked minted links, a real but bounded
post-recovery foothold). This is the v0.4 multi-token refactor leaving one earlier
section (§7.2) un-re-derived against it, the same fix-induced-regression pattern,
now down to a single, mechanical data-model gap.

## ADVISORYs (6)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A19 | §2.2 | The "5" cap is descriptive and likely unreachable under §2.1 (≤3 mints/15 min + 10-min expiry), state which control actually binds | Security, Skeptic |
| A20 | §3.2 | Consume-CAS linearizability under the now-replicated store (§3.3) is implicit; state it runs on the primary so a stale-replica GET can't enable double-consume | Security |
| A21 | §2.2 | Coalesce-to-in-flight needs a keyed marker, evaluated off the synchronous path so it can't become an existence oracle | Systems |
| A22 | §3.3/§8.1 | The ≤5 s NTP bound is named but unmonitored; a drifted node breaks expiry with no guardrail | Systems |
| A23 | §7.2 | Legacy first-sign-in enrolment is gated by inbox control only, so it inherits the §7.1 trust root, make that boundary explicit | Skeptic |
| A24 | §5/§6 | Multi-token model means a user may receive more than one email; set that expectation | Product |

## Required revisions for v0.5

The one FINDING must close; the advisories are individually deferrable, but most are
near-free one-clause clarifications and closing them reduces the chance a future fresh
read promotes one to a finding. **Keep the edits surgical**: at this depth, large
rewrites are how regressions get introduced.

1. **§3.1/§7.2 (F18)**: Per-token rows carry an indexed `account_id`; primary lookup
   stays by hash, a secondary account-scoped index exists, and recovery performs an
   account-scoped move of all `issued` rows to a terminal `revoked` state so "invalidate
   all live tokens" is literally executable.
2. **§2.2 (A19)**: Describe the live-token bound as a consequence of §2.1 (typically
   ≤3), with the hard ceiling as an explicit belt-and-suspenders guard against a future
   rate-limit relaxation, so one control unambiguously binds.
3. **§3.2 (A20)**: One clause: the CAS executes on the primary / a linearizable path;
   a stale-replica GET that only *presents* the confirm page can't weaken consumption.
4. **§2.2 (A21)**: One clause: coalescing is best-effort dedup on a short-TTL in-flight
   marker evaluated off the synchronous path (consistent with §4.0).
5. **§8.1 (A22)**: Add a node-clock-offset gauge alerting below the 5 s bound.
6. **§7.2 (A23)**: One sentence: legacy enrolment authority is inbox-control only and
   inherits the §7.1 trust root.
7. **§5.0/§6.0 (A24)**: Note the user may receive more than one email if they re-request.

Re-review v0.5 with a fresh full read and prompts perturbed a fifth time. Convergence
must be **proven**: every critic re-deriving the F18 closure, not assuming it.
