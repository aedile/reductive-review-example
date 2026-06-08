# The Reductive Review Protocol

A document is improved by repeated **rounds**, each one driving the residual
objection surface toward zero. This is the reusable core of the example: swap the
document and swap the panel, but keep this loop.

The loop has five non-negotiable parts. A version missing any one of them is just
a fancier one-shot review.

## 1. The panel

Several distinct adversarial critics, each with a standing brief in `prompts/`,
each reviewing the **same document version in parallel**. Critics are hostile by
construction: their job is to find what is wrong, not to be helpful or balanced.
This example uses four lenses — Security Adversary, Systems Engineer, Product/UX,
and Skeptical Generalist — but the panel is per-domain, not fixed.

Freeze the panel for the duration of a descent. Changing the panel starts a new
run and resets the convergence signal.

## 2. The findings format (required of every critic)

Every finding is **graded** and **located**. No free-form prose review — graded,
located findings are what let you measure progress across rounds.

```
## BLOCKER  (must fix before the doc can be trusted)
### §<section> — <short title>
- Problem: <what's wrong>
- Why it matters: <stakes>
- Suggested resolution: <concrete path forward>

## FINDING  (substantive; should fix)
### §<section> — <short title>
- Problem / Why it matters / Suggested resolution

## ADVISORY (worth noting; may defer)
### §<section> — <short title>
- Problem / Why it matters / Suggested resolution

## Cross-section coherence flags
- Contradictions, dangling references, sections that disagree with each other.

## Summary
- 2–3 sentences. MUST end by stating explicitly whether another round would be
  valuable, or whether you have nothing material to add.
```

Severity definitions, applied consistently:

- **BLOCKER** — the document cannot be trusted until this is fixed. Ship-stopping.
- **FINDING** — substantive; should be fixed, but does not by itself invalidate
  the document.
- **ADVISORY** — worth noting; may be deferred without harm.

## 3. The arbiter

The critics review independently; one **arbiter** then aggregates. When critics
disagree — and they will — the arbiter decides what gets acted on and records
**why** in the round's aggregate file. Disagreement is resolved and logged, not
silently averaged. The arbiter also de-duplicates: two critics flagging the same
issue from different angles is one finding, attributed to both.

## 4. Versioned revision

Acting on findings means **editing the document and bumping its version**, with a
recorded motivation. The round files plus the document changelog are the audit
trail. Never hand-edit the target doc outside a round's recorded decisions.

## 5. Termination

Stop when **every critic independently reports "nothing material to add."**
Convergence is the exit signal — not fatigue, not a round budget, not the human
losing patience. A single residual ADVISORY does not block convergence; an open
FINDING or BLOCKER does.

## Anti-rubber-stamp guards (do not skip)

Convergence rots into agreement theater: after a few rounds the critics start
agreeing to agree and stop reading carefully, and a round that should surface real
edge cases returns "looks good, no notes." Defend against it every round:

- **Force a fresh full read.** Critics read the current version end to end; they do
  not skim prior round notes and rubber-stamp the deltas.
- **Perturb the prompts between rounds.** Reorder or reword the lens checklists so
  the panel cannot pattern-match its own previous output.
- **Treat a sudden collapse to zero with suspicion, not celebration.** A panel that
  found ten things last round and zero this round either did great work or quit.
  The arbiter must make it prove which — by pointing at the specific revisions that
  resolved each prior item, not by asserting resolution.
- **Don't let "advisory" mean "ignore."** Re-grading a finding down to advisory is
  legitimate, but the arbiter records it and decides explicitly whether to fix or
  defer — softening severity is not the same as resolving the issue.
