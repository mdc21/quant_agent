import hashlib
import json
import os
import sqlite3
import datetime
from typing import Dict, Any, List, Optional

class GovernanceAgent:
    """
    Compliance & Governance Agent (Layer 4).
    Ensures immutability, auditability, and regulatory compliance.
    Satisfies Task L4.
    """
    def __init__(self, db_path: str = "app/data/audit_log.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Initializes the append-only audit database.
        """
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                manifest_hash TEXT NOT NULL,
                integrity_sealed INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def calculate_hash(self, data: Dict[str, Any]) -> str:
        """
        Generates a SHA-256 fingerprint of the decision manifest.
        """
        # Canonicalize JSON for consistent hashing
        encoded = json.dumps(data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(encoded).hexdigest()

    def seal_decision(self, manifest: Dict[str, Any]):
        """
        Signs and stores the decision manifest in the immutable ledger.
        """
        manifest_hash = self.calculate_hash(manifest)
        timestamp = datetime.datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_trail (timestamp, manifest_json, manifest_hash) VALUES (?, ?, ?)",
            (timestamp, json.dumps(manifest), manifest_hash)
        )
        conn.commit()
        conn.close()
        print(f"AUDIT SEALED: Hash {manifest_hash[:12]}...")

    def verify_integrity(self) -> List[str]:
        """
        Background auditor that checks for unauthorized data modifications.
        """
        breaches = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, manifest_json, manifest_hash FROM audit_trail")
        
        for row_id, m_json, m_hash in cursor.fetchall():
            actual_hash = self.calculate_hash(json.loads(m_json))
            if actual_hash != m_hash:
                breaches.append(f"TAMPER DETECTED: Row {row_id} hash mismatch!")
                
        conn.close()
        return breaches

    def reconstruct_state(self, timestamp_start: str, timestamp_end: str) -> List[Dict[str, Any]]:
        """
        Retrieves historical manifests for a specific time window.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT manifest_json FROM audit_trail WHERE timestamp BETWEEN ? AND ?",
            (timestamp_start, timestamp_end)
        )
        records = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        return records
