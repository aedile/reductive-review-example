# Magic Link Login — Design Spec (v0.1)

> Fictional teaching artifact. Intentionally incomplete and insecure. **Do not implement.**

## §1 Goal

Let users sign in by entering their email and clicking a link we send them.
No passwords.

## §2 Request flow

### §2.1 Requesting a link

User submits their email. We immediately generate a login link and email it.

*(SEEDED FLAW: no limit on how often this can be requested.)*

## §3 The token

### §3.1 Generation

The token in the link is derived from the current timestamp so it's unique.

*(SEEDED FLAW: predictable / low entropy.)*

### §3.2 Use

The link logs the user in when clicked.

*(SEEDED FLAW: no expiry; reusable / replayable.)*

### §3.3 Expiry

(expiry unspecified)

### §3.4 Session

On click we create a session.

*(SEEDED FLAW: no session rotation / fixation handling.)*

## §4 Responses

### §4.0 Result message

If the email isn't registered, we tell the user "no account found"; if it is, we
say "check your inbox."

*(SEEDED FLAW: account enumeration.)*

## §5 Delivery

### §5.0 Sending

We send the email and assume it arrives.

*(SEEDED FLAW: no delivery-failure path.)*

## §6 User experience

### §6.0 Happy path

User clicks the link and is logged in.

*(SEEDED FLAW: no handling of opening the link on a different device.)*

### §6.1 Other states

(error / empty / edge states unspecified; accessibility unspecified.)

## §1-scope note

(SEEDED FLAW: no account-recovery story if the user loses email access; no stated
threat model.)

## Changelog

- **v0.1** — initial draft. Deliberately weak; authored as a review target.
