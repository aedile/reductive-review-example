# Security Adversary — Round 001

Target: `docs/design/magic-link-auth.md` v0.1

## BLOCKER

### §3.1 — Token derived from timestamp is forgeable, enabling unauthenticated account takeover
- Problem: The token is "derived from the current timestamp so it's unique." Timestamps are public, low-entropy, and monotonic. An attacker who knows (or guesses to within a small window) the second the link was generated can reconstruct the token offline. Uniqueness is not the property required — unpredictability is.
- Why it matters: This is direct, unauthenticated account takeover. An attacker triggers a link for a victim's email (the §4.0 enumeration tells them the account exists), then brute-forces the small timestamp space to forge the victim's login token without ever touching the victim's inbox. The entire auth scheme collapses.
- Suggested resolution: Generate the token from a CSPRNG with at least 128 bits of entropy (e.g. 32 hex / 26 base32 chars), with no derivation from any observable input. Store only a hash of the token server-side and compare in constant time.

### §3.2 / §3.3 — No expiry and no single-use consumption: links are permanently replayable
- Problem: The link "logs the user in when clicked" with expiry unspecified (§3.3 empty) and no server-side invalidation on use. A consumed link logs anyone in, forever.
- Why it matters: Any historical link — in inbox archives, mail-server logs, browser history, referrer headers, corporate mail scanners, backups — is a permanent credential. Replay after use is trivial; there is no window that ever closes. Combined with §3.1 this is fatal even without forgery.
- Suggested resolution: Single-use tokens with mandatory short TTL (5–15 min). On the first successful consume, atomically mark the token consumed (server-side) so a second click fails closed. Tokens must also be invalidated when a new one is requested for the same account.

### §3.4 — Session created without rotation: session fixation
- Problem: "On click we create a session" with no session-identifier rotation noted. If a pre-authentication session id exists (anonymous cart, CSRF token, etc.), it is not rotated at login.
- Why it matters: An attacker who plants a known session id in the victim's browser before login keeps that id valid post-authentication, yielding an authenticated session the attacker also holds — account takeover without the token. Failure to rotate is a classic, exploitable fixation path.
- Suggested resolution: On successful consume, invalidate any existing session and issue a fresh session id with new server-side state. Bind the new session to first-party, `HttpOnly`, `Secure`, `SameSite` cookies.

## FINDING

### §2.1 — No send-rate limiting: email-bombing and inbox/relay abuse
- Problem: "We immediately generate a login link and email it" with explicitly no limit on request frequency.
- Why it matters: The send path is an unauthenticated, attacker-controlled email amplifier. An attacker can flood any victim's inbox (harassment / burying real mail), exhaust the sender's deliverability reputation (causing all real links to land in spam), and run up sending cost. It also enables enumeration scaling (see §4.0) and, with §3.1/§3.2, mass token-grinding.
- Suggested resolution: Per-email and per-IP rate limits with exponential backoff, a global send budget, CAPTCHA/proof-of-work on repeated requests, and collapse of repeated requests within a window to a single live token.

### §4.0 — Account enumeration via differential response copy
- Problem: Unregistered emails get "no account found"; registered emails get "check your inbox." The response directly discloses account existence.
- Why it matters: Enumeration is the precondition for the targeted attacks above (§3.1 forging, §2.1 bombing) and is itself a privacy leak (revealing who has an account on a sensitive service). Even if copy is unified, timing and observable email-send side effects can leak the same bit.
- Suggested resolution: Return an identical neutral message ("If an account exists, we've sent a link") for all inputs, with matched response timing and no observable difference in side effects between the registered/unregistered branches.

### §6.0 — Cross-device link opening widens interception surface and invites token mishandling
- Problem: Opening the link on a different device is unhandled. The implicit assumption that "click = the requester clicks" is false in practice (link opened on desktop after request on mobile, or vice versa).
- Why it matters: To "make it work" cross-device, implementers commonly weaken the token (longer TTL, multi-use, or detaching it from the requesting session/IP), each of which directly enlarges the replay/interception attack surface. Without a stated model, the door is open to exactly these regressions, and to logging the wrong device in.
- Suggested resolution: Define the cross-device model explicitly. Prefer binding consumption to the originating request (same-browser continuation) or require a short numeric verification code entered on the requesting device, rather than relaxing token properties.

## ADVISORY

### §1-scope — No threat model and no account-recovery story
- Problem: No stated threat model, and no recovery path when the user loses email access.
- Why it matters: With email as the sole factor, loss of inbox access = permanent lockout, and any out-of-band recovery channel added later becomes the new weakest link and a takeover vector if unscoped now. Absence of a threat model means the seeded flaws have no acceptance criteria to be measured against.
- Suggested resolution: State the threat model (adversary capabilities: inbox access, network position, enumeration). Specify whether recovery exists; if so, design it under the same adversarial scrutiny (it must not be a softer takeover path).

### §5.0 — "Assume it arrives" hides a silent denial-of-service and an oracle
- Problem: Delivery is assumed to succeed with no failure path.
- Why it matters: Bounces/drops produce a silent lockout (user never receives the only credential). Conversely, surfacing delivery status to the requester can leak whether the address is deliverable/real — a secondary enumeration oracle. Either direction has a security consequence.
- Suggested resolution: Handle delivery failure without leaking address validity to the requester; log/alert server-side; keep the user-facing message neutral and identical regardless of delivery outcome.

### §3.4 — Clock-skew authority undefined once expiry is introduced
- Problem: Fixing §3.3 introduces expiry, but no section states whose clock decides validity or what skew tolerance applies.
- Why it matters: If expiry is ever evaluated against a client-supplied or unsynchronized time, an attacker can extend a token's life; an over-generous skew tolerance reopens the replay window.
- Suggested resolution: Evaluate expiry solely against the server's monotonic clock with zero client trust and a small, explicit tolerance (e.g. ≤30s) only for issuance/validation host skew.

## Cross-section coherence flags
- §2.1 ("we immediately generate and email") and §3.3 (expiry unspecified) jointly imply an unbounded, ever-growing population of live valid tokens per account — no section caps concurrent live tokens or invalidates prior ones on re-request.
- §6.0 (cross-device unhandled) is in latent tension with the §3.x token model: the only safe ways to support cross-device contradict the short-TTL/single-use/session-bound properties the §3 fixes will require. These sections must be reconciled, not fixed independently.
- §3.3 is an empty placeholder yet §3.2's flaw note ("no expiry") depends on it; the doc asserts a property in one section that another section leaves blank.
- §4.0 enumeration is the force-multiplier for §3.1 and §2.1; treating them as independent findings understates combined severity (forge-a-known-target chain).

## Summary
Three BLOCKERs (forgeable timestamp token, no expiry/single-use replay, session fixation) mean the document cannot be trusted as an auth design — each independently yields account takeover, and they chain with the §4.0 enumeration and §2.1 unbounded send into a clean unauthenticated-takeover path. The remaining FINDINGs and ADVISORYs (rate limiting, cross-device, recovery, delivery oracle, clock authority) are substantive but secondary to closing the token and session model. Another round is clearly warranted: the BLOCKERs are still wide open at v0.1 and must be re-reviewed once the token, expiry/consumption, and session-rotation sections are rewritten — I have material objections remaining and nothing here is close to resolved.
