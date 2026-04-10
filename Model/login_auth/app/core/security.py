from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Tuple

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# OWASP recommends Argon2id for password storage. These defaults align with the
# common baseline of 19 MiB memory, 2 iterations, and parallelism 1.
PASSWORD_HASHER = PasswordHasher(
    time_cost=int(os.getenv("PASSWORD_HASH_TIME_COST", "2")),
    memory_cost=int(os.getenv("PASSWORD_HASH_MEMORY_COST", "19456")),
    parallelism=int(os.getenv("PASSWORD_HASH_PARALLELISM", "1")),
    hash_len=32,
    salt_len=16,
)

LEGACY_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    if not password:
        raise ValueError("Password cannot be empty")
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, stored_hash: str) -> Tuple[bool, bool]:
    """
    Verify a password against the stored hash.

    Returns:
        (is_valid, needs_rehash)

    needs_rehash is True when the stored credential should be upgraded, such as:
      - legacy SHA-256 hashes still present in DynamoDB
      - Argon2 hashes that no longer match the configured parameters
    """
    if not stored_hash:
        return False, False

    if stored_hash.startswith("$argon2"):
        try:
            PASSWORD_HASHER.verify(stored_hash, password)
        except VerifyMismatchError:
            return False, False
        except (VerificationError, InvalidHashError):
            return False, False
        return True, PASSWORD_HASHER.check_needs_rehash(stored_hash)

    # Legacy migration path for accounts created before Argon2id was added.
    if LEGACY_SHA256_RE.fullmatch(stored_hash):
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash), True

    return False, False
