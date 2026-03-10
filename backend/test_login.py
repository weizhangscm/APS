"""Test login functionality"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.database import get_db
from app.routers.auth import hash_password, verify_password
from app import models

db = next(get_db())

# Query admin user
user = db.query(models.User).filter(models.User.username == 'admin').first()

if user:
    print("[OK] Admin user exists")
    print(f"  Username: {user.username}")
    print(f"  Full name: {user.full_name}")
    print(f"  Is active: {user.is_active}")
    print(f"  Stored password hash: {user.hashed_password}")
    print()
    
    # Test password verification
    test_password = "admin123"
    computed_hash = hash_password(test_password)
    print(f"  Hash for 'admin123': {computed_hash}")
    print(f"  Hashes match: {computed_hash == user.hashed_password}")
    print(f"  verify_password result: {verify_password(test_password, user.hashed_password)}")
else:
    print("[ERROR] Admin user does not exist")
    print("  Creating default user...")
    from app.routers.auth import init_default_user
    init_default_user(db)
    print("[OK] Default user created")
