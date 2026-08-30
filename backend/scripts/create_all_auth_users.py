"""
Create Supabase Auth accounts for all seed users and link them to the users table.
Run once after the SQL migration.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

admin = create_client(SUPABASE_URL, SERVICE_KEY)

# All users to create (email, password, display_name)
USERS = [
    ("admin@railmadat.in", "admin123", "Admin User"),
    ("inspector1@railmadat.in", "inspector123", "Rajesh Kumar"),
    ("inspector2@railmadat.in", "inspector123", "Priya Sharma"),
    ("manager.signal@railmaintain.in", "manager123", "Jane Smith"),
    ("manager.track@railmaintain.in", "manager123", "John Doe"),
    ("staff1.signal@railmaintain.in", "staff123", "Amit Patel"),
    ("staff1.track@railmaintain.in", "staff123", "Suresh Yadav"),
    ("reporter1@railmaintain.in", "reporter123", "Vikram Singh"),
    ("reporter2@railmaintain.in", "reporter123", "Anita Desai"),
    # The local admin already exists
    ("admin@railmaintain.local", "123", "System Administrator"),
]


def main():
    for email, password, name in USERS:
        print(f"\n--- {email} ---")

        # Check if auth user already exists by trying to list users
        try:
            # Try to create the user
            result = admin.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
            })
            auth_user_id = result.user.id
            print(f"  Created auth user: {auth_user_id}")
        except Exception as e:
            if "already been registered" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  Auth user already exists, finding ID...")

                # List users and find by email
                try:
                    users_list = admin.auth.admin.list_users()
                    auth_user_id = None
                    for u in users_list:
                        if hasattr(u, 'email') and u.email == email:
                            auth_user_id = u.id
                            break
                    if auth_user_id:
                        print(f"  Found auth user ID: {auth_user_id}")
                    else:
                        print(f"  ERROR: Could not find auth user for {email}")
                        continue
                except Exception as e2:
                    print(f"  ERROR listing users: {e2}")
                    continue
            else:
                print(f"  ERROR creating user: {e}")
                continue

        # Link supabase_user_id in the users table
        try:
            result = admin.table("users").update(
                {"supabase_user_id": auth_user_id}
            ).eq("email", email).execute()

            if result.data:
                print(f"  Linked to users table: {result.data[0].get('id', 'ok')}")
            else:
                print(f"  WARNING: No row updated in users table for {email}")
        except Exception as e:
            print(f"  ERROR linking to users table: {e}")

    print("\n\n=== SUMMARY ===")
    print("All auth users created/linked.")
    print("\nLogin credentials:")
    print("=" * 60)
    for email, password, name in USERS:
        print(f"  {email:40s} / {password}")
    print("=" * 60)


if __name__ == "__main__":
    main()
