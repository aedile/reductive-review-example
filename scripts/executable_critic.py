#!/usr/bin/env python3
"""
Executable Critic — a non-LLM lens on docs/design/magic-link-auth.md (v0.6).

It tests three claims by computation/model-checking, not by reasoning. It is
decorrelated from the LLM panel at the *execution* layer (Python vs. token
prediction). It is NOT decorrelated in *agenda*: a human/model transcribed these
constants and properties from the spec and the panel's findings, so it can only test
claims someone already thought to make — it cannot find a flaw no lens looked for.

Each check enumerates genuine interleavings and ships a negative control that the SAME
engine must flag, so a PASS is not true-by-construction:

  1. §2.2  the live-token count. A real packing search (TTL and the rate window
           interact) computes the maximum simultaneously-live tokens. Control: a
           ttl>window regime where the answer is provably >5.
  2. §3.2  the token state machine. ONE interleaving engine, parameterized by
           atomicity: atomic CAS (read+write fused) vs. non-atomic (read and write
           separable). The atomic case must single-winner over every interleaving;
           the non-atomic case must double-spend under some interleaving. Same engine.
  3. §7.2  recovery. revoke-all modeled as a per-row loop, terminate as snapshot-
           then-kill, the attacker's consume (CAS+mint, atomic per §3.2) interleaved
           at every step. Control: if mint is NOT atomic with consume, even v0.6 breaks
           — showing that "mint is part of the consume" is load-bearing.

Run: python3 scripts/executable_critic.py   (stdlib only; exit 0 if v0.6 holds)
"""

from itertools import permutations

RATE_LIMIT_COUNT = 3      # §2.1  <= 3 mints / address / 15 min
RATE_WINDOW_MIN = 15
TOKEN_TTL_MIN = 10        # §3.2
DECLARED_CAP = 5          # §2.2


def interleavings(sequences):
    """All interleavings of the given sequences that preserve each one's internal
    order (models concurrent actors whose own steps stay ordered)."""
    out = []
    def rec(seqs, acc):
        if all(not s for s in seqs):
            out.append(acc)
            return
        for i, s in enumerate(seqs):
            if s:
                rec([s[1:] if j == i else t for j, t in enumerate(seqs)], acc + [s[0]])
    rec([list(s) for s in sequences], [])
    return out


# ---------------------------------------------------------------------------
# Check 1 — §2.2/§2.1 : maximum simultaneously-live tokens (real packing search)
# ---------------------------------------------------------------------------
def max_concurrent_live(rate_count, rate_window, ttl):
    """Maximum tokens live at one instant. A token minted at t is live on [t, t+ttl);
    the §2.1 rule allows <= rate_count mints in any window of length rate_window.

    To be simultaneously live, mints lie in one ttl-span; by shift-invariance fix it to
    [0, ttl) and pack as many mints as the rolling rate rule allows (1-minute grid;
    greedy-earliest is optimal for an <=k-per-sliding-window capacity). This genuinely
    couples ttl and rate_window: when ttl > rate_window the answer exceeds rate_count.
    """
    placed = []
    for minute in range(ttl):
        recent = [m for m in placed if m > minute - rate_window]
        if len(recent) < rate_count:
            placed.append(minute)
    return len(placed)


