# Magic Link Login — Design Spec (v0.3)

> Fictional teaching artifact. This spec began intentionally insecure (v0.1) and was
> hardened across review rounds. Several round-002 items are closed; see
> `docs/reviews/rounds/`. **Do not implement.**

## §1 Goal and scope

Let users sign in by entering their email address and clicking a one-time link we
send them. No passwords to choose, store, or leak.

**Scope:** low-frequency, low-assurance consumer sign-in for an account that already
has a verified email on file. Higher-assurance accounts must layer a second factor,
which is **out of scope** here — so §7.1's "add a second factor" note is a consequence
of this stated boundary, not an afterthought. Out of scope: account creation, MFA
step-up, and the internals of the recovery channel (its *requirements* are stated in
§7.2; its implementation lives elsewhere).

Why magic links over passkeys or TOTP for this segment: email possession is already
the de-facto recovery factor for these accounts, so making it the primary factor
removes a moving part for the common case. Passkeys/OTP are reasonable alternatives
and are not precluded later.

**Success criteria (acceptance bar):** median time-to-logged-in < 60 s; login
completion rate (link requested → session established) ≥ 95% for deliverable
addresses; email delivery SLA p95 < 30 s; lockout/support-ticket rate < 0.1% of
sign-ins. If completion rate sits below 90% after delivery and resend are addressed,
the passwordless premise is reconsidered (abandon condition).

## §2 Request flow

### §2.1 Requesting a link

