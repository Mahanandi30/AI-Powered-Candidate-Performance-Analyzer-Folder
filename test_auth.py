from app import app
from database.models import db, User
from werkzeug.security import check_password_hash

print("Testing Authentication System...")

with app.app_context():
    # 1. Verify DB Creation
    print("[1] Checking Database...")
    db.create_all()
    print("Database tables verified.")

    # 2. Verify Admin Creation
    print("\n[2] Verifying Admin User...")
    admin = User.query.filter_by(email='admin@college.edu').first()
    if admin:
        print(f"Admin found: {admin.email}")
        if check_password_hash(admin.password, 'admin123'):
            print("Admin password hash matches 'admin123'.")
        else:
            print("FAILURE: Admin password mismatch.")
    else:
        print("FAILURE: Admin user not found.")

print("\nAuthentication Test Complete.")
