from core.data.store import DataStore
from core.auth.user_store import UserStore

try:
    ds = DataStore()
    us = UserStore()
    print("Success")
except Exception as e:
    print("Error:", e)
