# The Reductive Descent: Improving Documents with Agents by Subtraction

Most people point an AI agent at a document the same way: *"review this and suggest
improvements."* They get back a wall of suggestions, apply some, and move on. It
feels productive. It usually isn't — because a one-shot review has no notion of
*done*. There's no signal that the document has stopped attracting legitimate
criticism. You just stop when you're tired.

There's a better pattern, and it's worth naming because it inverts the usual
instinct. Call it **reductive review**. The goal isn't to generate more — more
suggestions, more prose. The goal is to drive the document's residual-objection
surface down toward zero: to shrink the set of legitimate, material criticisms that
remain, the way gradient descent shrinks an error term. You're not adding to the
document. You're subtracting from the pile of things still wrong with it.

That "shrink the error term" framing isn't decoration, and it isn't mine. The
closest cousin to this idea in the agent world is Andrej Karpathy's *autoresearch*
loop — an agent that edits one training script, runs a time-boxed experiment,
measures the result against a metric, and keeps or reverts the change, all night.
It's hill-climbing for knowledge work: a closed loop with a number that's supposed
to go down. Reductive review is the same shape pointed at a document instead of a
training run, with a panel of adversaries standing in for the metric.

I want to be precise about the debt, because it's larger than a borrowed word or
two. I'd been running review roughly this way for a while before Karpathy published
autoresearch — the practice came first, in my hands at least. But practice isn't the
same as understanding it. What Karpathy actually gave the rest of us was a
**framework and a vocabulary for the whole class of thing**: the idea that "many
iterations toward a goal" is a *named pattern* with parts you can point at — a loop,
a metric, a keep-or-revert rule, a convergence signal — rather than a habit you
happen to have. That framing is what let me formalize what I was already doing:
descent, error term, convergence, the residual surface that's supposed to shrink. I
could run the process. I could not have *explained* it this cleanly on my own, and
an unexplained process can't be taught, audited, or handed to anyone else. Giving a
fuzzy practice a precise mental model is the harder and more generous contribution,
and it's the one I'm leaning on here.

## What the loop looks like

A reductive descent has five parts, and none is optional. A version missing any one
of them is just a fancier one-shot review.

**1. A panel of adversarial lenses, not one reviewer.** Several distinct critics,
each with its own standing brief and angle of attack, reviewing the same document in
parallel. They're hostile by construction: their job is to find what's wrong, not to
be helpful. A security adversary hunts takeover paths; a systems engineer hunts what
breaks under load; a product reviewer hunts the users who get stuck; a skeptical
generalist attacks the premise itself. One reviewer has one blind spot. Several have
overlapping coverage and no shared blind spot.

**2. A structured findings taxonomy.** Every critic returns findings in a fixed
format, graded by severity — BLOCKER / FINDING / ADVISORY — each tied to a section.
Free-form prose can't be tracked across rounds; graded, located findings can. This
is the move that turns *"is it better?"* into a measurable question. Three BLOCKERs
in round one and zero in round two is a fact you can point at, not a vibe.

**3. An arbiter.** When critics disagree — and they will — a single arbiter decides
what gets acted on and records *why*. Disagreement is resolved and logged, not
quietly averaged into mush. The arbiter also de-duplicates: when the security lens
and the product lens both flag the same enumerating error message, that's one
finding with two signatures, not two findings. Averaging hides the reasoning;
arbitration writes it down.

**4. Versioned revision.** Acting on findings means revising the document with a
change record and a version bump. Every edit carries a motivation. This is the audit
trail that lets you trust the process later — and lets a fresh reader see *why* v0.2
looks the way it does, not just *that* it does.

**5. A formal termination condition.** The loop stops when every critic
independently reports nothing material left to add. Convergence is the exit signal —
not a human running out of patience. Round over round, the count of open issues
trends toward zero, and when it flattens at zero across the panel, you're done.

Put those together and you have a loop that knows when it's finished, with a paper
trail explaining how it got there. That's the point.

## The thing that goes wrong: agreement theater

Here's the failure mode that turns this from a real technique into a comforting
ritual. After a few rounds the document looks settled, and the critics start
agreeing to agree. They stop reading carefully. A round that should surface real
edge cases returns *"looks good, no notes."* Convergence rots into rubber-stamping,
and you mistake exhaustion for quality.

This is worth taking seriously because the technique's whole claim — *we stopped
because the objections ran out* — is exactly the claim a lazy panel will counterfeit.
A panel that found ten things last round and zero this round either did great work or
quit, and from the outside those look identical. So guard against it deliberately:

- **Force a fresh full read each round.** Critics read the current version end to
  end; they don't skim the prior round's notes and rubber-stamp the deltas.
- **Perturb the prompts between rounds.** Reorder and reword each lens's checklist so
  the panel can't pattern-match its own previous output.
- **Treat a sudden drop to zero with suspicion, not celebration.** Make the panel
  *prove* the drop: each critic points at the specific revision that closed each
  prior finding and re-derives it from the current text, rather than asserting it's
  fixed because the changelog says so.
