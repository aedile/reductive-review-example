# Magic Link Login — Design Spec (v0.3)

> Fictional teaching artifact. This spec began life intentionally insecure (v0.1)
> and was hardened across three recorded review rounds. Even at v0.3 it is a
> teaching example, not a production design. **Do not implement.**

## §1 Goal

Let users sign in by entering their email address and clicking a one-time link we
send them. No passwords to choose, store, or leak.

In scope: first-party web sign-in for an account that already has a verified email
on file. Out of scope (and explicitly delegated elsewhere): initial account
creation, multi-factor step-up, and recovery when the user has lost access to the
email account itself — see §7.

## §2 Request flow

### §2.1 Requesting a link

A user submits their email address. If the address belongs to an account, we mint
a login token (§3) and email a link containing it. Requests are **rate-limited**:
no more than 3 link requests per address per 15 minutes and no more than 10 per
source IP per 15 minutes, with exponential backoff on repeated requests. Requests
beyond the limit are accepted at the UI layer (to avoid leaking which addresses
exist — see §4) but silently dropped before any email is sent. The same limits
protect the email path from being used to bomb a third party's inbox.

### §2.2 Idempotency

Requesting a second link before the first is consumed **invalidates the first**.
At most one live token exists per account at any time; the most recent request
wins. This bounds the replay surface and removes the "which of my three links is
the live one" confusion.

## §3 The token

### §3.1 Generation

The token is 32 bytes from a cryptographically secure RNG, encoded URL-safe. It is
**not** derived from the timestamp, the user id, or any guessable input. We store
only a hash of the token server-side; the raw token exists only in the emailed
link.

### §3.2 Single use and lifetime

A token is valid for a single successful login and is **invalidated server-side
the instant it is consumed**. Replaying a consumed link fails closed. Tokens also
expire after **10 minutes**; an expired or already-consumed link shows a "this
link has expired — request a new one" page (§6.1), never a session.

### §3.3 Expiry and clock skew

Expiry is evaluated against server time, not the email's timestamp. We allow a
fixed **±60 seconds** of skew tolerance so that a link clicked right at the
boundary on a client with a slightly wrong clock still behaves predictably. The
tolerance is a stated constant, not an accident of whichever host serves the
request.

### §3.4 Session creation and rotation

On a successful login we **rotate the session identifier**: any pre-login session
id is discarded and a fresh, server-issued session id is set. This closes the
session-fixation path where an attacker primes a victim's browser with a known
session id before login. Session cookies are `HttpOnly`, `Secure`, and
`SameSite=Lax`.

## §4 Responses

### §4.0 Uniform response

Whether or not the submitted address has an account, the UI returns the **same**
message and the **same** timing: "If an account exists for that address, we've
sent a sign-in link." We do not disclose account existence through copy, status
codes, or response latency. This closes account enumeration via the request
endpoint.

## §5 Delivery

### §5.0 Send, failure, and resend

We enqueue the email and treat delivery as **fallible**. The send path has a
bounded retry with backoff. If the provider reports a hard failure, we surface a
neutral "we couldn't send your link right now — try again shortly" state on the
next request rather than failing silently. The confirmation page includes a
**"didn't get it? resend"** control, governed by the §2.1 rate limits, and sets a
clear latency expectation ("links usually arrive within a minute; check spam").
Delivery outcomes are recorded as metrics (§8), not as user-identifying logs.

## §6 User experience

### §6.0 Cross-device flow

The common case — request the link on a phone, open it on a laptop — is supported.
The login completes in **whatever browser opens the link**; it does not require the
same device or session that made the request, because the token (§3) carries the
authority. The confirmation page states this plainly so a user who switches
devices is not left wondering whether it "worked on the wrong machine."

### §6.1 Error, empty, and edge states; accessibility

Defined states: link expired, link already used, link malformed, rate-limited,
delivery failed, and "wrong account" (the link is for a different address than the
one currently signed in). Each has neutral copy that does not leak account
existence. Pages and emails meet WCAG 2.1 AA: sufficient contrast, real focus
order, descriptive link text (no bare "click here"), and a plain-text email
alternative for clients that strip HTML.

## §7 Threat model, recovery, and lockout

### §7.1 Threat model (stated)

We defend against: token guessing, link replay, account enumeration, send-rate
abuse / inbox bombing, and session fixation. We **do not** defend against an
attacker who already controls the user's email inbox — that is the trust root of
this scheme and is stated as an explicit assumption, not an oversight. Shared or
forwarded inboxes inherit that assumption; high-assurance accounts should layer a
second factor (out of scope here).

### §7.2 Recovery and lockout

Because email access is the trust root, losing email access is the lockout case.
The recovery path is **delegated, not invented here**: an account that needs a
fallback must enrol a recovery method (a second verified channel or a support-
mediated identity check) at creation time. This spec does not silently assume the
user can always receive mail; it names the dependency and points to where recovery
lives.

## §8 Observability and logging

### §8.1 Metrics

We emit counters/timers for: link requests, links sent, send failures, link
clicks, successful logins, expired-link hits, and replay attempts. These let us
detect abuse spikes and delivery regressions.

### §8.2 Logging hygiene

Raw tokens are **never** logged — not in application logs, access logs, or error
traces; only the server-side token hash or an opaque request id appears. Email
addresses in logs are minimised. (Residual: log verbosity and retention on the
verify path are still coarse — see the open advisory in `docs/reviews/rounds/`.)

## Changelog

- **v0.1** — initial draft. Deliberately weak: timestamp-derived token, no expiry
  or single-use, no send rate-limiting, enumerating responses, no delivery-failure
  path, no session rotation, no cross-device/error/accessibility states, no
  recovery story, no stated threat model. Authored as a review target.
- **v0.2** — closed all three BLOCKERs from round-001: CSPRNG single-use token
  with a 10-minute expiry and server-side invalidation on use (§3.1–§3.2); send
  rate-limiting and abuse protection (§2.1); uniform "if an account exists" response
  (§4.0), which also closed account enumeration. Added stated clock-skew tolerance
  (§3.3) and single-live-token idempotency (§2.2) as a consequence of adding expiry.
- **v0.3** — closed the round-002 FINDINGs and the items the arbiter declined to
  let convergence soften: session rotation on login (§3.4); delivery-failure
  handling and a resend path (§5.0); explicit cross-device guidance (§6.0); defined
  error/empty/edge and accessibility states (§6.1); a stated threat model plus a
  delegated recovery/lockout story (§7); token-logging hygiene and send/verify
  metrics (§8). One non-material advisory on log verbosity remains open.
