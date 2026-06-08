#!/usr/bin/env python3
"""
Executable Critic — a non-LLM lens on docs/design/magic-link-auth.md (v0.6).

FAILURE-MODES.md argues that the only verifier that fully escapes a language model's
shared blind spots is a *different kind* of checker that runs. This is that checker.
It shares no training data and no reasoning basis with the panel; it just computes.

It tests three claims the LLM panel only reasoned about:

  1. §2.2  the live-token count. The spec caps it at 5 "belt and suspenders" and says
           the §2.1 rate limit is the binding control. Round 4 (Security, Skeptic)
           argued the 5 is unreachable. We compute the real maximum.
  2. §3.2  the token state machine: an atomic compare-and-set means at most one
           operation wins and terminal states are absorbing ("fail closed").
  3. §7.2  recovery ordering: revoke-tokens-then-terminate-sessions leaves no
           attacker session alive; the v0.5 order (terminate-then-revoke) did.

Each check ships with a NEGATIVE CONTROL — a deliberately broken variant the check
must flag — so a PASS on the real design is meaningful, not vacuous.

Run: python3 scripts/executable_critic.py
Exit code 0 if v0.6's claims hold, 1 if a v0.6 violation is found. Stdlib only.
"""

from itertools import permutations

# Spec constants (from magic-link-auth.md v0.6)
RATE_LIMIT_COUNT = 3      # §2.1  <= 3 mints per address ...
RATE_WINDOW_MIN = 15      # §2.1  ... per 15 minutes
TOKEN_TTL_MIN = 10        # §3.2  tokens expire 10 minutes after mint
DECLARED_CAP = 5          # §2.2  hard ceiling of 5


# ---------------------------------------------------------------------------
# Check 1 — §2.2 / §2.1 : maximum number of simultaneously-live tokens
# ---------------------------------------------------------------------------
def max_concurrent_live(rate_count, rate_window, ttl):
    """Largest N for which N tokens can be live at the same instant.

    A token minted at t is live on [t, t+ttl). For N to be live together, all N
    mints fall inside one ttl-length window. The §2.1 rule caps mints in any
    rate_window-length window at rate_count. We search upward for the largest
    feasible N by trying to place N mints inside a ttl-window without violating
    the rate rule in any rate_window-window.
    """
    def feasible(n):
        # Try to place n mints within a single ttl-window (minute grid 0..ttl-1),
        # densest-packed at the window start, and check the rate rule on every
        # rate_window-length window over the schedule's span.
        if n == 0:
            return True
        if n > ttl:
            # can't fit n distinct mint-minutes inside the ttl window at this grid
            # (clustering finer than a minute doesn't help the rate rule, which is
            #  what bounds us); fall through to the rate check which will reject.
            mints = [0] * n  # all at t=0 (allowed only if n <= rate_count)
        else:
            mints = list(range(n))  # 0,1,...,n-1  (all within the ttl window)
        # rate rule: every window of length rate_window contains <= rate_count mints
        span = max(mints) + 1
        for start in range(min(mints), max(mints) + 1):
            in_window = [m for m in mints if start <= m < start + rate_window]
            if len(in_window) > rate_count:
                return False
        return True

    n = 0
    while feasible(n + 1):
        n += 1
    return n


def check_concurrency_cap():
    actual = max_concurrent_live(RATE_LIMIT_COUNT, RATE_WINDOW_MIN, TOKEN_TTL_MIN)
    findings = []
    # The cap itself is never violated (actual <= DECLARED_CAP) — safety holds.
    cap_holds = actual <= DECLARED_CAP
    # But if actual < cap, the "5" is dead text: the binding control is the rate limit.
    if cap_holds and actual < DECLARED_CAP:
        findings.append((
            "ADVISORY", "§2.2",
            "The hard ceiling of 5 is unreachable",
            f"Computed maximum simultaneously-live tokens under the §2.1 rate limit "
            f"(<= {RATE_LIMIT_COUNT}/{RATE_WINDOW_MIN}min) and the §3.2 {TOKEN_TTL_MIN}min "
            f"expiry is {actual}, not {DECLARED_CAP}. The '5' never binds; the rate limit "
            f"is the only live-token control. This independently confirms the round-4 "
            f"advisory (A19) by computation rather than argument.",
        ))
    return {
        "name": "Concurrency cap (§2.2/§2.1)",
        "computed_max_live": actual,
        "declared_cap": DECLARED_CAP,
        "cap_safety_holds": cap_holds,
        "findings": findings,
        # negative control: a looser rate limit (e.g. 7/15min) WOULD breach the cap of 5
        "negative_control": max_concurrent_live(7, RATE_WINDOW_MIN, TOKEN_TTL_MIN) > DECLARED_CAP,
    }


# ---------------------------------------------------------------------------
# Check 2 — §3.2 : token state machine under concurrency
# ---------------------------------------------------------------------------
# Atomic CAS: an operation succeeds iff the row is currently 'issued'.
OPS = [("consume", "consumed"), ("revoke", "revoked"), ("expire", "expired")]


def run_atomic(order):
    """Apply a sequence of CAS attempts atomically; return list of winners."""
    state = "issued"
    winners = []
    for name, target in order:
        if state == "issued":            # atomic compare-and-set
            state = target
            winners.append(name)
    return state, winners


