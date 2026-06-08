# The Executable Critic: a non-LLM lens that runs

[`FAILURE-MODES.md`](FAILURE-MODES.md) argues the highest-leverage check is a
*different kind* of verifier that runs, convert judgment into computation. A repo that
asserts that and never does it has a claim without an artifact. So here is the artifact,
[`scripts/executable_critic.py`](../../scripts/executable_critic.py): a zero-dependency
model-checker over three v0.6 claims.

```
python3 scripts/executable_critic.py
```

## What "decorrelated" does and does not mean here

Be precise, because the easy version of this claim is false. The critic is decorrelated
from the LLM panel **at the execution layer**: it computes interleavings in Python
instead of predicting tokens, so it cannot inherit a reasoning slip. It is **not**
decorrelated in *agenda*: its constants and the properties it checks were transcribed
from the spec and from the panel's own findings (A19, F19) by the same hand. So it can
only test claims someone already thought to make, **it cannot find a flaw no lens looked
for, and it cannot catch a blind spot the panel shares.** It is a calculator pointed at
the panel's arithmetic, not an independent oracle.

## What it checks (each with a negative control the same engine must trip)

The earlier version of this file oversold two of these as "computed the real maximum"
and "model-checked over every interleaving" when the code was actually a pair of
tautologies. That was caught in review and the checks were rewritten to genuinely
enumerate interleavings; here is what they now do.

| # | Claim (v0.6) | How it's checked | Result | Control (proves the check can fail) |
|---|--------------|------------------|--------|-------------------------------------|
| 1 | §2.2 live-token count is bounded; the rate limit binds | an **exact maximizer** (`rate_count * ceil(ttl/window)`, the cluster-packing optimum), self-tested against hand-computed maxima | **max live = 3** | a `3/5min, 15min-ttl` regime computes **9 > 5**, and a built-in self-test fails loudly if the formula is wrong |
| 2 | §3.2 atomic CAS ⇒ at most one winner | **one** interleaving engine over read/write sub-steps, `atomic` flag fuses read+write, run on **two concurrent consumes** | atomic ⇒ winner-counts **{1}** | the *same* engine non-atomic ⇒ **{1,2}** (a real double-login: two sessions from one token) |
| 3 | §7.2 revoke-then-terminate leaves no attacker session | revoke (CAS), terminate as snapshot-then-kill, attacker consume (CAS+mint, atomic per §3.2) interleaved at the step level | **safe over every interleaving** | v0.5 terminate-then-revoke **is unsafe**; and if mint is *not* fused with consume, even v0.6 **breaks** |

All controls trip, including the self-test. Verdict on v0.6: **no new BLOCKER or FINDING**
on these three claims, one ADVISORY (below). The recovery check models the two recovery
steps at step granularity (not a per-row revoke loop), so it verifies the ordering claim,
not the finer per-row interleaving; that scoping is stated rather than oversold.

## The honest headline

It did **not** find something four LLM critics missed, v0.6 holds on these three
claims, and it would have been dishonest to manufacture otherwise. Given the agenda
caveat above, finding nothing *new* was the likely outcome; the value is narrower and real:

- **The checks now have teeth.** Check 2's atomic PASS means something *because the same
  engine, non-atomic, fails*, atomicity is shown to be necessary, not assumed. Check 3
  distinguishes the v0.5 and v0.6 orderings and shows the "mint is fused with consume"
  premise is load-bearing (drop it and even v0.6 breaks). These are genuine model-checks,
  not `return True` in a permutation loop.
- **It computes, rather than argues, the §2.2 bound.** The exact maximizer returns 3 here
  and 9 in a ttl>window regime (and 6 for 3/15min, 16min-ttl), so the "3, not 5" result is
  a computation, not the identity function the first version shipped. It corroborates
  round-4 advisory A19 (computed 3 against the spec's stated cap of 5) from the execution
  layer.
- **F19 is a consistency check, not independent confirmation.** Check 3's control *is*
  the v0.5 ordering, hand-modeled by the same author who wrote F19, so the model agreeing
  with the finding shows internal consistency, not an outside oracle vouching for it.

## What this does and does not buy you

It model-checks the *design's stated abstraction* (atomic CAS, the rate rule, the
revoke-then-terminate step ordering), not a running system, which doesn't exist. So it raises confidence in the design's internal logic, from a source decorrelated
in execution but not in agenda. Per [`FAILURE-MODES.md`](FAILURE-MODES.md): convergence is
not correctness, a model is not the territory, and a checker handed the panel's own claims
cannot test for the things the panel never thought to check. Within those limits it does
the one thing the four LLM lenses structurally could not: ask the world what happens
instead of asking the model what it thinks, on the claims someone already chose to make.

## The one finding

- **ADVISORY §2.2**: the ceiling of 5 is slack: the computed maximum live count is 3.
  Not a defect, the spec frames the 5 as a belt-and-suspenders guard against a future
  rate-limit relaxation, so a slack cap today is intended. Logged, same disposition as
  the round-4 advisory it reproduces.