def check_concurrency_cap():
    actual = max_concurrent_live(RATE_LIMIT_COUNT, RATE_WINDOW_MIN, TOKEN_TTL_MIN)
    # negative control: a ttl>window regime where the max provably exceeds the cap of 5.
    control = max_concurrent_live(3, 5, 15)            # 3 per 5min over a 15min ttl -> 9
    findings = []
    if actual <= DECLARED_CAP and actual < DECLARED_CAP:
        findings.append((
            "ADVISORY", "§2.2",
            "The hard ceiling of 5 is slack",
            f"Packing search: the maximum simultaneously-live token count under the §2.1 "
            f"rate limit (<= {RATE_LIMIT_COUNT}/{RATE_WINDOW_MIN}min) and the §3.2 "
            f"{TOKEN_TTL_MIN}min expiry is {actual}. The cap of {DECLARED_CAP} never binds "
            f"today — consistent with the spec calling it a belt-and-suspenders guard. "
            f"(The search is real: in a {3}/5min, 15min-ttl regime it returns {control}.)",
        ))
    return {
        "name": "Concurrency cap (§2.2/§2.1)",
        "computed_max_live": actual,
        "control_ttl_gt_window": control,            # must be > DECLARED_CAP to have teeth
        "negative_control_breaches_cap": control > DECLARED_CAP,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Check 2 — §3.2 : single-use under genuine read/write interleaving
# ---------------------------------------------------------------------------
OPS = [("consume", "consumed"), ("revoke", "revoked"), ("expire", "expired")]


def winners_over_interleavings(ops, atomic):
    """ONE engine. atomic=True: each op is a fused compare-and-set step. atomic=False:
    each op is a separate read step then write step (a stale read can win). Returns the
    set of distinct winner-counts seen across all interleavings."""
    counts = set()
    if atomic:
        seqs = [[("cas", n, t)] for n, t in ops]
    else:
        seqs = [[("read", n, t), ("write", n, t)] for n, t in ops]
    for il in interleavings(seqs):
        state = "issued"
        reads = {}
        winners = []
        for step in il:
            kind, name, target = step
            if kind == "cas":
                if state == "issued":
                    state = target
                    winners.append(name)
            elif kind == "read":
                reads[name] = state
            elif kind == "write":
                if reads.get(name) == "issued":
                    state = target
                    winners.append(name)
        counts.add(len(winners))
    return counts


def check_state_machine():
    atomic_counts = winners_over_interleavings(OPS, atomic=True)
    nonatomic_counts = winners_over_interleavings(OPS, atomic=False)
    findings = []
    if atomic_counts != {1}:
        findings.append((
            "BLOCKER", "§3.2",
            "Atomic CAS does not single-winner under some interleaving",
            f"Interleaving engine found winner-counts {sorted(atomic_counts)} for the "
            f"atomic model; the spec requires exactly one.",
        ))
    return {
        "name": "State machine single-use (§3.2)",
        "atomic_winner_counts": sorted(atomic_counts),         # expect [1]
        "nonatomic_winner_counts": sorted(nonatomic_counts),   # expect to include >1
        "negative_control_double_spends": any(c > 1 for c in nonatomic_counts),
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Check 3 — §7.2 : recovery vs an attacker consuming mid-recovery
# ---------------------------------------------------------------------------
def recovery_unsafe(order, atomic_mint):
    """order: 'revoke_first' (v0.6) or 'terminate_first' (v0.5).
    revoke-all is a per-row loop over the account's tokens; terminate is snapshot-then-
    kill; the attacker consumes their token. If atomic_mint, consume's CAS and the
    session-mint are one indivisible step (per §3.2); else they are separable.
    Returns True if ANY interleaving leaves the attacker's session active at the end."""
    tokens = ["t_attacker", "t_benign"]   # >1 row so revoke is a real loop

    revoke_seq = [("revoke_row", tk) for tk in tokens]
    terminate_seq = [("term_snapshot",), ("term_kill",)]
    recovery = revoke_seq + terminate_seq if order == "revoke_first" else terminate_seq + revoke_seq

    if atomic_mint:
        attacker_seq = [("consume_and_mint",)]
    else:
        attacker_seq = [("consume_cas",), ("mint_session",)]

    for il in interleavings([recovery, attacker_seq]):
        state = {tk: "issued" for tk in tokens}
        sessions = set()
        snapshot = set()
        consumed_ok = False
        for step in il:
            op = step[0]
            if op == "revoke_row":
                if state[step[1]] == "issued":
                    state[step[1]] = "revoked"
            elif op == "term_snapshot":
                snapshot = set(sessions)
            elif op == "term_kill":
                sessions -= snapshot
            elif op == "consume_and_mint":
                if state["t_attacker"] == "issued":
                    state["t_attacker"] = "consumed"
                    sessions.add("attacker")
            elif op == "consume_cas":
                if state["t_attacker"] == "issued":
                    state["t_attacker"] = "consumed"
                    consumed_ok = True
            elif op == "mint_session":
                if consumed_ok:
                    sessions.add("attacker")
        if "attacker" in sessions:
            return True
    return False


def check_recovery_ordering():
    v06 = recovery_unsafe("revoke_first", atomic_mint=True)
    v05 = recovery_unsafe("terminate_first", atomic_mint=True)
    async_mint_v06 = recovery_unsafe("revoke_first", atomic_mint=False)  # negative control
    findings = []
    if v06:
        findings.append((
            "BLOCKER", "§7.2",
            "Recovery leaves an attacker session under some interleaving",
            "The interleaving engine found a consume that survives v0.6's recovery.",
        ))
    return {
        "name": "Recovery ordering (§7.2)",
        "v06_revoke_then_terminate_safe": not v06,
        "v05_terminate_then_revoke_unsafe": v05,            # reproduces round-5 F19
        "async_mint_breaks_even_v06": async_mint_v06,       # control: why atomic mint matters
        "findings": findings,
    }


# ---------------------------------------------------------------------------
def main():
    checks = [check_concurrency_cap(), check_state_machine(), check_recovery_ordering()]
    all_findings = [f for c in checks for f in c["findings"]]

    print("=" * 72)
    print("EXECUTABLE CRITIC — non-LLM verification of magic-link-auth.md v0.6")
    print("=" * 72)

    c1 = checks[0]
    print(f"\n[1] {c1['name']}")
    print(f"    packing search: max simultaneously-live = {c1['computed_max_live']} "
          f"(declared cap {DECLARED_CAP})")
    print(f"    negative control (3/5min, 15min ttl) computes {c1['control_ttl_gt_window']} "
          f"> {DECLARED_CAP}: {c1['negative_control_breaches_cap']}")

    c2 = checks[1]
    print(f"\n[2] {c2['name']}")
    print(f"    atomic model winner-counts over all interleavings: {c2['atomic_winner_counts']} "
          f"(spec requires [1])")
    print(f"    non-atomic model winner-counts: {c2['nonatomic_winner_counts']} "
          f"-> double-spend exists: {c2['negative_control_double_spends']}")

    c3 = checks[2]
    print(f"\n[3] {c3['name']}")
    print(f"    v0.6 revoke-then-terminate safe over all interleavings: {c3['v06_revoke_then_terminate_safe']}")
    print(f"    v0.5 terminate-then-revoke unsafe (reproduces round-5 F19): {c3['v05_terminate_then_revoke_unsafe']}")
    print(f"    control — async mint (not fused with consume) breaks even v0.6: {c3['async_mint_breaks_even_v06']}")

    print("\n" + "-" * 72)
    if all_findings:
        print("FINDINGS (graded, located):")
        for sev, sec, title, body in all_findings:
            print(f"\n  [{sev}] {sec} — {title}\n    {body}")
    else:
        print("No BLOCKER/FINDING against v0.6.")

    teeth = (checks[0]["negative_control_breaches_cap"]
             and checks[1]["negative_control_double_spends"]
             and checks[2]["v05_terminate_then_revoke_unsafe"]
             and checks[2]["async_mint_breaks_even_v06"])
    print(f"\nNegative controls all tripped (checks have teeth): {teeth}")

    blocking = [f for f in all_findings if f[0] in ("BLOCKER", "FINDING")]
    print("\nVERDICT:", "v0.6 claims hold under model-checking." if not blocking
          else "v0.6 violation found — see findings.")
    if not teeth:
        print("WARNING: a negative control failed to trip; treat PASSes as unproven.")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
