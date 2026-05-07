import sys
from core.auth.user_store import UserStore

store = UserStore()
print("Registering...")
res1 = store.register("Test User", "test@example.com", "password123")
print(res1)
if "error" in res1 and "already exists" in res1["error"]:
    print("Already registered.")
    
print("Authenticating...")
res2 = store.authenticate("test@example.com", "password123")
print(res2)
