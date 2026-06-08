# Round 005 — Skeptical Generalist

Fresh full read of `magic-link-auth.md` v0.5. Perturbed entry order per this round's
instruction: (1) did the four v0.5 edits — `account_id` index, `revoked` state,
belt-and-suspenders cap, legacy-enrolment trust boundary — introduce any new seam between
lenses; (2) premise/scope and success bar; (3) recovery soundness. Then I re-tested my two
round-004 ADVISORYs against specific text.

## Re-test of round-004 ADVISORYs (did v0.5 close them?)

**(1) Implicit legacy-enrolment authority — CLOSED against the exact text I asked for.**
My round-004 advisory asked for "one sentence in §7.2 noting that legacy enrolment
authority is inbox-control only and therefore inherits the §7.1 trust root." v0.5 §7.2 now
carries precisely that: "(That first-sign-in enrolment is gated by inbox control only, so
it inherits the §7.1 trust root — it does not protect a legacy account whose inbox is
*already* compromised, which is out of scope by assumption.)" The boundary is now explicit,
not inferred. Nothing residual.

**(2) Possibly-unreachable concurrency cap — CLOSED against the exact text I asked for.**
My advisory asked the doc to "state that the cap is a belt-and-suspenders ceiling the rate
limit normally keeps slack, or reconcile the two constants so the binding control is
unambiguous." v0.5 §2.2 now names the binding control explicitly: "The **binding control on
the live-token count is the §2.1 rate limit** ... a hard ceiling of **5** is enforced
separately as a belt-and-suspenders guard so a future relaxation of §2.1 can't silently
unbound the count." The dead-text ambiguity is gone; the rate limit is the real bound, the
cap is a named guardrail. Nothing residual.

## Did the four v0.5 edits introduce a new seam? (the primary task this round)

I probed each edit for a seam that falls *between* lenses — the failure mode the
anti-rubber-stamp guard exists to catch.

- **`account_id` secondary index (§3.1).** The obvious worry is a new enumeration/timing
  surface: a second index keyed on account identity. §3.1 fences it correctly — "the
  primary verify path still goes only by hash," the index "equality *is* the comparison,"
  and the account-scoped index is used *only* by recovery (§7.2), never on the verify path.
  It is write-time populated and read only by an authenticated recovery operation, so it
  adds no oracle on the public request path (§4.0 parity is untouched). No new seam.

- **`revoked` terminal state (§3.2) vs. the consume CAS (race seam).** This is the sharpest
  candidate. Recovery revokes via an account-scoped CAS (`issued → revoked`) while a
  legitimate consume may be in flight (`issued → consumed`) on the same row. Both transitions
  start from `issued` and are terminal. §3.2 makes consume a "single atomic compare-and-set
  ... on the **primary / a linearizable path**," so the two CAS operations serialize on one
  row and the loser "fails closed." Whichever wins, the outcome is safe: if revoke wins, the
  link dies (intended); if consume wins, recovery *also* "terminates the account's other
  active sessions" (§7.2), so the freshly minted session is killed anyway. The race resolves
  to a safe terminal state on every interleaving. No new seam — the linearizable-path edit
  (also v0.4/v0.5) is exactly what closes it.

- **Belt-and-suspenders cap (§2.2).** Now explicitly subordinate to §2.1; it cannot
  contradict the limiter because it is declared a ceiling, not the bound. No seam.

- **Legacy-enrolment trust boundary (§7.2).** Addressed above; it closes a seam rather than
  opening one, and it correctly hands the inbox-compromise case to the §7.1 trust root.

## Premise / scope / success bar (re-read)

- The passwordless premise is defended on its own terms in §1 ("email possession is already
  the de-facto recovery factor ... Passkeys/OTP are reasonable alternatives, not precluded")
  and, crucially, is *falsifiable*: §1's abandon condition "completion rate < 90% after
  delivery and resend are addressed reconsiders the passwordless premise." The premise can
  lose. That is the strongest version of a stated bar.
- The lockout case — my lens's standing obligation — is owned (§7.2 named lockout class) and
  the metric that measures it gates action ("lockout/support rate breaching 0.1% for 3
  consecutive periods escalates a recovery-path review"). The recovery design and the success
  bar are mutually load-bearing, not decorative.

## BLOCKER

_None._

## FINDING

_None._ I tried to manufacture a material gap from each v0.5 edit and from the seams between
security/systems/recovery, and each candidate resolves inside an explicitly stated boundary
(the §7.1 trust root, the §2.1 limiter, or the linearizable consume path) rather than falling
between owners.

## ADVISORY

_None that I can in good conscience raise._ Both round-004 ADVISORYs are closed against the
specific text I requested, and the v0.5 edits introduced no new residual. I decline to
invent an advisory to decorate a clean convergence.

## Cross-section coherence flags

- `revoked` is consistent across all four places it appears: §3.2 (terminal state, "only via
  recovery, §7.2"), §6.1 ("already used (consumed or revoked-by-recovery)"), §7.2 (the
  account-scoped revoke operation), and §8.2 (`terminal_at` "defined for consumed, expired,
  *and* revoked"). The new state did not leave a dangling reference in any lens.
- The `account_id` index has exactly one declared reader (§7.2 recovery) and §3.1 states the
  verify path does not use it — §3.1 and §7.2 agree on its single purpose; no two sections
  disagree about what it is for.
- Expiry (10 min) and the NTP skew bound (≤ 5 s) remain consistent across §2.2, §3.2, §3.3,
  §5.1, and the §8.1 clock-offset gauge. No contradiction surfaced on the fresh read.
- The changelog's v0.5 entry accurately attributes each edit to the round-004 finding/
  advisories it closes; "Converged at round 005" matches the state I observe.

## Summary
v0.5 closes both of my round-004 ADVISORYs against the exact text I asked for (explicit
legacy-enrolment trust boundary in §7.2; the §2.1 rate limit named as the binding control
with the cap demoted to a stated guardrail in §2.2). I specifically hunted for a new seam in
each of the four v0.5 edits — the `account_id` index, the `revoked` state's race with the
consume CAS, the cap, and the legacy-enrolment boundary — and each resolves to a safe outcome
inside a stated boundary rather than falling between lenses. I have nothing material to add
and another round is not warranted from my lens; I decline to invent a finding to avoid a
convergence the document has earned.
