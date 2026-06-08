# The Executable Critic — a non-LLM lens that runs

[`FAILURE-MODES.md`](FAILURE-MODES.md) ends on a claim: the only verifier that fully
escapes a language model's shared blind spots is **a different *kind* of checker that
runs** — convert judgment into computation. A repo that asserts that and never does it
is exactly the claim-without-artifact gap this project keeps hunting. So here is the
artifact.

[`scripts/executable_critic.py`](../../scripts/executable_critic.py) is a zero-dependency
Python model-checker that tests three claims in `magic-link-auth.md` **v0.6** by
computing over them, not by reasoning about them. It shares no training data and no
reasoning basis with the LLM panel — it is the most decorrelated critic in the repo.

Run it yourself:

```
python3 scripts/executable_critic.py
```

## What it checks, and what it found

Each check ships with a **negative control** — a deliberately broken variant the check
must flag — so a PASS on the real design means something rather than nothing.

| # | Claim (v0.6) | Result | Negative control |
|---|--------------|--------|------------------|
| 1 | §2.2 live-token count is capped, rate limit binds | **max live = 3**, cap of 5 never binds | a loose 7/15min limit *does* breach the cap of 5 ✓ |
| 2 | §3.2 atomic CAS ⇒ at most one winner, fail-closed | **single winner over every interleaving** | the non-atomic variant double-spends (all 3 ops "win") ✓ |
| 3 | §7.2 revoke-then-terminate leaves no attacker session | **safe under every interleaving** | the v0.5 terminate-then-revoke order *is* unsafe ✓ |

All three negative controls tripped, so the checks have teeth. The verdict on v0.6:
**no new BLOCKER or FINDING.** One ADVISORY, below.

## The honest headline

It did **not** catch something four LLM critics missed — v0.6 holds up on these three
claims. That is the expected, reassuring outcome after six rounds, and it would have
been dishonest to manufacture drama. The value is different and real:

- **It proved by execution what the panel only argued.** "Exactly one of {consume,
  revoke, expire} wins" and "no attacker session survives recovery" went from *reasoned*
  to *model-checked over every interleaving.*
- **It independently re-derived a logged advisory.** Round 4 (Security, Skeptic)
  *argued* the §2.2 ceiling of 5 was unreachable. The critic *computed* the real maximum
  — exactly **3** — from a source with none of their priors. An LLM agreeing with an LLM
  is an echo; a model-checker agreeing is corroboration.
- **It reproduced a real fixed bug.** The negative control for check 3 is literally the
  v0.5 recovery ordering, and the critic flags it unsafe — confirming round-5 finding
  **F19** was a true positive, not a hallucination, and that v0.6 closes it.
- **It demonstrated why a requirement matters.** Check 2's negative control shows a
  non-atomic compare-and-set double-spends. The spec's insistence on *atomic* CAS isn't
  ceremony; remove it and the property breaks, on demand.

## The one finding

- **ADVISORY §2.2** — the hard ceiling of 5 is unreachable; the computed maximum
  simultaneously-live token count under the §2.1 rate limit (≤3/15min) and the §3.2
  10-minute expiry is **3**. This is not a defect: the spec already frames the 5 as a
  *belt-and-suspenders* guard against a future relaxation of §2.1, so a slack cap today
  is the intended state. The critic confirms the slack is real and pins the live number.
  Logged, not actioned — same disposition as the round-4 advisory it reproduces.

## What this does and does not buy you

It does **not** verify a running system — there is no implementation. It model-checks the
*design's stated abstraction* (atomic CAS, the rate rule, the recovery sequence). So it
raises confidence in the design's internal logic, from a decorrelated source; it says
nothing about code that doesn't exist (per [`FAILURE-MODES.md`](FAILURE-MODES.md) W1:
convergence is not correctness, and a model is not the territory).

But that is exactly the move the synthesis calls for, made concrete: where the document
makes a claim you can execute, stop asking the model what it thinks and ask the world
what happens. This is the repo eating its own most important conclusion — one lens, but
the right *kind* of lens, and the one the other six structurally could not be.
