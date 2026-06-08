# Security Adversary: Round 4 (v0.4)

Fresh full read of magic-link-auth.md v0.4. Per the round-4 perturbation I started
from the new bounded-multiple-token model (§2.2/§3.2), then the recovery path (§7.2),
then enumeration/timing (§4.0/§6.1), then re-derived the token/session core
(§3.1-§3.4). Findings re-derived from the v0.4 text, not the changelog.

## BLOCKER

None.

## FINDING

None.

## ADVISORY

### §2.2: The "5" cap is descriptive, not an enforced invariant; it is also non-binding under §2.1
- Problem: §2.2 states "up to 5 concurrently-valid … tokens may exist per account"
  but then says "the §2.1 rate limit is what bounds minting." So the 5 is a derived
  consequence of rate-limiting, not an independently checked cap. Re-deriving the
  arithmetic: §2.1 permits ≤ 3 mints per address per rolling 15 min and tokens expire
  at 10 min, so the count of concurrently-live tokens is bounded at roughly 3, and 5
  is never reached. The cap is therefore both non-enforced and non-binding.
- Why it matters: Not a replay or abuse path, each token is independently single-use
  (§3.2), so additional live tokens do not amplify replay, and more emails are
  separately bounded by §2.1 plus the coalescing rule. The only risk is descriptive
  drift: a future relaxation of §2.1 would silently change the real concurrency bound
  while the prose still says "5," and a reader may assume an explicit cap-5 enforcement
  exists where it does not.
- Suggested resolution: State which one governs. Either (a) make 5 a hard,
  separately-enforced per-account ceiling (reject/garbage-collect-oldest beyond 5,
  independent of §2.1), or (b) drop the specific number and describe the bound purely
  as a consequence of §2.1's rate limit. Today the spec asserts both framings at once.

### §3.2: Consume CAS is asserted atomic but its linearizability under the replicated store (§3.3) is left implicit
- Problem: §3.3 was rewritten in v0.4 specifically because the datastore is replicated
  (it retires the v0.3 "single datastore clock" assumption). §3.2 asserts consumption
  is "a single atomic compare-and-set on the token's own hash-keyed row" and that
  lookup and transition "contend on exactly one row by construction," but it does not
  state that the CAS executes against a linearizable / single-master path. In a
  replicated store the GET that *presents* the Confirm page (§6.0) can be served from a
  lagging replica and show "Confirm sign-in" for a token already consumed elsewhere;
  correctness then rests entirely on the POST's CAS being serialized at the primary.
- Why it matters: The double-consume / replay defense for the whole multi-token model
  reduces to "the CAS is linearizable." That property is currently inferred, not
  stated, in exactly the section whose sibling (§3.3) was reopened over replication.
  If the CAS were ever allowed to run on a replica, two clicks could both win. The
  design is fine if the CAS is primary-routed; the spec just doesn't say so.
- Suggested resolution: Add one clause to §3.2: the compare-and-set executes on the
  primary / a linearizable path, and a stale-replica GET that presents the page does
  not weaken consumption because only the primary-side CAS mints a session. This makes
  the multi-token replay closure explicit rather than implied.

## Cross-section coherence flags

- §2.2 "a new request never invalidates an existing token" vs §7.2 "successful recovery
  … invalidates all live login tokens": consistent, not contradictory, §2.2 governs
  the ordinary request path and §7.2 is a privileged recovery event. Re-derived and
  cleared; noting it so the arbiter sees it was checked, since it is the obvious-looking
  conflict in v0.4.
- §5.0 resend ("mints an additional token under the §2.2 cap; never invalidates a prior
  link") agrees with §2.2/§3.2. No conflict.
- §3.2 "Verifying a token in any terminal state returns the defined response in §6.1"
  and §6.1 "This set is the response §3.2 refers to", the dangling-reference pair from
  earlier rounds now resolves in both directions. Cleared.
- All §-cross-references in the document resolve to existing sections; no dangling
  pointers introduced by the v0.4 edits.

## Summary

The v0.4 swap to up to-N independent single-use tokens does **not** open a replay or
abuse path: each token remains an independent atomic single-use consume, so concurrency
does not amplify replay, and email fan-out stays bounded by §2.1 plus send-coalescing;
the recovery, enumeration/timing, session-rotation, and clock-authority cores all
re-derive cleanly. The two residuals are ADVISORY only, a descriptive-vs-enforced
ambiguity in the §2.2 "5" cap, and an implicit (not stated) linearizability assumption
for the §3.2 consume CAS under the now-replicated store, and neither, by the protocol's
definitions, is ship-stopping or invalidating. **From the security lens I have nothing
material (BLOCKER/FINDING) left to add; another round is not warranted on security
grounds.** The two advisories may be folded in opportunistically or deferred without
harm.
