from __future__ import annotations

import hashlib
import hmac
import os
import re


PBKDF2_ITERATIONS = 240_000


class Pbkdf2PasswordHasher:
    def normalize_phone_number(self, value: str) -> str:
        raw = re.sub(r"[\s()-]+", "", value.strip())
        if raw.startswith("+"):
            normalized = f"+{re.sub(r'[^0-9]', '', raw[1:])}"
        else:
            normalized = re.sub(r"[^0-9]", "", raw)

        if not re.fullmatch(r"(?:\+?[0-9]{9,15})", normalized):
            raise ValueError("Phone number must contain 9 to 15 digits")
        return normalized

    def validate_local_password(self, value: str) -> str:
        if len(value) < 8 or len(value) > 128:
            raise ValueError("password must be 8 to 128 characters")
        if not any(char.isalpha() for char in value):
            raise ValueError("password must contain at least one letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("password must contain at least one digit")
        return value

    def hash_password(self, value: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            value.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
            dklen=32,
        )
        return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        parts = password_hash.split("$")
        if len(parts) != 4:
            return False
        algorithm, iterations_text, salt_hex, digest_hex = parts
        if algorithm != "pbkdf2_sha256":
            return False
        derived_digest = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations_text),
            dklen=32,
        )
        return hmac.compare_digest(derived_digest.hex(), digest_hex)