- **Don't let "advisory" mean "ignore."** Re-grading a finding down to advisory is
  legitimate — once the BLOCKERs are gone, a missing error-state spec really is less
  severe than it looked. But softening the label isn't the same as resolving the
  issue. The arbiter records the downgrade and decides explicitly: fix it or defer
  it. Quiet downgrades are how real gaps slip through a panel that's pretending to
  converge.

The worked example that accompanies this article leans into this on purpose. In its
second round the panel downgrades three findings to advisories — and each critic
*flags its own downgrade for the arbiter*, who then pulls all three back into scope
rather than letting them evaporate. That's the guard doing its job, in writing.

## How this differs from the "Ralph Wiggum" loop

You've probably seen the opposite approach, sometimes called the **"Ralph Wiggum"
technique** — the deliberately-dumb brute-force loop, popularized by Geoffrey
Huntley. One fixed prompt, fed to one agent, looped indefinitely:

```bash
while true; do cat PROMPT.md | agent ; done
```

State lives in the filesystem; each pass picks up where the last left off. It's
"stupid but it works" — relentless repetition plus the codebase-as-memory eventually
grinds out a result. For greenfield generation it genuinely does; people have shipped
real software this way overnight. But it's the philosophical opposite of a reductive
descent.

| | **Ralph Wiggum loop** | **Reductive descent** |
|---|---|---|
| **Direction** | Additive — keeps producing | Reductive — drives objections toward zero |
| **Reviewers** | One generic agent, one prompt | Several specialized adversarial lenses |
| **Critique** | Implicit; self-judged next pass | Explicit, externalized, graded by independent critics |
| **Conflict** | None — single voice | An arbiter resolves and records why |
| **Termination** | Emergent; a human kills it | Formal: unanimous "nothing material left" |
| **Audit trail** | The diff is the only record | Every round versioned |
| **Posture** | Optimism — iterate until it looks done | Adversarial pessimism — assume it's still wrong |

One line: Ralph Wiggum is one loop trying to *make* the thing; a reductive descent is
a panel of adversaries trying to *break* the thing, looping until they can't. Ralph
converges by luck and persistence; the descent converges by exhausting a fixed set of
perspectives and measuring when objections hit zero. They share one trait — both use
the document or filesystem as durable memory across stateless runs. The difference is
what each does with it: Ralph extends; the descent interrogates and tightens.
(Karpathy's autoresearch sits closer to the descent end of this spectrum than to
Ralph: it has a metric and a keep-or-revert rule, which is exactly the "measure and
subtract" discipline a one-prompt loop lacks.)

## Make the critics yours, and keep them

The lenses are domain-specific, but the protocol — graded findings, arbiter,
versioned revision, convergence — is universal. So don't hand-write a panel from
scratch each time. Have the agent propose the right critics for *this* document and
draft any missing ones from a small set of examples; approve, edit, and keep them.
Over time you accumulate a personal library of reviewer agents in your own style that
travels between projects.

Two cautions. First, **generate critics from the domain, not from the document's own
claims.** A critic spun up to agree with the document will agree with it — if you ask
the document what its reviewers should care about, you get a panel of yes-men. Derive
the lenses from what the *domain* punishes (auth specs get attacked, so you need an
attacker), not from what the draft happens to mention. Second, **apply the reductive
ethic to the library itself.** A lens that never surfaces anything material across
several documents is dead weight; prune it. The panel is a document too.

## What counts as a real implementation

There are two independent axes, and it's worth being blunt about which one is
negotiable.

**Breadth** — how many critics, how finely tuned — can start small and grow. Two or
three good lenses is a legitimate panel. You do not need a dozen.

**Depth** — the round-over-round descent to convergence, with closure tracking, an
arbiter, a termination signal, and the anti-rubber-stamp guards — is non-negotiable.
A single pass with a panel is *not* a reductive descent; it's just a louder one-shot
review, and one-shot reviews are the thing we're replacing.

So the MVP framing is: ship the loop, even with a tiny panel, and you have the real
thing. Ship a big panel without the loop and you have nothing new — a more expensive
way to generate a wall of suggestions you'll stop reading when you're tired. Start
small, but start with the loop.

## See it work

A minimal, runnable example lives at
**[github.com/aedile/reductive-review-example](https://github.com/aedile/reductive-review-example)**
— a small panel, the
findings format, and the descent wired together, run against a fictional,
intentionally-flawed passwordless-login spec. The objection count falls 3/7/5 →
0/2/4 → 0/0/1 across three rounds, and every drop is recorded. Read the rounds in
order and watch the count fall — including the round where the panel tries to soften
three findings into advisories and the arbiter won't let it.

---

*The "Ralph Wiggum" loop is Geoffrey Huntley's
([ghuntley.com/ralph](https://ghuntley.com/ralph/)). The framework and vocabulary
for "iterate toward a goal until it converges" — descent, error term, convergence —
I owe to Andrej Karpathy's autoresearch; it's what let me formalize a practice I
already had but couldn't yet explain.*
