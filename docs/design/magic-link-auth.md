# Magic Link Login — Design Spec (v0.5)

> Fictional teaching artifact. This spec began intentionally insecure (v0.1) and was
> hardened across five recorded review rounds. Even at v0.5 it is a worked example,
> not a production design. **Do not implement.**

## §1 Goal and scope

Let users sign in by entering their email address and clicking a one-time link we
send them. No passwords to choose, store, or leak.

**Scope:** low-frequency, low-assurance consumer sign-in for an account that already
has a verified email on file. Higher-assurance accounts must layer a second factor,
which is **out of scope** here — so §7.1's "add a second factor" note is a consequence
of this stated boundary. Out of scope: account creation and MFA step-up. Account
creation is out of scope *as a process*, but this design **depends on a precondition it
imports from it** — see §7.2.

Why magic links over passkeys/TOTP for this segment: email possession is already the
de-facto recovery factor for these accounts, so making it the primary factor removes a
moving part for the common case. Passkeys/OTP are reasonable alternatives, not precluded.

**Success criteria (acceptance bar):** median time-to-logged-in < 60 s; login
completion rate ≥ 95% for deliverable addresses; email delivery SLA p95 < 30 s;
lockout/support-ticket rate < 0.1% of sign-ins. **Abandon/escalate conditions:**
completion rate < 90% after delivery and resend are addressed reconsiders the
passwordless premise; lockout/support rate breaching 0.1% for 3 consecutive periods
escalates a recovery-path review (the metric that measures whether the recovery design
works must itself gate something).

## §2 Request flow

### §2.1 Requesting a link

