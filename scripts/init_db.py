from arcticdb import Arctic
import os

def initialize_arctic_db():
    print("--- Initializing ArcticDB Libraries ---")
    
    # Path for local ArcticDB storage
    db_path = "lmdb://app/data/arctic_db"
    os.makedirs("app/data/arctic_db", exist_ok=True)
    
    ac = Arctic(db_path)
    
    libraries = ["market_data", "audit_log", "model_registry"]
    
    for lib in libraries:
        if lib not in ac.list_libraries():
            ac.create_library(lib)
            print(f"Created library: {lib}")
        else:
            print(f"Library already exists: {lib}")
            
    print("\nArcticDB Initialization Complete.")

if __name__ == "__main__":
    initialize_arctic_db()
