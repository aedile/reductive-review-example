# Magic Link Login — Design Spec (v0.2)

> Fictional teaching artifact. The three round-001 BLOCKERs are closed; several
> FINDINGs (delivery UX, cross-device, error/accessibility states, trust signals,
> success criteria) remain open — see `docs/reviews/rounds/`. **Do not implement.**

## §1 Goal

Let users sign in by entering their email address and clicking a one-time link we
send them. No passwords to choose, store, or leak.

Why magic links over passkeys or TOTP here: the audience is low-frequency consumer
sign-in where credential reset is the dominant support cost; email possession is
already the de-facto recovery factor, so making it the primary factor removes a
moving part. Passkeys/OTP are reasonable alternatives and are not precluded later.

## §2 Request flow

### §2.1 Requesting a link

A user submits their email address. If the address belongs to an account, we mint a
login token (§3) and email a link containing it. Requests are **rate-limited**: no
more than 3 per address per 15 minutes and no more than 10 per source IP per 15
minutes, with exponential backoff. Requests beyond the limit are accepted at the UI
layer (so the response can't enumerate — see §4) but dropped before any email is
sent. The same limits cap cost and protect the sender's reputation from being used
to bomb a third party's inbox.

### §2.2 Idempotency

Requesting a second link before the first is consumed **invalidates the first**. At
most one live token exists per account; the most recent request wins. Repeated
submits within a short window coalesce to the in-flight link rather than minting more.

## §3 The token

### §3.1 Generation

The token is 32 bytes from a cryptographically secure RNG, encoded URL-safe. It is
**not** derived from the timestamp, user id, or any guessable input. We persist only
a hash of the token (keyed for O(1) lookup) and compare in constant time; the raw
token exists only in the emailed link.

### §3.2 State machine and single use

A token record has states **issued → consumed** (terminal) and **issued → expired**
(terminal). Consumption is a single atomic compare-and-set (`issued → consumed`);
only the winner of a race mints a session, so two concurrent clicks cannot both
succeed. Verifying a consumed or expired token fails closed with a defined response
(see §6.1, still open). Tokens expire after **10 minutes**.

### §3.3 Expiry and clock skew

Expiry is evaluated against the datastore's authoritative server time, never a
client-supplied time, with a small fixed **±60 seconds** skew tolerance for
issuance/validation host differences. (This section was an empty placeholder in v0.1.)

### §3.4 Session creation and rotation

On a successful login we **rotate the session identifier**: any pre-login session id
is discarded and a fresh, server-issued id is set. This closes session fixation.
Session cookies are `HttpOnly`, `Secure`, and `SameSite=Lax`.

## §4 Responses

### §4.0 Uniform response

Whether or not the address has an account, the UI returns the **same** message and
the **same** timing: "If an account exists for that address, we've sent a sign-in
link." No account existence is disclosed through copy, status codes, latency, or
observable send side-effects.

## §5 Delivery

### §5.0 Sending

We send the email.

*(OPEN FINDING F3 from round-001: delivery is still treated as best-effort — no
retry, no failure surface, no resend, and email is the sole channel. To be closed in
a later revision.)*

## §6 User experience

### §6.0 Happy path

User clicks the link and is logged in.

*(OPEN FINDING F4: cross-device open — request on phone / open on laptop, and
email-scanner pre-fetch consuming the single-use token — is still undefined.)*

### §6.1 Other states

*(OPEN FINDINGs F5/F6: error / empty / edge states and accessibility are still
unspecified. The §3.2 "defined response" for consumed/expired tokens depends on this
being filled in.)*

## §7 Threat model, recovery, and lockout

### §7.1 Threat model (stated)

We defend against: token guessing, link replay, account enumeration, send-rate abuse
/ inbox bombing, and session fixation. We **do not** defend against an attacker who
already controls the user's email inbox — that is the trust root of this scheme and
is an explicit, accepted assumption. Shared/forwarded inboxes inherit it; high-
assurance accounts should layer a second factor (out of scope).

### §7.2 Recovery and lockout (ownership)

Because email access is the trust root, losing email access is the lockout case. We
**own the dependency by delegating it**: an account needing a fallback must enrol a
recovery method (second verified channel or support-mediated identity check) at
creation time. This spec does not silently assume the user can always receive mail.

## §8 Observability and retention

### §8.1 Metrics

Counters/timers for: link requests, sent, send-failures, clicks, logins, expired-
link hits, replay attempts — enough to detect an abuse spike or a delivery regression.

### §8.2 Logging and retention

Raw tokens are **never** logged; only the hash or an opaque request id appears.
Consumed/expired token rows are reaped on a defined TTL so the table doesn't grow
unbounded and the at-rest secret surface stays small.

## Changelog

- **v0.1** — initial draft. Deliberately weak; authored as a review target.
- **v0.2** — closed all three round-001 BLOCKERs (CSPRNG single-use token with atomic
  consume + 10-min expiry, §3.1–§3.2; session rotation, §3.4) plus the security-
  adjacent findings the arbiter scoped: send rate-limiting/idempotency (§2.1–§2.2),
  uniform response closing enumeration (§4.0), stated clock-skew authority (§3.3),
  stated threat model and owned recovery dependency (new §7), observability +
  retention (new §8), passwordless rationale (§1). Delivery UX, cross-device,
  error/accessibility states, trust signals, and success criteria remain open.
