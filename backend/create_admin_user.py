"""
Script to create the initial admin user.

Usage:
    python create_admin_user.py

This will create an admin user with:
    Username: admin
    Password: admin123  (CHANGE THIS IN PRODUCTION!)
    Email: admin@fuelslogistics.com
    Role: ADMIN
"""

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.auth import get_password_hash

def create_admin():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("❌ Admin user already exists!")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@fuelslogistics.com",
            full_name="System Administrator",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print("\n⚠️  IMPORTANT: Change the default password (admin123) after first login!")

        # Also create a demo operator user
        operator_user = User(
            username="coordinator",
            email="coordinator@fuelslogistics.com",
            full_name="Demo Coordinator",
            password_hash=get_password_hash("fuel2024"),
            role=UserRole.OPERATOR,
            is_active=True
        )

        db.add(operator_user)
        db.commit()
        db.refresh(operator_user)

        print("\n✅ Demo operator user created successfully!")
        print(f"   Username: {operator_user.username}")
        print(f"   Email: {operator_user.email}")
        print(f"   Role: {operator_user.role.value}")

    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
