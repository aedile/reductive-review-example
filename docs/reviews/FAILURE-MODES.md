# Failure Modes: when the descent lies to you

Reductive review borrows the language of gradient descent: drive the residual
objection surface toward zero. Borrowed language smuggles in borrowed problems, 
local minima, bad objectives, overfitting, and some failure modes that have nothing
to do with optimization at all. This document is an honest accounting, sorted by how
much we can actually back up.

Three buckets:

- **Wheat**: objections with real grounding (evidence, a citable result, or logical
  necessity). Addressed from the ground up, with mitigations.
- **Chaff**: objections that *sound* rigorous but are intuition or hard opinion. For
  each, the strongest "well, actually…", which either kills the objection or forces
  us to refine it into something defensible.
- **The universal ceiling**: objections that are true but **not differential**: they
  limit *all* review (human panels, peer review, even formal methods), so they argue
  for humility, not against this method specifically.

> Citations are named so you can check them; verify before quoting. Where a claim is
> intuition rather than evidence, it says so. This file practices what the repo
> preaches: graded, located, and honest about its own confidence.

---

## Wheat: grounded objections

### W1. Convergence is failure-to-falsify, not proof of correctness
You cannot establish "this design has no flaws" by failing to find them. This is the
problem of induction (Popper: theories are falsified, never verified). "Converged"
means *no flaw survived this particular battery of critics*, a real but weaker state
than "correct."
- **Well, actually:** you can get *bounded confidence* via coverage and seeding (see
  W2). True, but bounded confidence never reaches proof. The bound is the honest claim.
- **What we do:** say "no material objection survived N rounds," never "no flaws."
  Where you need actual proof (a protocol property, a state machine), use a method that
  provides it, a model checker, a type system, not a panel of opinions.

### W2. Recall is unobservable directly: but estimable
You observe the findings the panel surfaces (true and false positives). You **never**
observe the false negatives, the flaws it missed, without an external oracle.
Precision is measurable; recall is not, by construction. So "0 findings" tells you
nothing about *what fraction of real flaws you caught.*
- **Well, actually:** seed the document with *known* defects (mutation testing /
  fault injection, established practice in software testing) and measure how many the
  panel catches. That **estimates** recall. So recall is not *directly* observable, but
  it is estimable. This is the single most useful mitigation in this doc.
- **What we do:** plant canary defects each run; track the catch rate as a recall
  proxy; report it alongside the objection count so convergence carries a coverage
  number, not just a precision number.

### W3. The critics are correlated, so effective independence < N
Ensemble theory: the variance of an averaged estimator falls with the *number of
independent* members, but correlation erodes that, correlated weak learners buy you
less than their count suggests. Four instances of one model share priors, so they
share some blind spots.
- **Well, actually, but this is the easy version of the claim, and it's wrong:**
  correlation that *matters* for ensemble theory is correlation of *errors* (shared
  false negatives), and by W2 those are unobservable. This repo's run showed the four
  lenses surfacing *different findings*, but that measures division of labor (each lens
  looks at a different facet), **not** shared blind spots, it is guaranteed by giving
  them different briefs and says nothing about what they all miss together. We did **not**
  measure error correlation. The honest claim is only "outputs differed," which is
  weaker than "effective independence > 1." *(Intuition, not measurement.)*
- **What we do:** the real decorrelator is a **different *kind* of checker**, not a
  different LLM vendor (see the note on model diversity below). Add verifiers that share
  *no* training data with the model: executable tests, type checkers, fuzzers, model
  checkers, and humans. Measure inter-critic overlap and prune lenses that never add
  anything orthogonal.

### W4. Sycophancy / "agreement theater" is a documented LLM tendency
Models drift toward agreement and praise; this is trained-in, not incidental (Sharma
et al., *Towards Understanding Sycophancy in Language Models*, 2023; Perez et al.,
*Model-Written Evaluations*, 2022). Left unchecked, late rounds bias toward "looks
good."
- **Well, actually:** agreement theater has at least two drivers, (a) **shared context**
  / seeing the prior agreement, and (b) a weight-level RLHF pull. Running critics in
  **separate contexts with hostile mandates** removes (a), and prompt-perturbation and
  "default to refuted" framing blunt (b). *Which driver dominates is our intuition, not a
  measurement*, we have not isolated (a) vs (b), so "removes most of it" is a claim we
  can't back, only a design bet. The grounded part is that the existence of sycophancy is
  documented; the efficacy of these mitigations against it, here, is unmeasured.
- **What we do:** blind contexts per critic, adversarial prompts, perturbation every
  round after the first, and require each "closed" finding to be *proven* against the
  text, not asserted.

