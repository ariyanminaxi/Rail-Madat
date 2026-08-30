"""
RailMaintain — Create Administrator Script

One-time script to create an Administrator account.

WHY A SEPARATE SCRIPT (not an API endpoint):
Creating a user directly requires Supabase's ADMIN API, which needs the
SERVICE ROLE KEY — a secret that can bypass all access rules. That key
must never be loaded into main.py or shipped to a running server; it
should only ever be used locally, by a human, on purpose.

WHAT IT DOES:
  1. Creates a user in Supabase's auth.users table (email + password),
     pre-confirmed so no email-verification step blocks login.
  2. Inserts a matching row in our `profiles` table with the SAME id
     (UUID) and role="Administrator".

USAGE:
  1. Set environment variables SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
     ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_DISPLAY_NAME.
  2. Run: python scripts/create_admin.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@railmaintain.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_DISPLAY_NAME = os.environ.get("ADMIN_DISPLAY_NAME", "System Administrator")


def main():
    """Create the administrator user in Supabase and the profiles table."""

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)

    if not ADMIN_PASSWORD:
        print("ERROR: ADMIN_PASSWORD must be set.")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase")
        sys.exit(1)

    print(f"Connecting to Supabase: {SUPABASE_URL}")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Step 1: Create user in Supabase Auth
    print(f"Creating user: {ADMIN_EMAIL}")
    user_id = None
    try:
        auth_response = client.auth.admin.create_user({
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,  # Skip email verification
        })
        user_id = auth_response.user.id
        print(f"  User created: {user_id}")
    except Exception as exc:
        print(f"  WARNING: User creation may have failed: {exc}")
        print("  The user might already exist. Trying to find existing user...")
        # Try to find the existing user by listing users
        try:
            users = client.auth.admin.list_users()
            for u in users:
                if u.email == ADMIN_EMAIL:
                    user_id = u.id
                    print(f"  Found existing user: {user_id}")
                    break
        except Exception:
            pass

    # Step 2: Link supabase_user_id to existing profile or insert new one
    print(f"Linking auth user to profile...")
    try:
        # Check if profile already exists by email
        existing = client.table("users").select("id").eq("email", ADMIN_EMAIL).execute()
        if existing.data:
            # Update existing profile with supabase_user_id
            client.table("users").update({
                "supabase_user_id": user_id,
            }).eq("email", ADMIN_EMAIL).execute()
            print(f"  Linked existing profile to auth user {user_id}")
        else:
            # Insert new profile
            client.table("users").insert({
                "id": user_id,
                "supabase_user_id": user_id,
                "email": ADMIN_EMAIL,
                "full_name": ADMIN_DISPLAY_NAME,
                "role": "Administrator",
                "is_active": True,
            }).execute()
            print("  Profile created successfully.")
    except Exception as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    print("\nAdministrator account created successfully.")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Role:  Administrator")
    print(f"  UUID:  {user_id}")


if __name__ == "__main__":
    main()
