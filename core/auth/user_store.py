"""
UserStore: Handles secure user registration, authentication, and profile persistence.
Backed by ArcticDB. All PII fields are encrypted via SecurityManager before storage.
"""
import datetime
import json
import pandas as pd
from arcticdb import Arctic
import logging
from core.auth.security_manager import SecurityManager

logger = logging.getLogger(__name__)

from core.data.db import get_arctic

class UserStore:
    """
    Persists user profiles, authentication credentials, and session data.
    
    Schema (stored encrypted):
    - user_id: str (primary key, derived from email hash)
    - email: encrypted str
    - name: encrypted str  
    - role: 'user' | 'admin'
    - password_hash: str
    - created_at: datetime
    - last_login: datetime
    - risk_profile: str
    - onboarding_complete: bool
    """

    LIBRARY = "user_profiles"

    def __init__(self, uri: str = "lmdb://./data/arctic"):
        self.arctic = get_arctic(uri)
        self.sec = SecurityManager()

        if self.LIBRARY not in self.arctic.list_libraries():
            self.arctic.create_library(self.LIBRARY)
        self.lib = self.arctic.get_library(self.LIBRARY)

    def _user_key(self, email: str) -> str:
        """Derives a stable, non-PII storage key from email."""
        import hashlib
        return "user_" + hashlib.sha256(email.lower().encode()).hexdigest()[:16]

    def register(self, name: str, email: str, password: str, role: str = "user") -> dict:
        """
        Registers a new user. Returns {'success': True} or {'error': ...}.
        """
        user_key = self._user_key(email)
        if user_key in self.lib.list_symbols():
            return {"error": "An account with this email already exists."}

        record = {
            "user_key": user_key,
            "name_enc": self.sec.encrypt(name),
            "email_enc": self.sec.encrypt(email),
            "password_hash": self.sec.hash_password(password),
            "role": role,
            "onboarding_complete": False,
            "risk_profile": "Moderate",
            "created_at": str(datetime.datetime.now()),
            "last_login": ""
        }
        df = pd.DataFrame([record])
        self.lib.write(user_key, df, metadata={"role": role})
        return {"success": True, "user_key": user_key}

    def authenticate(self, email: str, password: str) -> dict:
        """
        Verifies credentials. Returns user profile dict or {'error': ...}.
        """
        try:
            user_key = self._user_key(email)
            if user_key not in self.lib.list_symbols():
                return {"error": "No account found with this email."}

            version = self.lib.read(user_key)
            row = version.data.iloc[0]

            if not self.sec.verify_password(password, row["password_hash"]):
                return {"error": "Incorrect password."}

            # Update last login
            if "last_login" not in version.data.columns:
                version.data["last_login"] = ""
            version.data.at[0, "last_login"] = str(datetime.datetime.now())
            self.lib.write(user_key, version.data, metadata=version.metadata)

            try:
                name = self.sec.decrypt(row["name_enc"])
                user_email = self.sec.decrypt(row["email_enc"])
            except Exception as e_dec:
                logger.error(f"Decryption failed for user {user_key}: {e_dec}")
                return {"error": "Authentication failed due to internal security mismatch."}

            return {
                "success": True,
                "user_key": user_key,
                "name": name,
                "email": user_email,
                "role": row.get("role", "user"),
                "risk_profile": row.get("risk_profile", "Moderate") if pd.notna(row.get("risk_profile")) else "Moderate",
                "onboarding_complete": bool(row.get("onboarding_complete")) if pd.notna(row.get("onboarding_complete")) else False,
            }
        except Exception as e:
            logger.error(f"Login failed for {email}: {e}")
            return {"error": f"Internal authentication error: {str(e)}"}

    def update_profile(self, user_key: str, updates: dict):
        """
        Updates a user's profile fields (risk_profile, onboarding_complete, etc.).
        """
        if user_key not in self.lib.list_symbols():
            return
        version = self.lib.read(user_key)
        for k, v in updates.items():
            version.data.at[0, k] = v
        self.lib.write(user_key, version.data, metadata=version.metadata)

    def get_profile(self, user_key: str) -> dict:
        """Returns the decrypted user profile."""
        if user_key not in self.lib.list_symbols():
            return {}
        version = self.lib.read(user_key)
        row = version.data.iloc[0]
        return {
            "user_key": user_key,
            "name": self.sec.decrypt(row["name_enc"]),
            "email": self.sec.decrypt(row["email_enc"]),
            "role": row.get("role", "user"),
            "risk_profile": row.get("risk_profile", "Moderate") if pd.notna(row.get("risk_profile")) else "Moderate",
            "onboarding_complete": bool(row.get("onboarding_complete")) if pd.notna(row.get("onboarding_complete")) else False,
            "created_at": row.get("created_at", ""),
            "last_login": row.get("last_login", ""),
        }