A user submits their email address. If the address belongs to an account, we mint a
login token (§3) and email a link. Requests are **rate-limited**: ≤ 3 per address per
15 min and ≤ 10 per source IP per 15 min, with exponential backoff. Over-limit requests
are accepted at the UI layer (so the response can't enumerate — §4) but dropped before
any send, and counted (§8.1).

### §2.2 Idempotency and supersession (scoped to avoid denial-of-login)

At most one live token exists per account. A new request **supersedes** the prior
live token via the atomic, account-keyed step in §3.2 (`issued → superseded`).
Supersession is **scoped to the originating session**: a request that does not carry
the original request's session context does **not** invalidate an outstanding token,
so a third party cannot kill a victim's just-delivered link or burn their budget
(closes the targeted login-denial path). Repeated submits within a short window
coalesce to the in-flight link.

## §3 The token

### §3.1 Generation and lookup

The token is ≥128 bits from a cryptographically secure RNG, encoded URL-safe, **not**
derived from any observable input. We persist only a hash. **Lookup model:** the
hash column is indexed; the index equality *is* the comparison — no plaintext-token
row is fetched and compared in application code — so there is no application-level
timing channel and no separate constant-time compare is required.

### §3.2 State machine and single use

States: `issued → consumed` (terminal), `issued → expired` (terminal), and
`issued → superseded` (terminal, from §2.2). Consumption and supersession are both
single atomic compare-and-set steps that **contend on the same account-keyed row**,
so exactly one of {consume, supersede} wins; the loser fails closed. Only the consume
winner mints a session. Verifying a token in any terminal state returns the defined
response in §6.1. Tokens expire after **10 minutes**.

### §3.3 Expiry and clock authority

Expiry is evaluated against a **single authoritative clock** — the datastore's time —
for both `issued_at` and the expiry check. Because one clock stamps and checks, there
is no host-skew window and **no validation-side grace is applied** (the v0.2 ±60 s
tolerance is removed as self-contradictory). App hosts require NTP but never supply
the time used for expiry.

### §3.4 Session creation and rotation

On a successful consume we **rotate the session identifier**: any pre-login id is
discarded and a fresh, server-issued id is set. Cookies are `HttpOnly`, `Secure`,
`SameSite=Lax` (Lax is required so the top-level navigation from the email works).
CSRF safety does **not** rely on SameSite: consumption is a POST (§6.0), and the
state-mutating step is never a bare GET (so prefetchers can't trigger it).

## §4 Responses

### §4.0 Uniform response (with the mechanism that makes it uniform)

Whether or not the address has an account, the UI returns the **same** message and
the **same** timing. The timing parity is produced by a *mechanism*, not asserted:
all account-dependent work (token mint, §2.2 supersession, send enqueue) happens
**asynchronously off the request path**, so the synchronous response is identical for
both branches. The message: "If an account exists for that address, we've sent a
sign-in link."

## §5 Delivery

### §5.0 Sending, failure, and resend

We enqueue the email on a **bounded, rate-limited queue** (per-recipient + global
throttle) with **async** workers, so request latency is decoupled from the provider
and a burst can't fan out unthrottled. Sends get bounded retry with backoff; hard
bounces vs transient failures are classified; exhausted sends are dead-lettered into
§8. The confirmation page sets a latency expectation ("usually within a minute; check
spam/promotions"), offers a **resend** control gated to the §2.1 limits and coalesced
per §2.2, and a "wrong address? re-enter it" affordance so a typo is recoverable.
A send failure surfaces a neutral "we couldn't send your link right now" state.

### §5.1 Email content, trust signals, and accessibility

The email is **multipart** (HTML + a plain-text part whose link is a full, readable
URL — never a bare "click here"). Trust signals: a consistent from-name and a single
known **first-party link domain** (no redirector/tracking wrappers that obscure the
destination); SPF/DKIM/DMARC alignment is a delivery requirement; a visible expiry
("expires in 10 minutes"); an "if this wasn't you, ignore this email"; and an explicit
"we will never ask for your password." HTML and pages meet **WCAG 2.1 AA**.

## §6 User experience

### §6.0 Cross-device flow and deliberate consumption

Consumption requires a **deliberate user gesture**: opening the link presents a
"Confirm sign-in" page; a **POST** from that page performs the atomic consume (§3.2).
A GET only *presents* — so email-scanner / link-preview pre-fetch cannot consume the
token. Cross-device is supported and explicit: the device that completes the
confirmation gets the session; the link works in whatever browser opens it because the
token carries the authority. The requesting device, if different, shows "signed in on
another device — you can close this tab."

### §6.1 Error, empty, and edge states; accessibility

Defined, account-existence-neutral states, each with plain-language copy and a single
"send me a new link" action (re-entering §2.1): **expired**, **already used**
(consumed or superseded), **malformed/unrecognized link**, **rate-limited**, and
**wrong-account** (link is for a different address than the one currently signed in).
This is the response §3.2 refers to. Pages meet WCAG 2.1 AA: contrast, keyboard focus
order, focus moved to the result heading on error/success, no color-only state. A
legitimately throttled user sees a non-enumerating hint ("Still waiting? Links can
take a minute; check spam before re-requesting") that steers without confirming
throttle state.

## §7 Threat model, recovery, and lockout

### §7.1 Threat model (assets, adversaries, defenses)

**Assets:** the account, the live session, the email channel.
**Adversaries (by capability):** passive network observer; attacker *without* inbox
access; attacker *with* the victim's inbox; shared/public-device attacker; and an
attacker targeting the recovery path (§7.2).
**Defenses, mapped:** token guessing → §3.1 entropy; replay → §3.2 single-use +
expiry; enumeration → §4.0 uniform response + mechanism; send-rate abuse / inbox
bombing → §2.1; session fixation → §3.4 rotation; recovery abuse → §7.2.
**Accepted assumption (trust root):** we do **not** defend against an attacker who
already controls the user's inbox. Shared/forwarded inboxes inherit this. Higher-
assurance accounts are out of scope (§1).

### §7.2 Recovery and lockout (mandatory, scoped, and threat-modeled)

A recovery method (a second verified channel meeting a stated possession+rate-limit
bar, or a support-mediated identity check with defined, replay-resistant identity
evidence) is **mandatory at account creation** — no account exists without one — so
the default user is not lockable-out by omission. Recovery is **inside the threat
model**: recovery *initiation and verification* are rate-limited and locked out
mirroring §2.1; support-mediated recovery requires defined identity evidence and is
logged/alerted (§8); and a **successful recovery rotates the session and invalidates
all live login tokens**. The recovery path is held to the same bar as the primary path,
so the §7.1 defense claims hold end-to-end.

## §8 Observability and retention

### §8.1 Metrics

Counters/timers for: link requests, **rate-limit drops** (dimensioned per-address vs
per-IP, with alert thresholds — this is how an abuse spike becomes visible), sent,
clicks, confirmations, logins, expired/superseded-link hits, replay attempts, and
recovery attempts. The `send-failures` counter is now live, since §5.0 defines failures.

### §8.2 Logging and retention

Raw tokens are **never** logged; only the hash or an opaque request id appears. Email
addresses in logs are minimised. Token rows are reaped on a stated TTL (consumed/
superseded: 7 days; expired: 24 h), but a minimal **tombstone** (hash + state +
consumed_at) is retained past row-reap for the replay-observation window so a replay
stays classifiable as a replay rather than collapsing into the unknown-token path.
Reaping never runs before expiry + the replay-observation window.

## Changelog

- **v0.1** — initial draft. Deliberately weak; authored as a review target.
- **v0.2** — closed the three round-001 BLOCKERs (token entropy/at-rest, expiry/single-
  use/state machine, session rotation) plus security-adjacent findings; left UX,
  delivery, recovery soundness, and success criteria open.
- **v0.3** — closed the three round-002 BLOCKERs the v0.2 fixes had introduced (unscoped
  recovery, invariant-without-state, error-states dangling reference) and the round-002
  findings: timing-parity mechanism (§4.0), originating-session-scoped idempotency to
  stop targeted login-denial (§2.2), async/retry delivery + resend (§5.0), POST-to-
  consume + cross-device model defeating scanner pre-fetch (§6.0), email trust signals
  + accessibility (§5.1/§6.1), observability/retention fixes (§8), success criteria and
  explicit scope (§1), and the clock/lookup cleanups (§3.1/§3.3).
