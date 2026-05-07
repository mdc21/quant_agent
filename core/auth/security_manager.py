"""
SecurityManager: Handles PII encryption/decryption for user financial data.
Uses Fernet (AES-128-CBC + HMAC) for symmetric encryption.
The MASTER_ENCRYPTION_KEY must be set in .env
"""
import os
import base64
import hashlib
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class SecurityManager:
    """
    Encrypts and decrypts sensitive user data (PII, financial details).
    All financial fields are encrypted before being persisted to ArcticDB.
    """

    def __init__(self):
        raw_key = os.getenv("MASTER_ENCRYPTION_KEY", "")
        if raw_key:
            # Derive a valid 32-byte Fernet key from the provided secret
            key_bytes = hashlib.sha256(raw_key.encode()).digest()
            self._fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
        else:
            # Generate a new key if none is set — warn the developer
            new_key = Fernet.generate_key()
            self._fernet = Fernet(new_key)
            print(
                "⚠️  WARNING: MASTER_ENCRYPTION_KEY not set in .env. "
                "A temporary key is being used — data will NOT be recoverable after restart. "
                f"Add this to your .env: MASTER_ENCRYPTION_KEY={new_key.decode()}"
            )

    def encrypt(self, data: dict | str) -> str:
        """Encrypts a dict or string to a base64 token."""
        if isinstance(data, dict):
            data = json.dumps(data)
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> dict | str:
        """Decrypts a token back to the original dict or string."""
        raw = self._fernet.decrypt(token.encode()).decode()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def hash_password(self, password: str) -> str:
        """One-way hash for password storage (SHA-256 + salt from master key)."""
        salt = os.getenv("MASTER_ENCRYPTION_KEY", "default_salt")
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        return self.hash_password(password) == hashed
