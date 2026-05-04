import sqlite3
import json
import os
from app.agents.governance import GovernanceAgent

def test_governance_logic():
    print("--- Starting Compliance & Governance (Layer 4) Test ---")
    
    db_path = "app/data/test_audit.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    gov = GovernanceAgent(db_path=db_path)
    
    # 1. Test Sealing
    print("\n[Scenario: Cryptographic Sealing]")
    manifest = {
        "timestamp": "2026-04-26T23:30:00",
        "regime": "BULL",
        "trades": [{"symbol": "RELIANCE", "qty": 100}]
    }
    
    gov.seal_decision(manifest)
    
    # 2. Test Integrity Monitor (Pass)
    print("\n[Scenario: Integrity Audit - Clean]")
    breaches = gov.verify_integrity()
    if not breaches:
        print("Success: Audit log integrity verified (No tampering).")

    # 3. Test Tamper Detection
    print("\n[Scenario: Tamper Detection]")
    # Manually modify the database behind the system's back
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Change the trade quantity from 100 to 999
    cursor.execute("SELECT id, manifest_json FROM audit_trail LIMIT 1")
    row_id, m_json = cursor.fetchone()
    tampered_json = m_json.replace("100", "999")
    cursor.execute("UPDATE audit_trail SET manifest_json = ? WHERE id = ?", (tampered_json, row_id))
    conn.commit()
    conn.close()
    
    print("Manually altered database row. Running audit...")
    breaches = gov.verify_integrity()
    for b in breaches:
        print(f"ALERT: {b}")
        
    if breaches and "TAMPER DETECTED" in breaches[0]:
        print("Success: Governance Agent correctly detected manual record alteration.")

    # 4. Test Reconstruction
    print("\n[Scenario: Historical Reconstruction]")
    # Re-insert clean record for reconstruction test
    gov.seal_decision({"note": "reconstruct_me"})
    history = gov.reconstruct_state("2000-01-01", "2099-12-31")
    print(f"Records retrieved: {len(history)}")
    if any(h.get("note") == "reconstruct_me" for h in history):
        print("Success: Historical state successfully reconstructed from audit log.")

if __name__ == "__main__":
    test_governance_logic()