def run_nonatomic_racing(order):
    """Broken variant: every op reads the state first, THEN all of them write
    (check-then-set with the reads racing ahead of the writes)."""
    reads = {name: "issued" for name, _ in order}   # all read 'issued' before any write
    state = "issued"
    winners = []
    for name, target in order:
        if reads[name] == "issued":      # decision based on a stale read
            state = target
            winners.append(name)
    return state, winners


def check_state_machine():
    findings = []
    # Atomic model: over every interleaving (order) of the three ops, at most one wins.
    atomic_ok = True
    for order in permutations(OPS):
        _, winners = run_atomic(list(order))
        if len(winners) != 1:            # exactly one transition out of 'issued'
            atomic_ok = False
    if not atomic_ok:
        findings.append((
            "BLOCKER", "§3.2",
            "Atomic CAS does not yield single-winner under some interleaving",
            "Model-check found an interleaving where !=1 operation succeeds.",
        ))
    # Negative control: the non-atomic variant MUST break (>1 winner) on the
    # all-read-then-write interleaving, proving the check can fail.
    _, bad_winners = run_nonatomic_racing(list(OPS))
    negative_control_breaks = len(bad_winners) > 1
    return {
        "name": "State machine single-use (§3.2)",
        "atomic_single_winner": atomic_ok,
        "negative_control_breaks": negative_control_breaks,
        "nonatomic_winners": bad_winners,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Check 3 — §7.2 : recovery step ordering vs an attacker consuming mid-recovery
# ---------------------------------------------------------------------------
def recovery_leaves_attacker_session(order):
    """order is a list of the two recovery steps. An attacker holds a live token
    and attempts to consume it (minting a session) at every interleaving gap.
    Return True if ANY interleaving leaves the attacker's session active."""
    def simulate(consume_pos):
        token = "issued"
        sessions = set()  # active session ids
        steps = list(order)
        # build the timeline with the attacker's consume spliced in at consume_pos
        timeline = steps[:consume_pos] + ["attacker_consume"] + steps[consume_pos:]
        for step in timeline:
            if step == "revoke_all":
                if token == "issued":
                    token = "revoked"
            elif step == "terminate_sessions":
                sessions.clear()          # kill all sessions active *now*
            elif step == "attacker_consume":
                if token == "issued":     # atomic CAS issued->consumed
                    token = "consumed"
                    sessions.add("attacker")
        return "attacker" in sessions
    return any(simulate(pos) for pos in range(len(order) + 1))


def check_recovery_ordering():
    v06_order = ["revoke_all", "terminate_sessions"]        # §7.2 (v0.6)
    v05_order = ["terminate_sessions", "revoke_all"]        # the v0.5 ordering (round-5 F19)
    v06_bad = recovery_leaves_attacker_session(v06_order)
    v05_bad = recovery_leaves_attacker_session(v05_order)
    findings = []
    if v06_bad:
        findings.append((
            "BLOCKER", "§7.2",
            "Recovery leaves an attacker session alive under some interleaving",
            "Model-check found a consume interleaving that survives v0.6's recovery.",
        ))
    return {
        "name": "Recovery ordering (§7.2)",
        "v06_revoke_then_terminate_safe": not v06_bad,
        "v05_terminate_then_revoke_unsafe": v05_bad,   # reproduces round-5 F19
        "findings": findings,
    }


# ---------------------------------------------------------------------------
def main():
    checks = [check_concurrency_cap(), check_state_machine(), check_recovery_ordering()]
    all_findings = [f for c in checks for f in c["findings"]]

    print("=" * 70)
    print("EXECUTABLE CRITIC — non-LLM verification of magic-link-auth.md v0.6")
    print("=" * 70)

    c1 = checks[0]
    print(f"\n[1] {c1['name']}")
    print(f"    computed max simultaneously-live tokens = {c1['computed_max_live']} "
          f"(declared cap {c1['declared_cap']})")
    print(f"    cap safety holds: {c1['cap_safety_holds']}")
    print(f"    negative control (loose 7/15min limit breaches cap 5): {c1['negative_control']}")

    c2 = checks[1]
    print(f"\n[2] {c2['name']}")
    print(f"    atomic CAS -> exactly one winner over all interleavings: {c2['atomic_single_winner']}")
    print(f"    negative control (non-atomic variant double-spends): {c2['negative_control_breaks']} "
          f"(winners={c2['nonatomic_winners']})")

    c3 = checks[2]
    print(f"\n[3] {c3['name']}")
    print(f"    v0.6 revoke-then-terminate is safe: {c3['v06_revoke_then_terminate_safe']}")
    print(f"    v0.5 terminate-then-revoke is unsafe (reproduces round-5 F19): "
          f"{c3['v05_terminate_then_revoke_unsafe']}")

    print("\n" + "-" * 70)
    if all_findings:
        print("FINDINGS (graded, located):")
        for sev, sec, title, body in all_findings:
            print(f"\n  [{sev}] {sec} — {title}\n    {body}")
    else:
        print("No BLOCKER/FINDING against v0.6.")

    # Sanity: every negative control must actually trip, or the checks are vacuous.
    teeth = (checks[0]["negative_control"] and checks[1]["negative_control_breaks"]
             and checks[2]["v05_terminate_then_revoke_unsafe"])
    print(f"\nNegative controls all tripped (checks have teeth): {teeth}")

    blocking = [f for f in all_findings if f[0] in ("BLOCKER", "FINDING")]
    print("\nVERDICT:", "v0.6 claims hold under model-checking." if not blocking
          else "v0.6 violation found — see findings.")
    if not teeth:
        print("WARNING: a negative control failed to trip; treat PASSes as unproven.")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
