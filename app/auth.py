"""Authentication.

Three ways in, one per surface, because the three roles have nothing in common.

  Inside     a DIN or NYSID, plus a PIN the person creates the first time
  Family     an invite code, plus a PIN they create the first time
  Staff      a staff ID, plus a PIN

The PII compliance regime is assumed away for this build. Hashing the PIN is
not part of that regime; it is just what you do, it costs nothing, and shipping
a prototype that stores PINs in the clear teaches the wrong habit to whoever
picks this up next. PINs are PBKDF2-HMAC-SHA256 with a per-user salt, and the
plaintext never reaches the store.

The threat this actually defends against is not a remote attacker. It is the
next person to use the tablet. So: short idle timeout, lockout after a handful
of wrong PINs, weak PINs refused, and no screen that leaves somebody's case
open after they walk away.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

PBKDF2_ROUNDS = 240_000
PIN_LENGTH = 6

# A personal device, but one that gets set down, carried through movement,
# and read with other people in line of sight.
IDLE_TIMEOUT = timedelta(minutes=15)
STAFF_IDLE_TIMEOUT = timedelta(hours=8)

MAX_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=15)

COOKIE_NAME = "bridge_session"


class AuthError(Exception):
    """Carries a sentence meant to be read by the person who hit it."""


# --------------------------------------------------------------------------
# PINs
# --------------------------------------------------------------------------

def _digits_only(pin: str) -> str:
    return "".join(ch for ch in (pin or "") if ch.isdigit())


def _is_run(pin: str) -> bool:
    deltas = {ord(b) - ord(a) for a, b in zip(pin, pin[1:])}
    return deltas in ({1}, {-1})


def check_pin_strength(pin: str, *, identifier: str = "") -> None:
    """Refuse the PINs that get shoulder-surfed or guessed in three tries.

    Not a strength meter. Four specific rules, each with a reason a person
    would accept if you said it out loud.
    """
    pin = _digits_only(pin)
    if len(pin) != PIN_LENGTH:
        raise AuthError(f"Your PIN needs to be {PIN_LENGTH} numbers.")
    if len(set(pin)) == 1:
        raise AuthError("Pick something other than the same number six times.")
    if _is_run(pin):
        raise AuthError("Pick something that is not just counting up or down.")
    if identifier and pin in "".join(ch for ch in identifier if ch.isdigit()):
        raise AuthError(
            "That is part of your own number, which anyone holding your "
            "paperwork can read. Pick something else."
        )


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", _digits_only(pin).encode(), salt, PBKDF2_ROUNDS
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}$" \
           f"{base64.b64encode(digest).decode()}"


def verify_pin(pin: str, stored: str) -> bool:
    try:
        algo, rounds, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", _digits_only(pin).encode(),
        base64.b64decode(salt_b64), int(rounds),
    )
    return hmac.compare_digest(candidate, base64.b64decode(digest_b64))


# --------------------------------------------------------------------------
# accounts
# --------------------------------------------------------------------------

@dataclass
class Account:
    """One login. Never holds a PIN, only its hash."""

    account_id: str
    role: str                  # inside | family | staff
    subject_id: str            # which client this account acts on
    login_key: str             # normalized DIN/NYSID, invite code, or staff id
    pin_hash: str | None = None
    display_name: str = ""
    failed_attempts: int = 0
    locked_until: str | None = None
    last_seen: str | None = None

    @property
    def enrolled(self) -> bool:
        return self.pin_hash is not None

    def lock_remaining(self, now: datetime | None = None) -> timedelta | None:
        if not self.locked_until:
            return None
        now = now or datetime.now(timezone.utc)
        until = datetime.fromisoformat(self.locked_until)
        return until - now if until > now else None

    def attempts_left(self) -> int:
        return max(0, MAX_ATTEMPTS - self.failed_attempts)


def enroll(account: Account, pin: str, confirm: str) -> None:
    """First use. The person picks the PIN; nobody issues it to them."""
    if account.enrolled:
        raise AuthError("This account already has a PIN.")
    if _digits_only(pin) != _digits_only(confirm):
        raise AuthError("Those two PINs are not the same. Try again.")
    check_pin_strength(pin, identifier=account.login_key)
    account.pin_hash = hash_pin(pin)
    account.failed_attempts = 0
    account.locked_until = None


def authenticate(account: Account, pin: str, now: datetime | None = None) -> None:
    """Raises on failure, mutating the lockout counters. Returns None on success."""
    now = now or datetime.now(timezone.utc)

    remaining = account.lock_remaining(now)
    if remaining is not None:
        minutes = max(1, int(remaining.total_seconds() // 60) + 1)
        raise AuthError(
            f"Too many wrong tries. Try again in about {minutes} minutes, or "
            f"ask your counselor to reset it."
        )

    if not account.enrolled:
        raise AuthError("This account has no PIN yet.")

    if verify_pin(pin, account.pin_hash):
        account.failed_attempts = 0
        account.locked_until = None
        account.last_seen = now.isoformat()
        return

    account.failed_attempts += 1
    if account.failed_attempts >= MAX_ATTEMPTS:
        account.locked_until = (now + LOCKOUT).isoformat()
        account.failed_attempts = 0
        raise AuthError(
            "That PIN was wrong too many times. The account is locked for 15 "
            "minutes. Your counselor can reset it sooner."
        )
    left = MAX_ATTEMPTS - account.failed_attempts
    # Saying how many are left is a small disclosure and it stops somebody
    # locking themselves out of their own case by accident.
    raise AuthError(f"That PIN is not right. {left} tries left before it locks.")


def reset_pin(account: Account) -> None:
    """A counselor clears it; the person sets a new one on their tablet.

    Staff never choose somebody else's PIN. Setting it for them would make the
    PIN something a staff member knows, which defeats the point of having one.
    """
    account.pin_hash = None
    account.failed_attempts = 0
    account.locked_until = None


# --------------------------------------------------------------------------
# sessions
# --------------------------------------------------------------------------

@dataclass
class Session:
    account_id: str
    role: str
    subject_id: str
    issued_at: float = field(default_factory=time.time)
    seen_at: float = field(default_factory=time.time)

    def idle_limit(self) -> timedelta:
        return STAFF_IDLE_TIMEOUT if self.role == "staff" else IDLE_TIMEOUT

    def expired(self, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        return (now - self.seen_at) > self.idle_limit().total_seconds()


def _secret() -> bytes:
    """Cookie signing key.

    From the environment in a real deployment. Generated and kept in the store
    otherwise, so a restart does not sign everyone out mid-demo.
    """
    env = os.environ.get("BRIDGE_SECRET")
    if env:
        return env.encode()

    from app.store import STATE, save

    if not STATE.secret:
        STATE.secret = secrets.token_urlsafe(32)
        save()
    return STATE.secret.encode()


def _sign(payload: bytes) -> str:
    mac = hmac.new(_secret(), payload, hashlib.sha256).digest()
    return (base64.urlsafe_b64encode(payload).decode().rstrip("=")
            + "." + base64.urlsafe_b64encode(mac).decode().rstrip("="))


def _unpad(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue(session: Session) -> str:
    body = json.dumps({
        "account_id": session.account_id,
        "role": session.role,
        "subject_id": session.subject_id,
        "issued_at": session.issued_at,
        "seen_at": session.seen_at,
    }, separators=(",", ":")).encode()
    return _sign(body)


def read(token: str | None) -> Session | None:
    """Returns None for anything not signed by us, tampered with, or idle out."""
    if not token or "." not in token:
        return None
    body_b64, mac_b64 = token.rsplit(".", 1)
    try:
        body = _unpad(body_b64)
        mac = _unpad(mac_b64)
    except Exception:
        return None
    expected = hmac.new(_secret(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        return None
    try:
        data = json.loads(body)
        session = Session(
            account_id=data["account_id"], role=data["role"],
            subject_id=data["subject_id"],
            issued_at=float(data["issued_at"]), seen_at=float(data["seen_at"]),
        )
    except Exception:
        return None
    return None if session.expired() else session


def touch(session: Session) -> str:
    """Slide the idle window forward on every request."""
    session.seen_at = time.time()
    return issue(session)