### W5. The landscape is non-stationary: fixes introduce regressions
This is not descent on a fixed surface. Each revision changes the document, and a fix
for one finding can open another, so it behaves like a dynamical system / adversarial
game, which can in principle **oscillate** (fix A breaks B, fix B breaks A).
- **Evidence:** observed directly in this repo, **four of six rounds** had a
  fix-induced regression the next round caught. This isn't a hypothetical.
- **Well, actually:** it *converged* here, so it doesn't diverge in general. But a
  different document could limit-cycle, and nothing in a naive loop would notice.
- **What we do:** require **K consecutive empty rounds** (not stop-on-first-zero), and
  **dedup proposed states against history** so an A↔B cycle is detected instead of run
  forever.

### W6. Goodhart: optimizing the *count* corrupts the count
"Drive objections to zero" makes the count a target; a target ceases to be a good
measure (Goodhart; Strathern's formulation). An author optimizing against fixed critics
can learn phrasings that dodge their patterns without fixing anything.
- **Well, actually:** Goodhart bites hardest when you optimize the *number*. Here the
  arbiter reads the *content* of each finding, not just the tally, which blunts it.
- **What we do:** never optimize the bare count; keep a human/arbiter reading the
  actual findings; vary the metric (reframe the objective periodically) so the author
  can't settle into one gameable pattern.

### W7. Same-model author + critics share correlated: not identical, blind spots
*(This is the retracted, corrected version of an earlier overclaim that the
verifier-generator gap "collapses" under one model. It does not.)*
- **Evidence both ways:** *Self-Refine* (Madaan et al., 2023) and Constitutional AI
  (Bai et al., 2022) show same-model self-critique **does** improve outputs, so it
  isn't worthless. The narrower real result, *LLMs Cannot Self-Correct Reasoning Yet*
  (Huang et al., 2023), finds that self-correction **with no new information** fails or
  degrades. The key is the condition: *no new information.*
- **Well, actually, and here is the equivocation to watch, including in our own
  earlier draft:** a critic with a different mandate and a fresh context is **new
  conditioning** (a different prompt), but Huang et al.'s failure condition is **no new
  *information*** (no external oracle/label). A re-prompted instance of the *same frozen
  weights* with no external signal supplies new conditioning, not new information about
  the world, so a hostile reframe does **not** obviously escape Huang's result. That it
  does is **our hypothesis, untested (n=1)**, not something the cited paper grants us.
  The only thing in this repo that supplies genuinely new information is the executable
  critic (an external computation). Honest claim: correlation, not collapse, and the
  "fresh context beats self-critique" mitigation is a bet, not a result.
- **What we do:** convert opinions into executable facts wherever possible (the only
  thing that fully leaves the model's epistemic basis), and decorrelate with non-LLM
  and human checkers (W3).

---

## Chaff: intuitions and hard opinions

### C1. "Subtraction converges to *unobjectionable*, never *excellent*"
**Honest correction (this was misfiled as chaff): the objection's kernel survives, it
is closer to wheat.** Only the *absolute phrasing* ("can't *reach* excellence") was chaff.
- **The chaff part:** if a lens's mandate is "object to anything mediocre, unoriginal,
  or that fails to delight," then *not excellent* becomes a finding and gets minimized
  like any other. So the wall isn't *absolute*, it depends on whether your panel has an
  ambition lens.
- **The kernel that survives (don't pretend it didn't):** subtraction can *demand*
  excellence (flag its absence) but cannot *generate* the creative content that satisfies
  the demand, that needs an additive/generative pass the loop structurally lacks. So
  reductive review raises the floor toward "unobjectionable *by your lenses*"; the ceiling
  needs a quality lens **and** a generative step. Calling the whole objection "chaff" was
  a motte-and-bailey on our part; the real status is "true, with a fixable half."

### C2. "Local minima: you can only descend in the subspace your critics span"
The gradient-descent framing is an **analogy**, not mathematics. The objection surface
isn't a vector space; "span" and "subspace" are borrowed sparkle.
- **Wheat kernel:** you cannot find what no lens looks for. Trivially true.
- **Refined:** drop the false precision. State it plainly, *coverage is the union of
  your lenses; shared gaps are invisible; you escape them with a new **kind** of lens,
  not more of the same kind.* Same practical advice, no fake math.

### C3. "Adversarial by prompt ≠ adversarially optimized"
- **Well, actually:** a prompted-adversarial critic that **can run the exploit** (has
  tools, executes the attack) is doing real adversarial work, gradient optimization
  isn't the thing that matters. The gap is *capacity to act*, not *optimization*.
- **Refined:** the objection isn't "not optimized," it's "**can't act.**" Give critics
  tools (run the code, fuzz the endpoint, attempt the bypass) and most of it dissolves.
  A critic that only *imagines* the attack is the weak case.

### C4. "The 'fresh read' is contaminated"
In this repo's run, the arbiter fed each round's critics the prior findings to verify
closures, which can steer them toward expected answers.
- **Well, actually:** that's an **implementation choice, not an inherent flaw.** Run
  critics genuinely blind to prior rounds (arbiter-only memory of history) and it's
  gone.
- **Refined:** a real risk we introduced and should fix by design, blind critics,
  with only the arbiter holding cross-round state.

### C5. "Calibration degrades as the document gets subtle (out-of-distribution)"
Plausible from OOD/calibration intuition, but largely unsupported here.
- **Well, actually:** our own data weakly **contradicts** the doom version, the subtle
  rounds (round 3, the deep concurrency arguments) drew the *most* effort and found
  *real* issues. Harder targets elicited more careful analysis, not less.
- **Refined:** soften to "calibration *may* drift on subtle documents; watch for it", 
  an unproven caution, n=1, not a demonstrated failure.

---

## The universal ceiling: true, but not this method's fault

These are real and old. Their trap is that they sound like indictments of reductive
review when they are limits on **all** review.

- **The criterion problem / underdetermination.** "Material" has no external definition
  except what the panel stops objecting to, so "good enough" is defined by the process
  meant to measure it. *(Caveat: this one is only **partly** universal. An executable
  test or a formal property has a criterion external to the reviewer, it holds or it
  doesn't, so panel-defined "material" is **more** circular than spec-defined
  correctness. This is a **differential** weakness of LLM-panel review, and it is exactly
  what the executable critic escapes. We shouldn't have filed it as fully shared.)*
- **The Münchhausen trilemma.** Why trust the arbiter? Every justification bottoms out
  in circularity, infinite regress, or an axiom. Here the axiom is "the arbiter's call."
- **Consensus ≠ truth.** Agents agreeing is a social fact, not a truth-maker.
- **Legibility ≠ correctness.** Counted, located findings make the process auditable,
  but you optimize what you can count, and countability is a property of the map.
- **Reflexivity.** Reviewing the review bottoms out when someone says "no further
  material objections", i.e., by fiat, the very thing the method claims to replace.

**The well, actually that matters:** every one of these applies identically to a human
expert panel, to peer review, and, via unproven axioms and a trusted checker, even to
formal verification. They are the epistemic ceiling for *any* process that decides "this
is good enough." They do not make reductive review *worse* than the alternatives; they
make it **honest about a ceiling everyone shares.** On the **auditability** axes, a
written criterion (graded findings), an explicit arbiter-of-record, a versioned audit
trail, a stated termination signal, this method sits above one-shot review. That is a
claim about *legibility, not correctness*: a fully-auditable process can still be wrong
(recall is unobservable, W2). "Above on the paperwork" is the most it earns here.

- **What we do:** keep the language humble ("converged" = "no material objection
  survived," never "correct"); ground the criterion externally wherever possible
  (executable success criteria, real-world metrics, planted canaries); and make the
  final stopping point an explicit, named human judgment rather than a pretended proof.

---

## The one-line synthesis

The escape from correlated-error local minima is **not** "more LLMs from a different
vendor", frontier models share a training corpus and therefore share much of their
error surface, so swapping families decorrelates less than the standard advice claims.
The escape is a **different *kind* of checker**, ideally one that **runs**: a test, a
type, a fuzzer, a proof, a human. The highest-leverage move in this whole document is to
stop asking the model what it thinks and start asking the world what happens, to convert
judgment into computation wherever the document makes a claim you can execute.

This repo makes a start on that, with the honest scoping it deserves:
[`EXECUTABLE-CRITIC.md`](EXECUTABLE-CRITIC.md) is a non-LLM model-checker
([`scripts/executable_critic.py`](../../scripts/executable_critic.py)) that tests three
v0.6 claims by genuinely enumerating interleavings (with negative controls that trip, so
the checks can fail). It is decorrelated at the **execution** layer, **not** in agenda, 
its constants and properties were transcribed from the spec and the panel's own findings,
so it can only test what someone already thought to check and **cannot catch a shared
blind spot**. Within that limit it computes the live-token maximum the panel had only
argued, and shows atomicity and revoke-ordering are load-bearing by breaking them on
demand. That is real corroboration from a different *kind* of checker, not independent
proof of correctness, and not a source free of the panel's priors.