A user submits their email address. If the address belongs to an account, we mint a
login token (§3) and email a link. Requests are **rate-limited**: ≤ 3 per address per
15 min and ≤ 10 per source IP per 15 min, with exponential backoff. Over-limit requests
are accepted at the UI layer (so the response can't enumerate — §4) but dropped before
any send, and counted (§8.1).

### §2.2 Concurrent tokens (no invalidation)

A new request **never invalidates an existing token.** Multiple concurrently-valid,
**independently single-use** tokens may exist per account. The **binding control on the
live-token count is the §2.1 rate limit** (≤ 3 mints/address/15 min against a 10-min
expiry ⇒ typically ≤ 3 live); a hard ceiling of **5** is enforced separately as a
belt-and-suspenders guard so a future relaxation of §2.1 can't silently unbound the
count. This deliberately replaces the v0.3 "single live token + supersession" model,
which could neither protect a victim from a third party killing their link nor serve a
legitimate new-device/lost-tab user without contradiction. With no invalidation: a third
party cannot kill a victim's link, and a user who re-requests from a fresh session simply
gets an additional working link (so they may receive **more than one email** — see §5.0).
Repeated submits within a short window **coalesce to the in-flight send** (no duplicate
email) without invalidating anything; coalescing is best-effort dedup keyed on a
short-TTL in-flight marker evaluated **off the synchronous path** (consistent with §4.0,
so it can't become an existence oracle), and a missed coalesce degrades only to a
duplicate send bounded by §2.1. The replay surface stays bounded by single-use
consumption, the 10-minute expiry, and the ceiling.

## §3 The token

### §3.1 Generation and lookup

The token is ≥128 bits from a CSPRNG, encoded URL-safe, **not** derived from any
observable input. We persist only its hash on a **per-token row** whose **primary lookup
is by that hash** (the index equality *is* the comparison — no plaintext-token row is
fetched and compared in app code, so there is no application-level timing channel). Each
row also carries an indexed `account_id`; this **account-scoped secondary index** exists
so recovery (§7.2) can enumerate and revoke an account's live tokens — the primary
verify path still goes only by hash.

### §3.2 State machine and single use

States per token: `issued → consumed` (terminal), `issued → expired` (terminal), and
`issued → revoked` (terminal; only via recovery, §7.2). There is no supersession.
Consumption is a single atomic compare-and-set on **the token's own hash-keyed row**
(`issued → consumed`), executed on the **primary / a linearizable path** — the same row
§3.1 resolves at verify time, so lookup and the state transition contend on exactly one
row by construction. A stale-replica GET that only *presents* the confirm page (§6.0)
cannot weaken consumption, because only the primary-side CAS mints a session. Only the
consume winner mints a session; a second click on the same token loses the CAS and fails
closed. Tokens are independent: consuming or expiring one has no effect on the others.
Verifying a token in any terminal state returns the defined response in §6.1. Tokens
expire 10 minutes after mint.

### §3.3 Expiry and clock authority

At mint we compute and persist an **absolute `expires_at`** (mint time + 10 min, stamped
by the primary). Expiry is the value comparison `now() ≥ expires_at`. All datastore and
app nodes are NTP-synced within a stated bound of **≤ 5 seconds**, which is the only skew
window in the system and is named here rather than left implicit; there is no separate
grace tolerance. (This replaces v0.3's "single datastore clock" claim, which silently
assumed a single-clock-domain — non-replicated — datastore.)

### §3.4 Session creation and rotation

On a successful consume we **rotate the session identifier**: any pre-login id is
discarded and a fresh server-issued id is set. Cookies are `HttpOnly`, `Secure`,
`SameSite=Lax` (Lax is required so the email's top-level navigation works). CSRF safety
does **not** rely on SameSite: consumption is a POST (§6.0); the state-mutating step is
never a bare GET, so prefetchers can't trigger it.

## §4 Responses

### §4.0 Uniform response (mechanism, not assertion)

Whether or not the address has an account, the UI returns the **same** message and the
**same** timing. Parity is produced by a mechanism: the account-existence lookup *and*
all account-dependent work (token mint, send enqueue) happen **asynchronously off the
synchronous request path**, so the response the caller observes is identical and
constant-time for both branches. Message: "If an account exists for that address, we've
sent a sign-in link."

## §5 Delivery

### §5.0 Sending, failure, and resend

We enqueue the email on a **bounded, rate-limited queue** (per-recipient + global
throttle) with **async** workers, decoupling request latency from the provider and
preventing unthrottled fan-out under burst. Sends get bounded retry with backoff; hard
bounces vs transient failures are classified; exhausted sends are dead-lettered into §8.
The confirmation page sets a latency expectation ("usually within a minute; check
spam/promotions"), offers a **resend** gated to §2.1 (resend mints an additional token
under the §2.2 cap; it never invalidates a prior link), and a "wrong address? re-enter
it" affordance. A send failure surfaces a neutral "we couldn't send your link right now."

### §5.1 Email content, trust signals, and accessibility

The email is **multipart** (HTML + a plain-text part whose link is a full, readable URL
— never a bare "click here"). Trust signals: consistent from-name; a single known
**first-party link domain** (no redirector/tracking wrappers); SPF/DKIM/DMARC alignment
as a delivery requirement; visible expiry ("expires in 10 minutes"); "if this wasn't
you, ignore this email"; "we will never ask for your password." HTML and pages meet
**WCAG 2.1 AA**.

## §6 User experience

### §6.0 Cross-device flow, deliberate consumption, and success landing

Consumption requires a **deliberate user gesture**: opening the link presents a "Confirm
sign-in" page; a **POST** from it performs the atomic consume (§3.2). A GET only
*presents*, so scanner/preview pre-fetch cannot consume a token. Cross-device is
explicit: the device that completes confirmation gets the session; the link works in
whatever browser opens it because the token carries the authority. A different requesting
device shows "signed in on another device — you can close this tab." On success the user
lands on the page they originally tried to reach, or a default home if none.

### §6.1 Error, empty, and edge states; accessibility

Defined, account-existence-neutral states, each with plain-language copy and a single
"send me a new link" action: **expired**, **already used** (consumed or
revoked-by-recovery), **malformed/unrecognized link**, **rate-limited**, **wrong-account**. The "rate-limited" state
renders **only** as a non-enumerating hint ("Still waiting? Links can take a minute;
check spam before re-requesting") — never as a throttle confirmation, so it cannot
re-open the §4.0 enumeration channel. This set is the response §3.2 refers to. Pages meet
WCAG 2.1 AA: contrast, keyboard focus order, focus moved to the result heading on
error/success, no color-only state.

## §7 Threat model, recovery, and lockout

### §7.1 Threat model (assets, adversaries, defenses)

**Assets:** the account, the live session, the email channel.
**Adversaries (by capability):** passive network observer; attacker *without* inbox
access; attacker *with* the victim's inbox; shared/public-device attacker; attacker
targeting the recovery path (§7.2).
**Defenses, mapped:** token guessing → §3.1; replay → §3.2; enumeration → §4.0;
send-rate abuse → §2.1; session fixation → §3.4; recovery abuse → §7.2.
**Accepted assumption (trust root):** we do **not** defend against an attacker who
already controls the user's inbox. Shared/forwarded inboxes inherit this; higher-
assurance accounts are out of scope (§1).

### §7.2 Recovery and lockout (precondition, enforcement, independence)

This design **depends on a precondition it imports from account creation**: no account
exists without an enrolled recovery method. Because account creation is out of scope
here, we state the dependency as a hard contract — account creation MUST reject creating
an account without a recovery channel, and this design does not function safely
otherwise — and we **enforce it in-scope at first sign-in**: a legacy/migrated account
with no recovery channel is prompted to enrol one **before a session is established**;
until then it is an explicitly owned, named lockout class, not a silent gap. (That
first-sign-in enrolment is gated by inbox control only, so it inherits the §7.1 trust
root — it does not protect a legacy account whose inbox is *already* compromised, which
is out of scope by assumption.)

The recovery method is a second verified channel **independent of the primary email**
(it must not be reachable solely by controlling that inbox — so a same-provider recovery
email doesn't count; shared/forwarded-inbox accounts fall to the support-mediated path),
**or** a support-mediated identity check requiring defined, replay-resistant identity
evidence. Recovery is inside the threat model: recovery initiation and verification are
rate-limited and locked out mirroring §2.1; support-mediated recovery is logged/alerted
(§8); and a **successful recovery rotates the session, terminates the account's other
active sessions, and invalidates all live login tokens** — the last via the §3.1
account-scoped index, moving every `issued` row for the account to `revoked` in one
account-scoped operation, so no attacker-minted link survives recovery. The path is held
to the primary-path bar, so §7.1's claims hold end-to-end.

## §8 Observability and retention

### §8.1 Metrics

Counters/timers for: link requests, **rate-limit drops** (per-address vs per-IP, with
alert thresholds — how an abuse spike becomes visible), sent, send-failures, clicks,
confirmations, logins, expired-link hits, replay attempts, and recovery attempts.
Leading indicators for the delivery path: a **send-queue depth gauge** with a
high-water alert and a **dead-letter-rate** counter, so saturation is visible *before*
sends start failing rather than after. A **node-clock-offset gauge** alerts when any
app/datastore node drifts toward the §3.3 ≤ 5 s NTP bound, so a drift that would break
the `now() ≥ expires_at` decision is caught before it affects tokens.

### §8.2 Logging and retention

Raw tokens are **never** logged; only the hash or an opaque request id appears; email
addresses in logs are minimised. Token rows are reaped on a stated TTL (consumed: 7
days; expired: 24 h), but a minimal **tombstone** (hash + state + **`terminal_at`** — the
time the token entered its terminal state, defined for consumed, expired, *and* revoked)
is retained past row-reap for the replay-observation window so any replay stays
classifiable. Reaping never runs before `expires_at` + the replay-observation window.

## Changelog

- **v0.1** — initial draft. Deliberately weak; authored as a review target.
- **v0.2** — closed the three round-001 BLOCKERs (token entropy/at-rest, expiry/single-
  use/state machine, session rotation) plus security-adjacent findings; left UX,
  delivery, recovery soundness, and success criteria open.
- **v0.3** — closed the three round-002 BLOCKERs the v0.2 fixes had introduced (unscoped
  recovery, invariant-without-state, error-states dangling reference) and the round-002
  findings (timing-parity mechanism, delivery/resend, POST-to-consume, trust signals,
  accessibility, observability, success criteria, scope).
- **v0.4** — closed the round-003 BLOCKER the v0.3 fix had introduced: dropped the
  single-live-token invariant and supersession for a bounded set of independent single-
  use tokens (§2.2/§3.2), which dissolves the supersession-vs-invariant contradiction and
  keeps targeted-login-denial closed. Also: token-hash-keyed consume serialization
  (§3.2), absolute `expires_at` + named NTP bound (§3.3), recovery precondition enforced
  in-scope at first sign-in with channel independence and session termination (§7.2/§1),
  and the round-003 advisories (success landing, rate-limited rendering, queue/DLQ
  metrics, `terminal_at` tombstone, lockout-rate abandon trigger).
- **v0.5** — closed the single round-004 FINDING: per-token rows carry an indexed
  `account_id` so recovery can enumerate and `revoke` all of an account's live tokens
  (§3.1/§3.2/§7.2), removing the post-recovery foothold. Folded in the round-004
  advisories: live-token bound attributed to §2.1 with a belt-and-suspenders ceiling and
  off-path coalescing key (§2.2), linearizable consume CAS (§3.2), legacy-enrolment trust
  boundary (§7.2), node-clock-offset monitoring (§8.1), and the multi-email expectation
  (§2.2/§5.0).
