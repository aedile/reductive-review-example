# Round 003 — Arbiter Aggregate

- **Document:** `docs/design/magic-link-auth.md` @ **v0.3**
- **Panel (frozen):** Security Adversary, Systems Engineer, Product/UX, Skeptical Generalist
- **Per-critic files:** `round-003/{security,systems,product,skeptic}.md`
- **Prompts perturbed** a third time.
- **Verdict:** **Almost there — not converged.** Security and Product both converged
  (0 BLOCKER / 0 FINDING, advisories only, each proving the closures against the
  text). But Systems and the Skeptic independently hit the same new seam: v0.3's
  fix for the targeted-login-denial finding *reopened* the single-live-token
  invariant. One narrow round remains.

## Counts (after arbitration and de-duplication)

| Severity | R001 | R002 | R003 |
|----------|:----:|:----:|:----:|
| BLOCKER  | 3 | 3 | 1 |
| FINDING  | 11 | 9 | 3 |
| ADVISORY | 4 | 5 | 7 |

Per-lens this round: Security 0/0/2, Product 0/0/2, Systems 1/2/2, Skeptic 0/2/2.
The advisory count *rising* as blockers fall is expected — with the big rocks gone,
the panel surfaces finer-grained polish.

## Proven closures (re-derived against v0.3 text, not the changelog)

- **B4 (recovery)** — closed. The Skeptic *tried to re-open the by-omission lockout
  and could not*: §7.2 is now mandatory-at-creation, rate-limited, threat-modeled,
  session-rotating, held to the primary-path bar; §7.1 adds the recovery adversary.
- **B5 (consume-vs-supersede race)** — closed: §3.2 gives `superseded` a real
  terminal state and a named CAS contention point (Systems re-derived half (a)).
- **B6 (undefined error states)** — closed: §6.1 defines the states and §3.2's
  reference now resolves (Product confirmed).
- Plus the round-002 findings on delivery, cross-device pre-fetch (POST-to-consume),
  trust signals, accessibility, timing-parity mechanism, success criteria, and the
  clock/lookup cleanups — all confirmed closed by at least one lens against the text.

## NEW BLOCKER (1) — introduced by the v0.3 fix

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| B7 | §2.2/§3.2 | Session-scoped supersession contradicts "at most one live token per account": a legitimate new-session / lost-tab / new-device re-request can neither supersede (by the anti-targeting rule) nor coexist (by the invariant) — so the design either mints a second live token (violating the invariant) or strands the user | Systems (BLOCKER), Skeptic (as composition FINDING) |

**Arbiter:** Systems graded this BLOCKER; the Skeptic raised the same root as a
FINDING from the lost-tab angle. Unified and **upheld as BLOCKER** — it is a direct
self-contradiction in a load-bearing invariant, and it is the *third consecutive
round* where a fix for one finding (here, F13 targeted-login-denial) created the next
round's headline issue. That pattern is the point of the descent, not a failure of it.

## FINDINGs (3)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| F15 | §3.1/§3.2 | Verify lookup is token-hash-keyed but the serialization point is an "account-keyed row"; the data model never reconciles them, so "exactly one of {consume,supersede} wins" may not hold | Systems |
| F16 | §3.3 | "Single authoritative datastore clock" assumes a single-clock-domain datastore (no replica/multi-primary) the doc never constrains — and the v0.2 tolerance that masked it was removed | Systems |
| F17 | §7.2/§1 | The lockout-fix invariant ("no account without a recovery channel") is enforced entirely inside account-creation, which §1 puts out of scope; silent on legacy/migrated accounts | Skeptic |

## ADVISORYs (7)

| # | § | Title | Raised by |
|---|-----|-------|-----------|
| A12 | §7.2 | Recovery success invalidates live *tokens* but doesn't explicitly terminate other live *sessions* | Security |
| A13 | §4.0 | The account-existence *check* itself may still be on the sync path (only the *work* was moved off) | Security |
| A14 | §6.0 | The positive post-login success landing is unspecified | Product |
| A15 | §5.0/§8.1 | Bounded queue has no depth/saturation gauge or dead-letter-rate — no leading indicator before sends fail | Systems |
| A16 | §8.2 | Tombstone carries `consumed_at` only; superseded/expired have no `terminal_at` basis for the reap-ordering rule | Systems |
| A17 | §1 | Abandon condition triggers only on completion rate; the lockout/support-rate criterion (the one measuring the recovery fix) has no trigger | Skeptic |
| A18 | §7.2 | Recovery "second verified channel" isn't required to be *independent* of the primary email, so it can collapse onto the same trust root for shared/forwarded inboxes | Skeptic |

Coherence flag to fix: §6.1's bare "rate-limited" label should explicitly render as the
non-enumerating hint, never a throttle confirmation (else it re-opens §4.0).

## Required revisions for v0.4

1. **§2.2/§3.2 (B7)** — Resolve the trilemma by **dropping the single-live-token
   invariant and supersession entirely**: allow a small bounded set (≤5) of
   concurrently-valid, **independently single-use** tokens per account; **no request
   ever invalidates another**. This closes B7 (no invariant to contradict; lost-tab
   user just gets an additional valid token) *and* keeps F13 closed (nothing
   invalidates, so no third party can kill a victim's link). Replay surface stays
   bounded by single-use + 10-min expiry + the §2.1 rate-limit cap.
2. **§3.1/§3.2 (F15)** — With supersession gone, consume contends **only on the
   token-hash row** (no account-keyed serialization). State that explicitly; the
   §3.1 hash-indexed lookup and the §3.2 CAS now operate on the same row by construction.
3. **§3.3 (F16)** — Persist an absolute `expires_at` at mint; require all datastore
   nodes NTP-synced within a stated bound (e.g., ≤5 s) and name that bound as the only
   skew window; or evaluate expiry on the primary. Make the topology assumption explicit.
4. **§7.2/§1 (F17)** — State the recovery invariant as a **hard precondition this
   design depends on**, name that account-creation (out of scope) MUST enforce it, and
   enforce it **in-scope at first sign-in** for legacy/no-recovery accounts (prompt to
   enrol before a session is established), or name them an owned lockout class.
5. **Cleanups (A12–A18 + coherence)** — recovery terminates other sessions (A12);
   move the existence check off the sync path (A13); define the success landing (A14);
   add queue-depth + DLQ metrics (A15); generalize the tombstone to `terminal_at`
   (A16); attach a trigger to the lockout-rate criterion (A17); require recovery-channel
   independence from the primary email (A18); clarify §6.1's rate-limited rendering.

Re-review v0.4 with a fresh full read and prompts perturbed a fourth time. Convergence
is plausible next round, but it must be **proven**, not assumed.
