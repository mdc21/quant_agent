from arcticdb import Arctic
import os

_ARCTIC_INSTANCE = None

def get_arctic(uri: str = "lmdb://./data/arctic") -> Arctic:
    global _ARCTIC_INSTANCE
    if _ARCTIC_INSTANCE is None:
        # Ensure data directory exists
        os.makedirs("./data/arctic", exist_ok=True)
        _ARCTIC_INSTANCE = Arctic(uri)
    return _ARCTIC_INSTANCE
